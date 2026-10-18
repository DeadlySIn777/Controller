"""Same exact OBS8 scope with bounded real F dogleg escapes and diagnostics."""
from pathlib import Path
p=Path(__file__).parent;s=(p/'route_root81_one_pair_io3_screen_r04.py').read_text()
s=s.replace("    center=mm(p.GetPosition());name=p.GetNetname();result=[]","    center=mm(p.GetPosition());name=p.GetNetname();result=[];stages=dict(candidates=0,via_clear=0,front_path=0,reference_circle=0,ground=0)")
old="            if not via_clear(pt,name,.6,.3)or not clear([center,pt],name,pcbnew.F_Cu):continue"
new="""            stages['candidates']+=1
            if not via_clear(pt,name,.6,.3):continue
            stages['via_clear']+=1
            front=next((path for path in paths(center,pt)if sum(math.dist(a,z)for a,z in zip(path,path[1:]))<=4.5 and clear(path,name,pcbnew.F_Cu)),None)
            if front is None:continue
            stages['front_path']+=1"""
assert old in s;s=s.replace(old,new)
s=s.replace("            ground=ground_at(pt)","            stages['reference_circle']+=1\n            ground=ground_at(pt)")
s=s.replace("            if ground:result.append(dict(position=pt,ground=ground))","            if ground:stages['ground']+=1;result.append(dict(position=pt,ground=ground,front_path_mm=front))")
s=s.replace('    return result\n\ndef add_segment',"    print(json.dumps(dict(escape_pad=p.GetParentFootprint().GetReference()+'.'+p.GetNumber(),stages=stages)),flush=True)\n    return result\n\ndef add_segment")
old="        all_segments=[(mm(p.GetPosition()),av,pcbnew.F_Cu),(mm(q.GetPosition()),zv,pcbnew.F_Cu)]+[(s,t,pcbnew.In2_Cu)for s,t in zip(path,path[1:])]"
assert old in s;s=s.replace(old,"        all_segments=[(s,t,pcbnew.F_Cu)for entry in(a,z)for s,t in zip(entry['front_path_mm'],entry['front_path_mm'][1:])]+[(s,t,pcbnew.In2_Cu)for s,t in zip(path,path[1:])]")
old="        signal.append(add_segment(mm(pad.GetPosition()),entry['position'],name,pcbnew.F_Cu))";assert old in s
s=s.replace(old,"        signal.extend(add_segment(s,t,name,pcbnew.F_Cu)for s,t in zip(entry['front_path_mm'],entry['front_path_mm'][1:]))")
(p/'route_root81_one_pair_doglegs_r05.py').write_text(s);compile(s,str(p/'route_root81_one_pair_doglegs_r05.py'),'exec')
