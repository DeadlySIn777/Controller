"""Native, source-preserving ISOW manufacturer-layout cell fixture.

The four HF caps intentionally overlap matching extended IC lands, as TI's
official EVM does. Courtyard profiles describe actual lead/body clearance at
these controlled same-net assembly sites; copper/paste/mask never change.
This fixture does not qualify the whole motherboard or its global planes.
"""
import argparse,collections,hashlib,json,math,shutil,subprocess
from pathlib import Path
import pcbnew as p
from motherboard_mechanical_audit import ROOT,sha,xy,rect,graphic_box,body_box,overlap,grown
from hardware_route_logic_return import identity,segment_distance,segment_hits_box,distance
from hardware_reconcile_motherboard_peripheral_pcb import piece
from hardware_route_local_signals import paths
from hardware_build_assembly import parse,dump,children,child,value,ref_property

CLI=Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')
BASE=ROOT/'reports/motherboard-pcb-integration-20260930/complete-mate-access-r25c/motherboard-mate-access-candidate.kicad_pcb'
SRC=ROOT/'hardware/motherboard_comms/design.json'
PROFILE=[(-6.2,-6.715),(6.2,-6.715),(6.2,3.85),(5.55,3.85),(5.55,6.10),(6.2,6.10),(6.2,6.715),(-6.2,6.715),(-6.2,6.10),(-5.55,6.10),(-5.55,3.85),(-6.2,3.85)]

def vec(point):return p.VECTOR2I(*[p.FromMM(z) for z in point])
def local(fp):
    f=p.FOOTPRINT(fp);f.SetOrientationDegrees(0);f.SetPosition(vec((0,0)));return f
def lands(fp):return sorted([piece(z) for z in local(fp).Pads()],key=repr)
def notch(fp):
    old=lands(fp);angle=fp.GetOrientationDegrees();pos=fp.GetPosition()
    fp.SetOrientationDegrees(0);fp.SetPosition(vec((0,0)))
    for s in list(fp.GraphicalItems()):
        if isinstance(s,p.PCB_SHAPE)and s.GetLayer()==p.F_CrtYd:fp.Remove(s)
    for a,b in zip(PROFILE,PROFILE[1:]+PROFILE[:1]):
        s=p.PCB_SHAPE(fp);s.SetShape(p.SHAPE_T_SEGMENT);s.SetLayer(p.F_CrtYd);s.SetWidth(p.FromMM(.05));s.SetStart(vec(a));s.SetEnd(vec(b));fp.Add(s)
    fp.SetPosition(pos);fp.SetOrientationDegrees(angle);assert old==lands(fp)
def recipe(ic,first,beads,iscan):
    q={ic:(0,0,0)}
    for offset,sign in [(0,-1),(4,1)]:
        for n,pose in enumerate([(sign*6.1,5.08,270),(sign*7.85,5.08,270),(sign*10.1,2.6,270),(sign*10.1,7.6,270)]):q['C'+str(first+offset+n)]=pose
    q['C'+str(first+8)]=(-7.4,-4.94,270)
    q['C'+str(first+9)]=(7.4,-4.94 if iscan else 0,270)
    q[beads[0]]=(13.5,4.445,0);q[beads[1]]=(13.5,5.715,0)
    return q

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',required=True,type=Path);a=ap.parse_args();out=a.out.resolve();assert not out.exists();out.mkdir(parents=True)
    before={str(q):sha(q)for q in [BASE,SRC,ROOT/'hardware/motherboard_comms/CNC_MB_Comms.pretty/ISOW_DFM20_TI.kicad_mod',Path(__file__)]}
    d=json.loads(SRC.read_text());b=p.LoadBoard(str(BASE));oldfps={f.GetReference():f for f in b.GetFootprints()}
    recipes=[recipe('U14812',14814,['U14814','U14815'],False),recipe('U14813',14825,['U14817','U14818'],True)]
    owned=set().union(*[set(r)for r in recipes]);assert len(owned)==26
    oldland={r:lands(oldfps[r])for r in owned}
    # Native Remove(FOOTPRINT) is unsafe in this bundled SWIG binding. Use an
    # explicit filtered native source fixture, never edit the parent board.
    tree=parse(BASE.read_text(encoding='utf-8'))
    for item in list(tree):
        if not isinstance(item,list):continue
        if item[0]=='footprint' and value(ref_property(item)[2])not in owned:tree.remove(item)
        elif item[0]in['segment','via','arc','zone']:tree.remove(item)
        elif item[0].startswith('gr_')and (child(item,'layer')is None or value(child(item,'layer')[1])!='Edge.Cuts'):tree.remove(item)
    filtered=out/'filtered-native-input.kicad_pcb';filtered.write_text(dump(tree)+'\n');b=p.LoadBoard(str(filtered))
    for f in b.GetFootprints():
        f.Reference().SetLayer(p.F_Fab)
        if f.GetReference().startswith('U1481')and f.GetReference()in['U14812','U14813']:notch(f)
    fps={f.GetReference():f for f in b.GetFootprints()};poses={}
    for i,q in enumerate(recipes):
        origin=(40+40*i,40)
        for ref,(x,y,angle)in q.items():
            f=fps[ref];f.SetOrientationDegrees(angle);f.SetPosition(vec((origin[0]+x,origin[1]+y)));poses[ref]=[origin[0]+x,origin[1]+y,angle]
    assert oldland=={r:lands(fps[r])for r in owned}
    # Project-only modified copy; source library and exact land geometry intact.
    for q in BASE.parent.iterdir():
        if q.is_dir()and(q.suffix=='.pretty'or q.name=='3dmodels'):shutil.copytree(q,out/q.name)
    for name in ['fp-lib-table']:shutil.copyfile(BASE.parent/name,out/name)
    for suffix in ['.kicad_pro','.kicad_dru']:shutil.copyfile(BASE.with_suffix(suffix),out/('isow-layout-fixture'+suffix))
    lib=out/'CNC_MB_Comms.pretty';lf=p.FootprintLoad(str(lib),'ISOW_DFM20_TI');oldlibland=lands(lf);notch(lf);p.PCB_IO_KICAD_SEXPR().FootprintSave(str(lib),lf);assert oldlibland==lands(p.FootprintLoad(str(lib),'ISOW_DFM20_TI'))
    pads={r:{z.GetNumber():z for z in f.Pads()}for r,f in fps.items()};added=[]
    def clear(points,net,layer,width=.4):
        for s,e in zip(points,points[1:]):
            for z in b.GetPads():
                if z.GetNetname()!=net and z.IsOnLayer(layer)and segment_hits_box(s,e,rect(z.GetBoundingBox()),.15+width/2):return False
            for t in b.GetTracks():
                tw=t.GetWidth(p.F_Cu) if isinstance(t,p.PCB_VIA) else t.GetWidth()
                if t.GetNetname()!=net and t.IsOnLayer(layer)and segment_distance(s,e,xy(t.GetStart()),xy(t.GetEnd()))<.15+width/2+p.ToMM(tw)/2-1e-6:return False
        return True
    def track(points,net,layer,width=.4):
        for s,e in zip(points,points[1:]):
            if s==e:continue
            t=p.PCB_TRACK(b);t.SetStart(vec(s));t.SetEnd(vec(e));t.SetWidth(p.FromMM(width));t.SetLayer(layer);t.SetNet(b.FindNet(net));b.Add(t);added.append(identity(t))
    def via(point,net):
        v=p.PCB_VIA(b);v.SetPosition(vec(point));v.SetWidth(p.FromMM(.6));v.SetDrill(p.FromMM(.3));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNet(b.FindNet(net));b.Add(v);added.append(identity(v))
    route=[]
    def connect(ref,pin,target,tpin):
        one,two=pads[ref][str(pin)],pads[target][str(tpin)];assert one.GetNetname()==two.GetNetname();net=one.GetNetname();s,e=xy(one.GetPosition()),xy(two.GetPosition())
        b.BuildConnectivity();already=two.m_Uuid.AsString()in{z.m_Uuid.AsString()for z in b.GetConnectivity().GetConnectedItems(one)if z.Type()==p.PCB_PAD_T}
        if already:route.append(dict(a=[ref,str(pin)],z=[target,str(tpin)],method='actual matching-land overlap'));return
        trial=next((q for q in paths(s,e)if clear(q,net,p.F_Cu)),None)
        if trial is not None:track(trial,net,p.F_Cu);route.append(dict(a=[ref,str(pin)],z=[target,str(tpin)],method='same-side F.Cu',points=trial));return
        # Bulk/low-frequency branches may use own-domain vias; HF always direct.
        for os in[(1,0),(-1,0),(0,1),(0,-1)]:
            vs=(s[0]+os[0]*.8,s[1]+os[1]*.8)
            if not clear([s,vs],net,p.F_Cu,.3)or not clear([vs,vs],net,p.F_Cu,.6):continue
            for oe in[(1,0),(-1,0),(0,1),(0,-1)]:
                ve=(e[0]+oe[0]*.8,e[1]+oe[1]*.8)
                if not clear([e,ve],net,p.F_Cu,.3)or not clear([ve,ve],net,p.F_Cu,.6):continue
                trial=next((q for q in paths(vs,ve)if clear(q,net,p.B_Cu)),None)
                if trial is None:continue
                track([s,vs],net,p.F_Cu,.3);track([e,ve],net,p.F_Cu,.3);via(vs,net);via(ve,net);track(trial,net,p.B_Cu);route.append(dict(a=[ref,str(pin)],z=[target,str(tpin)],method='own-domain bulk/logic B.Cu with two vias',points=trial));return
        raise ValueError('No local route '+ref+'.'+str(pin)+' -> '+target+'.'+str(tpin))
    hf=[];bulk=[]
    for ic,first,beads,can in [('U14812',14814,['U14814','U14815'],False),('U14813',14825,['U14817','U14818'],True)]:
        for off,pp,gp in[(0,9,10),(4,12,11)]:
            for n in range(4):
                ref='C'+str(first+off+n)
                connect(ref,1,ic,pp);connect(ref,2,ic,gp)
            h='C'+str(first+off);hf.append(dict(ref=h,owner=ic,power_pin=pp,return_pin=gp,all_F_Cu=True,actual_same_net_land_overlap=True,pad_centre_distance_mm=math.dist(xy(pads[h]['1'].GetPosition()),xy(pads[ic][str(pp)].GetPosition())),physical_pin_tip_to_cap_body_nominal_mm=[.510,.890],aggregate_relative_X_assembly_allowance_mm=.10,conditional_pin_tip_to_body_mm=[.410,.990],assembly_bound_qualified=False))
            for n in [2,3]:
                ref='C'+str(first+off+n);dist=[]
                for pin in['1','2']:
                    aa,bb=rect(pads[h][pin].GetBoundingBox()),rect(pads[ref][pin].GetBoundingBox());dx=max(0,aa[0]-bb[2],bb[0]-aa[2]);dy=max(0,aa[1]-bb[3],bb[1]-aa[3]);dist.append(math.hypot(dx,dy))
                assert all(2<=z<=4 for z in dist),(ref,dist);bulk.append(dict(ref=ref,HF=h,matching_terminal_edge_gaps_mm=dist,all_F_Cu=True,effective_C_at_bias_qualified=False))
        connect('C'+str(first+8),1,ic,1);connect('C'+str(first+8),2,ic,6)
        connect('C'+str(first+9),1,ic,20 if can else 16);connect('C'+str(first+9),2,ic,17 if can else 15)
        connect(beads[0],1,ic,12);connect(beads[1],1,ic,11)
        connect(beads[0],2,ic,20 if can else 16);connect(beads[1],2,ic,17 if can else 15)
        connect(ic,13,ic,12 if can else 11)
        if can:
            connect(ic,15,ic,16);connect(ic,16,ic,17)
    dest=out/'isow-layout-fixture.kicad_pcb';p.SaveBoard(str(dest),b)
    # Native SaveBoard can synthesize default ignore severities for the new
    # fixture basename. Restore the exact parent all-checks rules AFTER save.
    for suffix in ['.kicad_pro','.kicad_dru']:shutil.copyfile(BASE.with_suffix(suffix),dest.with_suffix(suffix))
    fresh=p.LoadBoard(str(dest));fresh.BuildConnectivity()
    assert oldland=={f.GetReference():lands(f)for f in fresh.GetFootprints()}
    cmd=[str(CLI),'pcb','drc','--format','json','--severity-all','--all-track-errors','-o',str(out/'drc.json'),str(dest)];res=subprocess.run(cmd,capture_output=True,text=True);(out/'drc-command.txt').write_text(res.stdout+res.stderr);drc=json.loads((out/'drc.json').read_text())
    assert before=={str(q):sha(Path(q))for q in before}
    report=dict(input_hashes=before,candidate_SHA256=sha(dest),fixture_only=True,source_modified=False,PCB_parent_modified=False,physical_parts=len(fresh.GetFootprints()),project_courtyard_only_override=True,exact_land_paste_mask_geometry_preserved=True,controlled_courtyard_polygon_mm=PROFILE,recipes=recipes,fixture_poses=poses,HF=hf,bulk=bulk,route_ledger=route,added_native_copper=added,native_DRC_regular_violations=len(drc['violations']),native_DRC_ignored_checks=drc.get('ignored_checks',[]),uncapped_missing_joins=fresh.GetConnectivity().GetUnconnectedCount(False),whole_board_return_and_raw_secondary_exclusion_verified=False,manufacturing_ready=False)
    (out/'receipt.json').write_text(json.dumps(report,indent=2)+'\n');shutil.copyfile(__file__,out/'issued-tool.py');print(json.dumps({k:v for k,v in report.items()if k not in['input_hashes','recipes','fixture_poses','HF','bulk','route_ledger','added_native_copper','controlled_courtyard_polygon_mm']}))
    assert not drc['violations']and not drc.get('ignored_checks')
if __name__=='__main__':main()
