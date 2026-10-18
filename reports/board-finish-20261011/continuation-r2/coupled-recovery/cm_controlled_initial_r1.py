"""Concrete controlled CM SCLK bulk + exact terminal neck ownership screen.

No board/profile installation. Full source/contact authority and native geometry
are bound before nominating additional coupled blockers for the wider route.
"""
import json,math,sys
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import audit_aux_exact_raw as A
import net_identity_exact as N
import native_flash_model as F
import xf_continuous_landings_r3 as X
P,G,S,C=A.P,A.G,A.S,A.C
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
CLK='/motherboard_compute/CM_CAN_SPI_SCLK'
MOSI='/motherboard_compute/CM_CAN_SPI_MOSI'
CONTROL=G.REPORT/'controlled-geometry'

def main():
    out=HERE/'cm-controlled-initial-r1.json'
    if out.exists():raise ValueError('Fresh receipt required')
    raw=A.read(G.SOURCE);now=C.inventory(raw);oldraw=A.read(S.overlay_tool.base.BASE);old=C.inventory(oldraw);identities=N.SourceNets(raw)
    native=json.loads(A.read(A.NATIVE/'geometry.json'));template=json.loads(A.read(S.overlay_tool.base.GEOM));template,proof=A.fresh_template(old,now,template,native)
    masks={u:set(ls) for u,ls in json.loads(A.read(A.NATIVE/'actual-via-flashes.json'))['vias'].items()}
    graph=json.loads(A.read(HERE/'conflict-graph.json'));row=next(r for r in graph['lost_route_rows'] if r['net']==CLK)
    geometry=json.loads(A.read(CONTROL/'geometry.json'));stackup=json.loads(A.read(CONTROL/'stackup.json'))
    for layer in ('F.Cu','B.Cu'):
        if geometry[layer]['IMP_50']['w_mm']!=.385 or geometry[layer]['IMP_50']['status']!='PROVISIONAL_AB':raise ValueError('Controlled outer geometry binding differs')
    for p in (CONTROL/'REPORT.txt',CONTROL/'future-copy-proposal/proposal.json',CONTROL/'native-check-r3/receipt.json'):A.read(p)
    blocker_ids=set(row['blocking_nets'][MOSI]['item_uuids'])
    clock_current={u for u,ch in now[4].items() if S.norm(S.overlay_tool.netname(ch))==CLK}
    if len(clock_current)!=13 or len(blocker_ids)!=2:raise ValueError('Owned original copper inventory differs')
    deleted=clock_current|blocker_ids;chunks={u:ch for u,ch in now[4].items() if u not in deleted};restores=set();added=set();operations=[]
    for u in sorted(clock_current):
        r=G.parse(u,now[4][u],{})
        if r['kind']!='segment' or r['layer']!='F.Cu' or r['w']!=.2:raise ValueError('Current clock role/width differs')
        uid,ch=identities.serial_segment(CLK,r['layer'],r['a'],r['b'],.385);chunks[uid]=ch;added.add(uid)
        operations.append({'original_uuid':u,'new_uuid':uid,'source':'current198b','bulk_width_mm':.385,'same_exact_endpoints':True})
    via_old={v['uuid']:v for v in template['vias']}
    neck_id='6b3a95ee-32b9-4838-a9bb-e094742b5bba';withheld={'b6486696-33f5-4ae9-8d51-d707a80259bb'}
    for item in row['missing_original_items']:
        u=item['uuid'];r=G.parse(u,old[4][u],{})
        if r['kind']=='via':chunks[u]=old[4][u];restores.add(u);masks[u]=set(via_old[u]['flashed']);continue
        if u in withheld:continue
        a,b=r['a'],r['b'];width=.385
        if u==neck_id:a,b=[128.252,167.175],[128.252,166.0];width=.2
        if u=='5f850a48-6b0c-4017-88fa-3a6ff675af56':b=[128.252,166.0]
        uid,ch=identities.serial_segment(CLK,r['layer'],a,b,width);chunks[uid]=ch;added.add(uid)
        operations.append({'original_uuid':u,'new_uuid':uid,'source':'originalr06','width_mm':width,'from_mm':a,'to_mm':b,'terminal_neck':u==neck_id})
    reserve,exempt=A.reservations();print('CM_CONTROLLED_INITIAL_MODEL',flush=True)
    g=identities.geometry(chunks,template);model=F.Model(g,reserve,exempt,native['vias'],{u:set(ls) for u,ls in json.loads(A.read(A.NATIVE/'actual-via-flashes.json'))['vias'].items()})
    parsed={u:G.parse(u,ch,{}) for u,ch in chunks.items() if u in added|restores};errors,clear,anti=A.clearance(model,parsed,added,restores)
    parts={S.norm(n):gs for n,gs in json.loads(A.read(G.REPORT/'measure/r07-four-fag-shared/partitions.json'))['nets'].items()};r06={S.norm(n):gs for n,gs in json.loads(A.read(P.R.R06_PART))['nets'].items()}
    _,_,ufs,groups=A.relationships(model,masks,parts,(CLK,MOSI));loss=[]
    for net in (CLK,MOSI):
        for label,rels in (('current198b',parts[net]),('r06',r06[net])):
            for rel in rels:
                if len({ufs[net].find(('p',p)) for p in rel})>1:loss.append({'net':net,'baseline':label,'relationship':rel})
    pad=next(p for p in template['pads'] if p['ref']=='J15001' and p['num']=='25');clockneck=next(op for op in operations if op.get('terminal_neck'))
    length=math.dist(clockneck['from_mm'],clockneck['to_mm'])
    sys.path.insert(0,str(CONTROL/'inputs'));import calculator as ic
    z_bulk,e_bulk=ic.hj_microstrip(.385,.22,.035,4.45);z_neck,e_neck=ic.hj_microstrip(.2,.22,.035,4.45)
    name='J15001_PAD25_CM_CAN_SCLK_TERMINAL_NECK_R1';rawnet=identities.raw(CLK)
    condition=f"A.Type == 'Track' && A.Layer == 'F.Cu' && A.NetName == '{rawnet}' && A.Width == 0.20mm && A.enclosedByArea('{name}')"
    profile={'scope':'NEW_ISOLATED_PROFILE_DELTA_ONLY_NOT_INSTALLED','exact_pad':{'ref':'J15001','num':'25','uuid':pad['uuid'],'net':rawnet,'native_source_at_mm':[pad['x'],pad['y']]},'terminal_region_name':name,'terminal_region_polygon_mm':[[128.142,165.89],[128.362,165.89],[128.362,167.285],[128.142,167.285]],'terminal_only_neck':clockneck,'neck_centreline_length_mm':length,'outside_source_pad_length_mm':length-.35,'condition':condition,'new_rule_text':f'(rule "J15001 exact CM CAN SCLK terminal neck only" (layer "F.Cu")\n (condition {json.dumps(condition)})\n (constraint track_width (min 0.20mm) (max 0.20mm))\n (constraint track_segment_length (max {length:.6f}mm)))\n','provisional_IMP50_condition_delta':'Exclude ONLY the same exact terminal predicate from its .375-.395 mm bulk rule; preserve literal U1001 predicate and every other rule','model_discontinuity':{'neck_B_ohm':z_neck,'bulk_B_ohm':z_bulk,'single_interface_reflection_magnitude':abs((z_neck-z_bulk)/(z_neck+z_bulk)),'neck_oneway_delay_ps':length*math.sqrt(e_neck)/.299792458,'source_h_mm':.22,'source_t_mm':.035,'source_er':4.45,'fabricator_pad_load_neighbour_copper_and_extracted_SI':'OPEN'},'rule_native_parse_enforcement':'NOT_RUN','original_project_rules_changed':False,'no_blanket_connector_neck_or_via_exemption':True}
    result={'schema':'cm-controlled-initial-r1','verdict':'COUPLED_BULK_AND_TERMINAL_RECIPE_REQUIRES_BLOCKER_REROUTE','source_sha256':A.SOURCE_SHA,'controlled_geometry_sha256':C.sha((CONTROL/'geometry.json').read_bytes()),'source_actual_annuli':model.source_annulus_proof,'fresh_pad_fill_proof':proof,'deleted_owned_clock_and_MOSI_items':sorted(deleted),'restored_original_vias':sorted(restores),'operations':operations,'added_serialized_chunks':[{'uuid':u,'sha256':C.sha(chunks[u]),'chunk':chunks[u].decode()} for u in sorted(added)],'initial_clearance_errors':errors,'prospective_restored_antipads':anti,'current_r06_relationship_losses_until_MOSI_repaired':loss,'scoped_terminal_profile':profile,'read_files_sha256':A.READS,'native_jobs':0,'gpu_jobs':0,'board_emitted':False,'adopted':False,'manufacturing_ready':False,'open_gates':['Reroute every nominated real blocker with complete current contact ledger','Qualified source-rooted full copper reference and actual transition returns','Exact candidate native annuli/refill/DRC and complete dual native current/r06 no-loss','Actual scoped new profile native parsing/effective rule enforcement','Current extracted bus/edge/termination/stub and neck discontinuity/real pad/load SI review']}
    out.write_text(json.dumps(result,indent=1)+'\n');print(json.dumps({'receipt':str(out),'clearance_errors':len(errors),'clock_obligation_loss':sum(x['net']==CLK for x in loss),'new_clock_segments':len(added),'neck_length_mm':length,'neck_model':profile['model_discontinuity']}))
if __name__=='__main__':main()
