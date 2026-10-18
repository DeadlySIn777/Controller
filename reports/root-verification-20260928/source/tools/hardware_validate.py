"""Check electrical-ledger consistency and expose manufacturing blockers.

Default success means internally consistent proposal, NOT permission to manufacture.
Use --release to make unresolved design/qualification items fail the process.
"""
from pathlib import Path
from collections import Counter, defaultdict
import argparse
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]


def validate(d):
    errors=[]; blockers=list(d.get("release_blockers",[])); warnings=[]
    def duplicate(items,key,kind):
        counts=Counter(x.get(key) for x in items)
        errors.extend(f"duplicate {kind}: {k}" for k,n in counts.items() if n>1)
    for key in ("components","channels","rails","domains","pin_reservations","power_loads","interfaces"):
        duplicate(d[key],"id",key)
    rails={x["id"]:x for x in d["rails"]}; parts={x["id"]:x for x in d["components"]}
    domains={x["id"]:x for x in d["domains"]}
    if len({x["ground"] for x in domains.values()}) != len(domains):
        errors.append("isolation domains alias a ground")
    for r in rails.values():
        if r["domain"] not in domains:errors.append(f"unknown rail domain: {r['id']}")
        if not 0<r["min_v"]<=r["nominal_v"]<=r["max_v"] or r["capacity_a"]<=0:
            errors.append(f"invalid rail envelope: {r['id']}")
    for need in d["required_parts"]:
        p=parts.get(need["id"])
        if not p or p["qty"]<need["minimum_qty"]:errors.append(f"required part missing/underquantity: {need['id']}")
    for p in parts.values():
        if isinstance(p["qty"],bool) or not isinstance(p["qty"],int) or p["qty"]<1:errors.append(f"invalid part quantity: {p['id']}")
        if not p.get("mpn"):blockers.append(f"MPN unresolved: {p['id']}")
        ports=list(p.get("supply_ports",[]))
        if p.get("rail"):ports.append({"rail":p["rail"],"allowed_supply_v":p.get("allowed_supply_v")})
        for port in ports:
            r=rails.get(port["rail"])
            if r is None:errors.append(f"unknown supply: {p['id']}");continue
            if port.get("allowed_supply_v"):
                lo,hi=port["allowed_supply_v"]
                if r["min_v"]<lo or r["max_v"]>hi:errors.append(f"supply outside device operating limits: {p['id']}")
    loading=defaultdict(float)
    for load in d["power_loads"]:
        if load["rail"] not in rails or load["budget_a"]<0:errors.append(f"invalid power load: {load['id']}");continue
        loading[load["rail"]]+=load["budget_a"]
    for name,amps in loading.items():
        cap=rails[name]["capacity_a"]
        if amps>cap+1e-9:errors.append(f"rail over budget: {name} {amps:.3f}A>{cap:.3f}A")
        elif amps>cap*0.8:warnings.append(f"less than 20% capacity headroom: {name} {amps:.3f}/{cap:.3f} A")
    # Cross-check conversion reservations instead of trusting handwritten load totals.
    loadmap={x["id"]:x["budget_a"] for x in d["power_loads"]}
    for sub,entry in (("IO_3V3","io3v3_input"),("ESP_3V3","esp3v3_input"),("CORE_1V2","core1v2_input")):
        minimum_sub=loading[sub]*rails[sub]["nominal_v"]/rails["CORE_5V"]["nominal_v"]/0.85
        if loadmap.get(entry,0)+1e-9<minimum_sub:errors.append(f"CORE5V input reservation {entry} understates {sub} conversion at assumed85% efficiency")
    minimum_input=loading["CORE_5V"]*rails["CORE_5V"]["nominal_v"]/0.85/rails["CORE_24V"]["min_v"]
    if loadmap["logic_converter_input"]+1e-9<minimum_input:errors.append("CORE24V input reservation understates5V conversion at assumed85% efficiency")
    expect={"step_dir":12,"encoder":6,"digital_input":22,"general_output":8,"drive_enable":6,"spindle_analog":1}
    actual=Counter(c["kind"] for c in d["channels"])
    if actual!=Counter(expect):errors.append(f"channel count mismatch: {dict(actual)}")
    seen=set(); pin_seen={};bank_load=defaultdict(float)
    for c in d["channels"]:
        key=(c["component"],c["device_channel"])
        if key in seen:errors.append(f"IC channel collision: {key}")
        seen.add(key)
        if c["domain"] not in domains:errors.append(f"unknown channel domain: {c['id']}")
        pin=c.get("fpga_package_pin")
        if pin is not None:
            if pin in pin_seen:errors.append(f"FPGA package pin collision: {pin}")
            pin_seen[pin]=c["id"]
            if c.get("bank") is None:errors.append(f"mapped FPGA pin lacks bank: {c['id']}")
        if c["kind"] in ("general_output","drive_enable"):
            if c["default"]!="off":errors.append(f"actuator default not off: {c['id']}")
            bank_load[c["component"]]+=c["load_target_a"]
            limit=0.5 if c["kind"]=="general_output" else 0.05
            if c["load_target_a"]>limit+1e-9:errors.append(f"channel target exceeded: {c['id']}")
    for bank,amps in bank_load.items():
        if amps>2+1e-9:errors.append(f"output bank over2A target: {bank}")
    if sum(bank_load.values())>loadmap["field_outputs"]+1e-9:errors.append("field output rail understates allocated loads")
    counts={prefix:(parts.get(pid,{}).get("qty",0),cap) for prefix,pid,cap in
            [("TX","tx",4),("RX","rx",4),("DI","di",2),("DO","do",4),("DAC","dac",1)]}
    for c in d["channels"]:
        for prefix,(instances,capacity) in counts.items():
            if c["component"].startswith(prefix):
                index=c["component"][len(prefix):]
                if not index.isdigit() or int(index)>=instances or not 1<=c["device_channel"]<=capacity:
                    errors.append(f"device channel exceeds fitted capacity: {c['id']}")
                break
        else:errors.append(f"channel references unknown component: {c['id']}")
    gpios=54+sum(x["count"] for x in d["pin_reservations"])
    if gpios>d["fpga"]["advertised_gpio"]:errors.append("FPGA advertised GPIO count exceeded")
    if not d["fpga"]["physical_mapping_complete"]:blockers.append(f"{gpios} signal/reserve GPIO budget has no reviewed physical pin/bank mapping")
    # Rail sets are taken from the fitted parts, so a link cannot claim an isolator the BOM does not power on both sides.
    part_rails={pid:{port["rail"] for port in ([{"rail":p["rail"]}] if p.get("rail") else [])+list(p.get("supply_ports",[]))} for pid,p in parts.items()}
    io_rails={rid for rid,r in rails.items() if abs(r["nominal_v"]-d["fpga"]["reserved_bank_voltage"])<1e-9}
    if not part_rails.get("fpga",set())&io_rails:errors.append("FPGA declares no supply port on the reserved I/O bank rail")
    for link in d["logic_links"]:
        if link["source_domain"]!=link["destination_domain"] and link["bridge"]!="galvanic_isolator":
            errors.append(f"unisolated domain crossing: {link['id']}")
        if link["bridge"]=="galvanic_isolator":
            span={link["source_rail"],link["destination_supply"]}
            fitted=[pid for pid,p in parts.items() if p.get("mpn") and p["mpn"]==link.get("isolator_mpn") and span<=part_rails[pid]]
            if not fitted:errors.append(f"isolator not fitted across both rails: {link['id']}")
            elif {rails[r]["domain"] for r in span}!={link["source_domain"],link["destination_domain"]}:
                errors.append(f"isolator rails do not match link domains: {link['id']}")
        if "source_voh_min" in link:
            if link["source_voh_min"]<link["destination_vih_min"] or link["source_vol_max"]>link["destination_vil_max"]:
                errors.append(f"logic noise margin violated: {link['id']}")
            if link["source_max_v"]>link["destination_input_abs_max"]:errors.append(f"logic input overvoltage: {link['id']}")
    termseen=set()
    for term in d["terminals"]:
        key=(term["connector"],term["position"])
        if key in termseen:errors.append(f"terminal collision: {key}")
        termseen.add(key)
        if not 1<=term["position"]<=8:errors.append(f"terminal outside8way allocation: {key}")
    if len(termseen)!=96:errors.append("terminal allocation must contain96uniquepositions")
    # Reconcile the public terminal map with the channel ledger: every channel must own its terminal
    # net(s) exactly once, in the channel's isolation domain, and no orphan signal net may appear.
    expected_terms={}
    for c in d["channels"]:
        nets={"step_dir":[c["id"]+"_P",c["id"]+"_N"],"encoder":[c["id"]+"_P",c["id"]+"_N"],
              "digital_input":[c["id"]+"_FIELD"],"general_output":[c["id"]+"_FIELD"],
              "drive_enable":[c["id"]+"_FIELD"],"spindle_analog":["SPINDLE_0_10V"]}.get(c["kind"],[])
        for net in nets:expected_terms[net]=c
    term_nets=Counter(t["net"] for t in d["terminals"])
    for net,c in expected_terms.items():
        if term_nets.get(net,0)!=1:errors.append(f"terminal net missing or duplicated for channel {c['id']}: {net}")
    signal_pattern=re.compile(r"^(STEP|DIR|ENC|DI|DO|SPINDLE)[0-9A-Z_]*$")
    for t in d["terminals"]:
        c=expected_terms.get(t["net"])
        if c is None:
            if signal_pattern.match(t["net"]) and not t["net"].endswith(("_5V_LIMITED",)):errors.append(f"terminal net has no ledger channel: {t['net']}")
        elif t["domain"]!=c["domain"]:errors.append(f"terminal domain differs from channel domain: {t['net']} {t['domain']}!={c['domain']}")
    if d["permission"]["esp_in_required_path"]:errors.append("ESP improperly placed in motion permission path")
    if set(d["permission"]["required_true"])!={"RAILS_OK","CONFIG_VALID","EXTERNAL_PERMIT","HW_WATCHDOG_OK","FPGA_ARM_LATCH"}:
        errors.append("required hardware permission term missing or altered")
    if d.get("manufacturing_ready"):errors.append("proposal incorrectly claims manufacturing ready")
    step=next(x for x in d["interfaces"] if x["id"]=="step_dir")
    if step["design_goal_steps_per_s"]>step["reference_rtl_limit_steps_per_s"]:
        warnings.append(f"STEP design goal {step['design_goal_steps_per_s']:g}/s is unachieved: reference RTL cap is {step['reference_rtl_limit_steps_per_s']:g}/s")
    if d["permission"]["hardware_implementation_status"]!="reviewed_complete":blockers.append("hardware permission circuitry not complete")
    return {"schema_version":1,"consistency_pass":not errors,"manufacturing_ready":False,"errors":errors,
            "warnings":warnings,"release_blockers":list(dict.fromkeys(blockers)),"counts":{"channels":len(d["channels"]),"fpga_signal_and_reserve_gpio":gpios,"terminals":len(termseen),"bom_groups":len(parts)},
            "rail_budget_a":{k:round(v,5) for k,v in loading.items()},
            "meaning":"Checks ledger relationships; does not simulate electrical behavior, replace ERC/DRC, prove timing or qualify hardware."}


def check_tx_netlist(path):
    tree=ET.parse(path)
    expected={"1":"STEP0_D","2":"STEP0_P","3":"STEP0_N","4":"TX_PERMIT","5":"DIR0_N","6":"DIR0_P","7":"DIR0_D","8":"LOGIC_GND","9":"STEP1_D","10":"STEP1_P","11":"STEP1_N","12":"SIGNAL_5V","13":"DIR1_N","14":"DIR1_P","15":"DIR1_D","16":"SIGNAL_5V"}
    actual={};nodes_by_net={}
    for net in tree.findall(".//nets/net"):
        name=net.attrib["name"].lstrip("/")
        nodes_by_net[name]={(n.attrib["ref"],n.attrib["pin"]) for n in net.findall("node")}
        for ref,pin in nodes_by_net[name]:
            if ref=="U1":actual[pin]=name
    errors=[]
    if actual!=expected:errors.append("TX U1 pin-net map differs from reviewed AM26C31 PW16 contract")
    for i,base in enumerate(("STEP0","DIR0","STEP1","DIR1"),1):
        expected_nodes={(f"R{i}","2"),(f"R{i+4}","1")}
        if not expected_nodes<=nodes_by_net.get(base+"_D",set()):errors.append(f"TX input series/default network missing: {base}")
    for ref in ("C1","C2"):
        if (ref,"1") not in nodes_by_net.get("SIGNAL_5V",set()) or (ref,"2") not in nodes_by_net.get("LOGIC_GND",set()):
            errors.append(f"TX decoupling not connected across supply: {ref}")
    if ("R9","1") not in nodes_by_net.get("TX_PERMIT",set()) or ("R9","2") not in nodes_by_net.get("LOGIC_GND",set()):errors.append("TX permit default-low resistor missing")
    return errors


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--design",type=Path,default=ROOT/"hardware/electrical-design.json")
    parser.add_argument("--report",type=Path,default=ROOT/"hardware/validation-report.json")
    parser.add_argument("--release",action="store_true")
    args=parser.parse_args()
    design_raw=args.design.read_bytes()
    result=validate(json.loads(design_raw.decode("utf-8")))
    result["design_sha256"]=hashlib.sha256(design_raw).hexdigest()
    netpath=ROOT/"hardware/tx_bank/netlist.xml"
    if netpath.exists():
        result["tx_netlist_errors"]=check_tx_netlist(netpath)
        result["errors"].extend(result["tx_netlist_errors"])
        result["consistency_pass"]=not result["errors"]
    else:result["release_blockers"].append("TX netlist export absent")
    args.report.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(f"Consistency: {'PASS' if result['consistency_pass'] else 'FAIL'}; {len(result['errors'])} errors; {len(result['release_blockers'])} release blockers")
    for item in result["errors"]:print(item)
    return 1 if result["errors"] or (args.release and result["release_blockers"]) else 0


if __name__=="__main__":sys.exit(main())
