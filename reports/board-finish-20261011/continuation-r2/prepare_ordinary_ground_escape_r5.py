"""Extend ordinary escape planning with a legal new, rooted ground-return stitch."""
import ast,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
def main():
    src=HERE/'new_via_escape_screen.py';raw=src.read_bytes();tree=ast.parse(raw.decode());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
    via=next(n for n in fn.body if isinstance(n,ast.FunctionDef) and n.name=='via_site')
    ground=ast.parse('''
def new_return_site(at):
    point=Point(at);body=point.buffer(.25,resolution=64);hole=point.buffer(.1,resolution=64)
    if not model.outline.buffer(-.775).covers(point):return None
    if len(smd.query(hole.buffer(.125),predicate='intersects')) or len(nv.query(body.buffer(.025),predicate='intersects')):return None
    if len(allvt.query(point.buffer(.8-1e-8),predicate='intersects')):return None
    if not all(refs[p].covers(body.buffer(.025)) for p in refs):return None
    cuts=[]
    for layer in g['copper_layers']:
        for i in model.trees[layer].query(body.buffer(.65),predicate='intersects'):
            r=model.records[layer][i]
            if r['kind']=='hole':
                if hole.distance(r['shape'])<.25+.025:return None
            elif r.get('net')=='/LOGIC_GND':continue
            elif r['kind']=='fill' and r.get('domain')=='DOM_LOGIC':
                if body.buffer(.175).intersects(r['shape']):cuts.append({'zone_uuid':r['uuid'],'layer':layer,'net':r['net'],'antipad_radius_mm':.425})
            else:
                required=.15 if r.get('domain')=='DOM_LOGIC' else .6
                if body.distance(r['shape'])<required+.025:return None
        for r in model.hard[layer]:
            if '/LOGIC_GND' not in r['exempt'] and body.buffer(.025).intersects(r['shape']):return None
    return {'at':list(at),'diameter_mm':.5,'drill_mm':.2,'raw_net':'/LOGIC_GND','source_anchor':'J11001.2#0','whole_copper_body_connected_reference_planes':['In1.Cu','In4.Cu'],'prospective_antipads':cuts,'all_six_native_annuli_required':True}
''').body[0]
    fn.body.insert(fn.body.index(via),ground)
    old=ast.unparse(via)
    find="if not options:\n        return None\n    distance, return_via = min(options, key=lambda x: x[0])"
    replace='''new_return=None
    if not options:
        for angle in range(32):
            theta=angle*2*math.pi/32
            ground_at=(round(at[0]+.95*math.cos(theta),9),round(at[1]+.95*math.sin(theta),9))
            site=new_return_site(ground_at)
            if site:
                new_return=site;distance=math.dist(at,ground_at);return_via={'uuid':None,'x':ground_at[0],'y':ground_at[1]};break
        if new_return is None:return None
    else:
        distance,return_via=min(options,key=lambda x:x[0])'''
    if old.count(find)!=1:raise ValueError('Exact inherited retained-return-only condition mismatch')
    changed=old.replace(find,replace)
    oldreturn="'D4_pitch_exception': pitch_exempt.covers(point)"
    if changed.count(oldreturn)!=1:raise ValueError('Exact return metadata derivation mismatch')
    changed=changed.replace(oldreturn,oldreturn+", 'new_return_stitch': new_return")
    fn.body[fn.body.index(via)]=ast.parse(changed).body[0]
    # New vias from the same prospective route must satisfy their mutual pitch.
    check=ast.parse('''
future=record['paths'][0]['new_signal_vias']
future_points=[v['at'] for v in future]+[v['new_return_stitch']['at'] for v in future if v.get('new_return_stitch')]
if any(math.dist(a,b)<.8-1e-8 for i,a in enumerate(future_points) for b in future_points[i+1:]):
    record['paths']=[]
else:
    record['paths'][0]['new_return_vias']=sum(v.get('new_return_stitch') is not None for v in future)
''').body
    inner_if=next(n for n in ast.walk(fn) if isinstance(n,ast.If) and isinstance(n.test,ast.Name) and n.test.id=='inner')
    append=next(i for i,n in enumerate(inner_if.body) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Attribute) and n.value.func.attr=='append' and isinstance(n.value.func.value,ast.Name) and n.value.func.value.id=='accepted')
    inner_if.body[append:append]=check
    # accepted must contain only a still-valid mutually spaced route.
    inner_if.body[append+len(check)]=ast.parse("if record['paths']:accepted.append(record)").body[0]
    derived=HERE/'new_via_escape_ground_r5.py'
    if derived.exists():raise ValueError('Fresh derived search required')
    derived.write_text(ast.unparse(ast.fix_missing_locations(tree))+'\n',encoding='utf-8')
    adapter=HERE/'continue_ordinary_escapes_r4.py';text=adapter.read_text(encoding='utf-8')
    text=text.replace('import new_via_escape_screen as R','import new_via_escape_ground_r5 as R').replace("R.OUT=HERE/'new-via-escape-r4'","R.OUT=HERE/'new-via-escape-r5'").replace("skip_nets={row['net'] for row in prior_plan['results']}","skip_nets={row['net'] for row in prior_plan['results'] if row['paths']}")
    wrapper=HERE/'continue_ordinary_escapes_r5.py'
    if wrapper.exists():raise ValueError('Fresh wrapper required')
    wrapper.write_text(text,encoding='utf-8')
    receipt={'original':str(src),'original_sha256':hashlib.sha256(raw).hexdigest(),'derived':str(derived),'derived_sha256':hashlib.sha256(derived.read_bytes()).hexdigest(),'wrapper':str(wrapper),'wrapper_sha256':hashlib.sha256(wrapper.read_bytes()).hexdigest(),'changes':['When no legal retained return lies within1mm, test32 new .5/.2 GND sites exactly.95mm from signal via','Both new return annuli bodies must lie wholly in actual J11001.2-rooted In1/In4 reference copper','Every drill/copper/keepout/domain clearance remains unchanged and all mutual new-via pitch checked','Reconsider failed retained-return-only nets; preserve previous audited ordinary route as obstacle'],'evidence_class':'finite host planner refinement; independent exact geometry and native all-contact/annulus/DRC/electrical gates remain OPEN','native_jobs':0,'board_emitted':False,'adopted':False}
    (HERE/'new-return-planner-derivation-r5.json').write_text(json.dumps(receipt,indent=1)+'\n',encoding='utf-8')
    print(json.dumps(receipt),flush=True)
if __name__=='__main__':main()
