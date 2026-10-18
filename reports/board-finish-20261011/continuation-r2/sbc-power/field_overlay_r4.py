"""Exact bound field return proposals and corrected C92 host geometry."""
import json,pickle,hashlib,copy
from pathlib import Path
from shapely import from_wkb
from shapely.ops import unary_union
import combined_overlay_r2 as B
L=B.L;p=B.p
FIELD=L.OUT.parent/'field-power/composed-field-geometry-r3';SHA='f6d2583961e906d6eb77d99a0e5bdff6fe750fea74eeed7e7751e666f6af9cb8'
def model(new_root_base=False):
    g,h,tail,binding=B.model(new_root_base);raw=(FIELD/'geometry.pkl').read_bytes();assert hashlib.sha256(raw).hexdigest()==SHA;fg=pickle.loads(raw);receipt=json.loads((FIELD/'receipt.json').read_text());assert receipt['geometry_sha256']==SHA
    original={z['uuid']:z for z in h['zones']};fz={z['uuid']:z for z in fg['zones']};missing=set(original)-set(fz);assert not missing,('field lost original zone definitions',missing)
    # Native source chunks remain root owned. Only field-owned prospective zone
    # fills and C92's corrected geometry are borrowed from this bound model.
    # Recompute all combined retreats from exact source fills. The field-only
    # retreat ledger is retained as evidence; reusing its already-cleared Cu
    # would hide legal openings created by the later CORE/control antipads.
    hh={**h,'zones':[copy.deepcopy(original[u]) for u in original]}
    pads=[q for q in h['pads'] if q['ref']!='C11092']+[copy.deepcopy(q) for q in fg['pads'] if q['ref']=='C11092'];fps=[q for q in h['footprints'] if q['ref']!='C11092']+[copy.deepcopy(q) for q in fg['footprints'] if q['ref']=='C11092'];hh.update(pads=pads,footprints=fps)
    returns=[]
    for uid,z in fz.items():
        if uid in original:continue
        assert z.get('prospective_not_native'),('unbound new field zone',uid)
        for layer,rs in z['fills'].items():returns.append({'uuid':uid,'label':'field-return-'+uid+'-'+layer,'net':z['net'],'layer':layer,'shape':unary_union(p.base.polygons(rs)),'field_geometry_sha256':SHA})
    assert len(returns)==9;domains=dict(h['domains_normalized']);domains.update(fg['domains_normalized']);hh['domains_normalized']=domains
    binding={**binding,'field_geometry_file':str((FIELD/'geometry.pkl').resolve()),'field_geometry_sha256':SHA,'field_receipt_sha256':hashlib.sha256((FIELD/'receipt.json').read_bytes()).hexdigest(),'field_retreat_count':len(receipt['prospective_foreign_clearance_voids']),'corrected_C92_geometry_incorporated':True,'effective_C92_native_pose_override':[80.5,210.5,0.],'effective_C92_pad_positions':[{'uuid':q['uuid'],'num':q['num'],'x':q['x'],'y':q['y']} for q in hh['pads'] if q['ref']=='C11092']}
    return g,hh,tail,binding,returns
if __name__=='__main__':
    g,h,tail,binding,returns=model();print('FIELD_OVERLAY',len(returns),binding['field_retreat_count']);print(json.dumps([{'net':q['net'],'layer':q['layer'],'area':q['shape'].area,'bounds':q['shape'].bounds} for q in returns]))
