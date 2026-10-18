"""Independent proposal contracts and arithmetic, not ERC/DRC or simulation."""
from pathlib import Path
import hashlib
import json
from collections import defaultdict

root = Path(__file__).resolve().parent
sources = {}
specs = {}
parts = {}
issues = []
for filename in ("logic_spec.json", "power_spec.json", "indicator_spec.json"):
    source = root / filename
    raw = source.read_bytes()
    specs[filename] = json.loads(raw.decode("utf-8-sig"))
    sources[filename] = {"sha256": hashlib.sha256(raw).hexdigest(),
                         "revision": specs[filename]["revision"]}
    group = specs[filename]["parts"]
    if isinstance(group, dict):
        group = group.values()
    for part in group:
        ref = part["reference"]
        if ref in parts:
            issues.append(f"Duplicate reference {ref}")
        parts[ref] = part

def expect(ref, expected):
    if ref not in parts or parts[ref]["pins"] != expected:
        issues.append(f"Pin contract differs: {ref}")

expect("U20", {"1":"BUCK_BST", "2":"GND", "3":"BUCK_FB",
               "4":"BUCK_EN", "5":"BUCK_VIN", "6":"BUCK_SW"})
expect("U21", {"1":"V_IND_IN", "2":"V_IND_3V3", "3":"GND"})
expect("U50", {"1":"V_IND_3V3", "2":"IND_LED_5V", "3":"IND_LED_12V",
               "4":"IND_ADC", "5":"IND_LED_24V", "6":"IND_UPDI", "7":None, "8":"GND"})
expect("SW1", {"1":"V5_SELECT", "2":"COM_PLUS", "3":"V_EXT_PROT"})
expect("J3", {"1":"COM_PLUS", "2":"PUL_MINUS", "3":"DIR_MINUS", "4":"ENA_MINUS"})
expect("D22", {"1":"BUCK_VIN", "2":"V_EXT_PROT"})
expect("D23", {"1":"BUCK_SW", "2":"GND"})
expect("D25", {"1":"V5_SELECT", "2":"V5_REG"})
expect("D26", {"1":"V_IND_IN", "2":"IND_FEED_R"})
expect("R28", {"1":"V5_REG", "2":"GND"})
if "0.1%" not in parts["R21"]["value"] or "0.1%" not in parts["R22"]["value"]:
    issues.append("Feedback tolerance correction not incorporated")
if parts["R26"]["mpn"] != "ERJ-P08F82R0V":
    issues.append("82ohm inrush correction not incorporated")
if "R28" in parts and "330" not in parts["R28"]["value"]:
    issues.append("330ohm output bleed value differs")
if parts["J2"]["pins"]["6"] is not None:
    issues.append("Host VIO must remain disconnected")

nets = defaultdict(list)
for part in list(parts.values()) + list(specs["indicator_spec.json"]["pcb_features"].values()):
    for pin, net in part["pins"].items():
        if net is not None:
            nets[net].append(f'{part["reference"]}.{pin}')
for net, members in nets.items():
    if len(members) < 2:
        issues.append(f"Singleton net {net}: {members}")
    if "HOST_VIO" in net or net == "VM":
        issues.append(f"Unexpected host power net {net}")

vmin = .792 * (1 + 124 * .999 / (23.7 * 1.001))
vmax = .832 * (1 + 124 * 1.001 / (23.7 * .999))
metrics = {
    "buck_ref_resistor_screen_v": [vmin, vmax],
    "com_low_with_0_4v_diode_drop_v": vmin-.4,
    "ldo_low_input_5ma_screen_v": vmin-.4-.45-.005*82*1.01,
    "normal_26_4v_startup_current_upper_ma": 26.4/(82*.99)*1000,
    "adc_max_from_resistors_at26_4v": 26.4*(3900*1.001)/(100000*.999+3900*1.001),
    "adc_source_current_upper_ma": 26.4/(100000*.999)*1000,
    "ldo_boundary_input_drain_screen_ua": .3/(4700*1.01)*3.51/2.9095*1e6,
    "buck_boundary_input_drain_screen_ua": 2.65/(330*1.01)*3.4/27.83*1e6,
    "buck_bleed_high_output_power_w": vmax*vmax/(330*.99),
}
receipt = {
    "status": "PROPOSAL_CONTRACT_CHECK_PASS" if not issues else "PROPOSAL_CORRECTIONS_PENDING",
    "scope": "Source pin/net contracts and independent arithmetic; not native ERC, PCB DRC, SPICE, firmware or physical validation",
    "manufacturing_ready": False,
    "sources": sources,
    "review_sha256": hashlib.sha256((root/"independent-circuit-review.txt").read_bytes()).hexdigest(),
    "purchased_part_count": len(parts),
    "pcb_feature_count": len(specs["indicator_spec.json"]["pcb_features"]),
    "non_nc_net_count": len(nets),
    "issues": issues,
    "arithmetic_screens_only": metrics,
    "retained_specific_gates": [
        "Actual host VOH/VOL, startup polarity and physical fit",
        "AP7375 VOUT minus VIN during input collapse and ADC injection",
        "Unselected MP2459 SW minus VIN during power removal below UVLO",
        "Buck voltage/ripple/current and diode drops through final cable",
        "Indicator firmware, calibration and measured voltage-class boundaries",
        "Final native circuit and layout checks before fabrication",
    ],
}
(root/"independent-circuit-review.json").write_text(json.dumps(receipt, indent=2)+"\n", encoding="utf-8")
print(json.dumps({"status":receipt["status"], "parts":len(parts), "issues":issues, "screens":metrics}))
