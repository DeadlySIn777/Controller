import json,pickle
from pathlib import Path
h=Path(__file__).resolve().parent;g=pickle.loads((h/'field-power/field-io3-crossing-contact-audit-r15e/geometry.pkl').read_bytes());keys=('/motherboard_power_entry/FIELD_A_24V_PROTECTED','/motherboard_power_entry/FIELD_B_24V_PROTECTED','/motherboard_motors/FIELD_GND','/motherboard_do/FIELD_B_0V')
print(json.dumps({k:g['domains_normalized'].get(k) for k in keys}))
