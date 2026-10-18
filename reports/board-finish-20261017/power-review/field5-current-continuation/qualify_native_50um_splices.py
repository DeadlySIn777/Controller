"""Host requalification of the exact six native lattice splice targets, no fill."""
from pathlib import Path
P=Path(__file__).resolve().parent
SOURCE=P/'qualify_50um_In2_physical_widening.py'
s=SOURCE.read_text()
s=s.replace("OUT=HERE/'50um-current-In2-widening-host-qualification-r1'","OUT=HERE/'native-50um-splice-host-qualification-r1'")
s=s.replace("CON=HERE/'bounded-current-In2-widening-construction-r2'","CON=HERE/'native-50um-splice-construction-r3'")
start=s.index('    files=[ACTUAL/')
end=s.index('    unchanged=[]',start)
s=s[:start]+'''    files=[ACTUAL/'actual-combined-full-after-model.pkl',ACTUAL/'actual-combined-full-after-all-net-groups.pkl',CON/'receipt.json',CON/'prospective-native-splice-target-model.pkl',CON/'field-support-patch.wkb',CON/'field-all-positive-target-Cu.wkb',CON/'field-native-positive-intent.wkb',SOURCE,Path(__file__),Path(K.__file__),Path(RF.__file__)]
    inputs={str(p):sha(p)for p in files};g=pickle.loads(files[0].read_bytes());oldgroups=pickle.loads(files[1].read_bytes());receipt=json.loads(files[2].read_text());h=pickle.loads(files[3].read_bytes());support,delta,intent=[shapely.from_wkb(p.read_bytes())for p in files[4:7]]
    fz=next(z for z in g['zones']if z['uuid']==ZID);oldintent=outline(fz);oldCu=unary_union(K.L.poly(fz['fills'][LY]));oldroot=K.root(oldgroups[T.NET],'L11003','2');oldsource=unary_union([q['shape']for q in oldroot if q['kind']=='fill'and q['layer']==LY]);assert oldintent.difference(intent).is_empty
    assert all(p.intersection(oldsource).area>1e-8 for p in RF.parts(support))
    cuts=receipt['FG_native_negative_splices'];masks={q['uuid']:shapely.from_wkb((CON/(q['uuid']+'-literal-intent-negative.wkb')).read_bytes())for q in cuts}
    assert all(not q['native_Cu_cut']['empty']or q['native_Cu_cut']['area_mm2']==0 for q in cuts)
    put('bounded-constructor-recheck.json',{'growth_mm':.05,'support':summary(support),'actual_new_Cu_target':summary(delta),'field_intent':summary(intent),'literal_all_old_field_intent_retained':True,'every_support_patch_finite_source_Cu_overlap_mm2':[p.intersection(oldsource).area for p in RF.parts(support)],'100um_constructor':'REJECTED; not used.','no_drills_or_component_moves':True,'exact_native_lattice_splice_input':str(CON/'receipt.json')})
    put('exact-FG-In2-cut-obligations.json',cuts)
''' + s[end:]
# FG is assessed after its exact native negative Cu splices, not excluded.
s=s.replace("if net==T.NET or(q['kind']=='fill'and net==FG):continue","if net==T.NET:continue\n        if q['kind']=='fill'and net==FG:\n            hz=next(z for z in h['zones']if z['uuid']==q['uuid']);shape=unary_union(K.L.poly(hz['fills'][LY]));q=q|{'shape':shape}\n            if shape.is_empty:continue")
s=s.replace("sum(q['desired_Cu_removed']['area_mm2']for q in cuts)","sum(q['native_Cu_cut']['area_mm2']for q in cuts)")
s=s.replace("'OPEN; no unsafe native packet emitted'","'Exact six native lattice intents constructed; KiCad native roundtrip and full native AFTER remain OPEN'")
# Preserve physical graph artifacts for the matched current solver and native binding.
s=s.replace("    fieldroot=K.root(newgroups[T.NET],'L11003','2');", "    (OUT/'prospective-two-net-groups.pkl').write_bytes(pickle.dumps(newgroups,protocol=5))\n    fieldroot=K.root(newgroups[T.NET],'L11003','2');")
exec(compile(s,str(SOURCE),'exec'),globals())
