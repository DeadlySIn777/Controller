"""Read-only exact-path verdict gate, cheap rejection controls and final blocker receipt."""
import copy,hashlib,json,math,sys
from pathlib import Path
from shapely.geometry import Point,LineString,box
import screen_sbc_198b_tapered_hubs as T
p,A,C,live,stage=T.p,T.A,T.C,T.live,T.stage
OUT=T.OUT;RAW=OUT/'tapered-hub-prerequisites.json';DEST=OUT/'final-bounded-blocker.json'

def route_accepted(route,start,end,free):
    """No truthy dictionaries: complete status, exact terminals and all geometry."""
    if not isinstance(route,dict) or route.get('verdict')!='HOST_PATH' or route.get('exact_native_endpoint_connectors_checked') is not True:return False
    points=route.get('points')
    if not isinstance(points,list) or not points:return False
    if any(not isinstance(pt,(tuple,list)) or len(pt)!=2 or any(not isinstance(v,(float,int)) or isinstance(v,bool) or not math.isfinite(v) for v in pt) for pt in points):return False
    if math.dist(points[0],start)>1e-8 or math.dist(points[-1],end)>1e-8:return False
    if not all(free.covers(Point(pt)) for pt in points):return False
    if not all(free.covers(LineString([a,b])) for a,b in zip(points,points[1:])):return False
    length=sum(math.dist(a,b) for a,b in zip(points,points[1:]))
    measured=route.get('length_mm')
    return isinstance(measured,(float,int)) and not isinstance(measured,bool) and math.isfinite(measured) and abs(measured-length)<1e-6

def controls():
    free=box(-1,-1,2,2);start,end=(0.,0.),(1.,1.)
    good={'verdict':'HOST_PATH','exact_native_endpoint_connectors_checked':True,'points':[[0.,0.],[1.,1.]],'length_mm':math.sqrt(2)}
    fixtures=[('valid exact route',good,free,True),('truthy NO_PATH dictionary',{'verdict':'NO_PATH_AT_GRID_OR_NODE_CAP'},free,False),
        ('HOST_PATH missing points',{**good,'points':None},free,False),('HOST_PATH missing connector evidence',{**good,'exact_native_endpoint_connectors_checked':False},free,False),
        ('wrong exact native terminal',{**good,'points':[[.001,0.],[1.,1.]]},free,False),('nonfinite point',{**good,'points':[[0.,0.],[float('nan'),1.]]},free,False),
        ('false reported length',{**good,'length_mm':1.},free,False),('diagonal through exact wall',good,free.difference(box(.4,-1,.6,2)),False)]
    rows=[{'name':name,'expected_accept':expect,'actual_accept':route_accepted(route,start,end,geometry)} for name,route,geometry,expect in fixtures]
    if any(r['expected_accept']!=r['actual_accept'] for r in rows):raise ValueError('raw route rejection control failed')
    return rows

def main():
    p.require(not DEST.exists(),'new immutable final receipt required')
    raw=json.loads(p.read(RAW));prior=json.loads(p.read(T.INPUT));assembly_path=OUT/'C15001-assembly-blocker.json';assembly=json.loads(p.read(assembly_path))
    p.require(raw['board_sha256']==prior['board_sha256']==assembly['board_sha256']==live.SHA,'candidate source hashes disagree')
    for path,sha in raw['read_set_sha256_before'].items():p.require(hashlib.sha256(p.read(path)).hexdigest()==sha,'frozen raw lead input changed')
    p.require(raw['read_set_sha256_before']==raw['read_set_sha256_after'],'raw read set changed')
    tests=controls()
    p.C05,p.C05_SHA=live.COMBINED,live.SHA;p.base.layer_reference=live.reference
    g,overlay=live.overlay();native=p.base.inventory(p.read(live.COMBINED))[3]
    ct={r['uuid'] for r in prior['whole_private_CT_old_manifest']};omit=set(C.REMOVED)|A.FANOUT|{A.GND_STUB}|ct
    original_manifest_checks=[]
    for row in prior['whole_private_CT_old_manifest']:
        okay=row['uuid'] in native and hashlib.sha256(native[row['uuid']]).hexdigest()==row['chunk_sha256']
        p.require(okay,'private CT is not current native exact owner')
        original_manifest_checks.append({'uuid':row['uuid'],'current_native_exact':okay})
    for row in prior['old_stage_shared_terminal_ledger']:
        pad=next(x for x in g['pads'] if x['ref']==row['ref'] and x['num']==row['pad'])
        p.require(pad['uuid']==row['pad_uuid'] and [pad['x'],pad['y']]==row['old_center'],'old stage terminal is not current native exact')
        for contact in row['native_track_contacts']:
            p.require(contact['uuid'] in native and hashlib.sha256(native[contact['uuid']]).hexdigest()==contact['chunk_sha256'],'old stage retained contact differs')
    model=copy.copy(g);model['tracks']=[r for r in g['tracks'] if r['uuid'] not in omit];model['vias']=[r for r in g['vias'] if r['uuid'] not in ct]
    candidate=stage.caps.moved(model,prior['deltas_mm']);areas=live.reservations();p.WINDOW=box(103,109,249,174)
    checked=[];observations=[]
    for screen in raw['screens']:
        observations.extend({'net_under_screen':screen['net'],'layer':screen['layer'],**r} for r in screen['bounded_rejected_site_observations'])
        if not screen['at_most_two_hub_choice_geometry_leads']:continue
        free=p.free_copper(candidate,areas,screen['net'],screen['layer'],window=p.WINDOW)
        wide=free.buffer(-screen['trunk_width_mm']/2);branch=free.buffer(-screen['branch_width_mm']/2)
        for index,lead in enumerate(screen['at_most_two_hub_choice_geometry_leads']):
            arrays=lead['arrays'];p.require(len(arrays)==2 and all(len(ar['branches'])==9 for ar in arrays),'raw nine-site schema differs')
            trunk_ok=route_accepted(lead['trunk_path'],arrays[0]['hub'],arrays[1]['hub'],wide)
            branch_checks=[]
            for ar in arrays:
                sites=[r['via'] for r in ar['branches']]
                spacing=all(math.dist(a,b)>=.8-1e-9 for i,a in enumerate(sites) for b in sites[i+1:])
                existing_spacing=all(math.dist(site,(v['x'],v['y']))>=.8-1e-9 for site in sites for v in candidate['vias'])
                for row in ar['branches']:
                    branch_checks.append({'endpoint':ar['endpoint'],'site':row['via'],'host_verdict':row['exact_path'].get('verdict'),
                        'exact_path_accept':route_accepted(row['exact_path'],row['via'],ar['hub'],branch),
                        'new_new_spacing_accept':spacing,'new_existing_spacing_accept':existing_spacing})
            accepted=trunk_ok and all(r['exact_path_accept'] and r['new_new_spacing_accept'] and r['new_existing_spacing_accept'] for r in branch_checks)
            checked.append({'net':screen['net'],'layer':screen['layer'],'raw_lead_index':index,'trunk_accept':trunk_ok,'branches':branch_checks,
                'geometry_accept_only':accepted,'trunk_length_mm':lead['trunk_path'].get('length_mm'),
                'current_sharing_and_frontpad_and_return_and_assembly_qualification':False})
    p.require(len(checked)==2,'raw lead inventory differs')
    print('RAW_GATE',json.dumps([{'index':r['raw_lead_index'],'trunk':r['trunk_accept'],'accepted':r['geometry_accept_only'],
        'failed_branches':[b for b in r['branches'] if not all(b[k] for k in ('exact_path_accept','new_new_spacing_accept','new_existing_spacing_accept'))]} for r in checked]),flush=True)
    for module in list(sys.modules.values()):
        file=getattr(module,'__file__',None)
        if file and Path(file).is_file():p.read(file)
    p.read(Path(__file__));p.read(sys.executable)
    for path,sha in p.READS.items():p.require(hashlib.sha256(Path(path).read_bytes()).hexdigest()==sha,'final inputs changed')
    result={'schema':'exact198b-final-one-bounded-SBC-source-proposal-blocker-v1','verdict':'WITHHELD_NO_LEGAL_COMPLETE_POWER_CANDIDATE',
        'board_sha256':live.SHA,'native_scope':'current r07 all exact copper plus287additions; no c05 footprint carryover',
        'packing_and_uniform_and_tapered_and_assembly_inputs':{str(path.resolve()):hashlib.sha256(p.read(path)).hexdigest() for path in (T.INPUT,OUT/'contacts-and-corridors.json',RAW,assembly_path)},
        'raw_driver_dict_truthiness_gate_defect':'raw driver did not check HOST_PATH before appending leads; this distinct checker requires explicit verdict/exact terminal/length/geometry/spacing gates and records each actual failure; raw file remains frozen',
        'raw_route_gate_controls':tests,'actual_trunk_branch_paths':checked,'actual_checked_paths':sum(1+len(r['branches']) for r in checked),
        'private_CT_current_native_exact_manifest_checks':original_manifest_checks,'old_stage_terminal_contacts_current_native_exact':True,
        'assembly_blocker':assembly,'exact_retained_probe_observations':observations,
        'bounded_trunk_findings':{'raw_provisional_output_leads':2,'independent_geometry_accepted_output_leads':sum(r['geometry_accept_only'] for r in checked),
            'upstream':'no paired4.6mmCOREupstream widehub found acrossF/B/In2/In3 for this changedset'},
        'stop_point':'exactC15001Y+.85pose fails ordinarySMDdrill/mask/paste requirement; no alternate pose or complete upstream/return/current path qualified; no board written; exploration stopped',
        'next_concrete_design_requirements':['solveC15001 ordinarygroundvia drill/mask/paste collision while retaining decoupling loop andJ15001courtyard; existingordinaryDRC0 does not authorize newVIPPO',
            'provide actual4.15A upstream70mV corridor and9ordinary.6/.3source transitions or expressly separated8compute+otherqualifiedbranches',
            'bind actualfrontsource/loadpad fanout and everyold17track+CT/ON/PG/localcap/ground terminal contact;9sitesalone do not implyadequate0.5Aeachsharing',
            'retain sourceanchored actualflash-aware In1/In4 and qualify prospectiveantipads/returncurrent without cuts or synthetic reservations',
            'apply separateC1106125Vsource correction withfresh complete source/native/power/timing/DFM/no-loss/DRC/SI/thermal checks beforeadoption'],
        'scope_limits':['sampled exactfivepartpose and fixed bounded ownership only, not wholelayout impossibility','retained probe observations are not necessary-removal proof or addedownership',
            'onlyindependently accepted geometry rows may be describedasprovisional leads; assembly, frontpad currentsharing andfullupstream/return are open','oldnativeCu fill usedconservatively; no198b freshfillgeometry claimed'],
        'full_current_A':{'compute':3.6,'USB':.5,'HDMI':.05,'common':4.15},'equal_sharing_assumed':False,
        'native_jobs':0,'GPU_jobs':0,'board_emitted':False,'source_changed':False,'adopted':False,'qualified_power':False,
        'source_sha256_before':p.READS,'source_sha256_after':{path:hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in p.READS}}
    DEST.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'receipt':str(DEST),'sha256':hashlib.sha256(DEST.read_bytes()).hexdigest(),'raw_gate_controls':len(tests),'actual_paths':result['actual_checked_paths'],'geometry_leads':len(checked),'verdict':result['verdict']}))
if __name__=='__main__':main()
