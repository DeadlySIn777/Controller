"""Exact isolated future controlled-rule delta for one J15001 clock neck."""
import json,sys,uuid
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import audit_aux_exact_raw as A
import net_identity_exact as N
from shapely.geometry import Polygon,LineString
P,G,S,C=A.P,A.G,A.S,A.C

def main():
    dest=HERE/'cm-terminal-profile-r1'
    if dest.exists():raise ValueError('Fresh isolated proposal directory required')
    dest.mkdir()
    geometry=G.REPORT/'controlled-geometry'
    source=A.read(G.SOURCE);identities=N.SourceNets(source)
    r=json.loads(A.read(HERE/'cm-controlled-initial-r2.json'));p=dict(r['scoped_terminal_profile'])
    name=p['terminal_region_name'];points=[[128.142,165.84],[128.362,165.84],[128.362,167.285],[128.142,167.285]]
    neck=p['terminal_only_neck'];body=LineString([neck['from_mm'],neck['to_mm']]).buffer(.1,resolution=128)
    if not Polygon(points).covers(body):raise ValueError('Scoped region does not cover exact selected terminal copper')
    chunks={z['uuid']:z['chunk'].encode() for z in r['added_serialized_chunks']}
    exact=G.parse(neck['new_uuid'],chunks[neck['new_uuid']],{})
    if exact['net']!='/motherboard_compute/CM_CAN_SPI_SCLK' or exact['layer']!='F.Cu' or exact['w']!=.2:raise ValueError('Exact neck identity differs')
    native_net=identities.raw(exact['net'])
    future=geometry/'future-copy-proposal'
    prior_rules=A.read(future/'board.kicad_dru.proposed');prior_project=A.read(future/'board.kicad_pro.proposed')
    lines=prior_rules.decode().splitlines(keepends=True);indices=[i for i,z in enumerate(lines) if '(rule "PROVISIONAL IMP_50 outer width"' in z]
    if len(indices)!=1:raise ValueError('Unique provisional bulk rule absent')
    idx=indices[0]+1;line=lines[idx]
    if not line.strip().startswith('(condition '):raise ValueError('Expected exact bulk condition syntax')
    encoded=line.strip()[len('(condition '):-1];before=json.loads(encoded)
    terminal=p['condition'];after=f'({before}) && !({terminal})'
    lines[idx]=f' (condition {json.dumps(after)})\n'
    rewritten=''.join(lines).encode();appended=p['new_rule_text'].encode()
    rules=rewritten+b'\n# Isolated proposal only: exact pad/native-net/region/selected-neck receipt binding below.\n'+appended
    if prior_rules.count(b'PROVISIONAL IMP_50 outer width')!=1:raise ValueError('Bulk rule count differs')
    # The literal U1001 exemption and every other condition/constraint stay
    # unchanged; only the named IMP_50 condition gains this exact exception.
    if prior_rules.replace(line.encode(),b'')!=rewritten.replace(lines[idx].encode(),b''):raise ValueError('Unscoped future rule bytes changed')
    area_uuid=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller/cm-terminal-neck-profile-r1/'+name))
    poly=' '.join(f'(xy {x:.6f} {y:.6f})' for x,y in points)
    area=(f'\t(zone\n\t\t(layer "F.Cu")\n\t\t(uuid "{area_uuid}")\n\t\t(name "{name}")\n\t\t(hatch edge 0.5)\n\t\t(connect_pads (clearance 0))\n\t\t(min_thickness 0.25)\n\t\t(keepout (tracks allowed) (vias allowed) (pads allowed) (copperpour allowed) (footprints allowed))\n\t\t(placement (enabled no) (sheetname ""))\n\t\t(fill (thermal_gap 0.5) (thermal_bridge_width 0.5) (island_removal_mode 0))\n\t\t(polygon (pts {poly}))\n\t)\n').encode()
    if C.pcbtext.chunk_kind(area)!='zone' or C.pcbtext.chunk_uuid(area)!=area_uuid:raise ValueError('Exact named area chunk serialization differs')
    (dest/'board.kicad_dru.proposed').write_bytes(rules);(dest/'board.kicad_pro.proposed').write_bytes(prior_project);(dest/'terminal-rule-area.chunk').write_bytes(area)
    result={'schema':'isolated-cm-terminal-profile-r1','scope':'NEW_PROPOSAL_ONLY_NOT_INSTALLED','subject_source_sha256':C.sha(source),'original_future_proposal_sha256':C.sha(A.read(future/'proposal.json')),'original_future_rules_sha256':C.sha(prior_rules),'original_future_project_sha256':C.sha(prior_project),'proposed_rules_sha256':C.sha(rules),'proposed_project_sha256':C.sha(prior_project),'area_uuid':area_uuid,'area_chunk_sha256':C.sha(area),'exact_selected_pad':p['exact_pad'],'exact_selected_neck_uuid':neck['new_uuid'],'exact_selected_neck_chunk_sha256':C.sha(chunks[neck['new_uuid']]),'native_raw_net':native_net,'terminal_region_polygon_mm':points,'terminal_centreline_length_mm':p['neck_centreline_length_mm'],'outside_native_pad_length_mm':p['outside_source_pad_length_mm'],'new_terminal_condition':terminal,'old_bulk_condition':before,'new_bulk_condition':after,'original_U1001_literal_and_all_other_rule_bytes_preserved':True,'future_project_bytes_preserved':True,'original_project_and_rules_modified':False,'mathematical_neck_discontinuity':p['model_discontinuity'],'clearance_rule_unchanged_mm':.15,'planner_margin_mm':.025,'grid_limited_geometry':'1.225 mm neck is the shortest .025mm endpoint increment preserving .175mm bulk-to-MOSI terminal planning gap in the chosen topology; final extracted pad/load SI remains open','installed':False,'board_area_installed':False,'native_parse_effective_composite_constraints':'OPEN','candidate_board_binding':'OPEN until complete coupled CM candidate and independent audit','read_files_sha256':A.READS,'manufacturing_ready':False}
    (dest/'proposal.json').write_text(json.dumps(result,indent=1)+'\n');print(json.dumps({'proposal':str(dest/'proposal.json'),'rules_sha256':C.sha(rules),'region':name,'neck_mm':p['neck_centreline_length_mm']}))
if __name__=='__main__':main()
