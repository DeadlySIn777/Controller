import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
source=HERE/'dic-stitch-r1/screen_dic_stitch.py'
destination=HERE/'dic-stitch-r2/screen_dic_stitch.py'
if destination.exists():raise ValueError('Distinct derivation only')
old="    if '(constraint hole_size (min 0.20mm))' not in rules or '(constraint hole_to_hole (min 0.25mm))' not in rules:raise ValueError('Original ordinaryvia/hole contract differs')"
new="""    project=json.loads(S.read(R.PRO));native_rules=project['board']['design_settings']['rules']
    if '(constraint hole_size (min 0.20mm))' not in rules or native_rules['min_hole_to_hole']!=.25 or native_rules['min_hole_clearance']!=.25 or native_rules['min_via_diameter']>.5:
        raise ValueError('Original custom0.20drill and native0.25hole/0.5via contract differs')
    if next(c for c in project['net_settings']['classes'] if c['name']=='DOM_LOGIC')['track_width']!=.2:raise ValueError('Ordinary LOGIC default width changed')"""
text=source.read_text(encoding='utf-8')
if text.count(old)!=1:raise ValueError('Expected isolated check missing')
text=text.replace(old,new).replace('dic-own-return-stitch-bounded-source-r1','dic-own-return-stitch-bounded-source-r2')
destination.parent.mkdir(exist_ok=True)
destination.write_text(text,encoding='utf-8')
receipt={'schema':'dic-stitch-source-derivation-r2','source_path':str(source),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'derived_path':str(destination),'derived_sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),'change':'Read hole_to_hole and hole_clearance minima from pinned native project settings, keep customhole_size min0.20 from originaldru. AssertDOM_LOGIC .2mm default. No rule/design mutation.','prior_run':'r1 stopped at incorrect assumption hole_to_hole was in.dru; no path evaluation/native job/board output, therefore not a feasibility failure','native_jobs':0,'board_emitted':False}
(destination.parent/'derivation.json').write_text(json.dumps(receipt,indent=1)+'\n',encoding='utf-8')
print(json.dumps(receipt))
