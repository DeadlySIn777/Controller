"""Read back the generated board BOM and check the current quote documents.

These checks supplement the prose review; they do not validate electronics,
manufacturing exports, commercial stock, or the physical first article.
"""
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent


def check():
    docs = {name: (ROOT / name).read_text(encoding="utf-8-sig") for name in (
        "QUOTE_SCOPE.txt", "ASSEMBLY_AND_WIRING.txt", "FUNCTIONAL_TEST.txt")}
    compact = {name: " ".join(text.split()) for name, text in docs.items()}
    quote = compact["QUOTE_SCOPE.txt"]
    assembly = compact["ASSEMBLY_AND_WIRING.txt"]
    test = compact["FUNCTIONAL_TEST.txt"]
    parts = json.loads((ROOT / "parts.json").read_text(encoding="utf-8"))["parts"]
    with (ROOT / "BOM.csv").open(encoding="utf-8-sig", newline="") as stream:
        bom = list(csv.DictReader(stream))
    refs = [ref.strip() for row in bom for ref in row["Designators"].split(",")]
    checks = {
        "bom_has_32_nonempty_MPN_and_manufacturer_rows": len(bom) == 32 and all(
            row["Manufacturer"].strip() and row["Manufacturer part number"].strip() for row in bom),
        "bom_all_50_source_references_once": len(refs) == len(set(refs)) == 50 and set(refs) == set(parts),
        "bom_quantities_are_per_board_and_five_boards": all(
            int(row["Quantity per board"]) == len(row["Designators"].split(",")) and
            int(row["Quantity for 5 boards"]) == 5 * int(row["Quantity per board"]) for row in bom),
        "bom_250_fitted_parts_for_five_boards": sum(int(row["Quantity for 5 boards"]) for row in bom) == 250
            and all(row["Fit"] == "Yes" for row in bom),
        "quote_five_boards_and_five_finished_harnesses": "five fully assembled adapters and five matching, completely finished 500 mm signal harnesses" in quote,
        "quote_45_SMT_and_5_THT_native_distribution": "45 SMT parts (9 top, 36 bottom) and all five through-hole components: J1, J2, J3, J4 and SW1" in quote,
        "quote_and_test_current_outline": "15.24 x 38.10 mm" in quote and "15.24 x 38.10 mm" in test,
        "quote_and_test_current_extension": "17.78 mm" in quote and "17.78 mm" in test,
        "quote_four_layer_arrangement": all(s in quote for s in (
            "F.Cu signals with GND fill", "In1.Cu continuous GND reference",
            "In2.Cu signal crossings with GND fill", "B.Cu signals with GND fill")),
        "purple_solder_mask_white_legend_in_quote_and_assembly": all(
            "purple solder mask, white legend and ENIG" in text for text in (quote, assembly)),
        "external_power_explicit_in_both_documents": "powers it in both switch positions" in quote
            and "EXTERNAL POWER IS REQUIRED IN BOTH MODES" in assembly,
        "assembly_normal_mode_matrix": all(s in assembly for s in (
            "12 V or 24 V 5V", "Regulated 5 V EXT", "Regulated 24 V EXT",
            "12 V EXT Only for a driver explicitly allowing it")),
        "test_all_four_normal_cases": all(s in test for s in (
            "5.00 V EXT", "12.00 V 5V", "24.00 V 5V", "24.00 V EXT")),
        "no_5V_terminal_buck_mode_support_claim": "Do not rate 5 V terminal input with the selector in 5V mode as supported." in test,
        "harness_four_contacts_six_finished_ends": "four SXH-001T-P0.6 contacts" in assembly
            and "label the six driver ends PUL+, DIR+, ENA+, PUL-, DIR-, ENA- individually" in assembly,
        "no_customer_soldering_crimping": "No customer soldering, crimping or splicing" in quote,
        "first_article_release_and_later_quantity_separated": "A first-article build requires a separate written release" in quote
            and "Remaining quantity or repeat manufacture follows approval of the measured first article" in quote,
        "no_quote_is_build_authorization": "Do not procure or build from this quotation request" in quote,
        "website_route_and_receipt_separate": "PCBWay website account" in quote and "separate portal receipt" in quote,
        "legacy_files_excluded": "Exclude the earlier preliminary-scope ZIP, r0.1 files and internal routing proposals/history" in quote,
    }
    # Confirm each CSV MPN/manufacturer and fitted count against the source.
    checks["bom_each_MPN_manufacturer_matches_source"] = all(
        parts[ref.strip()]["mpn"] == row["Manufacturer part number"] and
        parts[ref.strip()]["manufacturer"] == row["Manufacturer"]
        for row in bom for ref in row["Designators"].split(","))
    filenames = [*docs, "BOM.csv", "parts.json", "bom-pcb-review.json"]
    report = {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS - document and BOM consistency only" if all(checks.values()) else "FAIL",
        "checks": checks,
        "sha256": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in filenames},
        "prose_review": [
            "The quotation is for five finished adapters and five finished 500 mm harnesses; harness material is additional to the 50-component board BOM.",
            "Both selector modes require the external screw-terminal supply. The 5V position is for a nominal 12/24 V terminal supply; a nominal 5 V terminal supply uses EXT.",
            "Common-positive sink topology and shared ground are explicit. No universal host/driver compatibility or galvanic isolation is claimed.",
            "Fit, loaded voltage/current, timing, startup/enable, power faults and thermal behavior remain first-article qualification work.",
            "No manufacturing export check, zero-DRC result, physical validation or website submission is asserted by this review.",
        ],
        "release_status": "Quotation/DFM candidate. Procurement and fabrication require separate release; production readiness is not established.",
    }
    (ROOT / "document-consistency-review.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "checks_passed": sum(checks.values()), "checks_total": len(checks), "failed": [k for k, v in checks.items() if not v]}, indent=2))
    if not all(checks.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    check()
