"""Selected R42 bridge zone chunks for a separate exploratory native trial."""
import json,pickle,hashlib,sys,uuid
from shapely.geometry import Polygon,MultiPolygon
import core_inner_feed_r18 as I
L=I.L;p=I.p;FIELD=L.OUT.parent/'field-power';sys.path.insert(0,str(FIELD))
from emit_logic_zones_r1 import render
from verify_source import parse,children,child,atom
OUT=L.OUT/'owned-io3-selected-native-zones-r46'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def canonical_ring(r):return [[int(round(x*1e6)),int(round(y*1e6))] for x,y in list(r.coords)[:-1]]
def main():
    assert not OUT.exists();OUT.mkdir();prior=L.OUT/'owned-io3-layer-escape-repair-r42';zs=pickle.loads((prior/'proposed-zones.pkl').read_bytes());assert len(zs)==1
    dr=L.OUT/'owned-io3-native-recipe-r45/receipt.json';assert sha(dr)=='33f764e286538085341d130d7ede6f5d3d2a7330924605d9ee4d94eb52d5c0eb'
    g,h,binding,allzones,candidate=pickle.loads((prior/'model.pkl').read_bytes());rows=[];quant=[]
    for z in zs:
        outline=z.get('zone_outline_shape',z['shape']);canonical=[]
        for i,part in enumerate(sorted(p.hubs.components(outline),key=lambda x:(-x.area,x.bounds))):
            rings=[canonical_ring(part.exterior)]+[canonical_ring(r) for r in part.interiors]
            exact=Polygon([(x/1e6,y/1e6) for x,y in rings[0]],[[(x/1e6,y/1e6) for x,y in r] for r in rings[1:]]);assert exact.is_valid;canonical.append(exact)
            uid=z['uuid'] if i==0 else str(uuid.uuid5(uuid.UUID(z['uuid']),'io3-selected-detached-outer-'+str(i)))
            chunk=render(uid,z['net'],z['layer'],exact).replace('(priority 20)','(priority 124)').replace('Retained LOGIC_GND return repair','Selected IO3 source escape bridge')
            file=OUT/(uid+'.zone-chunk');file.write_text(chunk,encoding='utf-8',newline='');a=parse(chunk)
            rt=[[[round(float(v[1])*1e6),round(float(v[2])*1e6)] for v in child(q,'pts')[1:]] for q in children(a,'polygon')]
            assert rt==rings and atom(a,'net')==z['net'] and atom(a,'priority')=='124'
            rebuilt=Polygon([(x/1e6,y/1e6) for x,y in rt[0]],[[(x/1e6,y/1e6) for x,y in r] for r in rt[1:]]);assert rebuilt.equals(exact)
            assert not children(a,'filled_polygon') and not children(a,'fill_segments')
            contacts=[]
            for q in h['pads']:
                if q['net']==z['net'] and any(s.intersects(exact) for s in p.base.polygons(q['layers'].get(z['layer'],[]))):contacts.append({'kind':'pad','uuid':q['uuid'],'ref':q['ref'],'pin':q['num']})
            for q in h['vias']:
                from shapely.geometry import Point
                if q['net']==z['net'] and z['layer'] in q['flashed'] and Point(q['x'],q['y']).buffer(q['d']/2).intersects(exact):contacts.append({'kind':'via','uuid':q['uuid'],'at':[q['x'],q['y']]})
            rows.append({'uuid':uid,'proposal_uuid':z['uuid'],'raw_net':z['net'],'layer':z['layer'],'chunk_file':str(file.resolve()),'chunk_sha256':sha(file),'outline_integer_nm':rings,'outline_area_mm2':exact.area,'holes':len(rings)-1,'minimum_0p15_interior_survives':not exact.buffer(-.075).is_empty,'same_net_discrete_contacts_in_complete_host_model':contacts})
        final=canonical[0] if len(canonical)==1 else MultiPolygon(canonical)
        quant.append({'proposal_uuid':z['uuid'],'before_WKB_SHA256':hashlib.sha256(outline.wkb).hexdigest(),'integer_after_WKB_SHA256':hashlib.sha256(final.wkb).hexdigest(),'explicit_representation_added_area_mm2':final.difference(outline).area,'explicit_representation_removed_area_mm2':outline.difference(final).area})
    (OUT/'receipt.json').write_text(json.dumps({'verdict':'SELECTED_IO3_NATIVE_TRIAL_CHUNKS_FINAL_MUTUAL_GATES_OPEN','parent_native_board_sha256':'eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a','R42_model_SHA256':sha(prior/'model.pkl'),'native_zone_rows':rows,'new_zone_chunks':len(rows),'IO3_exact_delete_add_discrete_recipe_file':str(dr.resolve()),'IO3_exact_delete_add_discrete_recipe_SHA256':sha(dr),'integer_representation_ledger':quant,'required_new_via_native_postfill_flash':['F.Cu','In1.Cu'],'scope':'Selected bridge plus exact two IO3 owned deletions, one via, two segments; other complete R38 proposals excluded. This trial cannot validate complete source relationships or no-loss outside selected fresh native fill.','full_mutual_contact_current_native':'OPEN','final_guarded_antipad_and_all_same_net_zone_union':'OPEN','native_jobs':0,'board_written':False},indent=2)+'\n')
    print('IO3_SELECTED_NATIVE_ZONE_RECIPE',len(rows),sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
