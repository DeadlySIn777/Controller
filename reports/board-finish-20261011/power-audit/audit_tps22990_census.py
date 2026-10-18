"""Read-only TPS22990 CT/Bias census tied to frozen c05 and saved netlist."""
import hashlib
import json
import re
from pathlib import Path
import prepare_sbc_c05_proposal as p


def main():
    netlist_path=p.EXT/"agent-work/field-pdn/netlist.json"
    netlist=json.loads(p.read(netlist_path))
    model_path=p.EXT/"tools/verify/rail_model.json"
    model=json.loads(p.read(model_path))
    envelope_path=Path("hardware/sbc_power/design-envelope.json").resolve()
    envelope=json.loads(p.read(envelope_path))
    g, overlay=p.overlay()
    native=p.base.inventory(p.read(p.C05))[3]
    refs={ref for ref, comp in netlist["comps"].items() if comp["value"].startswith("TPS22990")}
    native_refs={p.base.ref_of(chunk) for chunk in native.values() if p.base.pcbtext.chunk_kind(chunk)=="footprint" and re.search(rb'\(property "Value" "TPS22990[^" ]*"',chunk)}
    p.require(refs==native_refs=={"U11010","U11011","U11012"},"switch census changed")
    rows=[]
    for ref in sorted(refs):
        pins=netlist["pins"][ref]
        pad_nets={pad["num"]:p.norm(pad["net"]) for pad in g["pads"] if pad["ref"]==ref}
        p.require({k:p.norm(v) for k,v in pins.items()}==pad_nets,"source/native pin mismatch "+ref)
        ct_net=pins["1"]
        caps=[other for other,num,*_ in netlist["nets"][ct_net] if other!=ref and other.startswith("C")]
        p.require((ref=="U11012" and caps==["C11061"]) or (ref!="U11012" and not caps and ct_net==f"unconnected-({ref}-CT-Pad1)"),"CT ownership changed")
        uid,chunk=next((uid,c) for uid,c in native.items() if p.base.pcbtext.chunk_kind(c)=="footprint" and p.base.ref_of(c)==ref)
        row={"ref":ref,"value":netlist["comps"][ref]["value"],"footprint_uuid":uid,"footprint_chunk_sha256":hashlib.sha256(chunk).hexdigest(),
            "CT_pin1_net":p.norm(ct_net),"VBIAS_pin4_net":p.norm(pins["4"]),"VIN_pin3_and_thermal11_nets":[p.norm(pins["3"]),p.norm(pins["11"])],
            "ON_pin5_net":p.norm(pins["5"]),"PG_pin7_net":p.norm(pins["7"]),"VOUT_pin8_9_10_nets":[p.norm(pins[x]) for x in ("8","9","10")],
            "CT_cap_refs":caps,"intent":"Preserve intentionally unconnected CT, fastest inherent switch slew and motor feed controls" if not caps else "Preserve CT ramp, capacitance effective bounds, input/output caps, SBC current and supervisor sequencing",
            "rail_model":model["rails"][p.norm(pins["8"])]}
        if caps:
            cap=caps[0]
            cap_uid,cap_chunk=next((uid,c) for uid,c in native.items() if p.base.pcbtext.chunk_kind(c)=="footprint" and p.base.ref_of(c)==cap)
            row["capacitor"]={"ref":cap,"source_properties":netlist["comps"][cap],"pins":netlist["pins"][cap],"native_uuid":cap_uid,"native_chunk_sha256":hashlib.sha256(cap_chunk).hexdigest()}
        rows.append(row)
    for path in (Path(__file__),p.EXT/"review/schematic/ds/tps22990.pdf",p.EXT/"review/schematic/ds/tps22990.txt"):
        p.read(path)
    for path,expected in p.READS.items():
        p.require(hashlib.sha256(Path(path).read_bytes()).hexdigest()==expected,"read input changed")
    receipt={"evidence_class":"Frozen source/native pin census plus official TI CT rating requirement; no electrical measurements",
        "board_sha256":p.C05_SHA,"source_native_switch_pin_parity":"PASS","instances":rows,"instance_count":len(rows),"external_CT_cap_count":1,
        "official_datasheet":"https://www.ti.com/lit/ds/symlink/tps22990.pdf","revision":"SLVSDK1C Rev.C section9.3.2 and12.1",
        "electrical_issue":{"ref":"C11061","source_voltage_rating_v":16,"minimum_TPS22990_CT_rating_v":25,"CT_may_reach_v":15,"status":"OPEN_ISOLATED_BOM_SOURCE_CORRECTION_REQUIRED"},
        "preserve_SBC_bounds":envelope["bounds"],"preserve_delivery_case":{"J15001_current_a":3.6,"source_output_copper_budget_mv":100,"CORE_input_budget_mv":70,"unchanged_motor_interfaces":12},
        "limits":["Only U11012 has external CT; do not invent motor CT components or silently change motor feed timings","A same-nominal higher-voltage CT capacitor has different DC-bias capacitance; effective .47–1.32uF timing/inrush envelope must be checked or recomputed on an isolated corrected source","Historical circuit envelope and drafted rail model are source assumptions, not full-board or physical proof","Placement proposals remain pinned to original geometry, with rating issue explicitly open"],
        "overlay":overlay,"read_set_sha256":p.READS,"implemented":False,"native_launched":False}
    path=p.OUT/"tps22990-census.json"
    path.write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"path":str(path),"sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"instances":len(rows),"CT_caps":1}))

if __name__=="__main__":
    main()
