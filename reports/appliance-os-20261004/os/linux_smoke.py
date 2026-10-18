"""Actual unprivileged Linux preflight and loopback HTTP from staged app files."""
import argparse
import hashlib
import http.client
import json
import os
from pathlib import Path
import re
import threading

from controller_config.setup_service import SetupService
from controller_os.preflight import preflight
from controller_os.image import _read
from controller_os.lifecycle import kiosk_recovery,boot_recipe
from controller_config.model import ConfigurationError
from controller_shell.server import make_server


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--root",type=Path,required=True);parser.add_argument("--workspace",type=Path,required=True);args=parser.parse_args()
    checks=[]
    def check(value,name):
        checks.append({"check":name,"passed":bool(value)})
        if not value:raise AssertionError(name)
    check(os.geteuid()!=0,"actual_nonroot_process")
    file=args.workspace/"setup.json";before=file.read_bytes();names=sorted(p.name for p in args.workspace.iterdir())
    check(args.workspace.stat().st_mode&0o222==0 and file.stat().st_mode&0o222==0,"actual_readonly_directory_and_settings")
    denied=False
    try:SetupService(file).backup_snapshot()
    except PermissionError:denied=True
    check(denied,"RW_export_lock_negative_control_denied")
    rejected=False
    try:_read(args.workspace.parent/"nonregular","fifo")
    except ConfigurationError as error:rejected=error.code=="OS_FILE"
    check(rejected,"actual_FIFO_refused_without_blocking")
    result=preflight(args.root,args.workspace,allow_development=True)
    check(result["status"]=="DEVELOPMENT_SHELL_START_ALLOWED","actual_linux_startup_preflight")
    check(result["settings"]["configuration_binding"]["generation"]==1,"existing_saved_generation_read_without_write_lock")
    report=kiosk_recovery(allow_development=True)
    check(report["outputs_inhibited"] is None and not report["output_state_observed"] and not report["settings_read"] and not report["runtime_signalled"],"kiosk_recovery_reports_unknown_runtime_without_actions")
    plan=boot_recipe(allow_development=True)
    check(not plan["kernel_arguments_applied"] and plan["updates"]["recovery_partition"] is None and plan["performance"]["usable_ui_seconds"] is None,"staged_boot_recipe_remains_unapplied_unmeasured")
    server=make_server(args.workspace,0);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    def get(path,headers=None):
        connection=http.client.HTTPConnection("127.0.0.1",server.server_port,timeout=3)
        connection.request("GET",path,headers=headers or {})
        response=connection.getresponse();body=response.read();status=response.status;fields=dict(response.getheaders());connection.close()
        return status,fields,body
    try:
        status,headers,body=get("/");check(status==200 and b"motion x12" in body.lower(),"staged_shell_home_http")
        check("frame-ancestors 'none'" in headers["Content-Security-Policy"],"original_CSP_retained")
        match=re.search(rb'<meta name="setup-token" content="([A-Za-z0-9_-]+)">',body);check(match is not None,"original_session_token_retained")
        token={"X-Setup-Token":match.group(1).decode()}
        status,_,body=get("/api/context",token);context=json.loads(body)
        check(status==200 and context["result"]["setup"]["generation"]==1,"staged_shared_service_reads_same_generation")
        check(context["result"]["simulation_only"] and not context["result"]["paid_ai_enabled"],"no_machine_or_paid_provider_authority")
        status,_,_=get("/workbench?view=readiness");check(status==200,"staged_original_workbench_http")
        status,_,_=get("/api/context");check(status==403,"missing_token_refused")
        status,_,_=get("/",{"Host":"foreign.invalid"});check(status==403,"foreign_host_refused")
    finally:server.shutdown();server.server_close();thread.join(5)
    check(file.read_bytes()==before and sorted(p.name for p in args.workspace.iterdir())==names,"settings_and_directory_bytes_unchanged")
    print(json.dumps({"status":"PASS","checks":checks,"euid":os.geteuid(),"preflight":result,
        "settings_sha256":hashlib.sha256(before).hexdigest(),"actual_physical_boot":False,"services_installed_or_enabled":False,
        "desktop_or_network_config_modified":False,"paid_api_calls":0,"physical_device_connections":0}),flush=True)

if __name__=="__main__":main()
