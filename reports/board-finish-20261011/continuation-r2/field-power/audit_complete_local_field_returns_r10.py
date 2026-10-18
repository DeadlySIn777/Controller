"""Full mutual retained-contact and signed endpoint audit of frozen r6/r8/r9."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,sys
from pathlib import Path
from shapely.ops import unary_union
from collections import defaultdict
from inventory import sha
import contact_layout as C
import fast_contacts as F
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent/'sbc-power'))
import zone_projection_r1 as N
from audit_field_io3_crossings_r15e import losses
OUT=HERE/'complete-local-field-return-contact-audit-r10'
def main():
    assert not OUT.exists();OUT.mkdir();rp=HERE.parent/'sbc-power/io3-field-crossings-r15';old,discrete,binding,zones,saved=pickle.loads((rp/'model.pkl').read_bytes());state=json.loads((rp/'precision-state-ledger.json').read_text());print('precision-state',list(state),flush=True);precids={q['uuid'] for q in zones if q.get('label')=='CORE-main-In2' or q.get('label','').startswith('IO3-r15-field-crossing-') or q.get('field_return_proposal') and q['layer']=='In2.Cu'}
    from shapely import set_precision
    assert len(precids)==9;zones=[{**q,'shape':set_precision(q['shape'],1e-6)} if q['uuid'] in precids else q for q in zones];inputs={}
    for name,file,key in [('source-rooted-local-field-returns-r6','proposed-zones.pkl','proposal_sha256'),('bridged-field-ground-dogbones-r8','proposed-zones.pkl','proposed_zones_sha256')]:
        path=HERE/name;receipt=json.loads((path/'receipt.json').read_text());assert sha(path/file)==receipt[key];zones+=pickle.loads((path/file).read_bytes());inputs[name]=sha(path/'receipt.json')
    r8p=HERE/'bridged-field-ground-dogbones-r8';r8=json.loads((r8p/'receipt.json').read_text());assert sha(r8p/'proposed-discrete.pkl')==r8['proposed_discrete_sha256'];ds=pickle.loads((r8p/'proposed-discrete.pkl').read_bytes());r9p=HERE/'fine-outer-field-ground-joins-r9';r9=json.loads((r9p/'receipt.json').read_text());assert sha(r9p/'proposed-tracks.pkl')==r9['proposal_sha256'];tracks=pickle.loads((r9p/'proposed-tracks.pkl').read_bytes());inputs[r9p.name]=sha(r9p/'receipt.json');h={**discrete,'tracks':discrete['tracks']+ds['tracks']+tracks,'vias':discrete['vias']+ds['vias']};bp=HERE/'field-io3-crossing-contact-audit-r15e';br=json.loads((bp/'receipt.json').read_text());assert sha(bp/'geometry.pkl')==br['geometry_sha256'];before=pickle.loads((bp/'geometry.pkl').read_bytes());prior=pickle.loads((bp/'groups.pkl').read_bytes());collisions=[]
    for i,a in enumerate(zones):
        for b in zones[i+1:]:
            if a['layer']!=b['layer'] or C.norm(a['net'])==C.norm(b['net']):continue
            gap=.15 if h['domains_normalized'][C.norm(a['net'])]==h['domains_normalized'][C.norm(b['net'])] else .6;dist=a['shape'].distance(b['shape'])
            if dist<gap+.024:collisions.append({'a':a['uuid'],'b':b['uuid'],'distance_mm':dist,'required_mm':gap+.024})
    after,cuts=N.projected(old,h,zones);oldZ={q['uuid']:q for q in before['zones']};changed=[]
    for z in after['zones']:
        if z['uuid'] not in oldZ:continue
        for l,rs in z['fills'].items():
            a=unary_union(C.poly(oldZ[z['uuid']]['fills'].get(l,[])));b=unary_union(C.poly(rs));delta=a.difference(b)
            if delta.area>1e-8:changed.append({'uuid':z['uuid'],'layer':l,'net_raw':z['net'],'additional_retreat_area_mm2':delta.area})
    nets=sorted(set(prior)|{C.norm(q['net_raw']) for q in changed});rows=[];gg={}
    for net in nets:
        a=prior.get(net)
        if a is None:a=F.graph(before,net)
        b=F.graph(after,net);gg[net]=b;lost=losses(a,b);row={'net':net,'verdict':'PASS' if not lost else 'REPAIR_REQUIRED','lost_old_discrete_relationships':lost,'prior_groups':len(a),'new_groups':len(b)};rows.append(row);print(net,row['verdict'],'lossgroups',len(lost),flush=True);(OUT/'checkpoint.json').write_text(json.dumps(rows,indent=1)+'\n')
    allocationp=HERE.parent/'field-signed-port-allocation-r4/receipt.json';allocation=json.loads(allocationp.read_text());sources=[];groupbounds=[]
    for bank,net,root in [('FA','/motherboard_motors/FIELD_GND','J11003'),('FB','/motherboard_do/FIELD_B_0V','J11005')]:
        groups=gg[net];ri=next(i for i,xs in enumerate(groups) if any(q['kind']=='pad' and (q['ref'],q['pin'])==(root,'2') for q in xs));mapping={q['uuid']:i for i,xs in enumerate(groups) for q in xs if q['kind']=='pad'};terms=[t for t in allocation['terms'] if t['domain']==bank];sourcepads={q['uuid'] for q in groups[ri] if q['kind']=='pad' and q['pin']};unrooted=[]
        for i,xs in enumerate(groups):
            physicalpads=[q for q in xs if q['kind']=='pad' and q['pin']]
            if not physicalpads:continue
            eligible=[];minimum=0.;maximum=0.
            for term in terms:
                current=term['signed_current_a'];points=term['eligible_physical_endpoints'];hits=[p for p in points if C.norm(p['raw_net'])==net and mapping.get(p['physical_pad_uuid'])==i]
                if not hits:continue
                allhere=len(hits)==len(points);lo=current if allhere or current<0 else 0.;hi=current if allhere or current>0 else 0.;minimum+=lo;maximum+=hi;eligible.append({'name':term['name'],'signed_term_A':current,'eligible_pad_UUIDs':[p['physical_pad_uuid'] for p in hits],'all_term_endpoints_in_group':allhere,'group_current_min_A':lo,'group_current_max_A':hi})
            groupbounds.append({'domain':bank,'group':i,'source_rooted':i==ri,'physical_pad_UUIDs':sorted({q['uuid'] for q in physicalpads}),'signed_group_min_A':minimum,'signed_group_max_A':maximum,'term_impacts':eligible})
            if i!=ri:unrooted.append({'group':i,'physical_pads':[C.identity(q) for q in physicalpads],'signed_min_A':minimum,'signed_max_A':maximum})
        sources.append({'domain':bank,'net':net,'source':root+'.2','source_group':ri,'rooted_named_physical_pads':len(sourcepads),'unrooted_named_groups':unrooted})
    (OUT/'geometry.pkl').write_bytes(pickle.dumps(after,protocol=5));(OUT/'groups.pkl').write_bytes(pickle.dumps(gg,protocol=5));(OUT/'group-signed-bounds.json').write_text(json.dumps({'rows':groupbounds,'planning_simplex_bounds_only':True,'group_extrema_not_independent_simultaneous_currents':True,'TPS26624_distinct_RTNGND_support_path_remains_open':True},indent=1)+'\n');receipt={'verdict':'PASS_RETAINED_CONTACTS_LOCAL_LOAD_GROUPS_AND_CURRENT_NATIVE_PENDING' if not collisions and all(q['verdict']=='PASS' for q in rows) else 'MUTUAL_CONTACT_REPAIR_REQUIRED','rows':rows,'source_root_status':sources,'all_foreign_new_plane_clearance_collisions':collisions,'local_recipe_receipt_SHA256s':inputs,'additional_prospective_original_fill_retreats':changed,'complete_retreat_ledger':cuts,'comparison_baseline':'Auditedr15e composed native-bound geometry; original198b CORE/native r06/r07 obligations remain separate','geometry_sha256':sha(OUT/'geometry.pkl'),'groups_sha256':sha(OUT/'groups.pkl'),'group_signed_bounds_sha256':sha(OUT/'group-signed-bounds.json'),'signed_allocation_r4_sha256':sha(allocationp),'native_discrete_base_sha256':br['native_discrete_sha256'],'new_vias':len(ds['vias']),'new_segments':len(ds['tracks'])+len(tracks),'all_new_via_layer_masks_prospective_native_confirmation_required':True,'B5_and_root_new_protected24_feeds_not_composed':True,'native_jobs':0,'board_written':False,'full_current_mesh_drop_native_refill_aperture_flash_and_thermal_gates':'OPEN'};(OUT/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n');print(sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
