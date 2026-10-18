"""Reuse issued exact-owner audit code, keeping the original94 receipt immutable."""
from pathlib import Path
root=Path(__file__).resolve().parents[2]
p=root/'reports/motherboard-cost-20260930/build_ai_comms_bypass_manifest.py'
s=p.read_text().replace("OUT=ROOT/'reports/motherboard-bypass-owners-20260930'","OUT=ROOT/'reports/motherboard-bypass-owners-20260930/r03-wide-input-frozen'")
s=s.replace("22 if k=='dc24' else 2,[2] if k=='dc24' else [1]","2,[1]")
s=s.replace("notes=['REC input pins22/23 share the local VIN loop.'] if k=='dc24' else []","notes=['TMR4WI actual input2/return1, NC/remote pins are not supply escapes.']")
s=s.replace("14 if k=='dc24' else 4,[16] if k=='dc24' else [6]","6,[7]")
s=s.replace("\ncom='motherboard_comms'","\nadd(ai,'C14756',b['precision_ldo'],1,[5,7],'LDO_output_storage',notes=['Effective >=1uF required over tolerance/bias/temp; nominal2.2uF. Place at actual OUT1/GND5/EP7 loop.'])\nadd(ai,'C14757',b['precision_ldo'],1,[5,7],'LDO_output_HF')\n\ncom='motherboard_comms'")
s=s.replace('len(rows)==94','len(rows)==96').replace("'motherboard_analog_input':166","'motherboard_analog_input':165").replace('capacitor_count=94','capacitor_count=96').replace('94 source capacitors: 55 in AI166','96 source capacitors: 57 in AI165').replace('PASS 94 exact capacitor owners','PASS 96 exact capacitor owners')
# The same two converter-side C14702/03 now also serve the real LDO IN6/EN4/GND5/EP7 loop;
# retain converter ownership and attach the second actual consumer as an explicit placement relationship.
s=s.replace("negative=[]","for row in rows:\n    if row['capacitor_reference'] in ['C14702','C14703']:\n        row['additional_actual_owner']={'reference':MODELS[ai]['blocks']['precision_ldo'],'power_pins':['6','4'],'matching_return_pins':['5','7'],'shared_net':'AI_5V_PREREG_12V','local_loop_required':True}\nnegative=[]")
exec(compile(s,str(p),'exec'))
