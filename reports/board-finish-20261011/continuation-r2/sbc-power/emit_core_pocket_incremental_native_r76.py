"""Exact native-ready R69 two-pocket additions, with honest scoped proof."""
import json,pickle,hashlib,sys,uuid
from pathlib import Path
from decimal import Decimal
from shapely.geometry import Polygon
import core_inner_feed_r18 as I
L=I.L;OUT=L.OUT/'core-pocket-incremental-native-recipe-r76'
sys.path.insert(0,str(L.OUT.parent/'field-power'))
from emit_logic_zones_r1 import render,PRIMARY
from verify_source import parse,children,child,atom
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def write(f,v):f.write_text(json.dumps(v,indent=2)+'\n')
def nm(x):
    a=Decimal(str(x))*1000000;assert a==a.to_integral_value(),x;return int(a)
def num(x):nm(x);return format(float(x),'.6f').rstrip('0').rstrip('.')
def main():
    assert not OUT.exists();OUT.mkdir();(OUT/'source-used.py').write_bytes(Path(__file__).read_bytes())
    parent=L.OUT/'core-pocket-outward-round-guards-r69';mf=parent/'model.pkl';df=parent/'proposed-discrete.pkl';zf=parent/'new-CORE-zones.pkl';rf=parent/'receipt.json';af=L.OUT/'core-pocket-independent-analytic-r71/receipt.json'
    assert sha(mf)=='48ce8a3f9708402708a139c8c642a447bf07e071c4e0b9216d51d8184ba54cff';assert sha(af)=='81cfdcf01be8735988284e526e77045e2969eccbf158848353b2721917a36695'
    g,h,b,z,c=pickle.loads(mf.read_bytes());_,ch,_,cz,_=pickle.loads((parent/'owned-correction-checkpoint.pkl').read_bytes());d=pickle.loads(df.read_bytes());newz=pickle.loads(zf.read_bytes())
    assert h==ch;assert [(q['uuid'],q['shape'].wkb,q.get('zone_outline_shape',q['shape']).wkb) for q in z]==[(q['uuid'],q['shape'].wkb,q.get('zone_outline_shape',q['shape']).wkb) for q in cz]
    assert len(d['vias'])==2 and len(d['tracks'])==7 and len(newz)==1
    cu=[];zr=[]
    for kind,rows in [('via',d['vias']),('segment',d['tracks'])]:
        for q in rows:
            if kind=='via':
                text='\t(via\n\t\t(at '+num(q['x'])+' '+num(q['y'])+')\n\t\t(size '+num(q['d'])+')\n\t\t(drill '+num(q['drill'])+')\n\t\t(layers "F.Cu" "B.Cu")\n\t\t(net '+json.dumps(q['net'])+')\n\t\t(uuid '+json.dumps(q['uuid'])+')\n\t)\n'
            else:
                text='\t(segment\n\t\t(start '+' '.join(num(v) for v in q['a'])+')\n\t\t(end '+' '.join(num(v) for v in q['b'])+')\n\t\t(width '+num(q['w'])+')\n\t\t(layer '+json.dumps(q['layer'])+')\n\t\t(net '+json.dumps(q['net'])+')\n\t\t(uuid '+json.dumps(q['uuid'])+')\n\t)\n'
            ast=parse(text);assert ast[0]==kind and atom(ast,'uuid')==q['uuid'] and atom(ast,'net')==q['net'];f=OUT/(q['uuid']+'.'+kind+'-chunk');f.write_text(text,newline='\n');cu.append({'kind':kind,'uuid':q['uuid'],'chunk_file':str(f.resolve()),'chunk_sha256':sha(f),'native_model':q})
    for q in newz:
        outline=q['zone_outline_shape'];parts=[outline] if outline.geom_type=='Polygon' else list(outline.geoms)
        for i,part in enumerate(parts):
            uid=q['uuid'] if len(parts)==1 else str(uuid.uuid5(uuid.UUID(q['uuid']),'native-outer-'+str(i)));settings={'priority':124,'local_clearance_mm':.15,'min_thickness_mm':.15,'pad_connect_mode':'FULL_SOLID','island_removal_mode':1,'thermal_gap_mm':.15,'thermal_bridge_width_mm':.3}
            for r in [part.exterior,*part.interiors]:
                for x,y in r.coords:nm(x);nm(y)
            text=render(uid,q['net'],q['layer'],part).replace('(priority 20)','(priority 124)').replace('Retained LOGIC_GND return repair','CORE two-pocket supply bridge')
            ast=parse(text);rs=[[(nm(float(x[1])),nm(float(x[2]))) for x in child(pp,'pts')[1:]] for pp in children(ast,'polygon')];wanted=[[(nm(x),nm(y)) for x,y in list(r.coords)[:-1]] for r in [part.exterior,*part.interiors]];assert rs==wanted;assert int(atom(ast,'priority'))==124 and atom(ast,'net')==q['net'] and atom(ast,'layer')==q['layer']
            f=OUT/(uid+'.zone-chunk');f.write_text(text,newline='\n');zr.append({'uuid':uid,'proposal_uuid':q['uuid'],'part_index':i,'net_raw':q['net'],'layer':q['layer'],'chunk_file':str(f.resolve()),'chunk_sha256':sha(f),'declared_native_settings':settings,'holes':len(part.interiors),'intended_area_mm2':part.area,'minimum_web_screen_nonempty_015mm_eroded_interior':not part.buffer(-.075).is_empty,'integer_nm_ring_AST_exact':True})
    receipt={'verdict':'EXACT_INCREMENTAL_NATIVE_CHUNKS_SCOPED_GEOMETRY_SOURCE_PASS_FINAL_COMPOSITION_OPEN','parent_full_host_model_sha256':sha(mf),'R69_receipt_sha256':sha(rf),'analytic_R71_receipt_sha256':sha(af),'analytic_checkpoint_final_model_discrete_and_owned_shapes_exact':True,'incremental_discrete_sha256':sha(df),'incremental_zones_sha256':sha(zf),'native_discrete_rows':cu,'native_zone_rows':zr,'required_new_via_actual_native_flashes':[{'uuid':d['vias'][0]['uuid'],'required':['B.Cu','In1.Cu']},{'uuid':d['vias'][1]['uuid'],'required':['F.Cu','In1.Cu']}],'all_prior_CORE_field_protected_and_retained_contact_dependencies':'Exact full R69 model; eedf-only selected clone cannot grant source topology of prior new planes.','existing_native_deletes':[],'existing_native_footprint_changes':[],'final_union_and_full_foreign_contact_current_native_refill_DRC_gates':'OPEN','original_native_board_and_source_unchanged':True,'native_jobs':0,'board_written':False,'native_zone_parser_primary_source':PRIMARY}
    write(OUT/'receipt.json',receipt);print('R76_NATIVE_INCREMENT',len(cu),len(zr),sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
