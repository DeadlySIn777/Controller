"""Actual In4 collar check and exact owned-new antipads for the source hypothesis."""
import json,pickle,hashlib,sys,copy
from pathlib import Path
from shapely.geometry import Point,LineString
from shapely import set_precision
import guarded_declared_settings_projection_r58 as GP
G=GP.G;p=G.p;H=Path(__file__).resolve().parent.parent;O=H/'sbc-power/core1v2-extra-In4-source-guarded-input-r112'
def sha(f):return hashlib.sha256(Path(f).read_bytes()).hexdigest()
def write(f,d):Path(f).write_text(json.dumps(d,indent=1)+'\n')
def main():
    assert not O.exists();O.mkdir()
    mp=H/'sbc-power/core1v2-source-barrel-extra-In4-proposal-r111/model.pkl';assert sha(mp)=='6cd64d115ca26c3edbe87f074ee2548e615d1ec464f322a0f9dde8cd953aa295'
    g,h,b,z,c=pickle.loads(mp.read_bytes());v=next(q for q in h['vias'] if q['uuid']=='f6ad6a15-3a41-4605-9ad5-72f4ba7d5d92');pt=Point(v['x'],v['y']);layer='In4.Cu';raw=v['net'];pairs=[];errors=[]
    def check(kind,q,gap,required):
        row={'kind':kind,'other_UUID':q['uuid'],'actual_gap_mm':gap,'required_gap_mm':required};pairs.append(row)
        if gap<required:errors.append(row)
    for q in h['pads']:
        if q['net']==raw:continue
        for sh in p.base.polygons(q['layers'].get(layer,[])):
            d=pt.distance(sh)-v['d']/2
            if d<1:check('actual_native_In4_pad',q,d,G.gap(h,raw,q['net'])+.025)
    for q in h['tracks']:
        if q['layer']!=layer or q['net']==raw:continue
        if max(q['a'][0],q['b'][0])+q['w']/2+2<v['x'] or min(q['a'][0],q['b'][0])-q['w']/2-2>v['x'] or max(q['a'][1],q['b'][1])+q['w']/2+2<v['y'] or min(q['a'][1],q['b'][1])-q['w']/2-2>v['y']:continue
        check('true_In4_track_caps',q,pt.distance(LineString([q['a'],q['b']]))-(v['d']+q['w'])/2,G.gap(h,raw,q['net'])+.025)
    for q in h['vias']:
        if q['net']==raw or layer not in q['flashed']:continue
        d=pt.distance(Point(q['x'],q['y']))-(v['d']+q['d'])/2
        if d<1:check('actual_native_In4_foreign_annulus',q,d,G.gap(h,raw,q['net'])+.025)
    ledger=[];zz=[]
    for q in z:
        if q['layer']!=layer or q['net']==raw:zz.append(q);continue
        before=q['shape'];outline=q.get('zone_outline_shape',before);clear=max(G.gap(h,raw,q['net']),float(q.get('clearance_mm',.15)))+.025
        radius=max(v['drill']/2+.275,v['d']/2+clear)+.000020;cut=GP.bounded_disk(v,radius)
        if not outline.intersects(cut):zz.append(q);continue
        after=set_precision(set_precision(before,1e-6).difference(cut),1e-6);oa=set_precision(set_precision(outline,1e-6).difference(cut),1e-6)
        if after.equals(before) and oa.equals(outline):zz.append(q);continue
        zz.append({**q,'shape':after,'zone_outline_shape':oa})
        prefix=O/q['uuid'].replace('/','_');files={}
        for label,sh in [('physical-before',before),('physical-after',after),('outline-before',outline),('outline-after',oa),('exact-outward-cutter',cut)]:
            f=Path(str(prefix)+'.'+label+'.wkb');f.write_bytes(sh.wkb);files[label]={'file':str(f.resolve()),'sha256':sha(f)}
        ledger.append({'new_owned_zone_UUID':q['uuid'],'raw_net':q['net'],'layer':layer,'files':files,'physical_removed_mm2':before.difference(after).area,'physical_quantization_added_mm2':after.difference(before).area,'outline_removed_mm2':outline.difference(oa).area,'outline_quantization_added_mm2':oa.difference(outline).area,'required_collar_Cu_guard_mm':clear,'explicit_extra_construction_reserve_mm':.000020,'existing_native_zone_outline_or_setting_changed':False})
    lf=O/'exact-owned-new-source-annulus-antipad-ledger.json';write(lf,ledger)
    if errors:
        write(O/'receipt.json',{'verdict':'FAIL_EXTRA_IN4_SOURCE_COLLAR_DISCRETE_GEOMETRY','parent_model_sha256':sha(mp),'errors':errors,'pairs':pairs,'no_route_model_emitted':True,'no_native_extra_flash_claim':True,'board_written':False,'native_jobs':0});print('EXTRA_IN4_COLLAR_FAIL',errors,flush=True);return
    b['CORE1V2_source_extra_In4_owned_antipads']={'ledger_file':str(lf.resolve()),'ledger_sha256':sha(lf),'full_foreign_contact_and_current_gate':'OPEN'}
    # The source-only constructor reprojects this net before accepting a route;
    # all foreign cached fills remain explicitly unqualified until its full gate.
    model=O/'model.pkl';model.write_bytes(pickle.dumps((g,h,b,zz,c),protocol=5))
    write(O/'receipt.json',{'verdict':'PASS_SCOPED_EXTRA_IN4_COLLAR_DISCRETE_ONLY_FUTURE_FILL_AND_SOURCE_GATES_OPEN','model_sha256':sha(model),'parent_model_sha256':sha(mp),'exact_owned_new_antipad_ledger_sha256':sha(lf),'modified_new_owned_foreign_zone_shapes':len(ledger),'errors':errors,'pairs':pairs,'existing_native_zone_definitions_changed':0,'native_extra_flash_still_prospective':True,'all_original_foreign_contacts_and_current_and_native':'OPEN','board_written':False,'native_jobs':0})
    print('EXTRA_IN4_COLLAR_SCOPED_PASS',sha(model),sha(O/'receipt.json'),'new-owned-cuts',len(ledger),flush=True)
if __name__=='__main__':main()
