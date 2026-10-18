"""Compose the exact C zone into R70 only for declared-priority contact scope."""
import json,pickle,hashlib,sys,copy
from pathlib import Path
from shapely.geometry import Polygon
HERE=Path(__file__).resolve().parent;R2=HERE.parent
sys.path.insert(0,str(R2/'field-power'))
from verify_source import parse,children,child,atom
OUT=HERE/'c-reference-priority-conflict-adapter-r67'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def digest(shape):return hashlib.sha256(shape.wkb).hexdigest()
def write(f,v):f.write_text(json.dumps(v,indent=2)+'\n')
def settings(z):return [float(z.get('clearance_mm',.15)),float(z.get('min_thickness_mm',.15)),z.get('pad_connect_mode','FULL_SOLID'),int(z.get('priority',124)),int(z.get('island_removal_mode',1)),float(z.get('thermal_gap_mm',.15)),float(z.get('thermal_bridge_width_mm',.3))]
def main():
    assert not OUT.exists();OUT.mkdir()
    base=R2/'field-power/regulated-final-power-search-base-r70/model.pkl';assert sha(base)=='1368cee2cc2e18bc670a2875f31c4148b6d8792bbc67e89e65289107d923b73d'
    g,h,b,z,_=pickle.loads(base.read_bytes());authority=R2/'coupled-recovery/c10036-native-owned-ledger-r32/receipt.json';assert sha(authority)=='017fb0ae11976a79059349bcc0364b8ce6cb0547b01ba542fb6a2a681bd76efb';r=json.loads(authority.read_text())
    recipe=R2/'coupled-recovery/c10036-r25-reference-bridge-recipe-r24.json';assert sha(recipe)=='016762020a735b19c932b4f0dc7a1d36b07854844c207f65aba6965caf438f6e';cr=json.loads(recipe.read_text());manifest=cr['new_zone_manifest'];qf=Path(manifest['prospective_zone_pickle']);assert sha(qf)==manifest['prospective_zone_pickle_sha256'];q=pickle.loads(qf.read_bytes());q=q[0] if isinstance(q,list) else q
    rows=[a for a in r['rows'] if a['action']=='add' and a['kind']=='zone'];assert len(rows)==1;row=rows[0];native=Path(row['exact_chunk_path']);assert sha(native)==row['exact_chunk_sha256'];old=native.read_bytes();a=parse(old.decode('utf-8'))
    uid=atom(a,'uuid');raw=atom(a,'net');layer=atom(a,'layer');assert uid==manifest['uuid'] and int(atom(a,'priority'))==124 and float(atom(child(a,'connect_pads'),'clearance'))==.25 and float(atom(a,'min_thickness'))==.15
    rings=[[(float(v[1]),float(v[2])) for v in child(poly,'pts')[1:]] for poly in children(a,'polygon')];outline=Polygon(rings[0],rings[1:]);assert outline.is_valid
    physical=q.get('shape',outline);conflicts=[]
    for other in z:
        if (other['net'],other['layer'],int(other.get('priority',124)))!=(raw,layer,124):continue
        s=other.get('zone_outline_shape',other['shape'])
        if outline.intersects(s):conflicts.append({'C_uuid':uid,'other_proposal_uuid':other['uuid'],'raw_net':raw,'layer':layer,'C_settings':[.25,.15,'FULL_SOLID',124,1,.15,.3],'other_settings':settings(other),'C_intended_WKB_sha256':digest(outline),'C_physical_WKB_sha256':digest(physical),'other_intended_WKB_sha256':digest(s),'other_physical_WKB_sha256':digest(other['shape']),'intended_contact_area_mm2':outline.intersection(s).area,'physical_contact_area_mm2':physical.intersection(other['shape']).area,'original_native_definition_untouched':True})
    conflict=OUT/'actual-C-zone-plus-R70-contact-conflicts.json';write(conflict,{'base_model_file':str(base.resolve()),'base_model_sha256':sha(base),'explicit_C_zone_authority_file':str(authority.resolve()),'explicit_C_zone_authority_sha256':sha(authority),'scope':'Actual zone-only composition of exact C32 zone with frozen R70; C discrete additions and circuit source/contact/clearance/current are separate gates','conflicts':conflicts})
    if not conflicts:
        write(OUT/'receipt.json',{'verdict':'NO_SAME_RAW_NEW_CONTACT_CONFLICT_C_PRIORITY_UNCHANGED','contact_ledger_sha256':sha(conflict),'native_jobs':0,'board_written':False});print('C_PRIORITY_R67_NO_CONFLICT',sha(OUT/'receipt.json'));return
    assert all(c['other_settings']!=c['C_settings'] for c in conflicts)
    new=old.replace(b'(priority 124)',b'(priority 125)',1);assert old.count(b'(priority 124)')==1 and new.replace(b'(priority 125)',b'(priority 124)',1)==old
    na=parse(new.decode('utf-8'));expected=copy.deepcopy(a);child(expected,'priority')[1]='125';assert expected==na
    oldfile=OUT/'C-reference-original-priority124.zone-chunk';oldfile.write_bytes(old);newfile=OUT/'C-reference-declared-priority125.zone-chunk';newfile.write_bytes(new)
    adapter={'schema':'exact-owned-new-zone-settings-only-adapter/v1','verdict':'C_ONLY_PRIORITY125_PROPOSAL_GEOMETRY_AND_OTHER_SETTINGS_EXACT_FRESH_NATIVE_REQUIRED','affected_proposal_uuid':uid,'raw_net':raw,'layer':layer,'before_settings':[.25,.15,'FULL_SOLID',124,1,.15,.3],'after_settings':[.25,.15,'FULL_SOLID',125,1,.15,.3],'exact_original_native_chunk_file':str(oldfile.resolve()),'exact_original_native_chunk_sha256':sha(oldfile),'exact_new_native_chunk_file':str(newfile.resolve()),'exact_new_native_chunk_sha256':sha(newfile),'C_native_intended_WKB_sha256':digest(outline),'C_original_prospective_pickle_file':str(qf.resolve()),'C_original_prospective_pickle_sha256':sha(qf),'C_physical_WKB_sha256':digest(physical),'conflict_ledger_file':str(conflict.resolve()),'conflict_ledger_sha256':sha(conflict),'authoritative_C32_receipt_file':str(authority.resolve()),'authoritative_C32_receipt_sha256':sha(authority),'authoritative_C24_recipe_file':str(recipe.resolve()),'authoritative_C24_recipe_sha256':sha(recipe),'all_geometry_and_non_priority_native_bytes_unchanged':True,'new_priority_only':125,'original_native_zone_definitions_and_all_authoritative_C_receipts_unchanged':True,'native_refill_source_paired_annulus_body_reference_DRC_and_current':'OPEN','native_jobs':0,'board_written':False}
    adapter['before_settings_sha256']=hashlib.sha256(json.dumps(adapter['before_settings'],separators=(',',':')).encode()).hexdigest();adapter['after_settings_sha256']=hashlib.sha256(json.dumps(adapter['after_settings'],separators=(',',':')).encode()).hexdigest()
    f=OUT/'C-reference-priority125-adapter.json';write(f,adapter);write(OUT/'receipt.json',{'verdict':adapter['verdict'],'adapter_file':str(f.resolve()),'adapter_sha256':sha(f),'conflict_pairs':len(conflicts),'original_C24_C32_unchanged':True,'native_jobs':0,'board_written':False});print('C_PRIORITY_R67',len(conflicts),sha(f),sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
