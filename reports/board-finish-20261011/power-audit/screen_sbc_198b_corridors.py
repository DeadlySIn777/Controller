"""Distinct host-only exact198b contact and uniform-trunk screen; no board writes."""
import copy, hashlib, json, math, sys
from pathlib import Path
from shapely.geometry import Point, box, shape, mapping
from shapely.ops import unary_union
import prepare_sbc_198b_five_part as A

p,C,live,stage,six=A.p,A.C,A.live,A.stage,A.six
OUT=p.HERE/'sbc-198b-source-proposal'
INPUT=OUT/'bounded-five-part-fanout-proposal.json'
DEST=OUT/'contacts-and-corridors.json'

def area_contact_groups(g,native,fp,selected,omit):
    """Exact layer-specific width-overlap components; vias require actual annuli."""
    out=[]
    for layer in sorted({r['layer'] for r in selected}):
        for net in sorted({p.norm(r['net']) for r in selected if r['layer']==layer}):
            groups=[]
            for r in selected:
                if r['layer']!=layer or p.norm(r['net'])!=net:continue
                body=p.base.body(r)
                touching=[x for x in groups if x['shape'].intersection(body).area>1e-7]
                item={'shape':body,'items':[r['uuid']]}
                for group in touching:
                    item['shape']=item['shape'].union(group['shape'])
                    item['items'].extend(group['items']);groups.remove(group)
                groups.append(item)
            for group in groups:
                contacts=C.contacts(g,native,fp,group['shape'],net,layer,omit=omit,native_vias=live.ACTUAL)
                for contact in contacts:
                    contact['treatment']='same_pad_identity_at_proposed_pose' if contact.get('ref') in A.POSES else 'outside_item_fixed_exact_physical_contact_required'
                out.append({'net':net,'layer':layer,'old_uuids':sorted(group['items']),
                    'surviving_physical_keys':contacts,'obligation':'all keys of this old physical component must stay mutually connected through actual annuli/layers; moved pads reconnect at new poses; duplicate widths not summed'})
    return out

def main():
    p.require(not DEST.exists(),'new immutable output required')
    prior=json.loads(p.read(INPUT))
    p.require(prior['board_sha256']==live.SHA,'packing receipt wrong native board')
    for path,expected in prior['read_set_sha256'].items():
        p.require(hashlib.sha256(p.read(path)).hexdigest()==expected,'frozen packing input changed: '+path)
    p.C05,p.C05_SHA=live.COMBINED,live.SHA
    p.overlay=live.overlay;p.base.layer_reference=live.reference
    g,overlay=live.overlay();native=p.base.inventory(p.read(live.COMBINED))[3]
    fp={p.base.ref_of(ch):{'uuid':uid,'sha256':hashlib.sha256(ch).hexdigest(),'pose':p.pose(p.base.children(ch)[1])}
        for uid,ch in native.items() if p.base.pcbtext.chunk_kind(ch)=='footprint'}
    ct={r['uuid'] for r in prior['whole_private_CT_old_manifest']}
    omit=set(C.REMOVED)|A.FANOUT|{A.GND_STUB}|ct
    byuid={r['uuid']:r for r in g['tracks']}
    selected=[byuid[r['uuid']] for r in prior['exact_proposed_removal_ledger']]
    p.require(len(selected)==17 and set(r['uuid'] for r in selected)==set(C.REMOVED)|A.FANOUT|{A.GND_STUB},'bounded owner mismatch')
    for row in prior['exact_proposed_removal_ledger']:
        p.require(hashlib.sha256(native[row['uuid']]).hexdigest()==row['old_chunk_sha256'],'old owner chunk changed')
    ledger=area_contact_groups(g,native,fp,selected,omit)
    model=copy.copy(g);model['tracks']=[r for r in g['tracks'] if r['uuid'] not in omit];model['vias']=[r for r in g['vias'] if r['uuid'] not in ct]
    candidate=stage.caps.moved(model,prior['deltas_mm'])
    oldpad=next(r for r in g['pads'] if r['ref']=='C15001' and r['num']=='2')
    newpad=next(r for r in candidate['pads'] if r['ref']=='C15001' and r['num']=='2')
    via=live.ACTUAL[C.GROUND_VIA]
    oldbody,newbody=[unary_union(p.base.polygons(r['layers']['F.Cu'])) for r in (oldpad,newpad)]
    annulus=Point(via['x'],via['y']).buffer(via['d']/2)
    drill=Point(via['x'],via['y']).buffer(via['drill']/2)
    target={'old_pad_uuid':oldpad['uuid'],'same_pad_uuid':oldpad['uuid']==newpad['uuid'],'net':p.norm(oldpad['net']),
        'retained_via_uuid':C.GROUND_VIA,'via_chunk_sha256':hashlib.sha256(native[C.GROUND_VIA]).hexdigest(),
        'old_pad_drill_overlap_mm2':oldbody.intersection(drill).area,'new_pad_drill_overlap_mm2':newbody.intersection(drill).area,
        'old_pad_annulus_overlap_mm2':oldbody.intersection(annulus).area,'new_pad_annulus_overlap_mm2':newbody.intersection(annulus).area,
        'minimum_mask_or_paste_waiver_added':False,'mask_paste_padstack_definitions_changed':False,
        'strict_generic_hole_mask_acceptance_still_withheld':True,'fresh_native_new_pose_DRC_and_decoupler_return_required':True,
        'interpretation':'both old/new pads geometrically meet exact retained same-net plated target; this diagnosis introduces no foreign-hole clearance exemption or assembly qualification'}
    courts={r['ref']:unary_union([poly for side in r['courtyard'].values() for poly in p.base.polygons(side)]) for r in candidate['footprints'] if r['ref'] in A.POSES or r['ref']=='J15001'}
    courtgaps=[{'a':a,'b':b,'gap_mm':courts[a].distance(courts[b]),'overlap_mm2':courts[a].intersection(courts[b]).area}
               for a,b in (('C15001','J15001'),('C15001','U11012'))]
    print('CONTACT_LEDGER',len(ledger),'GROUND_TARGET',json.dumps(target),'COURTS',json.dumps(courtgaps),flush=True)
    areas=live.reservations();p.WINDOW=box(103,109,249,174)
    corridor=[]
    for net,width,src,dst,budget,current in ((p.NET,3.,'U11012','J15001',100.,4.15),(stage.caps.CORE,4.6,'R11022','U11012',70.,4.15)):
        a=next(r for r in prior['array_necessary_conditions_even_if_pose_withheld'] if r['terminal']==src and r['net']==p.norm(net))
        b=next(r for r in prior['array_necessary_conditions_even_if_pose_withheld'] if r['terminal']==dst and r['net']==p.norm(net))
        ar,br=shape(a['source_front_connected_region']),shape(b['source_front_connected_region'])
        for layer in ('F.Cu','B.Cu','In2.Cu','In3.Cu'):
            print('BEGIN_CORRIDOR',p.norm(net),layer,width,flush=True)
            free=p.free_copper(candidate,areas,net,layer,window=p.WINDOW).buffer(-width/2)
            links=[];counts=[]
            for component in p.hubs.components(free):
                aa,bb=component.intersection(ar),component.intersection(br)
                na=p.hubs.pack_region(aa,aa.representative_point().coords[0]) if not aa.is_empty else []
                nb=p.hubs.pack_region(bb,bb.representative_point().coords[0]) if not bb.is_empty else []
                if na or nb:counts.append({'source_sites':len(na),'load_sites':len(nb),'area_mm2':component.area})
                if len(na)>=9 and len(nb)>=9:
                    start=min(na,key=lambda pt:Point(pt).distance(br));goal=min(nb,key=lambda pt:Point(pt).distance(ar))
                    path=six.five.exact_path(component,start,goal,node_cap=50000)
                    length=sum(math.dist(x,y) for x,y in zip(path,path[1:])) if path else None
                    drop=None if length is None else current*(.57003672*length/width+2*1.35481415/9)
                    links.append({'source_sites':na,'load_sites':nb,'exact_connector_trunk_centerline':path,'length_mm':length,
                        'ideal_strip_and_two_9via_arrays_drop_mV':drop,'pad_necks_contact_and_sharing_excluded':True})
            corridor.append({'net':p.norm(net),'layer':layer,'width_mm':width,'common_current_A':current,'budget_mV':budget,
                'per_component_endpoint_site_counts':counts,'components_with_9_at_each_end':links,
                'scope':'only a uniform single-layer trunk center region whose body and9 endpoint centers fit; zero result does not disprove tapered/split/multilayer layout'})
            print('CORRIDOR',p.norm(net),layer,'COUNTS',json.dumps(counts),'LINKS',len(links),flush=True)
    for module in list(sys.modules.values()):
        path=getattr(module,'__file__',None)
        if path and Path(path).is_file():p.read(path)
    p.read(sys.executable);p.read(Path(__file__))
    for path,expected in p.READS.items():p.require(hashlib.sha256(Path(path).read_bytes()).hexdigest()==expected,'input changed during host screen: '+path)
    result={'schema':'exact198b-bounded-contact-uniform-trunk-screen-v1','verdict':'SOURCE_PROPOSAL_WITHHELD_COMPLETE_NETWORK_OPEN',
        'native_board_sha256':live.SHA,'parent_packing_receipt_sha256':hashlib.sha256(INPUT.read_bytes()).hexdigest(),'overlay':overlay,
        'owned_original_layer_contact_component_obligations':ledger,'same_net_plated_target_diagnosis':target,'exact_courtyard_pair_gaps':courtgaps,
        'uniform_trunk_screens':corridor,'full_currents_A':{'compute':3.6,'USB':.5,'HDMI':.05,'common':4.15},
        'qualification_open':['local source fanout9individual0.5Amaxvias and actual resistance/current sharing','all17owned track contact components + relocatedCT/ON/PG/localcap and their source return contacts',
            'complete unchanged4.15A upstream70mV and output100mV networks','prospective foreign antipads plus source anchored return current/reference preservation',
            'exact current-source schematic/API parity and separateCT25V correction','fresh nativefill/no-loss/DRC/DFM/SI/thermal and physical power evidence'],
        'no_equal_current_split_assumed':True,'native_new_fill_claimed':False,'board_emitted':False,'source_or_live_board_changed':False,'native_jobs':0,'GPU_jobs':0,
        'read_set_sha256_before':p.READS,'read_set_sha256_after':{path:hashlib.sha256(Path(path).read_bytes()).hexdigest() for path in p.READS}}
    DEST.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('RECEIPT',str(DEST),'SHA',hashlib.sha256(DEST.read_bytes()).hexdigest(),flush=True)

if __name__=='__main__':main()
