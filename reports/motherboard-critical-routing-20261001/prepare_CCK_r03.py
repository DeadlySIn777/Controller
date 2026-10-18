from pathlib import Path
p=Path('reports/motherboard-critical-routing-20261001/route_actual_FPGA_CCK_ROOT84_F_In2_r01.py');s=p.read_text()
s=s.replace('checker=pieces.SourceAnchoredPiecesCheck',"moved_cap=next(f for f in b.GetFootprints()if f.GetReference()=='C1022');moved_cap.SetOrientationDegrees(90);moved_cap.SetPosition(xy((94.5,48.0)))\nchecker=pieces.SourceAnchoredPiecesCheck")
s=s.replace('receiver_ground=(109.,26.2)','receiver_ground=(109.,26.2);cap_feed=(93.6,48.8)')
s=s.replace("('/LOGIC_GND',receiver_ground,.5,.2))]","('/LOGIC_GND',receiver_ground,.5,.2),('/IO_3V3',cap_feed,.5,.2))]")
s=s.replace("add_via('/LOGIC_GND',source_ground,.5,.2,grounds);add_via('/LOGIC_GND',receiver_ground,.5,.2,grounds)","add_via('/LOGIC_GND',source_ground,.5,.2,grounds);add_via('/LOGIC_GND',receiver_ground,.5,.2,grounds)\ncap_cu=[];cap_power=next(p for p in moved_cap.Pads()if p.GetNumber()=='1');add_via('/IO_3V3',cap_feed,.5,.2,cap_cu);add_track('/IO_3V3',mm(cap_power.GetPosition()),cap_feed,pcbnew.B_Cu,.35,cap_cu)")
s=s.replace('tree=e.parse(BASE.read_text());old=copy.deepcopy(tree)',"temporary=OUT/'native-posed-copy.kicad_pcb';pcbnew.SaveBoard(str(temporary),b);tree=e.parse(temporary.read_text());old=copy.deepcopy(e.parse(BASE.read_text()))")
start=s.index('for t in added:');end=s.index("dest=OUT/'motherboard-FPGA-flash-CCK-candidate.kicad_pcb'")
s=s[:start]+'''# Native-save exact geometry remains subject to independent old-Cu/pad/pose comparison.
# Only C1022 native pose and the explicit additions are allowed.
'''+s[end:]
s=s.replace('new_SOURCE_ground_UUIDs=[t.m_Uuid.AsString()for t in grounds]',"new_SOURCE_ground_UUIDs=[t.m_Uuid.AsString()for t in grounds],new_C1022_local_power_UUIDs=[t.m_Uuid.AsString()for t in cap_cu],exact_C1022_pose_before=[[95.225,46.75],180],exact_C1022_pose_after=[[94.5,48],90],C1022_local_feed=cap_feed,owner_power_pad_distance_mm=math.dist(mm(cap_power.GetPosition()),mm(pads['U1001','L6'].GetPosition())),owner_2mm_engineering_target_NOT_passed=True")
Path('reports/motherboard-critical-routing-20261001/route_actual_FPGA_CCK_ROOT84_F_In2_r03.py').write_text(s)
