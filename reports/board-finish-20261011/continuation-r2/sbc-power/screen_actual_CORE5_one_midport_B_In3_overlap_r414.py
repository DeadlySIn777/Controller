"""Repair generated layer-token spacing; preserve the R413 syntax failure."""
import json
from pathlib import Path
P=Path(__file__).resolve().parent
F=P/'exact-expanded-one-midport-B-In3-geography-r413.py'
(P/'R413-generated-layer-token-syntax-failure.json').write_text(json.dumps({'status':'PRE_GEOMETRY_SYNTAX_FAILURE','generated_script':str(F),'cause':'Quoted layer replacement joined the following and/not token','source_native_jobs_or_board_edits':0,'repair':'R414'},indent=1)+'\n',encoding='utf-8')
s=F.read_text(encoding='utf-8').replace('layerand','layer and').replace('layernot','layer not')
s=s.replace('CORE5-existing-LOAD-to-SOURCE-one-midport-B-In3-geography-r413','CORE5-existing-LOAD-to-SOURCE-one-midport-B-In3-geography-r414').replace('R413_LAYER','R414_LAYER').replace('R413_COMPLETE','R414_COMPLETE')
E=P/'exact-expanded-one-midport-B-In3-geography-r414.py';assert not E.exists();E.write_text(s,encoding='utf-8')
exec(compile(s,str(E),'exec'),{'__name__':'__main__','__file__':str(E)})
