"""Complete the quoted-token spacing repair before any geometry work."""
import json,re
from pathlib import Path
P=Path(__file__).resolve().parent
F=P/'exact-expanded-one-midport-B-In3-geography-r414.py'
(P/'R414-generated-layer-token-syntax-failure.json').write_text(json.dumps({'status':'PRE_GEOMETRY_SYNTAX_FAILURE','generated_script':str(F),'cause':'Quoted layer replacement joined the following in token','source_native_jobs_or_board_edits':0,'repair':'R415'},indent=1)+'\n',encoding='utf-8')
s=F.read_text(encoding='utf-8').replace('layerin','layer in')
assert not re.search(r'\blayer(?:and|not|in)\b',s)
s=s.replace('CORE5-existing-LOAD-to-SOURCE-one-midport-B-In3-geography-r414','CORE5-existing-LOAD-to-SOURCE-one-midport-B-In3-geography-r415').replace('R414_LAYER','R415_LAYER').replace('R414_COMPLETE','R415_COMPLETE')
E=P/'exact-expanded-one-midport-B-In3-geography-r415.py';assert not E.exists();compile(s,str(E),'exec');E.write_text(s,encoding='utf-8')
exec(compile(s,str(E),'exec'),{'__name__':'__main__','__file__':str(E)})
