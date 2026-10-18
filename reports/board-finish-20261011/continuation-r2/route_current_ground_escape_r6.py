"""Continue finite ordinary escape search after the already-audited first route.

Planning only. Conservative predicted antipads and all six annuli for the two
new, not yet native-attested vias obstruct the next search.
"""
import ast,json,hashlib,sys
from pathlib import Path
sys.dont_write_bytecode=True
import new_via_escape_current_ground_r6 as R
F=R.F;S=R.S;C=R.C;HERE=R.HERE
def main():
    source=Path(R.__file__);raw=source.read_bytes();tree=ast.parse(raw.decode())
    fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
    setup=ast.parse('''
prior_plan=json.loads(F.read(HERE/'new-via-escape-r2/result.json'))
skip_nets={row['net'] for row in prior_plan['results'] if row['paths']}
prior_audit=json.loads(F.read(HERE/'escape-signal-audit-r1/audit.json'))
if prior_audit['verdict']!='HOST_READY_NATIVE_ELECTRICAL_OPEN':raise ValueError('Prior route independently rejected')
F.read(Path(__file__))
F.read(Path(R.__file__))
for row in prior_plan['results']:
    for route in row['paths']:
        for layer,path in [(route['source_escape']['outer_layer'],route['source_escape']['outer_path']),('In3.Cu',route['inner_path']),(route['target_escape']['outer_layer'],route['target_escape']['outer_path'])]:
            for i,(a,b) in enumerate(zip(path['points_mm'],path['points_mm'][1:])):
                g['tracks'].append({'uuid':'PLANNED_PREVIOUS_'+layer+'_'+str(i),'net':row['net'],'a':a,'b':b,'w':.2,'layer':layer})
        for via in route['new_signal_vias']:
            g['vias'].append({'uuid':'PLANNED_PREVIOUS_VIA_'+repr(via['at']),'net':row['net'],'x':via['at'][0],'y':via['at'][1],'d':.5,'drill':.2,'flashed':g['copper_layers']})
''').body
    # The inherited one-line initialization contains the g assignment followed
    # by reservations; inject only once immediately after that complete line.
    index=next(i for i,n in enumerate(fn.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='g' for t in n.targets))
    fn.body[index+1:index+1]=setup
    model_index=next(i for i,n in enumerate(fn.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='model' for t in n.targets))
    fn.body[model_index+1:model_index+1]=ast.parse('''
cutters=unary_union([Point(v['x'],v['y']).buffer(.425,resolution=128) for v in g['vias'] if v['uuid'].startswith('PLANNED_PREVIOUS_VIA_')])
for layer in g['copper_layers']:
    for record in model.records[layer]:
        if record['kind']=='fill' and record.get('domain')=='DOM_LOGIC':record['shape']=record['shape'].difference(cutters)
    model.trees[layer]=STRtree([record['shape'] for record in model.records[layer]])
''').body
    loop=next(n for n in fn.body if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='row' and ast.unparse(n.iter)=="old['results']")
    loop.body.insert(0,ast.parse("if row['net'] in skip_nets:continue").body[0])
    # Record the exact only semantic changes, leaving all thresholds intact.
    R.OUT=HERE/'current-ground-escape-r6';R.OUT.mkdir(exist_ok=False)
    deriv={'source':str(source),'source_sha256':hashlib.sha256(raw).hexdigest(),'changes':['Skip the ten nets already examined','Predict prior independently audited six-item route as conservative obstacle','Remove prior antipads from reference fills before deriving rooted references'],'clearance_pitch_return_thresholds_unchanged':True,'native_jobs':0,'board_emitted':False,'adopted':False,'derived_function_source':ast.unparse(fn)}
    (R.OUT/'continuation-derivation.json').write_text(json.dumps(deriv,indent=1)+'\n',encoding='utf-8')
    # main normally creates OUT; it now exists to save the derivation before run.
    mk=next(n for n in ast.walk(fn) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='mkdir')
    mk.keywords=[ast.keyword(arg='exist_ok',value=ast.Constant(True))]
    namespace=dict(R.__dict__);namespace['R']=R;namespace['__file__']=str(Path(__file__))
    exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),'continued-ordinary-escape-r3','exec'),namespace)
    namespace['main']()
if __name__=='__main__':main()
