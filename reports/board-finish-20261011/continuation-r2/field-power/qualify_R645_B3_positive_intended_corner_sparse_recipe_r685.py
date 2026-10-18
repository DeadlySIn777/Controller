"""Preserve R683 reader failure; use its exact explicit flashed-layer schema."""
import json,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent
P=H/'qualify_R645_B3_positive_intended_corner_sparse_recipe_r683.py'
O=H/'R645-B3-positive-intended-one-corner-qualified-sparse-native-recipe-r683'
F=O/'failure.json';assert not F.exists()
F.write_text(json.dumps({'status':'READER_SCHEMA_FAILURE_BEFORE_MODEL_OR_NATIVE_EMISSION','helper_SHA256':hashlib.sha256(P.read_bytes()).hexdigest(),'exact_error':'KeyError layers at same-raw via centre census; this exact current candidate binds actual layers under flashed. No geometry/model/native was emitted; partial WKB witnesses remain preserved.','explicit_correction':'Use v[flashed] directly, without broad span defaults or invented extra flash.'},indent=1)+'\n',encoding='utf-8')
s=P.read_text(encoding='utf-8');assert s.count("ly not in v['layers']")==1
s=s.replace("ly not in v['layers']","ly not in v['flashed']").replace('r683','r685').replace('R683','R685')
exec(compile(s,str(Path(__file__)),'exec'))
