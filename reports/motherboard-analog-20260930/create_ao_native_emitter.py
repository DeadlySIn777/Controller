"""Initial source-authoring helper, never a manufacturing exporter."""
from pathlib import Path
root=Path(__file__).resolve().parents[2]
p=root/'tools/hardware_build_motherboard_analog_output.py'
if 'def build(out=OUT):' in p.read_text(encoding='utf-8'):raise SystemExit('Initial emitter already authored. Regenerate using the final tools builder.')
s=(root/'tools/hardware_build_motherboard_process.py').read_text(encoding='utf-8')
t=s[s.index('def build(out=OUT):'):]
t=t.replace('motherboard_process','motherboard_analog_output').replace('Process source','Analog output source').replace('Motherboard PWM and floating process control','Motherboard independent isolated analog outputs')
t=t.replace('83.82+(ic//7)*139.7','83.82+(ic//7)*160.02').replace('800.1+(pas//17)*30.48','1201.42+(pas//17)*30.48').replace('1371.6+(bnd//7)*190.5','1691.64+(bnd//7)*190.5').replace('y=1600.2','y=2080.26').replace('1270 1650','1270 2200').replace('MOTION_5V_RAW','CORE_24V_PROTECTED').replace('#FLG144','#FLG146')
start=t.index(" note='");end=t.index('\n items.append',start)
t=t[:start]+" note='ACTUAL TWO ISOLATED AO ISLANDS / AD5683R-3 real SDO and hardware RESET, precision amplifier, normally CLOSED input clamp and normally OPEN output disconnect.\\nADS1115 reads actual terminal,12V,5V and reference; no cached command readback. Native source only, target/precision/20msqualification remain.'"+t[end:]
p.write_text(p.read_text(encoding='utf-8')+'\n'+t,encoding='utf-8')
