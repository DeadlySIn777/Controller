"""Source-role recipes and exact native ISO1212 alarm-cell layout audit."""
from pathlib import Path
import argparse,json,hashlib,math
import pcbnew
from hardware_route_logic_return import mm,segment_distance
ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def polygons(p):
    q=p.GetEffectivePolygon(pcbnew.F_Cu)
    return[[mm(q.Outline(k).CPoint(i))for i in range(q.Outline(k).PointCount())]for k in range(q.OutlineCount())]
def distance(p,q):
    return min(segment_distance(a,b,c,d)for pp in polygons(p)for qq in polygons(q)for a,b in zip(pp,pp[1:]+pp[:1])for c,d in zip(qq,qq[1:]+qq[:1]))
def recipes(model):
    groups={};rows=[]
    for pair in range(6):
        m=pair*2;u=f'U{6035+pair}';g={u:[0,0,0],f'C{6015+pair*3}':[-5.425,-1.5875,180]}
        for j,y in [(0,-1.6),(1,1.7)]:
            n=m+j;thr=f'R{6051+n*3}';sense=f'R{6052+n*3}';bias=f'R{6053+n*3}';cin=f'C{6013+pair*3+j}';tvs=f'D{6025+n}'
            g[thr]=[13,-3.3 if j==0 else 3.3,180];g[sense]=[5.6,y,270];g[bias]=[-5.425,.2 if j==0 else 1.9,180];g[cin]=[8.2,y-.825,0];g[tvs]=[20,-3.3 if j==0 else 3.3,0]
            assert model['components'][thr]['pins']['1']==f'ALM{n}_FIELD'and model['components'][sense]['pins']['1']==f'ALM{n}_SENSE'
            rows.append(dict(channel=n,iso_ref=u,threshold_ref=thr,sense_ref=sense,filter_ref=cin,bias_ref=bias,tvs_ref=tvs,bypass_ref=f'C{6015+pair*3}',field_sense_pin='16'if j==0 else'11',field_input_pin='15'if j==0 else'10',field_ground_pin='14'if j==0 else'9',logic_output_pin='4'if j==0 else'5'))
        groups[f'MOTOR_ALARM_{m}_{m+1}']=g
    return dict(groups=groups,channels=rows,primary_datasheet='research/digital-inputs/iso1212.pdf',primary_sha256=sha(ROOT/'research/digital-inputs/iso1212.pdf'),threshold_external_pad_clearance_min_mm=4.0,vcc_bypass_max_mm=2.0,thermal_SUB_policy='Separate floating approximately2x2mm thermal islands are recommended by manufacturer pin table; no ground/inter-island/other-signal connection. Reserve B.Cu field-side half for exact final islands.',isolation_voltage_board_qualified=False,manufacturing_ready=False)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--board',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();assert not a.out.exists()and a.out.resolve().is_relative_to(ROOT/'reports');a.out.mkdir(parents=True);digest=sha(a.board);model=json.loads((ROOT/'hardware/motherboard_motors/design.json').read_text());rec=recipes(model);(a.out/'alarm-layout-recipes.json').write_text(json.dumps(rec,indent=2)+'\n');b=pcbnew.LoadBoard(str(a.board.resolve()));fs={f.GetReference():f for f in b.GetFootprints()};ps={(r,p.GetNumber()):p for r,f in fs.items()for p in f.Pads()};rows=[]
    for c in rec['channels']:
        if c['iso_ref']not in fs:continue
        u=c['iso_ref'];p=ps[(c['threshold_ref'],'1')];critical=[q for q in fs[u].Pads()]+list(fs[c['sense_ref']].Pads())+list(fs[c['filter_ref']].Pads());mind=min(distance(p,q)for q in critical);near=min(critical,key=lambda q:distance(p,q));field=mm(ps[(u,'16')].GetPosition());logic=mm(ps[(u,'2')].GetPosition());v=(field[0]-logic[0],field[1]-logic[1]);norm=math.hypot(*v);v=(v[0]/norm,v[1]/norm);o=mm(fs[u].GetPosition())
        side=lambda ref:min((mm(q.GetPosition())[0]-o[0])*v[0]+(mm(q.GetPosition())[1]-o[1])*v[1]for q in fs[ref].Pads())
        bypass=ps[(c['bypass_ref'],'1')];vcc=ps[(u,'2')];bypass_distance=math.dist(mm(bypass.GetPosition()),mm(vcc.GetPosition()))
        rows.append(dict(**c,external_RTHR_native_pad_clearance_mm=mind,minimum_4mm_met=mind>=4,closest_sensitive_pad=near.GetParentFootprint().GetReference()+'.'+near.GetNumber(),field_side_support_correct=all(side(c[r])>0 for r in ['sense_ref','filter_ref','threshold_ref','tvs_ref']),logic_side_support_correct=all(side(c[r])<0 for r in ['bias_ref','bypass_ref']),vcc_pin_to_bypass_pad_centre_mm=bypass_distance,bypass_2mm_screen_met=bypass_distance<=2))
    assert sha(a.board)==digest
    receipt=dict(source_board=str(a.board),source_board_sha256=digest,source_board_unchanged=True,channels=rows,alarm_channels=len(rows),ISO1212_packages=len({r['iso_ref']for r in rows}),physical_cell_components=len({ref for name,g in rec['groups'].items()for ref in g if ref in fs}),primary_datasheet_sha256=rec['primary_sha256'],failed_RTHR_channels=[r['channel']for r in rows if not r['minimum_4mm_met']],role_mismatch_channels=[r['channel']for r in rows if not(r['field_side_support_correct']and r['logic_side_support_correct'])],failed_2mm_bypass_channels=[r['channel']for r in rows if not r['bypass_2mm_screen_met']],manufacturing_ready=False)
    (a.out/'native-alarm-layout-audit.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:v for k,v in receipt.items()if k!='channels'}))
if __name__=='__main__':main()
