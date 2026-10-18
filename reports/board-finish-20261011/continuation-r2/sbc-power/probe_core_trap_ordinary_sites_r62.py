"""Read-only local blocker census for the three remaining CORE traps."""
import json,pickle,hashlib
from pathlib import Path
from shapely import STRtree
from shapely.geometry import Point
import core_inner_feed_r18 as I
L=I.L;p=I.p;G=I.G
OUT=L.OUT/'core-ordinary-trap-site-census-r62'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def main():
    assert not OUT.exists();OUT.mkdir();f=L.OUT/'core-protected-outward-joint-r59/owned-composition-checkpoint.pkl';g,h,b,z,_=pickle.loads(f.read_bytes())
    net=next(q['net'] for q in h['pads'] if (q['ref'],q['num'])==('R11022','2'));recs=[];holes=[];smd=[]
    for q in h['pads']:
        for l,rs in q['layers'].items():
            for sh in p.base.polygons(rs):
                recs.append({'uuid':q['uuid'],'net':q['net'],'layer':l,'kind':'pad','ref':q['ref'],'pin':q['num'],'shape':sh})
                if q['smd']:smd.append({'uuid':q['uuid'],'ref':q['ref'],'pin':q['num'],'shape':sh})
        for sh in p.base.polygons(q.get('hole') or []):holes.append({'uuid':q['uuid'],'kind':'pad_hole','shape':sh})
    for q in h['tracks']:recs.append({'uuid':q['uuid'],'net':q['net'],'layer':q['layer'],'kind':'track','geometry':q,'shape':p.base.body(q)})
    for q in h['vias']:
        pt=Point(q['x'],q['y']);holes.append({'uuid':q['uuid'],'kind':'via_hole','shape':pt.buffer(q['drill']/2)})
        for l in q['flashed']:recs.append({'uuid':q['uuid'],'net':q['net'],'layer':l,'kind':'via','shape':pt.buffer(q['d']/2),'geometry':q})
    for q in z:recs.append({'uuid':q['uuid'],'net':q['net'],'layer':q['layer'],'kind':'owned_new_zone','shape':q['shape'],'clearance_mm':float(q.get('clearance_mm',.15))})
    rt=STRtree([q['shape'] for q in recs]);st=STRtree([q['shape'] for q in smd]);ht=STRtree([q['shape'] for q in holes]);sites=[]
    for ref,pin,at in [('U9001','10',(345.85,176.15)),('R17031','1',(249.127,32.222)),('U11007','6',(265.35,114.6))]:
        pt=Point(at);errors=[]
        for ii in rt.query(pt.buffer(1.2),predicate='intersects'):
            q=recs[int(ii)]
            if p.norm(q['net'])==p.norm(net):continue
            clear=max(G.gap(h,net,q['net']),float(q.get('clearance_mm',.15)))+.025;dist=pt.distance(q['shape']);required=.25+clear
            if dist<required:errors.append({**{k:v for k,v in q.items() if k!='shape'},'kind_gate':'all_layer_annulus_to_foreign_Cu','center_to_Cu_mm':dist,'required_mm':required,'shortfall_mm':required-dist})
        for ii in st.query(pt.buffer(.6),predicate='intersects'):
            q=smd[int(ii)];dist=pt.distance(q['shape']);required=.1+.275
            if dist<required:errors.append({**{k:v for k,v in q.items() if k!='shape'},'kind_gate':'drill_to_every_SMD','center_to_Cu_mm':dist,'required_mm':required,'shortfall_mm':required-dist})
        for ii in ht.query(pt.buffer(.8),predicate='intersects'):
            q=holes[int(ii)];dist=pt.distance(q['shape']);required=.1+.275
            if dist<required:errors.append({**{k:v for k,v in q.items() if k!='shape'},'kind_gate':'drill_to_every_old_new_drill','center_to_hole_mm':dist,'required_mm':required,'shortfall_mm':required-dist})
        sites.append({'ref':ref,'pin':pin,'site_mm':at,'ordinary_diameter_mm':.5,'drill_mm':.2,'errors':errors})
    (OUT/'receipt.json').write_text(json.dumps({'verdict':'READ_ONLY_LOCAL_BLOCKER_CENSUS_NO_GEOMETRY_ACCEPTED','model_file':str(f.resolve()),'model_sha256':sha(f),'sites':sites,'native_jobs':0,'board_written':False},indent=2)+'\n');print('CORE_SITE_CENSUS_R62',[(q['ref'],len(q['errors'])) for q in sites],sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
