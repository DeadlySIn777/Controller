import sys,json
from pathlib import Path
sys.path[:0]=[str(Path.cwd()/'tools'),str(Path(__file__).parent)]
import pcbnew
from check_exact_endpoint_antipad_union_r01 import ExactEndpointUnionCheck
b=pcbnew.LoadBoard(sys.argv[1]);decl=json.loads(Path(sys.argv[2]).read_text());actual={t.m_Uuid.AsString():t for t in b.GetTracks()};t=actual['9e3b3c61-a4fa-4f6d-a8e3-3105c611f45c'];check=ExactEndpointUnionCheck(b,{t.GetNetname():decl})
try:check.segment(t,decl)
except ValueError as error:
 print(json.dumps(dict(rejected=True,reason=str(error))))
else:
 print(json.dumps(dict(rejected=False)))
 sys.exit(1)
