"""Independent native ISOW source/loop/foreign-metal verifier, report only."""
import argparse,copy,json,math
from pathlib import Path
import pcbnew as p
from motherboard_mechanical_audit import ROOT,sha,xy,rect
from hardware_isow_layout_recipe import lands,vec
from hardware_apply_isow_cells import poly
from hardware_route_selected_additive import corridor_polygon

def intersection(a,b):
    z=p.SHAPE_POLY_SET();z.Append(a);z.BooleanIntersection(b);return z.OutlineCount()>0 and z.Area()>1
def rectangle(z):
    a,b,c,d=z;return poly([(a,b),(c,b),(c,d),(a,d)])
def land_template(f):return sorted([(z.GetNumber(),tuple(z.GetFPRelativePosition()),tuple(z.GetSize()),tuple(z.GetDrillSize()),z.GetShape(),z.GetLayerSet().FmtBin(),z.GetRoundRectRadiusRatio())for z in f.Pads()],key=repr)
def evaluate(board,source,receipt):
    fs={f.GetReference():f for f in board.GetFootprints()};errors=[];cells=[];board.BuildConnectivity()
    original=p.FootprintLoad(str(ROOT/'hardware/motherboard_comms/CNC_MB_Comms.pretty'),'ISOW_DFM20_TI')
    for ic,first in [('U14812',14814),('U14813',14825)]:
        f=fs[ic];tag='RS485'if ic=='U14812'else'CAN';ox,oy=xy(f.GetPosition());raw={z.GetNetname()for z in f.Pads()if z.GetNumber()in['11','12','13']};row=dict(owner=ic,actual_MPN=f.GetValue(),HF=[],raw_corridor_foreign_metal=[],raw_corridor_filled_zones=[])
        if land_template(f)!=land_template(original):errors.append(ic+' exact manufacturer land/paste/mask geometry changed')
        for off,ip,gp in[(0,'9','10'),(4,'12','11')]:
            cap=fs['C'+str(first+off)];cp={z.GetNumber():z for z in cap.Pads()};dp={z.GetNumber():z for z in f.Pads()}
            actual=[xy(cap.GetPosition())[0]-ox,xy(cap.GetPosition())[1]-oy,cap.GetOrientationDegrees()]
            if cap.GetLayer()!=p.F_Cu:errors.append(cap.GetReference()+' is not same F.Cu side')
            if max(abs(actual[0])-6.1,abs(actual[1]-5.08))>1e-5:errors.append(cap.GetReference()+' moved from reviewed HF window')
            overlap=[]
            for pin,ownerpin in[('1',ip),('2',gp)]:
                if cp[pin].GetNetname()!=dp[ownerpin].GetNetname():errors.append(cap.GetReference()+' source pin mismatch')
                a=rectangle(rect(cp[pin].GetBoundingBox()));b=rectangle(rect(dp[ownerpin].GetBoundingBox()));overlap.append(intersection(a,b))
                cluster={z.m_Uuid.AsString()for z in board.GetConnectivity().GetConnectedItems(cp[pin])if z.Type()==p.PCB_PAD_T}
                if dp[ownerpin].m_Uuid.AsString()not in cluster:errors.append(cap.GetReference()+' actual HF join is absent')
            if not all(overlap):errors.append(cap.GetReference()+' no longer has actual matching-land overlap')
            row['HF'].append(dict(ref=cap.GetReference(),reviewed_pose_relative_mm=actual,actual_matching_land_overlap=overlap,shortest_actual_same_net_land_gap_mm=0.0 if all(overlap)else None,physical_pin_tip_body_nominal_mm=[.510,.890],conditional_aggregate_relative_X_allowance_mm=.10,assembly_process_bound_qualified=False))
        area=next((z for z in board.Zones()if z.GetZoneName()==ic+'_RAW_CONVERTER_POUR_EXCLUSION'),None)
        if area is None:errors.append(ic+' missing converter exclusion');cells.append(row);continue
        enabled={n for n in range(64)if p.IsCopperLayer(n)and board.IsLayerEnabled(n)}
        if set(area.GetLayerSet().Seq())!=enabled or not area.GetDoNotAllowZoneFills():errors.append(ic+' incomplete all-layer pour exclusion')
        region=area.Outline()
        for pad in board.GetPads():
            if not pad.IsOnCopperLayer()or pad.GetNetname()in raw:continue
            if intersection(rectangle(rect(pad.GetBoundingBox())),region):row['raw_corridor_foreign_metal'].append(dict(kind='pad',ref=pad.GetParentFootprint().GetReference(),pin=pad.GetNumber(),net=pad.GetNetname()))
        for t in board.GetTracks():
            if t.GetNetname()in raw:continue
            width=t.GetWidth(p.F_Cu)if isinstance(t,p.PCB_VIA)else t.GetWidth()
            shape=corridor_polygon(tuple(t.GetStart()),tuple(t.GetEnd()),width/2)
            if intersection(shape,region):row['raw_corridor_foreign_metal'].append(dict(kind=t.GetClass(),UUID=t.m_Uuid.AsString(),net=t.GetNetname()))
        for z in board.Zones():
            if z.GetIsRuleArea():continue
            for layer in z.GetLayerSet().Seq():
                if z.HasFilledPolysForLayer(layer)and intersection(z.GetFilledPolysList(layer),region):row['raw_corridor_filled_zones'].append(dict(UUID=z.m_Uuid.AsString(),net=z.GetNetname(),layer=board.GetLayerName(layer)))
        if row['raw_corridor_foreign_metal']:errors.append(ic+' unrelated/filtered copper enters raw output corridor')
        if row['raw_corridor_filled_zones']:errors.append(ic+' actual filled plane enters raw output corridor')
        cells.append(row)
    for ref in receipt['exact_changed_poses']:
        s=source['components'][ref];f=fs[ref]
        if f.GetValue()!=s['value']:errors.append(ref+' source MPN/value changed')
        for z in f.Pads():
            wanted=s['pins'][z.GetNumber()]
            if wanted is not None and not z.GetNetname().endswith('/'+wanted):errors.append(ref+' wrong native pin/net '+z.GetNumber())
    return errors,cells

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',required=True,type=Path);a=ap.parse_args();out=a.out.resolve();assert not out.exists();out.mkdir(parents=True)
    bp=ROOT/'reports/motherboard-chassis-20261001/isow-full-cells-r03/motherboard-isow-cell-candidate.kicad_pcb';rp=bp.with_name('receipt.json');sp=ROOT/'hardware/motherboard_comms/design.json';primary=ROOT/'reports/motherboard-return-zoning-20260930/isow-bypass-review-r01/review.json';inputs={str(z):sha(z)for z in[bp,rp,sp,primary,Path(__file__)]};r=json.loads(rp.read_text());s=json.loads(sp.read_text());b=p.LoadBoard(str(bp));errors,cells=evaluate(b,s,r);assert not errors,errors
    # Native family geometry matches frozen electrical library exactly.
    source_fp=p.FootprintLoad(str(ROOT/'hardware/motherboard_comms/CNC_MB_Comms.pretty'),'ISOW_DFM20_TI');expected=lands(source_fp);native={f.GetReference():f for f in b.GetFootprints()}
    for ic in ['U14812','U14813']:assert land_template(source_fp)==land_template(native[ic]),ic
    negative=[]
    def test(name,mut):
        q=p.LoadBoard(str(bp));fs={f.GetReference():f for f in q.GetFootprints()};mut(q,fs);e,_=evaluate(q,s,r);negative.append(dict(name=name,rejected=bool(e),errors=e));assert e,name
    test('HF moved outside actual device-pin window',lambda q,fs:fs['C14814'].SetPosition(fs['C14814'].GetPosition()+vec((-.7,0))))
    test('HF placed on backside',lambda q,fs:fs['C14829'].SetLayer(p.B_Cu))
    test('HF source terminal net swapped',lambda q,fs:next(z for z in fs['C14818'].Pads()if z.GetNumber()=='1').SetNet(next(z for z in fs['U14812'].Pads()if z.GetNumber()=='11').GetNet()))
    test('IC manufacturer land widened',lambda q,fs:next(z for z in fs['U14812'].Pads()if z.GetNumber()=='9').SetSize(vec((2.2,.6))))
    def wrongarea(q,fs):
        area=next(z for z in q.Zones()if z.GetZoneName()=='U14813_RAW_CONVERTER_POUR_EXCLUSION');area.SetDoNotAllowZoneFills(False)
    test('Pour exclusion disabled',wrongarea)
    def foreign(q,fs):
        t=p.PCB_TRACK(q);t.SetLayer(p.F_Cu);t.SetWidth(p.FromMM(.25));t.SetStart(vec((380,96)));t.SetEnd(vec((384,96)));t.SetNet(q.FindNet('/LOGIC_GND'));q.Add(t)
    test('Filtered/foreign trace inserted in raw corridor',foreign)
    assert inputs=={z:sha(Path(z))for z in inputs}
    result=dict(input_hashes=inputs,independent_checks_pass=True,exact_source_lands_pass=True,actual_cells=cells,negative_controls=negative,all_negative_controls_rejected=True,source_or_PCB_modified=False,manufacturer_corridor_interpretation='Explicit right-hand raw-loop corridor follows TI Figure9-7 and EVM; permitted own raw-loop pads/traces/ferrite input are distinguished from prohibited unrelated traces and all global pours. Not a contradictory4mm circular ban around intrinsic neighboring package pads.',assembly_relative_tolerance_effective_C_EMC_qualified=False,manufacturing_ready=False)
    (out/'review.json').write_text(json.dumps(result,indent=2)+'\n');(out/'issued-tool.py').write_bytes(Path(__file__).read_bytes());print(json.dumps(dict(pass_=True,cells=len(cells),negative_controls=len(negative),foreign_metal=0,actual_fills=0)))
if __name__=='__main__':main()
