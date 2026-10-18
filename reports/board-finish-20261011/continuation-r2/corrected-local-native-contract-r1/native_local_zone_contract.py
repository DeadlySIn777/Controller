"""Read-only KiCad API attestation for exact new field-zone settings and rings."""
import hashlib,json,sys
from pathlib import Path
import pcbnew

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def canonical(points):
    points=[tuple(p) for p in points]
    if len(points)>1 and points[0]==points[-1]:points=points[:-1]
    if not points:raise ValueError('Empty native ring')
    candidates=[]
    for ring in (points,list(reversed(points))):
        least=min(ring)
        for i,p in enumerate(ring):
            if p==least:candidates.append(tuple(ring[i:]+ring[:i]))
    return min(candidates)
def points(chain):
    return [[int(chain.CPoint(i).x),int(chain.CPoint(i).y)] for i in range(chain.PointCount())]
def main():
    expected_path,board_path,out_path=map(Path,sys.argv[1:]);spec=json.loads(expected_path.read_bytes())
    if sha(board_path)!=spec['candidate_sha256']:raise ValueError('Native exact board differs')
    board=pcbnew.LoadBoard(str(board_path));zones={str(z.m_Uuid.AsString()):z for z in board.Zones()}
    errors=[];rows=[]
    for exp in spec['zones']:
        z=zones.get(exp['uuid'])
        if z is None:errors.append({'uuid':exp['uuid'],'reason':'Zone missing'});continue
        poly=z.Outline();actual={'raw_net':str(z.GetNetname()),'layers':sorted(str(board.GetLayerName(int(layer))) for layer in z.GetLayerSet().Seq()),'priority':int(z.GetAssignedPriority()),'local_clearance_IU':int(z.GetLocalClearance()),'minimum_thickness_IU':int(z.GetMinThickness()),'pad_connection':int(z.GetPadConnection()),'thermal_gap_IU':int(z.GetThermalReliefGap()),'thermal_spoke_IU':int(z.GetThermalReliefSpokeWidth()),'island_removal_mode':int(z.GetIslandRemovalMode()),'outer_count':int(poly.OutlineCount())}
        wanted={'raw_net':exp['raw_net'],'layers':[exp['layer']],'priority':124,'local_clearance_IU':150000,'minimum_thickness_IU':150000,'pad_connection':int(pcbnew.ZONE_CONNECTION_FULL),'thermal_gap_IU':150000,'thermal_spoke_IU':300000,'island_removal_mode':1,'outer_count':1}
        for key,value in wanted.items():
            if actual[key]!=value:errors.append({'uuid':exp['uuid'],'field':key,'expected':value,'actual':actual[key]})
        native=[]
        for i in range(poly.OutlineCount()):
            native.append(canonical(points(poly.COutline(i))))
            native.extend(canonical(points(poly.Hole(i,j))) for j in range(poly.HoleCount(i)))
        expected=[canonical(r) for r in exp['rings_IU']]
        exact=bool(native) and native[0]==expected[0] and sorted(native[1:])==sorted(expected[1:])
        if not exact:errors.append({'uuid':exp['uuid'],'reason':'Native outer or hole coordinates differ','native_ring_count':len(native),'expected_ring_count':len(expected)})
        rows.append({'uuid':exp['uuid'],'native_settings':actual,'outer_and_all_hole_integer_coordinates_exact':exact,'holes':len(native)-1,'native_ring_points':sum(len(r) for r in native)})
    report={'verdict':'PASS_NATIVE_52_CORRECTED_LOCAL_ZONES_ALL_RINGS_SETTINGS_RAW_NETS' if not errors else 'FAIL_NATIVE_FIELD_ZONE_CONTRACT','candidate_sha256':sha(board_path),'native_version':pcbnew.Version(),'rows':rows,'errors':errors,'native_zones_checked':len(rows),'native_holes_checked':sum(r['holes'] for r in rows),'source_2723_parts_and_all68_vias_gate':'SEPARATE_ATTESTATION_REQUIRED','no_native_save_or_refill':True,'native_fill_contact_current_DRC_and_final_SBC_mutual_composition':'OPEN','adopted':False}
    out_path.write_text(json.dumps(report,indent=1)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('verdict','native_zones_checked','native_holes_checked','errors')}),flush=True)
    return 0 if not errors else 1
if __name__=='__main__':raise SystemExit(main())
