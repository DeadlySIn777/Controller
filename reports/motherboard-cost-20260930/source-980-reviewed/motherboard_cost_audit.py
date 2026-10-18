#!/usr/bin/env python3
"""Immutable, exact-MPN catalogue-cost receipts for incomplete motherboard sources.

This is a source costing tool, not a supplier quotation or a manufacturing release.
Every unpriced line, missing parent circuit and unselected module remains unknown.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
from datetime import datetime, timezone
from decimal import Decimal, ROUND_CEILING, ROUND_HALF_UP
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports/motherboard-cost-20260930"
MC = ROOT / "reports/board-completion-20260930/mc-bom-cost-r04"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def freeze(snapshot: str) -> Path:
    """Never replace a snapshot. Check all live sources again after copying."""
    out = REPORT / snapshot
    if out.exists():
        raise SystemExit(f"Refusing to replace immutable snapshot: {out}")
    paths = sorted(p for p in (ROOT / "hardware/motherboard").rglob("*") if p.is_file())
    paths += [MC / name for name in ("MC_BOM_PRICE_SOURCES.json", "MC_BOM_INPUT.csv", "MC_BOM_COST.json", "receipt.json")]
    before = {str(p.relative_to(ROOT)).replace("\\", "/"): digest(p) for p in paths}
    for path in paths:
        dest = out / "inputs" / path.relative_to(ROOT)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, dest)
    after = {str(p.relative_to(ROOT)).replace("\\", "/"): digest(p) for p in paths}
    if before != after:
        raise SystemExit("Live sources changed while copying: snapshot retained as failed, do not cost it.")
    for rel, sha in before.items():
        assert digest(out / "inputs" / rel) == sha, rel
    model = json.loads((out / "inputs/hardware/motherboard/design.json").read_text(encoding="utf-8"))
    with (out / "inputs/hardware/motherboard/bom.csv").open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == len(model["components"])
    write_json(out / "snapshot.json", {
        "schema_version": 1,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "snapshot": snapshot,
        "component_count": len(rows),
        "unique_mpns": len(set(r["MPN"] for r in rows)),
        "source_revision": model["revision"],
        "scope": "Immutable incomplete motherboard source and original dated exact-MPN MC offers. No manufacturing release.",
        "manufacturing_ready": False,
        "files_sha256": before,
    })
    return out


def money(value: Decimal) -> str:
    return str(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def check_frozen(out: Path):
    receipt = json.loads((out / "snapshot.json").read_text(encoding="utf-8"))
    for rel, sha in receipt["files_sha256"].items():
        assert digest(out / "inputs" / rel) == sha, f"Frozen input changed: {rel}"
    return receipt


def nominal_package(mpn: str) -> tuple[str, list[str]]:
    """Family checks are a sourcing screen, never a pin/land-pattern release."""
    if mpn.startswith(("CRCW0603", "PLT0603")):
        return "0603 / 1608", ["Resistor_SMD:R_0603_1608Metric"]
    if mpn.startswith("CRCW1210"):
        return "1210 / 3225", ["Resistor_SMD:R_1210_3225Metric"]
    if mpn.startswith("SMM0204"):
        return "MMA0204 MiniMELF, 3.6x1.4mm", ["Resistor_SMD:R_MiniMELF_MMA-0204"]
    if mpn.startswith(("GRM188", "CL10", "C0603", "06033")) or mpn in {"885012206040", "885012206046", "885012206052"}:
        return "0603 / 1608", ["Capacitor_SMD:C_0603_1608Metric"]
    if mpn.startswith(("C2012","GRM21B")) or mpn == "885012207053":
        return "0805 / 2012", ["Capacitor_SMD:C_0805_2012Metric"]
    if mpn == 'PCB_COPPER_TEST_PAD_D1.0':
        return 'Bare PCB copper test pad; no purchased component', ['TestPoint:TestPoint_Pad_D1.0mm']
    if mpn.startswith("C3216"):
        return "1206 / 3216", ["Capacitor_SMD:C_1206_3216Metric"]
    if mpn in {"AM26C31IPWR", "AM26LV32EIPWR"}:
        return "PW: TSSOP16, 4.4x5.0mm body", ["Package_SO:TSSOP-16_4.4x5mm_P0.65mm"]
    if mpn == "ISO1212DBQR":
        return "TI DBQ16: SSOP16, 3.9x4.9mm body", ["CNC_MB_DI:ISO1212_DBQ16_TI", "CNC_Motors:ISO1212_DBQ16_TI", "Package_SO:SSOP-16_3.9x4.9mm_P0.635mm"]
    if mpn in {"SN74LVC07APWR", "SN74LVC00APWR", "74LVC07APW,118", "74LVC14APW,118"}:
        return "PW: TSSOP14, 4.4x5.0mm body", ["Package_SO:TSSOP-14_4.4x5mm_P0.65mm"]
    if mpn == "SN74LVC244APWR":
        return "PW: TSSOP20, 4.4x6.5mm body", ["Package_SO:TSSOP-20_4.4x6.5mm_P0.65mm"]
    if mpn in {"SN74LVC1G08DCKR", "74LVC1G17GW"}:
        return "DCK / SOT353: SC70-5", ["Package_TO_SOT_SMD:SOT-353_SC-70-5"]
    if mpn.endswith("DCUR"):
        return "DCU: VSSOP8, 2.3x2.0mm body", ["Package_SO:VSSOP-8_2.3x2mm_P0.5mm"]
    if mpn in {"SN74LVC1G17DBVR", "SN74LVC1G34DBVR", "74AHCT1G17GVH"}:
        return "DBV / SOT753: SOT23-5", ["Package_TO_SOT_SMD:SOT-23-5"]
    if mpn.endswith("DBVR"):
        return "DBV: SOT23-6", ["Package_TO_SOT_SMD:SOT-23-6"]
    if mpn == "LTC6994IS6-2#TRPBF":
        return "S6: TSOT23-6", ["Package_TO_SOT_SMD:TSOT-23-6", "Package_TO_SOT_SMD:SOT-23-6"]
    named = {
        "ASE-50.000MHZ-L-C-T": ("Abracon ASE 3.2x2.5mm 4-pad", ["Oscillator:Oscillator_SMD_Abracon_ASE-4Pin_3.2x2.5mm"]),
        "LTC2962HUD#PBF": ("UD QFN16 + EP17, 3x3mm", ["CNC_MC_Power:LTC2962_UD16"]),
        "TPS3851G18SDRBT": ("DRB VSON8 + EP9, 3x3mm", ["CNC_IS1:TPS3851_DRB8"]),
        "TPS62901RPJR": ("RPJ VQFN9, 1.5x2mm", ["CNC_MC_Power:TPS62901_RPJ9"]),
        "W25Q32JVSSIQ": ("SS SOIC8, 208mil 5.3mm body", ["Package_SO:SOIC-8_5.3x5.3mm_P1.27mm"]),
        "T20F256I4": ("Efinix F256 BGA256, nominal 13x13mm/0.8mm pitch; custom NSMD", ["CNC_Motion:T20F256_Efinix_NSMD"]),
        "SMBJ33CA-E3/52": ("DO214AA / SMB", ["Diode_SMD:D_SMB"]),
        "TLP3640A(TPL,E)": ("Toshiba 11-3C1 SO4", ["CNC_Motors:TLP3640A_SO4_11-3C1"]),
        "TLP3640A(TPL,E": ("Toshiba 11-3C1 SO4", ["CNC_Motors:TLP3640A_SO4_11-3C1"]),
        "TLP4176A(TP,F)": ("Toshiba 11-5H1S 2.54SOP4", ["CNC_Motors:TLP4176A_2.54SOP4_11-5H1S"]),
        "TLP4176A(TP,F": ("Toshiba 11-5H1S 2.54SOP4", ["CNC_Motors:TLP4176A_2.54SOP4_11-5H1S"]),
        "XGL4020-102MEC": ("Coilcraft XGL4020, 4x4x2mm", ["CNC_MC_Power:XGL4020"]),
        "XGL4020-222MEC": ("Coilcraft XGL4020, 4x4x2mm", ["CNC_MC_Power:XGL4020"]),
    }
    return named.get(mpn, ("Unreviewed exact package", []))


def sourcing_notes(mpn: str, mc_unknown: dict) -> list[str]:
    notes = []
    if mpn == "74LVC1G17GW":
        notes.append("Manufacturer type number is valid SOT353-1, but exact orderable suffix is unresolved; official Nexperia lists 74LVC1G17GW,125. No unapproved suffix normalization.")
    if mpn.startswith("PLT0603"):
        notes.append("Vishay PLT supports nonstandard resistance values. These strings follow PLT0603/Z/value/L/S/T1 grammar; T1 is 1000 minimum and 1000 multiple. Unlisted exact values need sourcing confirmation, not a claim of nonexistence or an E96 restriction.")
    if mpn == "GRM188R71H105KA12D":
        notes.append("Exact name occurs in official TI TIDA-01464 BOM (1uF/50V/X7R/0603); present manufacturer/orderable catalogue and USD price not verified. Different KAALD suffix is not substituted.")
    if mpn in {"TLP3640A(TPL,E)", "TLP4176A(TP,F)"}:
        notes.append("Inherited source adds a final ')' while distributor manufacturer-product-number strings omit it. Exact procurable ordering-code equivalence requires explicit manufacturer evidence; alternate punctuation offer is not applied automatically.")
    if mpn in {"TLP3640A(TPL,E", "TLP4176A(TP,F"}:
        notes.append("Exact spelling matches Toshiba representative order code and distributor MPN. Earlier source's closing-parenthesis alias is retained only in its historical receipt. Accepted factory packing suffix/PCBWay handling still require procurement confirmation.")
    if mpn == "SMM02040C1001FB300":
        notes.append("Exact MiniMELF is documented in TI ISO1212 EVM BOM. LCSC's accessible USD tiers are reference-only with zero stock; selected purchasable offer remains unknown.")
    if mpn == "C2012C0G2A103J125AA":
        notes.append("Exact 0805/100V/C0G/5% product confirmed; accessible detailed primary price is CAD. No inferred currency conversion or substitute tolerance price used.")
    if mpn == "SN74LVC2G74DCUR":
        notes.append("TI SCES203Q confirms SINGLE 8-pin DFF with CLK1,D2,/Q3,GND4,Q5,/CLR6,/PRE7,VCC8. SN74LVC1G74DCUR uses the same pin map. '2G' does not imply dual; no invalid-package assertion is supported here.")
    if mpn == "ISO1212DBQR":
        notes.append("Nominal DBQ family fits both source libraries. The initial 685 snapshot had six generic motor SSOP land patterns and twelve exact-TI DI patterns; later snapshots list their actual source footprints here. Full native land/pin verification is separate hardware evidence.")
    if not notes and mpn in mc_unknown:
        notes.append(mc_unknown[mpn])
    return notes


def calculate(out: Path, observations: dict) -> dict:
    receipt = check_frozen(out)
    inp = out / "inputs"
    model = json.loads((inp / "hardware/motherboard/design.json").read_text(encoding="utf-8"))
    with (inp / "hardware/motherboard/bom.csv").open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    assert {r["Reference"] for r in rows} == set(model["components"]), "BOM/model reference mismatch"
    for row in rows:
        part = model["components"][row["Reference"]]
        assert row["MPN"] == part["mpn"] and row["Footprint"] == part["footprint"], row["Reference"]
        if "DNP" in row:
            assert (row["DNP"].lower() in {"yes", "true", "1"}) == bool(part.get("dnp",False)), row["Reference"]
    mc = json.loads((inp / MC.relative_to(ROOT) / "MC_BOM_PRICE_SOURCES.json").read_text(encoding="utf-8"))
    offers = {o["mpn"]: dict(o, evidence_origin="frozen_MC_r04_exact_MPN") for o in mc["offers"]}
    for offer in observations["offers"]:
        assert offer["mpn"] not in offers, "Do not replace original exact-MPN MC offer"
        offers[offer["mpn"]] = dict(offer,evidence_origin="new_primary_catalogue_observation")
    assert all(o["currency"] == "USD" for o in offers.values())
    groups = defaultdict(list)
    for row in rows:
        groups[row["MPN"]].append(row)
    lines, summaries, packages = [], [], []
    for mpn, parts in sorted(groups.items()):
        family, accepted = nominal_package(mpn)
        footprints = sorted({p["Footprint"] for p in parts})
        packages.append(dict(mpn=mpn,nominal_package=family,source_footprints=footprints,
            nominal_family_screen_pass=bool(accepted) and all(fp in accepted for fp in footprints),
            detailed_geometry_and_pin_release=False,
            sourcing_notes=sourcing_notes(mpn,mc.get("unknown_notes",{}))))
    for build in (1,10,100):
        cash = used = matched = extra = Decimal(0)
        priced = unknown = moq = priced_pieces = unpriced_pieces = 0
        stock_short = stock_unknown = 0
        fitted_total = 0
        bare_geometry_total = 0
        for mpn, parts in sorted(groups.items()):
            fitted = [p for p in parts if not model["components"][p["Reference"]].get("dnp",False)]
            dnp = [p for p in parts if model["components"][p["Reference"]].get("dnp",False)]
            bare_geometry = [p for p in fitted if model['components'][p['Reference']].get('kind')=='TP'
                             and p['MPN']=='PCB_COPPER_TEST_PAD_D1.0']
            required = (len(fitted)-len(bare_geometry))*build
            bare_geometry_total += len(bare_geometry)*build
            fitted_total += required
            offer = offers.get(mpn)
            line = dict(mpn=mpn,build_boards=build,physical_footprints_per_board=len(parts),
                fitted_per_board=len(fitted),dnp_per_board=len(dnp),required_pieces=required,
                fitted_references=sorted(p["Reference"] for p in fitted),dnp_references=sorted(p["Reference"] for p in dnp),
                buy_pieces=None,excess_pieces=None,minimum=None,multiple=None,selected_tier_minimum=None,
                unit_usd=None,consumed_inventory_value_usd=None,published_purchase_cash_usd=None,
                quantity_matched_purchase_cash_usd=None,observed_stock_pieces=None,
                observed_stock_covers_required=None,observed_stock_covers_buy=None,
                required_stock_shortfall_pieces=None,buy_stock_shortfall_pieces=None,
                availability_qualified=False,status="unpriced",supplier=None,packaging=None,
                observed_date=None,source_url=None,evidence_origin=None,
                notes=sourcing_notes(mpn,mc.get("unknown_notes",{})))
            if bare_geometry:
                assert len(bare_geometry)==len(fitted), 'Mixed purchased/test-pad MPN group'
                line['status']='bare_PCB_copper_no_purchase'
                line['notes']=['Copper is included in PCB fabrication; no placement or purchased BOM line.']
            elif required == 0:
                line["status"] = "DNP_only_no_purchase"
            elif offer:
                minimum, multiple = int(offer["minimum"]), int(offer["multiple"])
                buy = max(minimum,((required+multiple-1)//multiple)*multiple)
                tier = max((t for t in offer["price_breaks"] if int(t["minimum"]) <= buy), key=lambda t:int(t["minimum"]))
                unit = Decimal(tier["unit_usd"])
                spent, consumed, excess = buy*unit, required*unit, buy-required
                stock = offer.get("observed_stock_pieces")
                stock = int(stock) if stock is not None else None
                line.update(minimum=minimum,multiple=multiple,buy_pieces=buy,excess_pieces=excess,
                    selected_tier_minimum=int(tier["minimum"]),unit_usd=str(unit),
                    consumed_inventory_value_usd=str(consumed),published_purchase_cash_usd=str(spent),
                    quantity_matched_purchase_cash_usd=str(spent) if excess == 0 else None,
                    observed_stock_pieces=stock,
                    observed_stock_covers_required=stock >= required if stock is not None else None,
                    observed_stock_covers_buy=stock >= buy if stock is not None else None,
                    required_stock_shortfall_pieces=max(0,required-stock) if stock is not None else None,
                    buy_stock_shortfall_pieces=max(0,buy-stock) if stock is not None else None,
                    supplier=offer["supplier"],packaging=offer["packaging"],observed_date=offer["observed_date"],
                    source_url=offer["source_url"],evidence_origin=offer["evidence_origin"],
                    status="priced_quantity_matching" if excess == 0 else "priced_MOQ_excess",
                    source_cache_note=offer.get("source_cache_note","Original dated MC catalogue record; not reserved"))
                cash += spent; used += consumed; extra += excess*unit
                priced += 1; priced_pieces += required
                if excess: moq += 1
                else: matched += spent
                if stock is None: stock_unknown += 1
                elif stock < buy: stock_short += 1
            else:
                unknown += 1; unpriced_pieces += required
                if mpn.startswith("PLT0603") and mpn.endswith("T1"):
                    line.update(minimum=1000,multiple=1000,
                        buy_pieces=max(1000,((required+999)//1000)*1000),
                        note="Manufacturer T1 package MOQ known; price and order acceptance unknown, never treated as zero.")
            lines.append(line)
        assert used + extra == cash
        assert fitted_total == priced_pieces + unpriced_pieces
        summaries.append(dict(build_boards=build,physical_footprint_pieces=len(rows)*build,
            fitted_component_pieces=fitted_total,purchased_fitted_component_pieces=fitted_total,
            bare_PCB_copper_testpad_pieces=bare_geometry_total,
            dnp_footprint_pieces=len(rows)*build-fitted_total-bare_geometry_total,
            unique_BOM_mpns=len(groups),priced_mpn_count=priced,unpriced_mpn_count=unknown,
            priced_fitted_component_pieces=priced_pieces,unpriced_fitted_component_pieces=unpriced_pieces,
            quantity_matching_mpn_count=priced-moq,MOQ_excess_priced_mpn_count=moq,
            known_quantity_matching_subtotal_usd=money(matched),
            known_consumed_inventory_value_subtotal_usd=money(used),
            known_consumed_inventory_value_per_board_usd=money(used/build),
            known_catalogue_purchase_cash_subtotal_usd=money(cash),
            known_excess_inventory_value_usd=money(extra),
            priced_mpn_observed_stock_shortfall_count=stock_short,priced_mpn_stock_unknown_count=stock_unknown,
            full_component_purchase_total_usd=None,stock_qualified_purchase_total_usd=None,
            complete_manufactured_custom_board_total_usd=None,complete_controller_kit_total_usd=None))
    modules = [dict(category=x,selected_mpn=None,quantity=None,cost_usd_by_build={str(n):None for n in (1,10,100)}) for x in [
        "CM4/CM5 or separately electrically qualified BTT compute module; exact RAM/storage/wireless SKU unselected",
        "Purchased replaceable ESP32 service module; exact board and socket unselected",
        "Boot/data/settings storage: microSD / eMMC / NVMe choices; exact SKU and mounting unselected",
        "Optional AI compute/accelerator accessory; exact SKU unselected",
        *[f"Complete {size}-inch-class touchscreen/touch/interface/cables/power/mounting package; exact SKU unselected" for size in (7,10,12,14,18,21)]]]
    manufacture = [dict(category=x,cost_usd_by_build={str(n):None for n in (1,10,100)},quote_exists=False) for x in [
        "PCBWay fabrication: completed dimensions/layers/stackup/finish/impedance/yield",
        "PCBWay turnkey accepted exact-component sourcing and procurement fees",
        "PCBWay assembly/stencil/setup/feeder/reeling/tube/tray/attrition/BGA inspection",
        "Programming images/gateware/settings/license provisioning and fixture amortization",
        "Electrical/functional/thermal tests, calibration, traceability and test fixture amortization",
        "Cooling/heatsinks/fans, supply unit, enclosure, retained wiring/harnesses and mounting",
        "Shipping, tariff, tax, packaging, warranty allowance and support overhead"]]
    missing = [dict(region=x,missing_part_count=None,missing_cost_usd=None) for x in [
        "Compute carrier/socket/profile routing, Ethernet/USB/display and boot/recovery",
        "Parent power entry/protection/all field rails and motor/input protected supplies",
        "Real pluggable field terminals, compute/ESP/storage sockets and mating hardware",
        "Remaining DI sensor/safety protected supplies and authentic fault monitoring; drawn acquisition is costed where present",
        "DO isolated field supplies/health and routing qualification; drawn smart switches and control are costed where present",
        "Analog input/output and process/communications/expansion/status hardware not in this source"]]
    return dict(schema_version=1,date="2026-09-30",currency="USD",snapshot=receipt,
        scope="Cost of fitted parts in an incomplete ONE-motherboard schematic source. No full board or kit price and no manufacturing quotation.",
        tier_semantics="Aggregate exact MPN across all fitted references before multiplying board quantity. Exclude model DNP. Round up MOQ/multiple, select highest published CUT-TAPE (or inherited exact selected packaging) tier covered by piece purchase quantity. No interpolation, automatic MPN/suffix substitution, full-reel credit or currency conversion.",
        summaries=summaries,lines=lines,nominal_package_screen=packages,
        package_screen_limit="Nominal family screen only, using existing reviewed hardware/source package assignments and primary catalogue attributes. It does not verify every copper pad, pin assignment, orientation or assembly clearance.",
        original_MC_offers=mc["offers"],additional_exact_MPN_offers=observations["offers"],
        excluded_reference_offers=observations["excluded_reference_offers"],
        unselected_off_board_modules=modules,manufacturing_extras_unknown=manufacture,
        missing_motherboard_source_regions=missing,
        original_MC_known_MOQ_cash=dict(PLT0603Z1001LST1="5630.00",PLT0603Z1002LST1="5570.00",minimum_combined_cash_usd="11200.00"),
        conditional_Coilcraft_leader_trailer_usd_per_MPN="25.00",conditional_two_MPN_fee_usd="50.00",
        conditional_Coilcraft_fee_included=False,
        manufacturing_ready=False,physical_qualification=False,procurement_qualified=False,
        supplier_contact=False,orders=False,native_ERC_DRC_rerun=False)


def audit(snapshot: str, observation_path: Path) -> Path:
    out = REPORT / snapshot
    check_frozen(out)
    if (out / "MOTHERBOARD_COST.json").exists():
        raise SystemExit("Refusing to replace an issued cost receipt; freeze a new snapshot/version.")
    obs = json.loads(observation_path.read_text(encoding="utf-8"))
    shutil.copyfile(observation_path,out / "CATALOGUE_OBSERVATIONS.json")
    shutil.copyfile(Path(__file__),out / "motherboard_cost_audit.py")
    result = calculate(out,obs)
    write_json(out / "MOTHERBOARD_COST.json",result)
    fields = list(result["lines"][0])
    fields += sorted({k for row in result["lines"] for k in row} - set(fields))
    with (out / "MOTHERBOARD_COST.csv").open("w",newline="",encoding="utf-8") as stream:
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader()
        for row in result["lines"]:
            writer.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in row.items()})
    write_json(out / "PARTS_SOURCING_REVIEW.json",result["nominal_package_screen"])
    render(out,result)
    write_json(out / "receipt.json",dict(schema_version=1,created_utc=datetime.now(timezone.utc).isoformat(),
        snapshot=snapshot,input_snapshot_sha256=digest(out/"snapshot.json"),
        observation_sha256=digest(out/"CATALOGUE_OBSERVATIONS.json"),
        issued_tool_sha256=digest(out/"motherboard_cost_audit.py"),
        artifacts_sha256={p.name:digest(p) for p in [out/"MOTHERBOARD_COST.json",out/"MOTHERBOARD_COST.csv",out/"PARTS_SOURCING_REVIEW.json",out/"README.md"]},
        manufacturing_ready=False,full_cost_known=False))
    return out


def render(out: Path, result: dict):
    first=result["summaries"][0]
    lines=["# Incomplete motherboard source: exact-MPN component cost", "",
        f"30 September 2026; USD; `{out.name}`. **{first['physical_footprint_pieces']} physical footprints / {first['fitted_component_pieces']} purchased fitted parts / {first['bare_PCB_copper_testpad_pieces']} bare PCB test pads / {first['dnp_footprint_pieces']} DNP footprints / {first['unique_BOM_mpns']} exact source MPN/geometry groups.**",
        "", "These totals are a partial catalogue basket for this immutable schematic snapshot. Omitted circuitry, unpriced parts, commodity modules and all PCBWay manufacture costs remain unknown. They are not a complete board price, available procurement basket, turnkey quote or selling price.", "",
        "| Boards | Qty-matching priced subtotal | Priced fitted inventory value | Catalogue purchase cash incl. excess | Unpriced MPNs / fitted pieces |",
        "|---:|---:|---:|---:|---:|"]
    for s in result["summaries"]:
        lines.append(f"| {s['build_boards']} | ${s['known_quantity_matching_subtotal_usd']} | ${s['known_consumed_inventory_value_subtotal_usd']} | ${s['known_catalogue_purchase_cash_subtotal_usd']} | {s['unpriced_mpn_count']} / {s['unpriced_fitted_component_pieces']} |")
    lines += ["", "Fitted inventory value allocates the price of consumed parts at the applicable purchase tier. Purchase cash includes unused MOQ inventory. Neither proves delivery or design qualification. The two inherited PLT 1k/10k T1 lots require **$11,200 minimum known cash**, with prices of $5.63/$5.57 per piece at 1,000 each. The eight unpriced PLT strings also use the manufacturer's T1 packaging syntax; their unit prices and order acceptance are unknown.", "",
        "R7015/R7016 MPG termination footprints are DNP in the initial source model and are excluded from purchasing even though the old CSV lacked a DNP column. Their physical footprints remain in counts. Subsequent receipts use their own frozen DNP states.", "",
        "[All quantity rows](MOTHERBOARD_COST.csv), [complete calculation and exclusions](MOTHERBOARD_COST.json), [exact observed price evidence](CATALOGUE_OBSERVATIONS.json), [part sourcing/package screen](PARTS_SOURCING_REVIEW.json), [input hashes](snapshot.json) and [issued artifact hashes](receipt.json).", "",
        "## Sourcing and package findings", "",
        "The nominal footprint-family screen is distinct from full IC pin/land/orientation verification. It preserves exact source MPNs and never infers suitability merely from a quote.", ""]
    for part in result["nominal_package_screen"]:
        if part["sourcing_notes"] or not part["nominal_family_screen_pass"]:
            lines.append(f"- **{part['mpn']}**: " + " ".join(part["sourcing_notes"]) + (" Nominal footprint family needs review." if not part["nominal_family_screen_pass"] else ""))
    lines += ["", "The 2G74/1G74 package and pin-map finding is supported by [TI SCES203Q](https://www.ti.com/lit/ds/symlink/sn74lvc2g74.pdf) and [TI SCES794G](https://www.ti.com/lit/ds/symlink/sn74lvc1g74.pdf). The [Vishay PLT ordering specification](https://www.vishay.com/docs/60030/plt.pdf) permits nonstandard resistance values and specifies T1's 1,000-piece minimum/multiple. The [Nexperia ordering list](https://www.nexperia.com/chemical-content/74LVC1G17GW.html) separates type number from orderable suffix. [TI TIDA-01464 BOM](https://www.ti.com.cn/lit/pdf/TIDRTP7) records the otherwise unverified exact Murata 1uF name.", "",
        "## Unpriced exact MPNs", ""]
    for row in result["lines"]:
        if row["build_boards"]==1 and row["status"]=="unpriced":
            lines.append(f"- `{row['mpn']}`: {row['fitted_per_board']} fitted/board; cost unknown.")
    lines += ["", "## Stock is a separate constraint", "",
        "All observed inventory is dated, unreserved catalogue evidence. A price can exist with zero or insufficient stock. Future expected receipts are not treated as available. Aggregate supervisor demand uses every actual fitted source reference in the quantity rows, rather than only the historical three retained MC devices. Unknown stock stays null.", "",
        "| Boards | Priced MPNs short of purchase quantity | Priced MPNs with unknown stock | Stock-qualified complete basket |",
        "|---:|---:|---:|---|"]
    for s in result["summaries"]:
        lines.append(f"| {s['build_boards']} | {s['priced_mpn_observed_stock_shortfall_count']} | {s['priced_mpn_stock_unknown_count']} | Unknown |")
    lines += ["", "## Separate modules and complete kit costs", "",
        "No exact compute, ESP32, storage/settings or optional AI module SKU is selected here. Their price and purchasing quantity remain unknown. Complete touchscreen assemblies in the 7-, 10-, 12-, 14-, 18- and 21-inch classes remain six explicit independent package rows, including touch controller, interface, cable, power and mounting costs. Screen size never changes the motherboard I/O/channel scope.", "",
        "PCBWay fabrication/stackup/finish/impedance/yield; accepted exact-part turnkey sourcing; assembly, stencil, setup, feeders, attrition, reeling/tube/tray/BGA inspection; programming; test/fixtures/calibration; cooling, PSU, enclosure/harness/mounting; shipping/tax/tariff; packaging/warranty/support all remain individually null at 1/10/100. No quote has been requested and no files uploaded. The optional Coilcraft $25 leader/trailer fee per inductor MPN ($50 for two) remains a conditional extra, not assumed free or included.", "",
        "Only the exact drawn source population is included. Required compute/ESP/storage sockets, actual field terminal mates, complete power/health and further analog/comms/process/expansion/status implementation remain separate engineering gates. Drawn DI/DO/control parts are included where present; their existence does not qualify operation. Bare PCB test pads are fabrication geometry and have no purchased part or assembly-placement charge. Missing part counts and costs remain unknown, not zero. A component count or a clean schematic cannot close them.", "",
        "No source hardware was changed by this audit. No native ERC/DRC, target compilation, FPGA synthesis or physical test is claimed. Receipt verification checks immutable hashes, BOM/model identity, DNP exclusion, exact-MPN arithmetic, tier/MOQ, nulls, stock and adversarial negative controls."]
    (out/"README.md").write_text("\n".join(lines)+"\n",encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["freeze", "audit"])
    parser.add_argument("snapshot")
    parser.add_argument("--observations", type=Path, default=REPORT/"CATALOGUE_OBSERVATIONS.json")
    args = parser.parse_args()
    if args.command == "freeze":
        out = freeze(args.snapshot)
        print(out.relative_to(ROOT))
        print((out / "snapshot.json").read_text(encoding="utf-8"))
    elif args.command == "audit":
        out=audit(args.snapshot,args.observations)
        result=json.loads((out/"MOTHERBOARD_COST.json").read_text())
        print(json.dumps(dict(snapshot=args.snapshot,summaries=result["summaries"]),indent=2))


if __name__ == "__main__":
    main()
