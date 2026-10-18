"""Correct normalized lookup only; serialized native raw tokens stay exact."""
import json,hashlib
from pathlib import Path
p=Path(__file__).resolve().parent
failed=p/'u19008-source-return-reference-r98'
if not (failed/'receipt.json').exists():(failed/'receipt.json').write_text(json.dumps({'verdict':'FAIL_GRAPH_LOOKUP_RAW_TOKEN_USED_WITH_NORMALIZED_FILTER','exception':'StopIteration locating J11005.2 using raw curly-slash lookup; physical reference corridor has zero missing area but no source return body was emitted.','source_file_sha256':hashlib.sha256((p/'construct_u19008_source_return_reference_r98.py').read_bytes()).hexdigest(),'native_jobs':0,'board_written':False},indent=1)+'\n',encoding='utf-8')
s=(p/'construct_u19008_source_return_reference_r98.py').read_text().replace("OUT=H/'u19008-source-return-reference-r98'","OUT=H/'u19008-source-return-reference-r99'").replace('gs=F.graph(a,gn);','gs=F.graph(a,C.norm(gn));').replace('controller-u19008-r98/','controller-u19008-r99/').replace("print('R98","print('R99")
exec(compile(s,str(p/'construct_u19008_source_return_reference_r98.py'),'exec'))
