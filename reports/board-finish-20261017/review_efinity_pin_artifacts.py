"""Independently compare the generated native pin CSV/XML to the frozen ISF."""
import ast
import collections
import csv
import hashlib
import io
import json
from pathlib import Path
import xml.etree.ElementTree as ET

H = Path(__file__).resolve().parent
RUN = H / "efinity-native-pincheck-r1"
OUT = H / "efinity-native-pincheck-review-r1"
ISF = H / "release-review/vendor-constraints-r1/R299-T20F256-physical-pin-voltage.isf"


def sha(p):
    with Path(p).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    assert not OUT.exists()
    expected, modes, clocks = {}, {}, set()
    for node in ast.walk(ast.parse(ISF.read_text(encoding="utf-8"))):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        name = node.func.attr
        args = [ast.literal_eval(arg) for arg in node.args]
        if name == "assign_pkg_pin":
            expected[args[0]] = args[1]
        if name in ("create_input_gpio", "create_output_gpio", "create_input_clock_gpio"):
            modes[args[0]] = "output" if name == "create_output_gpio" else "input"
        if name == "create_input_clock_gpio":
            clocks.add(args[0])
    assert set(expected) == set(modes) and len(expected) == 135
    csvfile = RUN / "generated/controller_is2_R299_pincheck.pinout.csv"
    rows = list(csv.DictReader(io.StringIO("\n".join(line for line in csvfile.read_text().splitlines() if line.strip() and not line.startswith("#")))))
    assert len(rows) == len({r["Pin Number"] for r in rows}) == 256
    active = {r["Signal Name"]: r for r in rows if r["Signal Name"] in expected}
    assert set(active) == set(expected)
    for name, ball in expected.items():
        row = active[name]
        assert row["Pin Number"] == ball and row["Direction"].lower() == modes[name]
        assert row["I/O Bank Voltage"] == "3.3 V" and row["I/O Standard"] == "3.3 V LVTTL / LVCMOS"
    assert len({r["Bank"] for r in active.values()}) == 7
    ns = {"p": "http://www.efinixinc.com/peri_design_db"}
    peri = RUN / "controller_is2_R299_pincheck.peri.xml"
    root = ET.parse(peri).getroot()
    assert root.attrib["device_def"] == "T20F256" and root.attrib["version"] == "2026.1.132"
    gpio = {g.attrib["name"]: g for g in root.findall("p:gpio_info/p:gpio", ns)}
    assert set(gpio) == set(expected)
    for name, item in gpio.items():
        assert item.attrib["mode"] == modes[name]
        assert item.attrib["io_standard"] == "3.3 V LVTTL / LVCMOS"
    assert clocks == {"FPGA_CLK_50M"} and expected["FPGA_CLK_50M"] == "H3"
    clock = gpio["FPGA_CLK_50M"].find("p:input_config", ns)
    assert clock.attrib["conn_type"] == "gclk"
    vendor = json.loads((RUN / "receipt.json").read_bytes())
    assert vendor["interface_imported"] and vendor["vendor_design_check_passed"]
    assert not vendor["package_pin_errors"] and not vendor["bank_voltage_errors"] and not vendor["bitstream_generated"]
    OUT.mkdir()
    record = {"status": "NATIVE_PIN_CSV_XML_AND_SOURCE_ISF_EXACT_INDEPENDENT_REVIEW_PASS_PACKAGE_SCOPE_ONLY",
              "all_256_package_rows_unique": True, "assigned_pins": 135, "directions": dict(collections.Counter(modes.values())),
              "physical_source_IO_banks_3V3": 7, "all135_native_IO_standards_match": True,
              "source_clock": "FPGA_CLK_50M/H3/native GCLK", "source_ISF_SHA256": sha(ISF),
              "first_interface_run_missing_full_project_XML_warning": "RETAINED; default programming settings used, not industrial-speed timing qualification",
              "functional_RTL_physical_wrapper_device_fit_timing": "OPEN", "bitstream_or_programming": False,
              "input_SHA256": {str(p): sha(p) for p in [Path(__file__), ISF, *RUN.rglob("*")] if p.is_file()},
              "adopted": False, "manufacturing_ready": False}
    (OUT / "receipt.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": record["status"], "assigned_pins": 135, "physical_source_IO_banks_3V3": 7}))


if __name__ == "__main__":
    main()
