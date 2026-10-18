"""Adversarial host gate fixtures; no KiCad load or board evidence claim."""
import json,sys
from pathlib import Path
from types import SimpleNamespace
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import audit_aux_exact as A
P,S=A.P,A.S
from shapely.geometry import Point,LineString,box
from shapely.strtree import STRtree
NET='/fixture/signal';FOREIGN='/fixture/foreign'

def fixture_model(rows,pads=None,vias=None):
    records={'F.Cu':rows,'B.Cu':[]}
    return SimpleNamespace(records=records,trees={l:STRtree([r['shape'] for r in rs]) for l,rs in records.items()},
                           domains={NET:'DOM_LOGIC',FOREIGN:'DOM_LOGIC'},pads=pads or {},hard_trees={},hard={},
                           outline=box(-5,-5,5,5),g={'copper_layers':['F.Cu','B.Cu'],'vias':vias or [],'pads':[]})
def run():
    out=HERE/'aux-audit-negative-controls-r1.json'
    if out.exists():raise ValueError('Fresh controls receipt required')
    controls=[]
    v={'uuid':'probe-via','kind':'via','at':[0,0],'d':.5,'drill':.2,'net':NET}
    cases=[('foreign_copper_clearance',{'uuid':'foreign-pad','kind':'pad','net':FOREIGN,'domain':'DOM_LOGIC','pad_id':'Q.1#0','shape':Point(.4,0).buffer(.1)}),
           ('same_net_SMD_registration',{'uuid':'own-smd','kind':'pad','net':NET,'domain':'DOM_LOGIC','pad_id':'Q.1#0','shape':Point(.35,0).buffer(.1)}),
           ('unrelated_drill_clearance',{'uuid':'foreign-hole','kind':'hole','net':FOREIGN,'shape':Point(.44,0).buffer(.1)})]
    for name,foreign in cases:
        model=fixture_model([foreign],pads={'Q.1#0':{'smd':True}})
        errors,_,_=A.clearance(model,{'probe-via':v},{'probe-via'},set())
        if not errors:raise ValueError('Gate failed to reject '+name)
        controls.append({'control':name,'bad_fixture_rejected':True,'detected_errors':len(errors)})
    model=fixture_model([],vias=[{'uuid':'other-via','x':.79,'y':0,'drill':.2}])
    errors,_,_=A.clearance(model,{'probe-via':v},{'probe-via'},set())
    if not any(r.get('kind')=='ordinary_via_pitch' for r in errors):raise ValueError('Ordinary pitch gate ineffective')
    controls.append({'control':'ordinary_via_pitch','bad_fixture_rejected':True})
    # The same source pad pair may connect only through an actually flashed
    # annulus. A nominal through span never supplies the suppressed B annulus.
    rows=[]
    def rec(kind,uid,layer,shape,key,pid=None):
        r={'kind':kind,'uuid':uid,'layer':layer,'shape':shape,'key':key,'net':NET}
        if pid:r['pad_id']=pid
        rows.append(r)
    rec('pad','p0','F.Cu',Point(0,0).buffer(.2),('p','P0.1#0'),'P0.1#0')
    rec('track','t0','F.Cu',LineString([(0,0),(1,0)]).buffer(.1),('t','t0'))
    for l in ('F.Cu','B.Cu'):rec('via','v0',l,Point(1,0).buffer(.25),('v','v0'))
    rec('track','t1','B.Cu',LineString([(1,0),(2,0)]).buffer(.1),('t','t1'))
    rec('pad','p1','B.Cu',Point(2,0).buffer(.2),('p','P1.1#0'),'P1.1#0')
    model=SimpleNamespace(own={NET:rows},g={'copper_layers':['F.Cu','B.Cu']})
    uf,_=P.physical(model,NET,{'v0':{'F.Cu','B.Cu'}})
    if uf.find(('p','P0.1#0'))!=uf.find(('p','P1.1#0')):raise ValueError('Positive actual-annulus control failed')
    uf,_=P.physical(model,NET,{'v0':{'F.Cu'}})
    if uf.find(('p','P0.1#0'))==uf.find(('p','P1.1#0')):raise ValueError('Suppressed annulus fabricated contact')
    controls.append({'control':'suppressed_actual_via_annulus','bad_fixture_rejected':True,'positive_actual_annulus_fixture_connected':True})
    # Native pads can remain connected while a pad-free branch is severed.
    # Full entity obligations must catch that failure independently of pads.
    branch={'kind':'track','uuid':'branch','layer':'F.Cu','shape':LineString([(0,0),(0,1)]).buffer(.1),'key':('t','branch'),'net':NET}
    bridge={'kind':'track','uuid':'bridge','layer':'F.Cu','shape':LineString([(0,1),(0,2)]).buffer(.1),'key':('t','bridge'),'net':NET}
    stub={'kind':'track','uuid':'stub','layer':'F.Cu','shape':LineString([(0,2),(1,2)]).buffer(.1),'key':('t','stub'),'net':NET}
    source=SimpleNamespace(own={NET:rows+[branch,bridge,stub]},g=model.g)
    uf,groups=P.physical(source,NET,{'v0':{'F.Cu','B.Cu'}})
    obligations=[{r['key'] for r in group['records'] if r['uuid']!='bridge'} for group in groups]
    damaged=SimpleNamespace(own={NET:rows+[branch,stub]},g=model.g)
    uf,_=P.physical(damaged,NET,{'v0':{'F.Cu','B.Cu'}})
    pads_still_connected=uf.find(('p','P0.1#0'))==uf.find(('p','P1.1#0'))
    branch_loss=any(len({uf.find(k) for k in ks})>1 for ks in obligations)
    if not pads_still_connected or not branch_loss:raise ValueError('Pad-free branch loss control ineffective')
    controls.append({'control':'surviving_pad_free_branch_loss','bad_fixture_rejected':True,'pad_relationship_still_connected':True})
    for p in (Path(__file__),Path(A.__file__),Path(P.__file__),Path(S.__file__)):A.read(p)
    result={'schema':'aux-host-gate-negative-controls-r1','verdict':'PASS','controls':controls,'read_files_sha256':A.READS,
            'evidence_class':'Adversarial synthetic host fixtures only; not board/native/electrical evidence','native_jobs':0,'gpu_jobs':0}
    out.write_text(json.dumps(result,indent=1)+'\n',encoding='utf-8');print(json.dumps({'verdict':'PASS','controls':len(controls),'receipt':str(out)}))
if __name__=='__main__':run()
