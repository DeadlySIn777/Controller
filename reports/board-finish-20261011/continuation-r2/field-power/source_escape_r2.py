"""Preserve r1 partial screen; use deterministic micron precision and checkpoint caches."""
import pathlib
from source_escape import *
from shapely import set_precision
import source_escape as M
M.OUT=M.HERE/'source-escape-r2.json'
text=pathlib.Path(M.__file__).read_text(encoding='utf-8')
text=text.replace("OUT=HERE/'source-escape-r1.json'", "OUT=HERE/'source-escape-r2.json'")
text=text.replace("['In1.Cu','In4.Cu','In2.Cu','In3.Cu','F.Cu','B.Cu']", "['In1.Cu','In4.Cu','In2.Cu','In3.Cu']")
text=text.replace('blocked=unary_union(obs);', 'blocked=set_precision(unary_union(obs),.001);')
text=text.replace("fr=outline.buffer(-.5-w/2-.025).difference(blocked.buffer(w/2));", "fr=set_precision(outline.buffer(-.5-w/2-.026),.001).difference(set_precision(blocked.buffer(w/2+.001),.001));")
text=text.replace("source-escape-checkpoint.json", "source-escape-r2-checkpoint.json")
text=text.replace(";print(bank,layer,", ";data=pickle.dumps(caches,protocol=5);(HERE/'source-escape-r2-partial.pkl').write_bytes(data);(HERE/'source-escape-r2-partial-binding.json').write_text(json.dumps({'cache_sha256':hashlib.sha256(data).hexdigest(),'board_sha256':g['sha256']},indent=1)+'\\n',encoding='utf-8');print(bank,layer,")
text=text.replace("source-escape-r1.pkl", "source-escape-r2.pkl").replace("source-escape-r1-binding.json", "source-escape-r2-binding.json")
text=text.replace("'scope':'Global", "'precision_mm':.001,'supersedes_partial_r1':'GEOS outer-layer topology error preserved via source-escape-checkpoint.json; this bounded r2 screens native flashed inner layers and checkpoints each layer. Additional conservative .001mm buffer applied before .001mm precision snap.','scope':'Global")
exec(compile(text,M.__file__,'exec'),dict(M.__dict__,set_precision=set_precision,__name__='__main__'))
