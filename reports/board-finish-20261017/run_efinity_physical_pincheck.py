"""Execute real Efinity135-pin/package/bank checks without a functional bitstream.

This is an interface-only check. Complete motherboard RTL binding, industrial
speed4 implementation, external delays, fit and timing remain independent gates.
"""
import ast
import ctypes
from ctypes import wintypes
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import traceback
sys.dont_write_bytecode = True
for name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[name] = "2"
kernel = ctypes.windll.kernel32
kernel.GetCurrentProcess.restype = wintypes.HANDLE
kernel.SetProcessAffinityMask.argtypes = (wintypes.HANDLE, ctypes.c_size_t)
kernel.SetPriorityClass.argtypes = (wintypes.HANDLE, wintypes.DWORD)
assert kernel.SetProcessAffinityMask(kernel.GetCurrentProcess(), sum(1 << i for i in range(16, 28)))
assert kernel.SetPriorityClass(kernel.GetCurrentProcess(), 0x4000)

H = Path(__file__).resolve().parent
OUT = H / "efinity-native-pincheck-r1"
ISF = H / "release-review/vendor-constraints-r1/R299-T20F256-physical-pin-voltage.isf"
INSTALL = Path("C:/Efinity/2026.1")


def sha(p):
    with Path(p).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def put(name, data):
    (OUT / name).write_text(json.dumps(data, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def main():
    assert not OUT.exists()
    assert sha(ISF) == "7b19f9cccb9d3e4b1dbf327aaaefb4d51b0cb69dfcfdbae5fdcb95a81e6cef93"
    OUT.mkdir()
    started = time.monotonic()
    assert os.environ["EFINITY_HOME"].replace("\\", "/").rstrip("/") == INSTALL.as_posix()
    sys.path.insert(0, str(INSTALL / "pt/bin"))
    from api_service.design import DesignAPI
    pins = {str(p): sha(p) for p in (Path(__file__), ISF, INSTALL / "bin/efx_run.bat",
            INSTALL / "pt/bin/api_service/design.py", INSTALL / "doc/pdf/efinity-python-api.pdf")}
    expected, expected_banks = {}, {}
    tree = ast.parse(ISF.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "assign_pkg_pin":
                port, ball = [ast.literal_eval(arg) for arg in node.args]
                assert port not in expected
                expected[port] = ball
            elif node.func.attr == "set_iobank_voltage":
                bank, voltage = [ast.literal_eval(arg) for arg in node.args]
                expected_banks[bank] = voltage
    assert len(expected) == 135 and len(set(expected.values())) == 135 and len(expected_banks) == 7
    design = DesignAPI(is_verbose=True)
    design.create("controller_is2_R299_pincheck", "T20F256", path=str(OUT), auto_save=False, overwrite=False)
    put("status.json", {"phase": "OFFICIAL_VENDOR_INTERFACE_IMPORT_RUNNING", "bitstream": False})
    imported, import_issues = design.import_design(str(ISF), gen_issue_csv=True, path=str(OUT))
    put("import-result.json", {"imported": bool(imported), "issues": [str(issue) for issue in import_issues]})
    design.save_as(str(OUT / "controller_is2_R299_pincheck.peri.xml"), overwrite=False)
    names = design.get_all_gpio_name()
    observed = {name: {"package_pin": design.get_pkg_pin(name), "IO_STANDARD": design.get_property(name, "IO_STANDARD")}
                for name in names}
    bank_voltages = design.get_iobank_voltage()
    put("actual-vendor-GPIO-pins-standards.json", observed)
    put("actual-vendor-bank-voltages.json", bank_voltages)
    errors = [{"port": name, "expected": ball, "observed": observed.get(name)} for name, ball in expected.items()
              if observed.get(name, {}).get("package_pin") != ball]
    extras = sorted(set(observed) - set(expected))
    bank_errors = [{"bank": name, "expected": voltage, "observed": bank_voltages.get(name)}
                   for name, voltage in expected_banks.items() if str(bank_voltages.get(name)) != voltage]
    checked = design.check_design()
    issues = design.get_design_check_issue()
    put("vendor-design-check.json", {"PASS": bool(checked), "issues": [str(issue) for issue in issues]})
    design.export_design(isf_file=str(OUT / "actual-vendor-export.isf"), export_all_pin=True)
    generated = False
    if imported and checked and not errors and not extras and not bank_errors:
        design.generate(False, outdir=str(OUT / "generated"))
        generated = True
    assert all(sha(Path(path)) == digest for path, digest in pins.items())
    passed = imported and checked and not errors and not extras and not bank_errors
    put("receipt.json", {"status": "VENDOR_PHYSICAL_PIN_BANK_INTERFACE_CHECK_PASS_FULL_DESIGN_FIT_TIMING_OPEN" if passed else "VENDOR_INTERFACE_DIAGNOSTIC_REPAIR_REQUIRED",
            "utc": dt.datetime.now(dt.timezone.utc).isoformat(), "installed_release": "2026.1.132", "target_fitted_MPN": "T20F256I4",
            "interface_package": "T20F256", "interface_imported": bool(imported), "vendor_design_check_passed": bool(checked),
            "135_package_pin_matches": not errors and not extras, "observed_GPIO_count": len(observed),
            "package_pin_errors": errors, "unexpected_GPIO": extras, "bank_voltage_errors": bank_errors,
            "constraints_generated_without_bitstream": generated, "complete_runtime_RTL_binding": "OPEN",
            "I4_device_fit_place_route_and_static_timing": "UNEXECUTED", "external_delays_CDC_reset_drive_slew_unused_pin_defaults": "OPEN",
            "bitstream_generated": False, "hardware_connected_or_programmed": False, "input_SHA256": pins,
            "inputs_unchanged": True, "elapsed_seconds": time.monotonic() - started, "adopted": False, "manufacturing_ready": False})
    print(f"Vendor135-pin check complete: import={imported}, design_check={checked}, package_errors={len(errors)}, bank_errors={len(bank_errors)}", flush=True)


if __name__ == "__main__":
    try:
        main()
    except BaseException as error:
        if OUT.is_dir():
            put("failure.json", {"status": "VENDOR_RUN_FAILED_RESULTS_RETAINED", "type": type(error).__name__, "error": str(error)})
            (OUT / "traceback.txt").write_text(traceback.format_exc(), encoding="utf-8")
        raise
