"""Non-actuating appliance boot/lifecycle recipes and kiosk recovery report."""
from copy import deepcopy

BRAND = {"product": "Motion X12", "publisher": "GarciaMech", "appearance": "dark_red",
         "mark": "usr/share/controller/branding/motion-x12.svg"}


def lifecycle_contract():
    return {"schema_version": 1, "kind": "motion_x12_development_lifecycle",
        "gui": {"unit": "user/controller-kiosk.service", "restart_delay_seconds": 3,
                "start_budget": 3, "budget_interval": "infinity",
                "exhausted_action": "user/controller-kiosk-recovery.target",
                "browser_sandbox_required": True, "recovery_restarts_application": False,
                "recovery_changes_runtime": False, "manual_retry_required_after_budget": True},
        "application": {"unit": "system/controller-shell.service", "fresh_preflight_each_start": True,
                        "preflight_is_machine_permission": False, "settings_preserved": True,
                        "restart_delay_seconds": 3, "start_budget": 3, "budget_interval": "infinity",
                        "exhausted_action": "system/controller-recovery.target",
                        "recovery_automatic_restore": False, "restart_restores_homing": False,
                        "restart_outputs_inhibited_required": True},
        "runtime": {"unit": None, "installed_by_overlay": False, "lifecycle_implemented": False,
                    "qualification": "Pending independent qualified runtime supervisor; no GUI/app dependency may control motion",
                    "continuity_measured": False, "physical_authority": False},
        "system_units_enabled": False, "user_units_enabled": False,
        "physical_authority": False, "motion_authorized": False}


def boot_recipe(profile="dev-x86_64-posix-v1", *, allow_development=False):
    from .image import definition
    contract = definition(profile, allow_development=allow_development)
    return {"schema_version": 1, "kind": "motion_x12_unapplied_boot_recipe",
        "profile_id": contract["profile_id"], "branding": deepcopy(BRAND),
        "status": "PENDING_EXACT_TARGET_BASE_BOOT_GRAPHICS_QUALIFICATION",
        "kernel_arguments_proposed": ["quiet", "splash", "systemd.show_status=auto"],
        "kernel_arguments_applied": False, "bootloader_file": None,
        "splash_renderer": {"candidate": "Qualified initramfs/Plymouth integration",
                            "installed": False, "theme_activated": False,
                            "asset": BRAND["mark"], "raster_conversion_and_theme_build": "Pending exact base-image renderer"},
        "diagnostics": {"journal_preserved": True, "boot_errors_hidden_by_recipe": False,
                        "failure_console_and_recovery_access": "Required in exact target integration; not disabled by this recipe",
                        "verbose_service_mode": "Omit quiet/splash in a deliberately reviewed service boot entry"},
        "performance": {"cold_boot_measured": False, "usable_ui_seconds": None,
                        "five_to_ten_second_boot_qualified": False, "graphics_frame_pacing_measured": False},
        "updates": {"status": "UNAVAILABLE", "signed_update_installer_implemented": False,
                    "update_partition": None, "recovery_partition": None, "slot_count": None,
                    "requirements": ["Exact approved compute/carrier/storage/base/kernel and bootloader",
                                     "Authenticated signed offline release and exact dependency closure",
                                     "Measured slot/recovery/update headroom and boot selection",
                                     "Interrupted update/power-loss recovery preserving settings/entitlement/calibration",
                                     "Independent inhibited unhomed restart before machine commissioning"]},
        "disk_or_partition_writes": 0, "services_enabled": False,
        "bootable_image_qualified": False, "signed_release": False,
        "physical_authority": False, "motion_authorized": False}


def kiosk_recovery(profile="dev-x86_64-posix-v1", *, allow_development=False):
    from .image import definition
    definition(profile, allow_development=allow_development)
    return {"schema_version": 1, "kind": "motion_x12_kiosk_recovery_report",
        "status": "DESKTOP_REQUIRES_DELIBERATE_RETRY", "branding": deepcopy(BRAND),
        "reason": "Kiosk failed or its bounded start budget was exhausted; inspect user-service journal",
        "application_status": "NOT_OBSERVED", "runtime_status": "NOT_OBSERVED_OR_CONTROLLED",
        "recovery_page": "usr/share/controller/branding/kiosk-recovery.html",
        "next_action": "Inspect the local application separately. Review the browser/display cause before manually resetting only the user kiosk retry budget.",
        "automatic_browser_restart": False, "application_restarted": False,
        "runtime_signalled": False, "settings_read": False, "settings_written": False,
        "homed_restored": False, "output_state_observed": False, "outputs_inhibited": None,
        "recovery_grants_output_authority": False,
        "physical_authority": False, "motion_authorized": False, "paid_api_calls": 0}
