"""One exact five-part/eleven-fanout extension. JSON only; no native/GPU job.

This preflight does not remove or save board copper. Its immutable receipt binds
every proposed removal and retained same-layer physical contact. Geometry leads
are never advertised as source, current, DRC, return or timing qualification.
"""
import copy
import hashlib
import json
import math
from pathlib import Path
from shapely.geometry import Point, box, mapping
from shapely.ops import unary_union
import prepare_sbc_targeted_changed_set as C

p,v,six,stage,T=C.p,C.v,C.six,C.stage,C.T
FANOUT={
 '0b6aeb7d-0e86-4600-8e2a-44811be48706','422cc7ed-cd60-4dec-8d68-daf823e67eba',
 '64314061-f573-44f2-8536-d2f77a5515ca','6b25b5ba-efb3-431b-8d68-a03df143f4d0',
 '7e79d80c-ca8f-4182-a69e-55f890ab14a0','7fa32e8f-1ee0-4c40-ad5f-7dbae9864e5b',
 '88fdda22-b5b9-4f78-be49-683cf5500615','bf966c2c-2201-46e7-8940-39b222b3666d',
 'd1801c80-617c-4428-bdb8-baf41955831f','d2014e54-d5c8-4139-be4a-576f47a4e3a1',
 'e12c7a27-8688-4e48-ba20-f550fa262075'}
GND_STUB='b56da44c-43f7-45b5-9705-042310985a09'
POSES={**C.POSES,'C15001':[114.602,164.525,90.]}
LOCAL=box(109,156,124,171)
SOURCE=box(110,157,122,166)


def strict_site_region(g,areas,net,terminal,window):
    # Copper-radius hole envelope is inherited from corrected v6, and ordinary
    # new-to-existing centre spacing is additionally checked on every net.
    # Native export serializes some hierarchical separators as {slash}. The
    # inherited source component selector requires exact native net spelling.
    names={r['net'] for r in g['pads'] if r['ref']==terminal and p.norm(r['net'])==p.norm(net)}
    p.require(len(names)==1,'terminal source native net is missing or ambiguous')
    region=C.landing(g,areas,next(iter(names)),terminal,window)
    close=unary_union([Point(r['x'],r['y']).buffer(.8) for r in g['vias']
                      if Point(r['x'],r['y']).intersects(window.buffer(2))])
    return region.difference(close)


def retained_blockers(g,owned,native,fp):
    rows=[]
    for pad in g['pads']:
        if pad['ref'] not in owned:continue
        for layer,records in pad['layers'].items():
            if layer not in ('F.Cu','B.Cu'):continue
            body=unary_union(p.base.polygons(records))
            def check(poly,net,ident):
                if p.norm(net)==p.norm(pad['net']):return
                gap=.15 if g['domains_normalized'].get(p.norm(net))==g['domains_normalized'].get(p.norm(pad['net'])) else .6
                d=body.distance(poly)
                if d<gap+p.MARGIN-1e-8:
                    rows.append({'ref':pad['ref'],'pad':pad['num'],'layer':layer,
                                 'other_net':p.norm(net),'distance_mm':d,'minimum_mm':gap+p.MARGIN,**ident})
            for r in g['tracks']:
                if r['layer']==layer and p.base.body(r).intersects(LOCAL):
                    check(p.base.body(r),r['net'],{'kind':'segment','uuid':r['uuid'],'a':r['a'],'b':r['b'],'width_mm':r['w'],'chunk_sha256':hashlib.sha256(native[r['uuid']]).hexdigest()})
            for r in g['vias']:
                if Point(r['x'],r['y']).intersects(LOCAL):
                    check(Point(r['x'],r['y']).buffer(r['d']/2),r['net'],{'kind':'via','uuid':r['uuid'],'at':[r['x'],r['y']],'chunk_sha256':hashlib.sha256(native[r['uuid']]).hexdigest()})
            for other in g['pads']:
                if other['ref'] in owned:continue
                for poly in p.base.polygons(other['layers'].get(layer,[])):
                    if poly.intersects(LOCAL):check(poly,other['net'],{'kind':'pad','other_ref':other['ref'],'other_pad':other['num'],'uuid':other['uuid'],'footprint_sha256':fp[other['ref']]['sha256']})
    return rows


def main():
    dest=p.OUT/'bounded-five-part-fanout-proposal.json'
    p.require(not dest.exists(),'distinct immutable receipt required')
    prior=json.loads(p.read(p.OUT/'targeted-changed-set-proposal.json'))
    g,overlay=p.overlay()
    native=p.base.inventory(p.read(p.C05))[3]
    native_export=json.loads(p.read(p.base.GEOM))
    via_native={r['uuid']:r for r in native_export['vias']}
    fp={p.base.ref_of(ch):{'uuid':uid,'sha256':hashlib.sha256(ch).hexdigest(),'pose':p.pose(p.base.children(ch)[1])}
        for uid,ch in native.items() if p.base.pcbtext.chunk_kind(ch)=='footprint'}
    ct={r['uuid'] for r in prior['whole_private_CT_old_manifest']}
    remove=set(C.REMOVED)|FANOUT|{GND_STUB}|ct
    byuid={r['uuid']:r for r in g['tracks']}
    p.require(len(FANOUT)==11 and all(p.norm(byuid[u]['net'])==p.norm(p.NET) and byuid[u]['layer']=='F.Cu' for u in FANOUT),'fanout identity/net/layer mismatch')
    p.require(p.norm(byuid[GND_STUB]['net'])==v.GND and byuid[GND_STUB]['w']==.25,'ground stub identity mismatch')
    ledger=[]
    for uid in sorted(set(C.REMOVED)|FANOUT|{GND_STUB}):
        r=byuid[uid]
        ledger.append({'uuid':uid,'old_chunk_sha256':hashlib.sha256(native[uid]).hexdigest(),'net':p.norm(r['net']),'layer':r['layer'],'width_mm':r['w'],'a':r['a'],'b':r['b'],
                       'outside_retained_interior_and_endpoint_contacts':C.contacts(g,native,fp,p.base.body(r),r['net'],r['layer'],omit=remove,native_vias=via_native),
                       'proposed_treatment':'exact whole item replace/reconnect; all original outside component contacts must survive'})
    deltas={ref:[pose[0]-fp[ref]['pose'][0],pose[1]-fp[ref]['pose'][1]] for ref,pose in POSES.items()}
    p.require(0<deltas['C15001'][1]<.9 and all(POSES[r][2]==fp[r]['pose'][2] for r in POSES),'placement bounds/rotation changed')
    model=copy.copy(g)
    model['tracks']=[r for r in g['tracks'] if r['uuid'] not in remove]
    model['vias']=[r for r in g['vias'] if r['uuid'] not in ct]
    candidate=stage.caps.moved(model,deltas)
    stage.REFS=set(POSES)
    areas=six.five.old.reservations()
    masks,courts=stage.cache(model,areas)
    # No repour occurs here. Strict retained outer fill and native hole masks are
    # part of acceptance. A separate diagnostic distinguishes frozen fills and
    # intentional same-net pad-to-plated-via contact from foreign obstacles.
    placement=T.check_placement(candidate,masks,courts)
    print('PLACEMENT',json.dumps(placement),flush=True)
    blockers=retained_blockers(candidate,set(POSES),native,fp)
    fill_findings=[];hole_findings=[]
    for pad in candidate['pads']:
        if pad['ref'] not in POSES:continue
        for layer in ('F.Cu','B.Cu'):
            body=unary_union(p.base.polygons(pad['layers'].get(layer,[])))
            if body.is_empty:continue
            for zone in candidate['zones']:
                if p.norm(zone['net'])==p.norm(pad['net']):continue
                for poly in p.base.polygons(zone['fills'].get(layer,[])):
                    gap=.15 if candidate['domains_normalized'].get(p.norm(zone['net']))==candidate['domains_normalized'].get(p.norm(pad['net'])) else .6
                    if body.distance(poly)<gap+p.MARGIN-1e-8:
                        fill_findings.append({'ref':pad['ref'],'pad':pad['num'],'layer':layer,'zone_uuid':zone['uuid'],'net':p.norm(zone['net']),'distance_mm':body.distance(poly),'minimum_mm':gap+p.MARGIN})
            for r in candidate['vias']:
                hole=Point(r['x'],r['y']).buffer(r['drill']/2)
                if body.distance(hole)<.25+p.MARGIN-1e-8:
                    hole_findings.append({'ref':pad['ref'],'pad':pad['num'],'layer':layer,'via_uuid':r['uuid'],'via_net':p.norm(r['net']),'distance_mm':body.distance(hole),'required_mm':.25+p.MARGIN,'same_net_plated_target':p.norm(r['net'])==p.norm(pad['net']) and r['uuid']==C.GROUND_VIA,'hole_overlap_mm2':body.intersection(hole).area})
    # Geometric necessary condition only: with strict retained fills and no pad
    # contact waiver, check source and load site feasibility even when the pose
    # is held. A positive count cannot authorize an invalid body/courtyard.
    pack=[]
    p.WINDOW=box(103,109,249,174)
    for net,terminal,window in ((p.NET,'U11012',SOURCE),(p.NET,'J15001',box(110,164,124,172)),(stage.caps.CORE,'U11012',SOURCE),(stage.caps.CORE,'R11022',box(236,109,249,123))):
        region=strict_site_region(candidate,areas,net,terminal,window)
        sites=p.hubs.pack_region(region,region.representative_point().coords[0]) if not region.is_empty else []
        pack.append({'net':p.norm(net),'terminal':terminal,'via_mm':[.6,.3],'ordinary_new_existing_and_new_new_spacing_mm':.8,'source_front_connected_region':mapping(region),'sampled_sites':sites,'sampled_count':len(sites),'minimum_common_current_sites':9,'geometry_only_not_current_sharing_or_native_qualification':True})
        print('PACK',p.norm(net),terminal,len(sites),flush=True)
    jcourt=next(f for f in candidate['footprints'] if f['ref']=='J15001')
    ccourt=next(f for f in candidate['footprints'] if f['ref']=='C15001')
    gap=unary_union(p.base.polygons(jcourt['courtyard']['F'])).distance(unary_union(p.base.polygons(ccourt['courtyard']['F'])))
    source_regions={r['terminal']+r['net']:r for r in pack}
    # Retained GND target is actual native all-six-annulus, not the obstacle
    # overlay's conservative all-layer projection.
    ground=via_native[C.GROUND_VIA]
    p.require(ground['flashed']==g['copper_layers'] and ground['span']==g['copper_layers'],'ground target actual native layers mismatch')
    for path in (Path(__file__),Path(C.__file__),Path(T.__file__),Path(stage.__file__),Path(stage.caps.__file__),Path(six.__file__),Path(six.five.__file__),Path(p.__file__),p.EXT/'tools/verify/rail_model.json'):
        p.read(path)
    for path,sha in p.READS.items():p.require(hashlib.sha256(Path(path).read_bytes()).hexdigest()==sha,'input changed')
    blocked=placement['verdict']!='HOST_BODY_PLACEMENT_PASS' or any(r['sampled_count']<9 for r in pack)
    receipt={'schema':'sbc-one-bounded-five-part-eleven-fanout-source-proposal-v1','verdict':'WITHHELD_BOUNDED_SET' if blocked else 'LOCAL_GEOMETRY_LEAD_REQUIRES_COMPLETE_ROUTE','evidence_class':'Exact host-only ownership/placement/source-array prerequisite screen',
      'board_sha256':p.C05_SHA,'overlay':overlay,'old_components':{r:fp[r] for r in POSES},'new_component_poses':POSES,'deltas_mm':deltas,'C15001_J15001_courtyard_gap_mm':gap,
      'exact_proposed_removal_ledger':ledger,'whole_private_CT_old_manifest':prior['whole_private_CT_old_manifest'],'old_stage_shared_terminal_ledger':prior['old_stage_shared_terminal_ledger'],
      'placement_strict_retained_copper_holes_fills_reservations':placement,'exact_foreign_copper_blockers':blockers,'frozen_outer_fill_observations':fill_findings,'actual_hole_observations':hole_findings,'array_necessary_conditions_even_if_pose_withheld':pack,
      'retained_ground_via':{'uuid':C.GROUND_VIA,'chunk_sha256':hashlib.sha256(native[C.GROUND_VIA]).hexdigest(),'actual_native_flashed':ground['flashed'],'actual_native_span':ground['span'],'at':[ground['x'],ground['y']],'unchanged':True},
      'current_contract':{'compute_A':3.6,'USB_A':.5,'HDMI_A':.05,'common_A':4.15,'output_budget_mV':100,'input_budget_mV':70,'via_A_max':.5,'minimum_common_transition_sites':9,'dedicated_compute_transition_sites':8,'dedicated_vs_other_branch_separation_qualified':False,'equal_sharing_assumed':False,'nominal_CT_uF':4.7,'corrected_CT_V':25,'timing_qualified':False},
      'replacement_paths':'NOT_EMITTED_UNTIL_PHYSICAL_PACKING_AND_SOURCE_ARRAY_PREREQUISITES_PASS','outside_items_fixed':True,'no_ownership_expansion':True,'board_emitted':False,'implemented':False,'native_jobs':0,'gpu_jobs':0,'qualified_power':False,
      'limits':['One exact five-part pose and authorized11SBCfanout+5powersegments+ownC15001groundstub+privateCT are screened; no further ownership expansion','All removed widths and original retained interior/endpoint contacts are ledgered; no preservation claim until a complete layer-specific physical contact graph is checked','Retained In1/In4 reference planes, foreign copper, every historical reservation and ordinary via spacing remain unchanged','Frozen F/Bfill obstruction is recorded separately; no repour/plane cut or mask waiver is silently used for acceptance','Array counts are bounded samples, not maximal-packing impossibility proofs or equal-current-sharing qualification','Same-net C15001pad/retained456via relationship is recorded as prospective plated-contact geometry, not a broad hole clearance waiver','Full upstream/downstream resistance, actual current sharing, localcapCTONPGground connections, source return anchoring/native no-loss, DRC and SI remain mandatory','Current4.7uF25VCT geometry/source correction does not inherit historical1uF50V standalone timing'],
      'read_set_sha256':p.READS}
    dest.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'path':str(dest),'placement':placement,'foreign_blockers':len(blockers),'hole_observations':len(hole_findings),'courtyard_gap_mm':gap,'arrays':[(r['terminal'],r['net'],r['sampled_count']) for r in pack],'board_emitted':False}),flush=True)


if __name__=='__main__':main()
