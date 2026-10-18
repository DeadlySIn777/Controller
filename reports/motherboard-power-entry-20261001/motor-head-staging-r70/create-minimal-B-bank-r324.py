import ast,json
from pathlib import Path
p=Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/BankB-minimal-pose-screen-r322.py');t=ast.parse(p.read_text());base=next(ast.literal_eval(q.value)for q in t.body if isinstance(q,ast.Assign)and any(isinstance(x,ast.Name)and x.id=='base'for x in q.targets));Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/BankB-minimal-poses-r324.json').write_text(json.dumps(base,indent=2))
s=Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/bankB-builder-r165.py').read_text();s=s.replace('bankB-poses-r165.json','BankB-minimal-poses-r324.json').replace("or r=='R11047'","or r in ['R11047','R11046']")
# Only current Bank B head/latch/clock/bypasses/biases move. All four existing contacts and both complete health LED graphs remain unchanged.
s=s.replace("wire('U11024','2','U11020','4',.3,pcbnew.F_Cu,'CORE_LED_B_actual_sink',step=.5,padding=30,max_nodes=90000)","# Existing CORE_LED_B actual sink graph remains unchanged.")
a=s.index(" bn=ps['U11030','2'].GetNetname();");z=s.index(" # Native fill must join",a);s=s[:a]+''' # Existing FIELD_LED_B sink and both series-LED current sources remain unchanged.
 wire('U11011','7','R11046','2',.2,pcbnew.B_Cu,'B_PG_actual_receiving_pullup',step=.25,padding=15,max_nodes=70000)
 wire('R11046','1','R11043','1',.25,pcbnew.F_Cu,'B_PG_actual_existing_IO3_source')
 # Actual clock buffer receives its own original C11087 bypass.
 wire('U11033','5','C11087','1',.25,pcbnew.B_Cu,'B_clock_buffer_actual_own_bypass')
 wire('U11033','3','C11087','2',.25,pcbnew.B_Cu,'B_clock_buffer_actual_own_return')
 wire('C11087','1','C11059','1',.35,pcbnew.B_Cu,'B_clock_buffer_actual_RAW_feed',step=.25,padding=12,max_nodes=45000)
''' + s[z:];Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/BankB-minimal-builder-r324.py').write_text(s)
