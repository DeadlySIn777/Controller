"""Adversarial offline appliance staging and startup/recovery contract checks."""
from copy import deepcopy
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import tarfile
import tempfile
import unittest
import xml.etree.ElementTree as ET
from unittest.mock import patch
import uuid

from controller_config.model import ConfigurationError
from controller_config.service import canonical, digest
from controller_config.setup_service import SetupService, example_draft
from controller_os import image
from controller_os.preflight import preflight, recovery, settings_status
from controller_os.__main__ import main
from controller_os.lifecycle import boot_recipe, kiosk_recovery, lifecycle_contract

ROOT=Path(__file__).resolve().parents[1]


class ControllerOSTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.directory=Path(self.temp.name);self.output=self.directory/"candidate"
        self.workspace=self.directory/"machine"

    def build(self,output=None):
        return image.stage(ROOT,output or self.output,allow_development=True,release_id="test-r1")

    def verify(self):
        return image.verify_image(self.output/"rootfs",allow_development=True,exact_overlay=True)

    def refuse(self,code,callback):
        with self.assertRaises(ConfigurationError) as caught:callback()
        self.assertEqual(caught.exception.code,code)

    def rewrite_manifest(self,change):
        path=self.output/"rootfs"/image.MANIFEST
        value=json.loads(path.read_text());change(value)
        value.pop("manifest_sha256");value["manifest_sha256"]=digest(value)
        path.write_bytes(canonical(value)+b"\n")

    def test_opt_in_and_all_physical_compute_profiles_refuse_before_output(self):
        self.refuse("OS_DEVELOPMENT_OPT_IN",lambda:image.stage(ROOT,self.output))
        for row in image.profiles():
            if row["id"]!=image.DEV_PROFILE:
                with self.subTest(profile=row["id"]):
                    self.assertFalse(row["production_approved"])
                    self.refuse("OS_PROFILE_UNQUALIFIED",lambda:image.stage(ROOT,self.output,profile=row["id"],allow_development=True))
        self.assertFalse(self.output.exists())

    def test_deterministic_archive_complete_assets_no_settings_or_secrets(self):
        first=self.build();second=image.stage(ROOT,self.directory/"second",allow_development=True,release_id="test-r1")
        self.assertEqual(first["overlay_sha256"],second["overlay_sha256"])
        self.assertEqual(first["manifest_sha256"],second["manifest_sha256"])
        manifest=self.verify()
        self.assertIn("controller_shell/web/index.html",manifest["source_sha256"])
        self.assertIn("controller_config/web/setup.js",manifest["source_sha256"])
        self.assertIn("controller_lab/__init__.py",manifest["source_sha256"])
        self.assertIn("controller_appliance/service.py",manifest["source_sha256"])
        self.assertIn("controller_os/assets/motion-x12.svg",manifest["source_sha256"])
        self.assertNotIn("controller_lab/run_scenarios.py",manifest["source_sha256"])
        with tarfile.open(self.output/"controller-overlay.tar") as archive:
            members=archive.getmembers()
            self.assertTrue(all(m.isfile() and m.mtime==0 and m.uid==m.gid==0 and m.mode==0o644 for m in members))
            self.assertEqual(len(members),len(manifest["entries"])+1)
            self.assertTrue(all("/var/lib/" not in "/"+m.name and "budget.json" not in m.name and "setup.json" not in m.name for m in members))
        self.assertFalse(first["services_installed_or_enabled"])
        self.assertFalse(first["bootable_image_qualified"])
        self.assertFalse(first["signed_release"])

    def test_existing_destination_preserved(self):
        self.output.mkdir();file=self.output/"customer-file";file.write_bytes(b"preserve")
        self.refuse("OS_OUTPUT_EXISTS",self.build)
        self.assertEqual(file.read_bytes(),b"preserve")
        self.assertEqual(list(self.output.iterdir()),[file])

    def test_stale_or_resealed_source_closure_and_unlisted_files_rejected(self):
        self.build();target=self.output/"rootfs"/image.APP/"controller_shell/server.py"
        target.write_bytes(target.read_bytes()+b"\n# changed after publication\n")
        self.refuse("OS_SOURCE_CLOSURE",self.verify)
        # A valid self-checksum may not omit a still-installed dependency.
        self.rewrite_manifest(lambda m:m["source_sha256"].pop("controller_shell/server.py"))
        self.refuse("OS_SOURCE_CLOSURE",self.verify)

    def test_resealed_service_command_cannot_bypass_generated_contract(self):
        self.build();name="etc/systemd/system/controller-shell.service"
        target=self.output/"rootfs"/name;body=target.read_bytes().replace(b"--port 8769",b"--port 9999");target.write_bytes(body)
        def reseal(m):m["entries"][name]["sha256"]=hashlib.sha256(body).hexdigest()
        self.rewrite_manifest(reseal)
        self.refuse("OS_INTEGRITY",self.verify)

    def test_resealed_authority_profile_and_numeric_types_rejected(self):
        for field,value in (("motion_authorized",True),("outputs_inhibited",False),("physical_authority",True),("signed_release",True),("schema_version",True)):
            output=self.directory/field;self.build(output);old=self.output;self.output=output
            self.rewrite_manifest(lambda m:m.__setitem__(field,value))
            self.refuse("OS_MANIFEST" if field=="schema_version" else "OS_AUTHORITY",self.verify);self.output=old
        output=self.directory/"wrong-profile";self.build(output);self.output=output
        self.rewrite_manifest(lambda m:m["definition"].__setitem__("profile_id","cm5-emmc"))
        self.refuse("OS_MANIFEST",self.verify)

    def test_added_files_or_missing_assets_and_duplicate_json_refused(self):
        self.build();root=self.output/"rootfs";extra=root/"usr/extra.py";extra.write_text("pass\n")
        self.refuse("OS_SOURCE_CLOSURE",self.verify);extra.unlink()
        asset=root/image.APP/"controller_shell/web/index.html";asset.unlink()
        self.refuse("OS_SOURCE",self.verify)
        path=root/image.MANIFEST;path.write_text('{"schema_version":1,"schema_version":1}')
        self.refuse("OS_MANIFEST",self.verify)

    def test_unsafe_manifest_paths_rejected(self):
        self.build()
        for name in ("../escape", "/etc/passwd", "usr//manifest.json", "C:/windows", "usr\\manifest"):
            with self.subTest(path=name):
                self.refuse("OS_PATH",lambda:image.verify_image(self.output/"rootfs",manifest_path=name,allow_development=True))

    def test_nonregular_manifest_refused_before_read(self):
        self.build();path=self.output/"rootfs"/image.MANIFEST
        path.unlink();path.mkdir()
        self.refuse("OS_FILE",self.verify)

    def test_missing_settings_readiness_does_not_initialize_any_workspace(self):
        result=settings_status(self.workspace)
        self.assertFalse(result["initialized"])
        self.assertFalse(result["settings_written"])
        self.assertFalse(self.workspace.exists())
        self.assertFalse(result["readiness"]["physical_commissioning_complete"])

    def test_valid_saved_settings_binding_and_recovery_preserve_exact_bytes(self):
        self.build();self.workspace.mkdir();service=SetupService(self.workspace/"setup.json")
        service.initialize();service.save_draft(example_draft("sim-machine-12motor"),0)
        service.commit(service.preview(),str(uuid.uuid4()))
        before=service.path.read_bytes();result=recovery(self.output/"rootfs",self.workspace,allow_development=True)
        self.assertEqual(result["checks"]["settings"]["configuration_binding"]["generation"],1)
        self.assertEqual(service.path.read_bytes(),before)
        self.assertFalse(result["automatic_restore"]);self.assertFalse(result["physical_machine_start_allowed"])
        self.assertEqual(set(self.workspace.iterdir()),{service.path,Path(str(service.path)+".setup.lock")})

    def test_existing_store_preflight_never_opens_export_write_lock(self):
        self.build();self.workspace.mkdir();service=SetupService(self.workspace/"setup.json")
        service.initialize();service.save_draft(example_draft("sim-machine-12motor"),0)
        service.commit(service.preview(),str(uuid.uuid4()))
        lock=Path(str(service.path)+".setup.lock");lock.unlink()
        before=service.path.read_bytes()
        host={"os":"Linux","architecture":"x86_64","python":[3,11,0],"kernel_release":"authored readonly contract fixture"}
        with patch("controller_os.preflight.observed_host",return_value=host),patch.object(SetupService,"backup_snapshot",side_effect=AssertionError("startup must not acquire RW export lock")):
            result=preflight(self.output/"rootfs",self.workspace,allow_development=True)
        self.assertEqual(result["settings"]["configuration_binding"]["generation"],1)
        self.assertEqual(result["settings"]["readiness"]["configuration_binding"],result["settings"]["configuration_binding"])
        self.assertEqual(service.path.read_bytes(),before);self.assertFalse(lock.exists())

    def test_readiness_generation_conflict_refused(self):
        with patch("controller_os.preflight.ReadinessService.status",return_value={"configuration_binding":{"foreign":"generation"}}):
            self.refuse("OS_SETTINGS_CHANGED",lambda:settings_status(self.workspace))
        self.assertFalse(self.workspace.exists())

    def test_corrupt_settings_and_image_report_recovery_without_repair(self):
        self.build();self.workspace.mkdir();file=self.workspace/"setup.json";file.write_bytes(b"broken preserve")
        target=self.output/"rootfs"/image.APP/"controller_shell/server.py";target.write_text("broken image")
        result=recovery(self.output/"rootfs",self.workspace,allow_development=True)
        self.assertEqual(result["checks"]["image"]["status"],"BLOCKED")
        self.assertEqual(result["checks"]["settings"]["status"],"BLOCKED")
        self.assertEqual(file.read_bytes(),b"broken preserve")
        self.assertFalse(result["settings_written"]);self.assertFalse(result["motion_authorized"])

    def test_startup_exact_host_guard_and_settings_are_read_only(self):
        self.build();host={"os":"Linux","architecture":"x86_64","python":[3,11,0],"kernel_release":"authored test fixture"}
        with patch("controller_os.preflight.observed_host",return_value=host):
            result=preflight(self.output/"rootfs",self.workspace,allow_development=True)
            self.assertEqual(result["status"],"DEVELOPMENT_SHELL_START_ALLOWED")
            self.assertFalse(result["kernel_realtime_qualified"]);self.assertFalse(self.workspace.exists())
        for changed in ({**host,"os":"Windows"},{**host,"architecture":"aarch64"},{**host,"python":[3,10,9]}):
            with patch("controller_os.preflight.observed_host",return_value=changed):
                self.refuse("OS_HOST_PROFILE",lambda:preflight(self.output/"rootfs",self.workspace,allow_development=True))

    def test_units_separate_kiosk_recovery_and_limit_privileges(self):
        units={name:body.decode() for name,body in image.unit_files().items()}
        shell=units["etc/systemd/system/controller-shell.service"]
        self.assertIn("Requires=controller-preflight.service",shell)
        for guard in ("PrivateDevices=yes","NoNewPrivileges=yes","ProtectSystem=strict","IPAddressDeny=any","IPAddressAllow=localhost"):
            self.assertIn(guard,shell)
        self.assertIn("Conflicts=controller-shell.service",units["etc/systemd/system/controller-recovery.target"])
        self.assertNotIn("--no-sandbox",units["etc/systemd/user/controller-kiosk.service"])
        self.assertIn("http://127.0.0.1:8769/launch",units["etc/systemd/user/controller-kiosk.service"])
        self.assertNotIn("WantedBy",shell)

    def test_kiosk_failure_graph_has_no_application_or_runtime_control(self):
        units={name:body.decode() for name,body in image.unit_files().items()}
        # Follow all staged failure/require edges from the browser, rather than
        # assuming separation because a unit happens to be under user/.
        pending=["controller-kiosk.service"];seen=set()
        while pending:
            name=pending.pop()
            if name in seen:continue
            seen.add(name);body=units["etc/systemd/user/"+name]
            self.assertNotIn("--no-sandbox",body)
            for line in body.splitlines():
                if line.startswith(("OnFailure=","Requires=","Wants=","PartOf=","BindsTo=","Conflicts=")):
                    for dependency in line.split("=",1)[1].split():
                        self.assertTrue(dependency.startswith("controller-kiosk"),dependency)
                        pending.append(dependency)
                if line.startswith("Exec"):
                    self.assertNotIn("systemctl",line);self.assertNotIn("controller_shell",line)
                    self.assertNotIn("cnc3",line);self.assertNotIn("kill",line)
        self.assertEqual(seen,{"controller-kiosk.service","controller-kiosk-recovery.target","controller-kiosk-recovery.service"})

    def test_kiosk_and_application_have_total_budget_with_deliberate_recovery(self):
        units={name:body.decode() for name,body in image.unit_files().items()}
        for name in ("etc/systemd/user/controller-kiosk.service","etc/systemd/system/controller-shell.service"):
            body=units[name];self.assertIn("StartLimitIntervalSec=infinity",body)
            self.assertIn("StartLimitBurst=3",body);self.assertIn("RestartSec=3",body)
            self.assertIn("StartLimitAction=none",body)
            self.assertNotIn("OnFailureJobMode=isolate",body)
        report=kiosk_recovery(allow_development=True)
        self.assertEqual(report["application_status"],"NOT_OBSERVED")
        self.assertIsNone(report["outputs_inhibited"]);self.assertFalse(report["output_state_observed"])
        self.assertFalse(report["recovery_grants_output_authority"])
        for field in ("automatic_browser_restart","application_restarted","runtime_signalled","settings_read","settings_written","motion_authorized"):
            self.assertIs(report[field],False)
        runtime=lifecycle_contract()["runtime"]
        self.assertIsNone(runtime["unit"]);self.assertFalse(runtime["lifecycle_implemented"])

    def test_every_application_start_rechecks_image_and_settings_after_prior_success(self):
        self.build();self.workspace.mkdir();service=SetupService(self.workspace/"setup.json")
        service.initialize();service.save_draft(example_draft("sim-machine-12motor"),0)
        service.commit(service.preview(),str(uuid.uuid4()))
        host={"os":"Linux","architecture":"x86_64","python":[3,11,0],"kernel_release":"authored fixture"}
        with patch("controller_os.preflight.observed_host",return_value=host):
            self.assertEqual(preflight(self.output/"rootfs",self.workspace,allow_development=True)["status"],"DEVELOPMENT_SHELL_START_ALLOWED")
            original=service.path.read_bytes();service.path.write_bytes(b"corrupted after first startup")
            with self.assertRaises(ConfigurationError):preflight(self.output/"rootfs",self.workspace,allow_development=True)
            self.assertEqual(service.path.read_bytes(),b"corrupted after first startup")
            service.path.write_bytes(original)
            target=self.output/"rootfs"/image.APP/"controller_shell/server.py"
            target.write_bytes(target.read_bytes()+b"\n# stale after first startup\n")
            self.refuse("OS_SOURCE_CLOSURE",lambda:preflight(self.output/"rootfs",self.workspace,allow_development=True))
        units={name:body.decode() for name,body in image.unit_files().items()}
        pre=next(line[10:] for line in units["etc/systemd/system/controller-preflight.service"].splitlines() if line.startswith("ExecStart="))
        launches=[line[13:] for line in units["etc/systemd/system/controller-shell.service"].splitlines() if line.startswith("ExecStartPre=")]
        self.assertEqual(launches,[pre]);self.assertFalse(launches[0].startswith("-"))

    def test_resealed_browser_sandbox_bypass_and_retry_loop_refused(self):
        self.build();name="etc/systemd/user/controller-kiosk.service"
        target=self.output/"rootfs"/name
        for old,new in ((b"--kiosk",b"--kiosk --no-sandbox"),(b"StartLimitBurst=3",b"StartLimitBurst=999")):
            original=target.read_bytes();body=original.replace(old,new);target.write_bytes(body)
            self.rewrite_manifest(lambda m:m["entries"][name].update(sha256=hashlib.sha256(body).hexdigest(),bytes=len(body)))
            self.refuse("OS_INTEGRITY",self.verify);target.write_bytes(original)

    def test_brand_assets_are_local_inert_and_bound_to_boot_plan(self):
        self.build();manifest=self.verify();root=self.output/"rootfs"
        svg=root/"usr/share/controller/branding/motion-x12.svg";tree=ET.fromstring(svg.read_bytes())
        self.assertEqual(tree.tag,"{http://www.w3.org/2000/svg}svg")
        self.assertIn("Motion X12",svg.read_text());self.assertIn("GarciaMech",svg.read_text())
        self.assertNotIn("script",svg.read_text());self.assertNotIn("http://",svg.read_text().replace("http://www.w3.org/2000/svg",""))
        page=(root/"usr/share/controller/branding/kiosk-recovery.html").read_text()
        self.assertNotIn("<script",page);self.assertNotIn("<form",page);self.assertNotIn("fetch(",page)
        plan=json.loads((root/"usr/share/controller/boot-plan.json").read_text())
        self.assertEqual(plan,boot_recipe(allow_development=True))
        self.assertIn("usr/share/controller/branding/motion-x12.svg",manifest["entries"])
        self.assertFalse(any(name.startswith(("boot/","dev/")) for name in manifest["entries"]))

    def test_boot_recipe_never_fakes_partitions_image_or_speed(self):
        plan=boot_recipe(allow_development=True)
        self.assertFalse(plan["kernel_arguments_applied"]);self.assertIsNone(plan["bootloader_file"])
        self.assertIsNone(plan["performance"]["usable_ui_seconds"])
        self.assertFalse(plan["performance"]["five_to_ten_second_boot_qualified"])
        self.assertEqual(plan["updates"]["status"],"UNAVAILABLE")
        for field in ("update_partition","recovery_partition","slot_count"):self.assertIsNone(plan["updates"][field])
        self.assertFalse(plan["splash_renderer"]["theme_activated"])
        self.refuse("OS_DEVELOPMENT_OPT_IN",boot_recipe)
        self.refuse("OS_PROFILE_UNQUALIFIED",lambda:boot_recipe("cm5-emmc",allow_development=True))

    def test_hard_link_source_and_settings_refused_without_mutation(self):
        self.workspace.mkdir();file=self.workspace/"setup.json";file.write_bytes(b"retained")
        linked=self.workspace/"retained-original";os.link(file,linked)
        self.refuse("OS_FILE",lambda:settings_status(self.workspace))
        self.assertEqual(linked.read_bytes(),b"retained")

    def test_structured_cli_profiles_and_failure_contract(self):
        with patch("sys.stdout",new_callable=io.StringIO) as output:
            self.assertEqual(main(["profiles"]),0)
            self.assertFalse(json.loads(output.getvalue())["result"]["physical_authority"])
        with patch("sys.stdout",new_callable=io.StringIO) as output:
            self.assertEqual(main(["stage","--source-root",str(ROOT),"--output",str(self.output)]),1)
            self.assertEqual(json.loads(output.getvalue())["error"]["code"],"OS_DEVELOPMENT_OPT_IN")

    def test_public_boot_and_kiosk_recovery_cli_require_opt_in_and_report_unknowns(self):
        for command in ("boot-plan","kiosk-recovery"):
            with patch("sys.stdout",new_callable=io.StringIO) as output:
                self.assertEqual(main([command]),1)
                self.assertEqual(json.loads(output.getvalue())["error"]["code"],"OS_DEVELOPMENT_OPT_IN")
            with patch("sys.stdout",new_callable=io.StringIO) as output:
                self.assertEqual(main([command,"--allow-development"]),0)
                result=json.loads(output.getvalue())["result"]
                self.assertFalse(result["motion_authorized"]);self.assertFalse(result["physical_authority"])
                if command=="kiosk-recovery":self.assertIsNone(result["outputs_inhibited"])
                else:self.assertIsNone(result["updates"]["recovery_partition"])
        self.assertFalse(self.workspace.exists())


if __name__=="__main__":unittest.main()
