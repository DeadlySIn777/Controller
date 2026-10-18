"""Read-only compute-module pin-source comparison; writes only this report folder.

This deliberately does not generate a schematic, runtime module profile, or
permission to power an assembled carrier. Connector facts are not qualification.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCES = HERE / "sources"
MODELS = ("cm4", "cm5", "cb1", "cb2")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(name: str, value) -> None:
    (HERE / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    inputs = {p.name: sha(p) for p in SOURCES.iterdir() if p.is_file()}
    tables = {m: json.loads((SOURCES / f"{m}-pin-table.json").read_text(encoding="utf-8")) for m in MODELS}
    manual = {m: json.loads((SOURCES / f"{m}-manual-pin-table.json").read_text(encoding="utf-8")) for m in ("cb1", "cb2")}
    # PDF text wraps pin 102's name around the row. The original text and the
    # wiki agree on the name; do not mistake its final suffix for a signal.
    manual["cb2"]["102"]["signal"] = "PCIE20_CLKREQn_M2"
    for m, t in tables.items():
        assert set(map(int, t)) == set(range(1, 201)), m
    for m, t in manual.items():
        assert set(map(int, t)) == set(range(1, 201)), m
    ground_sets = {m: {int(p) for p, row in t.items() if row["signal"] == "GND"} for m, t in tables.items()}
    assert all(v == ground_sets["cm4"] for v in ground_sets.values())
    grounds = ground_sets["cm4"]
    power = {77, 79, 81, 83, 85, 87}
    aux33, aux18 = {84, 86}, {88, 90}
    ethernet = {3, 4, 5, 6, 9, 10, 11, 12}
    hdmi = {151, 153, 170, 172, 176, 178, 182, 184, 188, 190, 199, 200}
    usb = {103, 105}
    spi = {38: "SCLK", 40: "MISO", 44: "MOSI", 54: "CS_FB candidate", 47: "CS_CMD candidate"}
    boot = {93, 101}
    sd = {57, 61, 62, 63, 67, 69}
    risk = {16, 18, 19, 35, 36, 39, 41, 64, 68, 70, 72, 73, 75, 76, 89, 92, 94, 96,
            99, 100, 104, 106, 111, 128, 130, 134, 136, 140, 142, 143, 145, 146,
            147, 148, 152, 154, 157, 159, 163, 165, 169, 171}
    assert [tables[m]["38"]["signal"] for m in MODELS] == ["GPIO11", "GPIO11", "PH6", "GPIO3_C3"]
    assert [tables[m]["40"]["signal"] for m in MODELS] == ["GPIO9", "GPIO9", "PH8", "GPIO3_C2"]
    assert [tables[m]["44"]["signal"] for m in MODELS] == ["GPIO10", "GPIO10", "PH7", "GPIO3_C1"]
    assert [tables[m]["54"]["signal"] for m in MODELS] == ["GPIO4", "GPIO4", "PC7", "GPIO3_A1"]
    assert [tables[m]["47"]["signal"] for m in MODELS] == ["GPIO23", "GPIO23", "PC11", "GPIO4_C6"]
    assert tables["cb1"]["39"]["signal"] == "NC"
    assert tables["cb1"]["36"]["signal"] == "NC"
    assert all(tables[m]["78"]["signal"] == "NC" for m in ("cb1", "cb2"))
    assert tables["cb1"]["103"]["signal"] == "USB1-DM"
    assert tables["cb1"]["140"]["signal"] == "USB0-DM"
    assert tables["cm5"]["140"]["signal"] == "USB3-0-TX_N"
    assert tables["cb2"]["41"]["signal"] == "GPIO3_C4"
    assert manual["cb2"]["41"]["signal"] == "GPIO0_C4"

    def disposition(p: int) -> tuple[str, str, str, str]:
        if p in grounds:
            return "common ground", "return", "0 V", "Connect all 51 documented grounds; preserve high-speed return paths."
        if p in power:
            return "common main power", "carrier -> module", "4.75-5.25 V", "One regulated 5 V supply across all six contacts; not six independent 2 A feeds."
        if p in aux33:
            return "module auxiliary output", "module -> carrier", "3.3 V nominal", "Use only as module-domain reference/light qualified load; never join to independently regulated MC/ESP rails."
        if p in aux18:
            return "module auxiliary output", "module -> carrier", "1.8 V nominal", "Leave unconnected in base common subset; never feed with carrier power."
        if p == 78:
            return "Pi GPIO supply / BTT NC", "module-domain output -> Pi VREF input", "module's own 3.3 V", "Tie to pins 84/86 for Pi 3.3 V signalling; BTT tables list NC. No external always-on 3.3 V."
        if p in ethernet:
            return "Ethernet PHY MDI", "bidirectional analog", "PHY-specific; not GPIO", "1:1 magnetics/ESD review required. CB1 uses two pairs only, with documented 10/12 RX polarity difference."
        if p in hdmi:
            return "common HDMI0", "video out; DDC bidirectional; HPD in", "HDMI interface-specific", "Use HDMI0 only with exact ESD/DDC/5 V/backfeed and signal-integrity qualification."
        if p in usb:
            return "common USB2 host / profile recovery", "USB2 bidirectional", "USB2 interface-specific", "Host touch/adapters candidate; Pi/CB2 OTG recovery, CB1 SD USB1 host only. Separate protected port-role mux."
        if p in spi:
            dr = "FPGA -> module" if p == 40 else "module -> FPGA"
            return "dedicated motion SPI: " + spi[p], dr, "3.3 V nominal; GPIO-domain qualification pending", "Five-channel powered-off protected interface; own module profile, exclusive bus and measured dual-CS timing."
        if p == 93:
            return "boot recovery request", "manual passive grounding candidate", "module-specific", "Pi nRPIBOOT / CB1 FEL / CB2 RECOVERY. Do not drive from ESP. Exact revision procedure and LOW level remain profile-specific."
        if p == 101:
            return "USB role input / CB1 NC", "passive role switch candidate", "3.3 V on Pi; BTT confirm exact revision", "Ground for Pi/CB2 host mode; release for supported recovery. Do not share a live powered-host port with a recovery host."
        if p in sd:
            return "SD boot storage candidate", "module-specific SD", "SD bank; 3.3/1.8 V depends profile", "Only qualified Lite/CB1-SD/storage population; eMMC models and power/voltage switching not a universal circuit."
        if p in risk:
            return "conflict / restricted", "module-specific", "module-specific or NC", "Leave unrouted/DNP in base common subset; named profile/revision review required before use."
        return "outside base common subset", "module-specific", "not audited for active use", "Leave unrouted/DNP; existence of a same-position signal is not electrical or software qualification."

    rows = []
    differences = []
    for p in range(1, 201):
        role, direction, voltage, rule = disposition(p)
        row = {"global_pin": p, "connector": "A" if p <= 100 else "B",
               "connector_contact": p if p <= 100 else p - 100,
               **{m + "_signal": tables[m][str(p)]["signal"] for m in MODELS},
               "cb1_manual_signal": manual["cb1"][str(p)]["signal"],
               "cb2_manual_signal": manual["cb2"][str(p)]["signal"],
               "cm4_pdf_page_1based": tables["cm4"][str(p)]["pdf_page"],
               "cm5_pdf_page_1based": tables["cm5"][str(p)]["pdf_page"],
               "role_proposed": role, "direction_proposed": direction,
               "voltage_scope": voltage, "routing_rule": rule,
               "cb1_emmc_scope": "No full 200-contact revision source audited; SD table must not be inherited"}
        if p == 41:
            row["routing_rule"] += " CB2 wiki GPIO3_C4 contradicts manual GPIO0_C4; unresolved."
        rows.append(row)
        for m in ("cb1", "cb2"):
            a, b = tables[m][str(p)]["signal"], manual[m][str(p)]["signal"]
            if re.sub(r"[\s_-]", "", a).upper() != re.sub(r"[\s_-]", "", b).upper():
                differences.append({"module": m, "pin": p, "wiki_signal": a, "manual_signal": b,
                                    "assessment": "unresolved GPIO identity" if (m, p) == ("cb2", 41) else "power/name/function alias; retained explicitly"})
    dump("pin-matrix.json", {"scope": "source comparison, not socket qualification", "global_pin_count": 200,
         "profiles": ["CM4", "CM5 DS-6", "CB1 published SD V2.2", "CB2 published manual/wiki"],
         "source_conflicts_and_aliases": differences, "pins": rows})
    with (HERE / "pin-matrix.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    spi_profiles = {
        "cm4": {"controller": "BCM2711 SPI0", "sclk": "GPIO11", "miso": "GPIO9", "mosi": "GPIO10", "cs_fb_candidate": "GPIO4", "cs_cmd_candidate": "GPIO23", "driver": "New GPIO-CS CNC3 target transport/pinmux needed; not native CE0/CE1 wiring"},
        "cm5": {"controller": "RP1 SPI0", "sclk": "GPIO11", "miso": "GPIO9", "mosi": "GPIO10", "cs_fb_candidate": "GPIO4", "cs_cmd_candidate": "GPIO23", "driver": "New RP1 GPIO-CS CNC3 target transport/pinmux needed; BCM2711 MMIO path is not portable"},
        "cb1_sd_v22": {"controller": "H616 SPI1", "sclk": "PH6", "miso": "PH8", "mosi": "PH7", "cs_fb_candidate": "PC7", "cs_cmd_candidate": "PC11", "driver": "Separate Allwinner profile; disable TFT35/MCP2515/other clients on bus"},
        "cb1_emmc": {"controller": "H616 SPI1", "sclk": "PH6 (40-pin documentation only)", "miso": "PH8 (40-pin documentation only)", "mosi": "PH7 (40-pin documentation only)", "cs_fb_candidate": "PI14 (40-pin documentation; bay continuity not established)", "cs_cmd_candidate": "PI5 (40-pin documentation; bay continuity not established)", "driver": "Full exact-revision 200-contact schematic/continuity is required before accepting the SD candidate circuit"},
        "cb2": {"controller": "RK3566 SPI1 M1", "sclk": "GPIO3_C3", "miso": "GPIO3_C2", "mosi": "GPIO3_C1", "cs_fb_candidate": "GPIO3_A1 (BSP spi1 reg 1)", "cs_cmd_candidate": "GPIO4_C6 (BSP spi1 reg 0)", "driver": "Separate Rockchip profile; official BSP default disabled; supplied spidev overlays request 1 MHz"},
    }
    dts = (SOURCES / "btt-kernel-cb2.dts").read_text(encoding="utf-8")
    pinctrl = (SOURCES / "btt-rk3568-pinctrl.dtsi").read_text(encoding="utf-8")
    rejected = (SOURCES / "btt-cb2-dts.txt").read_text(encoding="utf-8")
    assert 'model = "BigTreeTech CB2"' in dts
    assert 'model = "Rockchip RK3566 OPi 3B"' in rejected
    assert re.search(r"&spi1\s*\{[\s\S]*?status = \"disabled\";[\s\S]*?pinctrl-0 = <&spi1m1_pins>;", dts)
    assert "cs-gpios = <&gpio4 RK_PC6 GPIO_ACTIVE_LOW>" in dts
    assert "<&gpio3 RK_PA1 GPIO_ACTIVE_LOW>" in dts
    for p in ("<3 RK_PC3 3 &pcfg_pull_none>", "<3 RK_PC2 3 &pcfg_pull_none>", "<3 RK_PC1 3 &pcfg_pull_none>"):
        assert p in pinctrl, p
    for p in ("rk3566-spidev1_0.dts", "rk3566-spidev1_1.dts"):
        assert "spi-max-frequency = <1000000>" in (SOURCES / p).read_text(encoding="utf-8")
    for m, profile in spi_profiles.items():
        profile.update({"machine_use_enabled": False, "target_build_observed": False, "physical_dual_cs_exchange_observed": False,
                        "loaded_servo_timing_observed": False, "pin_mapping_status": "partial eMMC source only" if m == "cb1_emmc" else "source-mapped proposal; no custom carrier circuit qualified"})
    dump("transport-profiles.json", {"physical_contacts": {"SCLK": 38, "MISO": 40, "MOSI": 44, "CS_FB_candidate": 54, "CS_CMD_candidate": 47},
                                     "logical_contract": "Frozen IS-1 dual CS_FB/CS_CMD, 176-byte feedback and 96-byte command; proposal does not change logical wire ABI",
                                     "profiles": spi_profiles})
    urls = {}
    for name in ("initial-urls.json", "additional-urls.json", "btt-pinned-kernel-urls.json", "cb2-overlay-urls.json", "kernel-source-urls.json"):
        urls.update(json.loads((SOURCES / name).read_text(encoding="utf-8")))
    urls["pi4b-schematic.pdf"] = (SOURCES / "pi4b-schematic-url.txt").read_text(encoding="utf-8").strip()
    storage_requests = json.loads((SOURCES / "storage-source-urls.json").read_text(encoding="utf-8"))
    urls.update({n: r["url"] for n, r in storage_requests.items() if r["downloaded"]})
    release = json.loads((SOURCES / "cb2-v302-release.json").read_text(encoding="utf-8"))
    assert "RK3566 won't boot directly from NVMe" in release["body"]
    assert "SD Card or eMMC" in release["body"]
    assert all(tables["cb1"][str(p)]["signal"] == "NC" for p in (102, 109, 110, 112, 116, 118, 122, 124))
    assert "<1 RK_PB2 RK_FUNC_GPIO &pcfg_pull_none>" in pinctrl or "<1 RK_PB2 RK_FUNC_GPIO &pcfg_pull_none>" in dts
    assert "reset-gpios = <&gpio1 RK_PB2 GPIO_ACTIVE_HIGH>" in dts
    assert "/* pcie20_perstnm2 */" in pinctrl and "<1 RK_PB2 4 &pcfg_pull_none>" in pinctrl
    # GPIO4_B1 is present in the BSP supply recipe but is not identified as an
    # exposed GPIO in the bay pin table. This is not proof of an on-board net.
    assert not any(r["signal"] == "GPIO4_B1" for r in tables["cb2"].values())
    dump("selector-and-storage.json", {
        "selector_codes_requested": {"0": "AUTO", "1": "CM4", "2": "CM5", "3": "CB1", "4": "CB2", "5": "future/reserved", "6": "future/reserved", "7": "future/reserved"},
        "scope": "proposal metadata; not installed firmware or populated switch circuit",
        "automatic_universal_pre_power_module_id": False,
        "supported_module_swap_goal": "stable FPGA-facing bus, preinstalled profiles, no FPGA/ESP/motherboard reflash; matching Linux module image required",
        "selector_grants_machine_permission": False,
        "gpio_chip_select_contacts_proposed": {"CS_FB": 54, "CS_CMD": 47},
        "pci_e_contacts_proposed": {"CLKREQ_N": 102, "PERST_N": 109, "REFCLK_P": 110, "REFCLK_N": 112, "MODULE_RX_P": 116, "MODULE_RX_N": 118, "MODULE_TX_P": 122, "MODULE_TX_N": 124},
        "cb1_native_pcie_contacts": "NC in the audited SD source; no native PCIe route established for eMMC",
        "cb2_nvme_initial_bootloader_medium": ["SD", "eMMC"],
        "cb2_nvme_target_boot_measured": False,
        "pi_nvme_target_boot_measured": False,
        "optane_original_16_32": {"medium": "NVMe storage, not DRAM/AI compute", "form_factor_mm": [22, 80], "interface": "PCIe 3.0 x2",
                                  "listed_active_power_w": 3.5, "current_at_3v3_a_arithmetic": 3.5 / 3.3, "peak_current_established": False,
                                  "independent_storage_supply_required": True, "exact_seller_mpn_established": False, "arm_boot_measured": False}
    })
    dump("source-manifest.json", {"observed_date": "2026-09-30", "source_files": [{"file": n, "sha256": h,
         "url": urls.get(n), "kind": "downloaded primary source" if n in urls else "derived text, parsed table, API snapshot or rendering"} for n, h in sorted(inputs.items())],
         "commit_pins": {"CB1": "38b117016699cf363ea2f452e828a5ce93c1de16", "CB2_manual": "a5fc72264062e27b603a024f08ade60eeba3f0ec",
                         "CB2_kernel": "340c270b968917f78c6ced356a4f0365b453f545", "PI4B": "3411b7207abd1d0d5806034a3bf041aafc0a24e9"},
         "rejected_as_cb2_pin_evidence": {"file": "btt-cb2-dts.txt", "reason": "Path names CB2 but model/compatible are OPi3B in the archived build tree; proper official CB2 BSP is used instead"}})
    after = {p.name: sha(p) for p in SOURCES.iterdir() if p.is_file()}
    assert inputs == after, "Audit source snapshots changed during comparison"
    report_path = HERE.parent / "COMPUTE_BAY_PIN_AUDIT.md"
    dump("review.json", {"result": "SOURCE_AUDIT_COMPLETE; ELECTRICAL_AND_MACHINE_RELEASE_NOT_GRANTED", "date": "2026-09-30",
         "contact_rows": len(rows), "module_contact_entries": 800, "all_tables_cover_exactly_1_to_200": True,
         "common_ground_count": len(grounds), "common_5v_contacts": sorted(power), "primary_manual_tables_crosschecked": ["CB1", "CB2"],
         "spi_contacts_source_asserted": sorted(spi), "manual_wiki_unresolved_conflicts": [{"module": "CB2", "pin": 41}],
         "input_files_unchanged": inputs == after, "input_file_count": len(inputs), "hardware_edits": False,
         "frozen_interface_edits": False, "schematic_erc_observed": False, "board_drc_observed": False,
         "target_compilation_observed": False, "physical_measurements_observed": False,
         "all_motion_profiles_disabled_until_qualification": all(not v["machine_use_enabled"] for v in spi_profiles.values()),
         "selector_proposal": {"code_bits": 3, "AUTO_code": 0, "requested_family_codes_preserved": True, "existing_reader_firmware_implemented": False,
                               "pre_power_universal_module_identification": False, "per_module_compatible_image_required": True, "motion_permission_granted_by_selector": False},
         "storage_source_assertions": {"cb1_pcie_nc": True, "cb2_initial_sd_emmc_bootloader": True, "cb2_perst_m2_pinctrl_matches_gpio1_b2": True},
         "comparison_script_sha256": sha(Path(__file__)), "report": {"file": "../COMPUTE_BAY_PIN_AUDIT.md", "sha256": sha(report_path)},
         "outputs": {n: sha(HERE / n) for n in ("pin-matrix.json", "pin-matrix.csv", "transport-profiles.json", "selector-and-storage.json", "source-manifest.json")}})
    print(json.dumps({"rows": len(rows), "contact_entries": 800, "grounds": len(grounds), "sources_stable": inputs == after,
                      "profile_count": len(spi_profiles), "motion_qualified_count": 0}, indent=2))


if __name__ == "__main__":
    main()
