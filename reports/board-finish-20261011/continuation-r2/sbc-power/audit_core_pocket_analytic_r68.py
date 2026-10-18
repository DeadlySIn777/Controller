"""Independent analytic barrel/cap geometry checks on R64's exact additions."""
import json,pickle,hashlib
from pathlib import Path
from shapely import STRtree
from shapely.geometry import Point,LineString
import core_inner_feed_r18 as I
L=I.L;p=I.p;G=I.G
OUT=L.OUT/'core-pocket-independent-analytic-r68'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def main():
    assert not OUT.exists();OUT.mkdir();m=L.OUT/'remaining-core-reachable-ordinary-pockets-r64/model.pkl';assert sha(m)=='b64dcb07508abee53cd4d1935a3894d21fe78bc5908cab5ebb0f3b183adade87';g,h,b,z,c=pickle.loads(m.read_bytes());df=m.parent/'proposed-discrete.pkl';d=pickle.loads(df.read_bytes());nf=m.parent/'new-CORE-zones.pkl';nz=pickle.loads(nf.read_bytes())
    newids={q['uuid'] for k in ('vias','tracks') for q in d[k]};recs={l:[] for l in I.LAYERS};holes=[];smd=[];pairs=[];errors=[]
    for q in h['pads']:
        for l,rs in q['layers'].items():
            for sh in p.base.polygons(rs):
                recs[l].append({'uuid':q['uuid'],'kind':'pad','net':q['net'],'shape':sh})
                if q['smd']:smd.append({'uuid':q['uuid'],'ref':q['ref'],'pin':q['num'],'shape':sh})
        for sh in p.base.polygons(q.get('hole') or []):holes.append({'uuid':q['uuid'],'shape':sh,'net':q['net'],'kind':'pad_hole'})
    for q in h['tracks']:recs[q['layer']].append({'uuid':q['uuid'],'kind':'track','net':q['net'],'shape':LineString([q['a'],q['b']]),'radius':q['w']/2})
    for v in h['vias']:
        pt=Point(v['x'],v['y']);holes.append({'uuid':v['uuid'],'kind':'via_hole','net':v['net'],'shape':pt,'radius':v['drill']/2})
        for l in v['flashed']:recs[l].append({'uuid':v['uuid'],'kind':'via','net':v['net'],'shape':pt,'radius':v['d']/2})
    trees={l:STRtree([q['shape'].buffer(q.get('radius',0)) for q in rs]) for l,rs in recs.items()};ht=STRtree([q['shape'].buffer(q.get('radius',0)) for q in holes]);st=STRtree([q['shape'] for q in smd])
    def record(kind,uid,other,dist,required,layer=None):
        row={'gate':kind,'new_uuid':uid,'other_uuid':other['uuid'],'layer':layer,'actual_gap_mm':dist,'required_gap_mm':required};pairs.append(row)
        if dist<required:errors.append(row)
    for v in d['vias']:
        pt=Point(v['x'],v['y'])
        for l in I.LAYERS:
            for ii in trees[l].query(pt.buffer(1.2),predicate='intersects'):
                q=recs[l][int(ii)]
                if q['net']==v['net']:continue
                record('via_annulus_foreign_Cu',v['uuid'],q,pt.distance(q['shape'])-v['d']/2-q.get('radius',0),G.gap(h,v['net'],q['net'])+.025,l)
        for ii in st.query(pt.buffer(.7),predicate='intersects'):
            q=smd[int(ii)];record('hole_every_SMD',v['uuid'],q,pt.distance(q['shape'])-v['drill']/2,.275)
        for ii in ht.query(pt.buffer(1),predicate='intersects'):
            q=holes[int(ii)]
            if q['uuid']==v['uuid']:continue
            record('hole_every_old_new_drill',v['uuid'],q,pt.distance(q['shape'])-v['drill']/2-q.get('radius',0),.275)
        for q in z:
            if q['net']==v['net']:continue
            record('via_foreign_owned_plane',v['uuid'],q,pt.distance(q['shape'])-v['d']/2,max(G.gap(h,v['net'],q['net']),float(q.get('clearance_mm',.15)))+.025,q['layer'])
    for t in d['tracks']:
        assert t['w']>=.2;line=LineString([t['a'],t['b']])
        for ii in trees[t['layer']].query(line.buffer(1),predicate='intersects'):
            q=recs[t['layer']][int(ii)]
            if q['net']==t['net']:continue
            record('analytic_round_segment_foreign_Cu',t['uuid'],q,line.distance(q['shape'])-t['w']/2-q.get('radius',0),G.gap(h,t['net'],q['net'])+.025,t['layer'])
        for q in z:
            if q['layer']==t['layer'] and q['net']!=t['net']:record('analytic_round_segment_owned_plane',t['uuid'],q,line.distance(q['shape'])-t['w']/2,max(G.gap(h,t['net'],q['net']),float(q.get('clearance_mm',.15)))+.025,t['layer'])
    for a in nz:
        for ii in trees[a['layer']].query(a['shape'].buffer(1),predicate='intersects'):
            q=recs[a['layer']][int(ii)]
            if q['net']==a['net']:continue
            record('new_plane_analytic_foreign_Cu',a['uuid'],q,a['shape'].distance(q['shape'])-q.get('radius',0),G.gap(h,a['net'],q['net'])+.025,a['layer'])
        for q in z:
            if q['layer']==a['layer'] and q['net']!=a['net']:record('new_plane_foreign_owned_plane',a['uuid'],q,a['shape'].distance(q['shape']),max(G.gap(h,a['net'],q['net']),float(a.get('clearance_mm',.15)),float(q.get('clearance_mm',.15)))+.025,a['layer'])
    receipt={'verdict':'PASS_SCOPED_ANALYTIC_APERTURE_CAP_PLANE' if not errors else 'FAIL_SCOPED_ANALYTIC_APERTURE_CAP_PLANE','model_sha256':sha(m),'new_discrete_sha256':sha(df),'new_zone_sha256':sha(nf),'errors':errors,'pairs':pairs,'exact_round_caps_and_barrel_radii_not_inscribed_polygon_distances':True,'all_old_retained_contacts_current_native_flashes_refill_DRC':'OPEN','native_jobs':0,'board_written':False}
    (OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print('CORE_POCKET_ANALYTIC_R68',len(errors),errors,sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
