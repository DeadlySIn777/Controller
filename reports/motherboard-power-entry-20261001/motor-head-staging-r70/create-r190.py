from pathlib import Path
s=Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/health-U20-cell-r177.py').read_text().replace('ROOT94-health-U20-cell-r177','ROOT94-health-U26-cell-r190')
a=s.index('frozen=json.loads(');z=s.index("ps={(f.GetReference()",a)
s=s[:a]+'''h=json.loads(Path('reports/motherboard-power-entry-20261001/health-supply-r99/receipt.json').read_text());ret={v['uuid']for v in h['exact_added_copper']if v['role'].startswith(('U11026_own','FIELD_sink_actual_own_supply'))};ofs={f.GetReference():f for f in original.GetFootprints()};pns={p.GetNumber():p for p in ofs['U11026'].Pads()};control_source={}
for pn,p in pns.items():
 pt=mm(p.GetPosition());ret|={t.m_Uuid.AsString()for t in original.GetTracks()if t.GetNetname()==p.GetNetname()and (pt==mm(t.GetStart())or pt==mm(t.GetEnd()))}
for pn in['1','3']:
 n=pns[pn].GetNetname();other=[p for p in original.GetPads()if p.GetNetname()==n and p.GetParentFootprint().GetReference()!='U11026'];assert len(other)==1 and other[0].GetParentFootprint().GetReference()=='U11025';control_source[pn]=(other[0].GetParentFootprint().GetReference(),other[0].GetNumber());ret|={t.m_Uuid.AsString()for t in original.GetTracks()if t.GetNetname()==n}
t=parse(without_generated_fills(B.read_text()));t=[v for v in t if not(isinstance(v,list)and v and v[0]in['segment','via']and value(child(v,'uuid')[1])in ret)];D=O/'literal-retired-input.kicad_pcb';D.write_text(dump_board(t))
for e in['.kicad_pro','.kicad_dru']:shutil.copyfile(B.with_suffix(e),D.with_suffix(e))
b=pcbnew.LoadBoard(str(D));fs={f.GetReference():f for f in b.GetFootprints()};oldposes={r:dict(point_mm=mm(fs[r].GetPosition()),angle=fs[r].GetOrientationDegrees(),layer=b.GetLayerName(fs[r].GetLayer()))for r in['U11026','C11081']};fs['U11026'].SetPosition(xy((334.5,191)));fs['C11081'].SetPosition(xy((335.3375,190.225)))
for r in oldposes:
 for z in fs.values():
  if z.GetReference()!=r and z.GetLayer()==fs[r].GetLayer():assert not intersects(side_box(fs[r]),side_box(z),0),('COURT',r,z.GetReference())
''' +s[z:]
a=s.index("pg=ps['U11020'");z=s.index('debug();pcbnew.ZONE_FILLER',a)
s=s[:a]+'''pg=ps['U11026','5'].GetNetname();gn=ps['U11026','2'].GetNetname();pv=(336.0875,191);gv=(336.8875,191);og=(332.9125,191)
via(pv,pg,'U11026_local_positive_transfer');via(gv,gn,'U11026_local_Source_return_stitch');via(og,gn,'U11026_actual_ground_pin_transfer')
route(mm(ps['U11026','5'].GetPosition()),pv,pg,pcbnew.F_Cu,'U11026_own_positive_F');route(mm(ps['C11081','1'].GetPosition()),pv,pg,pcbnew.B_Cu,'U11026_own_positive_B');route(mm(ps['C11081','2'].GetPosition()),gv,gn,pcbnew.B_Cu,'U11026_own_bypass_return');route(mm(ps['U11026','2'].GetPosition()),og,gn,pcbnew.F_Cu,'U11026_actual_own_Ground_pin')
for pn in['1','3']:
 p=ps['U11026',pn];route(mm(p.GetPosition()),mm(ps[control_source[pn]].GetPosition()),p.GetNetname(),pcbnew.F_Cu,'U11026_actual_input_'+pn,.2)
for pn,rv,sv in [('4',(336.3375,191.95),(327.5875,191.65)),('6',(336.3375,190.05),(329.0875,190.35))]:
 p=ps['U11026',pn];n=p.GetNetname();via(rv,n,'U11026_LED_POWER_'+pn+'_local_transfer');route(mm(p.GetPosition()),rv,n,pcbnew.F_Cu,'U11026_LED_POWER_'+pn+'_F',.2);route(rv,sv,n,pcbnew.B_Cu,'U11026_LED_POWER_'+pn+'_B',.2)
route(pv,(332.5875,191),pg,pcbnew.B_Cu,'U11026_actual_field_supply_from_U11025',.25)
''' +s[z:]
s=s.replace("[('U11020','5','C11079','1'),('U11020','2','C11079','2'),('U11020','5','C11029','1'),('U11020','2','C11088','2')]","[('U11026','5','C11081','1'),('U11026','2','C11081','2'),('U11026','5','C11055','1'),('U11026','2','C11055','2')]").replace('motor-health-U20-cell-candidate','motor-health-U26-cell-candidate')
Path('reports/motherboard-power-entry-20261001/motor-head-staging-r70/health-U26-cell-r190.py').write_text(s)
