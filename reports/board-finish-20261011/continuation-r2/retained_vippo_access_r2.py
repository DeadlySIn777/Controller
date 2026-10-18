"""Reconcile already-present registered VIPPO contacts for retained-via planning.

No new hole or manufacturing waiver. Current exact pad/net/body relationships
must agree with the original explicit treatment registry; fab positions remain
a separate, unqualified reconciliation obligation.
"""
import ast,csv,hashlib,io,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
import retained_via_routes as R
F=R.F;S=R.S;HERE=R.HERE
from shapely.geometry import Point
from shapely.ops import unary_union

def approved_existing_contacts(g):
    registry=Path('Z:/pcb-runs/fab-check/assembly/vippo.csv');raw=F.read(registry);rows=list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
    if len(rows)!=291:raise ValueError('Original explicit VIPPO registry count differs')
    pads=[];names=[];nets=[]
    for pad in g['pads']:
        if not pad['smd']:continue
        for layer,polygons in pad['layers'].items():
            if layer not in ('F.Cu','B.Cu'):continue
            pads.append(unary_union(S.poly(polygons)));names.append(pad['ref']+'.'+pad['num']);nets.append(S.norm(pad['net']))
    tree=R.STRtree(pads);vias={v['uuid']:v for v in g['vias']};accepted={};rejected=[]
    for row in rows:
        v=vias.get(row['via_uuid'])
        if not v:rejected.append({'uuid':row['via_uuid'],'reason':'Absent current via'});continue
        if row['treatment']!='VIPPO: IPC-4761 Type VII resin fill, planarize, copper cap (both sides)' or not (v['drill']==float(row['drill_mm']) and v['d']==float(row['via_diameter_mm']) and S.norm(v['net'])==S.norm(row['via_net'])):
            rejected.append({'uuid':v['uuid'],'reason':'Original process/net/dimensions differ'});continue
        hole=Point(v['x'],v['y']).buffer(v['drill']/2,resolution=128);touch=tree.query(hole,predicate='intersects');actual={names[i] for i in touch};expected=set(row['pads'].split(';'))
        if actual!=expected or any(nets[i]!=S.norm(v['net']) for i in touch) or not all(pads[i].covers(hole) for i in touch):
            rejected.append({'uuid':v['uuid'],'reason':'Current exact native pad/drill relationship differs','actual':sorted(actual),'original_registered':sorted(expected)});continue
        accepted[v['uuid']]={'current_at':[v['x'],v['y']],'original_registered_at':[float(row['x_mm']),float(row['y_mm'])],'pads':sorted(actual),'source_net':v['net'],'diameter_mm':v['d'],'drill_mm':v['drill'],'treatment':row['treatment'],'no_drill_geometry_changed':True,'manufacture_position_reconciliation':'OPEN'}
    F.write('registered-retained-contact-reconciliation.json',{'registry':str(registry),'registry_sha256':hashlib.sha256(raw).hexdigest(),'current_board_sha256':g['sha256'],'matched_current_exact_contacts':accepted,'rejected':rejected,'new_holes':0,'manufacturing_process_or_placement_qualification':False,'adopted':False})
    return accepted

def main():
    source=Path(R.__file__);tree=ast.parse(source.read_text(encoding='utf-8'));fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
    R.OUT=HERE/'retained-vippo-access-r2'
    gindex=next(i for i,n in enumerate(fn.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='g' for t in n.targets))
    fn.body[gindex+1:gindex+1]=ast.parse('approved=approved_existing_contacts(g)').body
    for n in ast.walk(fn):
        if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='prior_paths' for t in n.targets):n.value=ast.List(elts=[],ctx=ast.Load())
        if isinstance(n,ast.If) and ast.unparse(n.test)=="old['paths'] or old['verdict'] == 'WITHHELD_GRAPH_MISMATCH'":n.test=ast.parse("old['verdict']=='WITHHELD_GRAPH_MISMATCH'",mode='eval').body
        if isinstance(n,ast.If) and ast.unparse(n.test)=="len(st.query(drill, predicate='intersects'))":n.test=ast.parse("len(st.query(drill,predicate='intersects')) and v['uuid'] not in approved",mode='eval').body
        if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ref' for t in n.targets):n.value=ast.parse("refs[S.REF_LAYER[layer]].buffer(-.125).union(allowance)",mode='eval').body
    # Retain the exact 1mm maximum here. D4-specific 1.2mm cases would need a
    # separate exact component/return mapping, not a global radius enlargement.
    node=next(n for n in fn.body if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='v')
    if not any(isinstance(n,ast.If) and 'not in approved' in ast.unparse(n.test) for n in ast.walk(node)):raise ValueError('Exact registered-contact exclusion derivation failed')
    fn.body.insert(1,ast.parse('F.read(Path(__file__))\nF.read(Path(R.__file__))').body[0]);fn.body.insert(2,ast.parse('F.read(Path(R.__file__))').body[0])
    namespace=dict(R.__dict__);namespace.update(approved_existing_contacts=approved_existing_contacts,R=R,__file__=str(Path(__file__)))
    exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),'retained-exact-registered-contact-planning','exec'),namespace)
    namespace['main']()
if __name__=='__main__':main()
