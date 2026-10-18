"""One bounded nine-site tapered-array/hub screen; never emits native copper."""
import copy,hashlib,json,math,sys
from pathlib import Path
from shapely.geometry import Point,LineString,box,shape
from shapely.ops import unary_union
import screen_sbc_198b_corridors as S
p,A,C,live,stage,six=S.p,S.A,S.C,S.live,S.stage,S.six
OUT=S.OUT;INPUT=S.INPUT;DEST=OUT/'tapered-hub-prerequisites.json'

def grid_hub(region,centre):
    if region.is_empty:return None
    x0,y0,x1,y1=region.bounds;pts=[]
    for ix in range(math.ceil(x0*5),math.floor(x1*5)+1):
        for iy in range(math.ceil(y0*5),math.floor(y1*5)+1):
            pt=(ix/5,iy/5)
            if region.contains(Point(pt)):pts.append(pt)
    return min(pts,key=lambda pt:math.dist(pt,centre)) if pts else None

def nearby_observations(g,net,layer,site,width,native):
    # Exact retained near-site objects that constrain this chosen narrow branch
    # or widehub probe; these are observations, never a necessary-removal set.
    point=Point(site);radius=width/2;rows=[]
    domain=g['domains_normalized'].get(p.norm(net))
    def take(body,other,identity,clearance=None):
        gap=clearance if clearance is not None else (.15 if g['domains_normalized'].get(p.norm(other))==domain else .6)
        distance=point.distance(body)
        if distance<radius+gap+p.MARGIN:
            rows.append({**identity,'net':p.norm(other),'distance_from_probe_center_mm':distance,'required_center_distance_mm':radius+gap+p.MARGIN})
    for r in g['tracks']:
        if r['layer']==layer and p.norm(r['net'])!=p.norm(net) and p.base.body(r).intersects(point.buffer(radius+1)):
            take(p.base.body(r),r['net'],{'kind':'segment','uuid':r['uuid'],'width_mm':r['w'],'chunk_sha256':hashlib.sha256(native[r['uuid']]).hexdigest()})
    for pad in g['pads']:
        if p.norm(pad['net'])!=p.norm(net):
            for body in p.base.polygons(pad['layers'].get(layer,[])):take(body,pad['net'],{'kind':'pad','ref':pad['ref'],'pad':pad['num'],'uuid':pad['uuid']})
        for hole in p.base.polygons(pad.get('hole') or []):take(hole,pad['net'],{'kind':'pad_hole','ref':pad['ref'],'pad':pad['num'],'uuid':pad['uuid']},.25)
    for via in g['vias']:
        if p.norm(via['net'])!=p.norm(net):take(Point(via['x'],via['y']).buffer(via['d']/2),via['net'],{'kind':'via_copper','uuid':via['uuid'],'at':[via['x'],via['y']],'chunk_sha256':hashlib.sha256(native[via['uuid']]).hexdigest()})
        take(Point(via['x'],via['y']).buffer(via['drill']/2),via['net'],{'kind':'via_hole','uuid':via['uuid'],'at':[via['x'],via['y']],'chunk_sha256':hashlib.sha256(native[via['uuid']]).hexdigest()},.25)
    return rows

def main():
    p.require(not DEST.exists(),'new immutable receipt required')
    prior=json.loads(p.read(INPUT))
    p.require(prior['board_sha256']==live.SHA,'frozen packing receipt differs')
    for path,sha in prior['read_set_sha256'].items():p.require(hashlib.sha256(p.read(path)).hexdigest()==sha,'packing input differs')
    p.C05,p.C05_SHA=live.COMBINED,live.SHA;p.overlay=live.overlay;p.base.layer_reference=live.reference
    g,overlay=live.overlay();native=p.base.inventory(p.read(live.COMBINED))[3]
    ct={r['uuid'] for r in prior['whole_private_CT_old_manifest']};omit=set(C.REMOVED)|A.FANOUT|{A.GND_STUB}|ct
    model=copy.copy(g);model['tracks']=[r for r in g['tracks'] if r['uuid'] not in omit];model['vias']=[r for r in g['vias'] if r['uuid'] not in ct]
    candidate=stage.caps.moved(model,prior['deltas_mm']);areas=live.reservations();p.WINDOW=box(103,109,249,174)
    screens=[]
    for net,width,src,dst,current,budget in ((p.NET,3.,'U11012','J15001',4.15,100.),(stage.caps.CORE,4.6,'R11022','U11012',4.15,70.)):
        a=next(r for r in prior['array_necessary_conditions_even_if_pose_withheld'] if r['terminal']==src and r['net']==p.norm(net))
        b=next(r for r in prior['array_necessary_conditions_even_if_pose_withheld'] if r['terminal']==dst and r['net']==p.norm(net))
        ar,br=shape(a['source_front_connected_region']),shape(b['source_front_connected_region'])
        ac,bc=ar.centroid.coords[0],br.centroid.coords[0]
        for layer in ('F.Cu','B.Cu','In2.Cu','In3.Cu'):
            print('BEGIN_TAPER',p.norm(net),layer,flush=True)
            free=p.free_copper(candidate,areas,net,layer,window=p.WINDOW)
            branch=free.buffer(-.4);wide=free.buffer(-width/2)
            endpoint=[];groups=[]
            for name,region,centre in (('source',ar,ac),('load',br,bc)):
                rows=[];good=[]
                for part in p.hubs.components(branch):
                    landing=part.intersection(region)
                    sites=p.hubs.pack_region(landing,centre) if not landing.is_empty else []
                    if sites:
                        rows.append({'count':len(sites),'sampled_sites':sites,'component_area_mm2':part.area})
                        if len(sites)>=9:good.append((part,sites))
                endpoint.append({'endpoint':name,'nine_via_branch_components':sum(r['count']>=9 for r in rows),'all_branch_component_samples':rows})
                groups.append(good)
            choices=[]
            for trunk in p.hubs.components(wide):
                for sp,ss in groups[0]:
                    hs=grid_hub(sp.intersection(trunk),ac)
                    if hs is None:continue
                    for lp,ls in groups[1]:
                        hl=grid_hub(lp.intersection(trunk),bc)
                        if hl is not None:choices.append((math.dist(hs,ac)+math.dist(hl,bc),trunk,sp,ss,lp,ls,hs,hl))
            leads=[]
            # At most two actual hub choices per layer, exact connectors for all
            # source/load branches. Geometric overlap never implies equal share.
            for _,trunk,sp,ss,lp,ls,hs,hl in sorted(choices,key=lambda r:r[0])[:2]:
                path=six.five.exact_path(trunk,hs,hl,node_cap=50000)
                if not path:continue
                arrays=[];complete=True
                for name,part,sites,hub in (('source',sp,ss,hs),('load',lp,ls,hl)):
                    rows=[]
                    for site in sorted(sites,key=lambda pt:math.dist(pt,hub))[:9]:
                        route=six.five.exact_path(part,site,hub,node_cap=50000)
                        if not route:complete=False;break
                        rows.append({'via':site,'width_mm':.8,'exact_path':route,'current_assignment':'NOT_ASSUMED_OR_QUALIFIED'})
                    arrays.append({'endpoint':name,'hub':hub,'branches':rows})
                if complete:leads.append({'trunk_width_mm':width,'trunk_path':path,'arrays':arrays,'current_sharing_capacity_and_Fpad_fanout_open':True})
            rejected=[]
            for label,record in (('source',a),('load',b)):
                for site in record['sampled_sites']:
                    if not branch.contains(Point(site)):
                        rows=nearby_observations(candidate,net,layer,site,.8,native)
                        if rows:rejected.append({'endpoint':label,'site':site,'nearby_exact_retained_observations':rows})
                        if len(rejected)>=6:break
            screens.append({'net':p.norm(net),'layer':layer,'branch_width_mm':.8,'trunk_width_mm':width,'common_current_A':current,'budget_mV':budget,
                'endpoints':endpoint,'shared_wide_hub_pair_count':len(choices),'at_most_two_hub_choice_geometry_leads':leads,
                'bounded_rejected_site_observations':rejected,'counts_are_samples_not_impossibility_proof':True})
            print('TAPER',p.norm(net),layer,'SOURCE_COUNTS',[r['count'] for r in endpoint[0]['all_branch_component_samples']],
                'LOAD_COUNTS',[r['count'] for r in endpoint[1]['all_branch_component_samples']],'CHOICES',len(choices),'LEADS',len(leads),flush=True)
    p.read(Path(__file__));p.read(Path(S.__file__));p.read(sys.executable)
    for module in list(sys.modules.values()):
        file=getattr(module,'__file__',None)
        if file and Path(file).is_file():p.read(file)
    for path,sha in p.READS.items():p.require(hashlib.sha256(Path(path).read_bytes()).hexdigest()==sha,'input changed')
    result={'schema':'exact198b-one-bounded-nine-site-tapered-array-hub-screen-v1','verdict':'SOURCE_ONLY_COMPLETE_POWER_NETWORK_WITHHELD',
        'board_sha256':live.SHA,'packing_receipt_sha256':hashlib.sha256(INPUT.read_bytes()).hexdigest(),'same_bounded_owner_and_pose_set':True,
        'screens':screens,'strict_source_anchored_native_flash_reference_policy':overlay,
        'no_equal_current_split_assumed':True,'current_A':{'compute':3.6,'USB':.5,'HDMI':.05,'common':4.15},
        'still_open':['front-pad-to-source/load-array physical and adequate-current fanout','actual nine-way current split, sharedbranch necks and full70/100mV drops',
            'every original17track contact component and relocatedCT/ON/PG/cap/ground relationship','newpowerantipads and complete source-anchored supply/return/current paths',
            'C15001 changed plated-pad assembly/nativeclearance qualification; no maskwaiver created','fresh native0loss/fill/DRC/parity/DFM/SI/thermal and actual power verification'],
        'limitations':['only0.8mm branch/3mm output/4.6mm upstream uniformhub family onF/B/In2/In3, at most two exact hub choices perlayer; cannot label whole layout impossible',
            'nearby retained objects are exact probe observations, not proof that all must be moved or an authorized ownership expansion',
            'no broad copper ownership, reducedload, brokenreturn, referenceplanecut, syntheticreservation or newmaskwaiver'],
        'native_jobs':0,'GPU_jobs':0,'board_emitted':False,'implemented':False,'qualified_power':False,
        'read_set_sha256_before':p.READS,'read_set_sha256_after':{path:hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in p.READS}}
    DEST.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('FINAL',str(DEST),hashlib.sha256(DEST.read_bytes()).hexdigest(),flush=True)
if __name__=='__main__':main()
