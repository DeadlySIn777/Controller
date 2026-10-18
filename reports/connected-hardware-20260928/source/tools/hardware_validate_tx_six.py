"""Review the actual KiCad netlist against the baseline ledger and PW16 pin contract."""
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "hardware/tx_six"


def validate(tree, design):
    errors = []
    actual = {}
    seen_nodes = set()
    for net in tree.findall(".//nets/net"):
        name = net.attrib["name"].lstrip("/")
        if name in actual:
            errors.append(f"Duplicate net name: {name}")
        nodes = [(node.attrib["ref"],node.attrib["pin"]) for node in net.findall("node")]
        for node in nodes:
            if node in seen_nodes:
                errors.append(f"Pin appears twice: {node}")
            seen_nodes.add(node)
        actual[name] = set(nodes)
    expected = defaultdict(set)
    def connect(net, *nodes):
        expected[net].update((ref,str(pin)) for ref,pin in nodes)
    channels = [channel for channel in design["channels"] if channel["kind"] == "step_dir"]
    expected_ids = [f"{kind}{joint}" for joint in range(6) for kind in ("STEP","DIR")]
    if [channel["id"] for channel in channels] != expected_ids:
        return ["Ledger does not match the distinct baseline six-joint scope"]
    pin_groups = ((1,2,3),(7,6,5),(9,10,11),(15,14,13))
    expected_values = {}
    for index, channel in enumerate(channels):
        bank, local = divmod(index,4)
        if (channel["component"],channel["device_channel"],channel["logic_net"],channel["domain"]) != (f"TX{bank}",local+1,channel["id"]+"_FPGA","LOGIC"):
            errors.append(f"Ledger bank/channel/logic mismatch: {channel['id']}")
        driver,series,pull = f"U{bank+1}",f"R{index+1}",f"R{index+13}"
        data,positive,negative = pin_groups[local]
        connect(channel["id"]+"_D",(driver,data),(series,2),(pull,1))
        connect(channel["logic_net"],(series,1),("JLOGIC1",index+4))
        connect("LOGIC_GND",(pull,2))
        expected_values[series],expected_values[pull] = "33R 1%","10k 1%"
        for polarity,pin in (("P",positive),("N",negative)):
            net = channel["id"]+"_"+polarity
            terms = [t for t in design["terminals"] if t["net"] == net]
            if len(terms) != 1:
                errors.append(f"Ledger terminal missing/ambiguous: {net}")
                continue
            term = terms[0]
            nominal_position = local*2+(1 if polarity == "P" else 2)
            if (term["connector"],term["position"],term["domain"]) != (f"JTX{bank}",nominal_position,"LOGIC"):
                errors.append(f"Ledger baseline terminal assignment changed: {net}")
            connect(net,(driver,pin),(term["connector"],term["position"]))
    connect("SIGNAL_5V",("JLOGIC1",1))
    connect("LOGIC_GND",("JLOGIC1",2),("JLOGIC1",16),("JREF1",1),("JREF1",2),("JREF1",3))
    connect("TX_PERMIT",("JLOGIC1",3))
    for bank in range(3):
        driver,permit = f"U{bank+1}",f"R{bank+25}"
        connect("SIGNAL_5V",(driver,12),(driver,16))
        connect("LOGIC_GND",(driver,8),(permit,2))
        connect("TX_PERMIT",(driver,4),(permit,1))
        expected_values[driver],expected_values[permit] = "AM26C31IPWR","10k 1%"
        for number,value in ((bank*2+1,"100nF 25V X7R"),(bank*2+2,"1uF 25V X7R")):
            cap = f"C{number}"
            connect("SIGNAL_5V",(cap,1))
            connect("LOGIC_GND",(cap,2))
            expected_values[cap] = value
        references = [t for t in design["terminals"] if t["connector"] == "JPOWER" and t["position"] == bank+5]
        if len(references) != 1 or references[0]["net"] != f"TX{bank}_REFERENCE":
            errors.append(f"Ledger separate reference boundary changed: TX{bank}")
    # PWR_FLAG declarations are deliberately excluded from KiCad's exported netlist.
    for name in sorted(set(actual) | set(expected)):
        if actual.get(name,set()) != expected.get(name,set()):
            missing = sorted(expected.get(name,set()) - actual.get(name,set()))
            extra = sorted(actual.get(name,set()) - expected.get(name,set()))
            errors.append(f"Net {name}: missing={missing}, unexpected={extra}")
    components = {component.attrib["ref"]:component for component in tree.findall(".//components/comp")}
    expected_refs = set(expected_values) | {"JLOGIC1","JREF1","JTX0","JTX1","JTX2"}
    if set(components) != expected_refs:
        errors.append("Component population differs from three drivers, 27 resistors, six capacitors and five boundaries")
    for ref,value in expected_values.items():
        component = components.get(ref)
        if component is None or component.findtext("value") != value:
            errors.append(f"Value/default provision changed: {ref}")
        if ref.startswith("U") and component is not None:
            if (component.findtext("footprint") != "Package_SO:TSSOP-16_4.4x5mm_P0.65mm" or
                    component.findtext("./fields/field[@name='MPN']") != "AM26C31IPWR"):
                errors.append(f"Driver package/MPN differs from reviewed PW16 contract: {ref}")
    return errors


def main():
    design = json.loads((ROOT / "hardware/electrical-design.json").read_text(encoding="utf-8"))
    errors = validate(ET.parse(OUT / "netlist.xml"),design)
    erc = json.loads((OUT / "erc.json").read_text(encoding="utf-8"))
    violations = [item for sheet in erc["sheets"] for item in sheet["violations"]]
    if violations:
        errors.append(f"KiCad ERC reports {len(violations)} violations")
    sources = ["hardware/electrical-design.json","tools/hardware_build_tx_schematic.py",
               "tools/hardware_build_tx_six.py","tools/hardware_validate_tx_six.py",
               "tests/test_tx_six.py"]
    sources += [str(path.relative_to(ROOT)).replace("\\","/") for path in sorted(OUT.iterdir())
                if path.is_file() and path.name not in ("validation.json",)]
    result = {"schema_version":1,"scope":"baseline six-joint transmitter block", "consistency_pass":not errors,
              "manufacturing_ready":False,"errors":errors,"driver_count":3,"differential_channels":12,
              "output_terminal_positions":24,"signal_nets":51,"kicad_version":erc["kicad_version"],
              "erc_violations":len(violations),"erc_ignored_checks":erc["ignored_checks"],
              "source_sha256":{path:hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for path in sources},
              "boundary":"Net connectivity, default and component-value review; no FPGA pins, layout, power, loaded cable or physical fault measurements"}
    (OUT / "validation.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(f"TX6: {'PASS' if not errors else 'FAIL'}; {len(errors)} netlist/ledger/ERC issues; 12 channels; manufacturing blocked")
    return bool(errors)


if __name__ == "__main__":
    sys.exit(main())
