"""Cross-check the real two-ABZ receiver netlist, ledger and termination envelope."""
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "hardware/rx_abz"


def validate(tree,design,mapping):
    errors = []
    channels = [c for c in design["channels"] if c["kind"] == "encoder"]
    if [c["id"] for c in channels] != [f"ENC{enc}_{sig}" for enc in range(2) for sig in "ABZ"]:
        return ["Ledger does not match the baseline two-ABZ scope"]
    actual,seen = {},set()
    for net in tree.findall(".//nets/net"):
        name = net.attrib["name"].lstrip("/")
        if name in actual:
            errors.append(f"Duplicate net: {name}")
        nodes = [(n.attrib["ref"],n.attrib["pin"]) for n in net.findall("node")]
        for node in nodes:
            if node in seen:
                errors.append(f"Pin belongs to multiple nets: {node}")
            seen.add(node)
        actual[name] = set(nodes)
    expected = defaultdict(set)
    def connect(net,*nodes):
        expected[net].update((ref,str(pin)) for ref,pin in nodes)
    # Datasheet PW16 groups, independent of the schematic generator.
    groups = ((2,1,3),(6,7,5),(10,9,11),(14,15,13))
    for index,channel in enumerate(channels):
        bank,local = divmod(index,4)
        encoder,signal = divmod(index,3)
        receiver = f"U{bank+1}"
        positive,negative,output = groups[local]
        if (channel["component"],channel["device_channel"],channel["logic_net"],channel["domain"]) != (f"RX{bank}",local+1,channel["id"]+"_FPGA","LOGIC"):
            errors.append(f"Ledger receiver allocation changed: {channel['id']}")
        for polarity,pin,terminal,resistorpin in (("P",positive,signal*2+1,1),("N",negative,signal*2+2,2)):
            net = channel["id"]+"_"+polarity
            row = [term for term in design["terminals"] if term["net"] == net]
            if len(row) != 1 or (row[0]["connector"],row[0]["position"],row[0]["domain"]) != (f"JENC{encoder}",terminal,"LOGIC"):
                errors.append(f"Ledger encoder terminal changed: {net}")
            connect(net,(receiver,pin),(f"JENC{encoder}",terminal),(f"R{index+1}",resistorpin))
        connect(channel["logic_net"],(receiver,output),("JLOGIC1",index+3))
    connect("IO_3V3",("JLOGIC1",1),("U1",4),("U1",12),("U1",16),
            ("U2",4),("U2",12),("U2",16),("U2",10),("U2",14))
    connect("LOGIC_GND",("JLOGIC1",2),("U1",8),("U2",8),("U2",9),("U2",15),
            ("JENC0",8),("JENC1",8),("JPWR1",2),("JPWR1",4))
    for encoder in range(2):
        net = f"ENC{encoder}_5V_LIMITED"
        connect(net,(f"JENC{encoder}",7),("JPWR1",encoder*2+1))
        for position,expectednet in ((7,net),(8,"LOGIC_GND")):
            terms = [term for term in design["terminals"] if term["connector"] == f"JENC{encoder}" and term["position"] == position]
            if len(terms) != 1 or terms[0]["net"] != expectednet:
                errors.append(f"Ledger encoder supply/reference changed: JENC{encoder}.{position}")
    for cap in ("C1","C2","C3","C4"):
        connect("IO_3V3",(cap,1))
        connect("LOGIC_GND",(cap,2))
    for channel,pin in ((3,11),(4,13)):
        connect(f"unconnected-(U2-{channel}Y-Pad{pin})",("U2",pin))
        nodes = tree.findall(f".//nets/net/node[@ref='U2'][@pin='{pin}']")
        if len(nodes) != 1 or nodes[0].attrib.get("pintype") != "tri_state+no_connect":
            errors.append(f"Unused U2 output {pin} lacks an explicit no-connect")
    for net in sorted(set(actual) | set(expected)):
        if actual.get(net,set()) != expected.get(net,set()):
            errors.append(f"Net {net}: missing={sorted(expected.get(net,set())-actual.get(net,set()))}; unexpected={sorted(actual.get(net,set())-expected.get(net,set()))}")
    components = {c.attrib["ref"]:c for c in tree.findall(".//components/comp")}
    if set(components) != {"U1","U2","JENC0","JENC1","JLOGIC1","JPWR1",*[f"C{i}" for i in range(1,5)],*[f"R{i}" for i in range(1,7)]}:
        errors.append("Receiver component population differs from the reviewed block")
    for ref,component in components.items():
        value = component.findtext("value")
        footprint = component.findtext("footprint")
        mpn = component.findtext("./fields/field[@name='MPN']")
        if ref.startswith("U") and (value,footprint,mpn) != ("AM26LV32EIPWR","Package_SO:TSSOP-16_4.4x5mm_P0.65mm","AM26LV32EIPWR"):
            errors.append(f"Wrong receiver part/package: {ref}")
        if ref.startswith("R"):
            if (value,footprint,mpn) != ("120R 1% 0.5W / FIT","Resistor_SMD:R_1210_3225Metric","CRCW1210120RFKEA"):
                errors.append(f"Termination resistance/power/package differs: {ref}")
            if any(prop.attrib.get("name","").lower() == "dnp" for prop in component.findall("property")):
                errors.append(f"Termination marked DNP while this evidence describes fitted: {ref}")
        if ref.startswith("C") and value != ("100nF 25V X7R" if ref in ("C1","C3") else "1uF 25V X7R"):
            errors.append(f"Supply bypass changed: {ref}")
    term = mapping["termination"]
    target = {"state":"fitted_120R","alternate":"DNP_open_only_not_a_bypass","mpn_reference":"CRCW1210120RFKEA",
              "ohms":120,"tolerance":0.01,"tcr_ppm_per_k":100,"conservative_temperature_excursion_k":150,
              "maximum_applied_differential_v":5.5,"nominal_rating_w_at_70c":0.5,
              "initial_local_ambient_max_c":70,"physical_thermal_qualified":False}
    if any(term.get(key) != value for key,value in target.items()):
        errors.append("Termination operating assumptions differ from the reviewed envelope")
    minimum = 120*0.99*0.985
    power = 5.5**2/minimum
    for key,expected_value in (("minimum_ohms_with_tolerance_and_tcr",minimum),
                               ("calculated_worst_case_w_per_channel",power),
                               ("calculated_worst_case_w_all_six",6*power)):
        if (type(term.get(key)) not in (float,int) or
                not math.isfinite(term[key]) or abs(term[key]-expected_value)>1e-9):
            errors.append(f"Termination calculation mismatch: {key}")
    if power >= 0.5:
        errors.append("Declared termination envelope exceeds its nominal rating")
    return errors


def main():
    design = json.loads((ROOT / "hardware/electrical-design.json").read_text(encoding="utf-8"))
    mapping = json.loads((OUT / "channel-map.json").read_text(encoding="utf-8"))
    errors = validate(ET.parse(OUT / "netlist.xml"),design,mapping)
    erc = json.loads((OUT / "erc.json").read_text(encoding="utf-8"))
    violations = [row for sheet in erc["sheets"] for row in sheet["violations"]]
    if violations:
        errors.append(f"ERC reports {len(violations)} violations")
    sources = ["hardware/electrical-design.json","tools/hardware_build_tx_schematic.py","tools/hardware_build_rx_abz.py",
               "tools/hardware_validate_rx_abz.py","tests/test_rx_abz.py"]
    sources += [str(path.relative_to(ROOT)).replace("\\","/") for path in sorted(OUT.iterdir())
                if path.is_file() and path.name != "validation.json"]
    result = {"schema_version":1,"scope":"baseline two-ABZ receiver block","consistency_pass":not errors,
              "manufacturing_ready":False,"errors":errors,"receiver_count":2,"used_channels":6,"unused_channels":2,
              "input_terminal_positions":16,"kicad_version":erc["kicad_version"],"erc_violations":len(violations),
              "erc_ignored_checks":erc["ignored_checks"],"termination":mapping["termination"],
              "source_sha256":{path:hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for path in sources},
              "boundary":"Connectivity/ERC and bounded arithmetic only; supply limiting, line protection, thermal/EMC and physical encoder behavior are unqualified"}
    (OUT / "validation.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(f"RX ABZ: {'PASS' if not errors else 'FAIL'}; {len(errors)} netlist/ledger/ERC issues; six channels; manufacturing blocked")
    return bool(errors)


if __name__ == "__main__":
    sys.exit(main())
