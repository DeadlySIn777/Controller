"""General rigid poses; exact named IO3 terminal hole, source-local screen only."""
from pathlib import Path
H=Path(__file__).resolve().parent.parent
p=H/'sbc-power/nominate_R371_R7035_small_rigid_move_two_stubs_ordinary_return_r382.py'
s=p.read_text(encoding='utf-8').replace('r382','r383').replace('R382','R383')
s=s.replace('from shapely.geometry import Point,LineString','from shapely.geometry import Point,LineString,box')
s=s.replace("ref=zero(unary_union([rr['shape']for rr in lg if rr['kind']=='fill'and rr['layer']=='In1.Cu']));base=", "refFull=zero(unary_union([rr['shape']for rr in lg if rr['kind']=='fill'and rr['layer']=='In1.Cu']));localBox=box(79,19,90,31);ref=zero(refFull.intersection(localBox));put(O/'exact-local-source-reference-screen-envelope.json',{'source':'actual J11001.2 In1','local_clip_bounds':[79,19,90,31],'all_nomination_pad_and_terminal_shapes_strictly_inside_envelope':True,'full_source_reference_final_audit':'OPEN; local clip is only a routing screen and never a native/source replacement'});base=")
old="poses=sorted([(round(dx*.1,6),round(dy*.1,6))for dx in range(-15,16)for dy in range(-18,19)if dx or dy],key=lambda v:(math.hypot(*v),v[1]<0,abs(v[0])))"
new="poses=sorted([(angle,round(dx*.1,6),round(dy*.1,6))for angle in (0,-90,90,180)for dx in range(-15,16)for dy in range(-18,19)if angle or dx or dy],key=lambda v:(math.hypot(v[1],v[2])+.05*abs(v[0])/90,v[2]<0,abs(v[1]),abs(v[0])))"
assert old in s;s=s.replace(old,new)
s=s.replace('for dx,dy in poses:\n  movedcourt=affinity.translate(owncourt,dx,dy)', "for angle,dx,dy in poses:\n  rigid=lambda sh:affinity.translate(affinity.rotate(sh,angle,origin=(fp['x'],fp['y'])),dx,dy)\n  movedcourt=rigid(owncourt)")
s=s.replace("sh=affinity.translate(unary_union(L.poly(p['layers']['F.Cu'])),dx,dy)","sh=rigid(unary_union(L.poly(p['layers']['F.Cu'])))")
s=s.replace("'xy':[round(p['x']+dx,6),round(p['y']+dy,6)]", "'xy':[round(rigid(Point(p['x'],p['y'])).x,6),round(rigid(Point(p['x'],p['y'])).y,6)]")
s=s.replace("'translation_mm':[dx,dy]", "'host_rigid_pose_deg_dx_dy':[angle,dx,dy],'translation_mm':[dx,dy]")
s=s.replace("'rotation_and_native_local_AST_unchanged':True", "'native_angle_delta_degrees':(-angle)%360,'native_local_AST_unchanged':True")
s=s.replace("':'+str(dx)+':'+str(dy)", "':'+str(angle)+':'+str(dx)+':'+str(dy)")
needle="uid,n,s=holes[int(j)];distance=shape.distance(s)"
assert needle in s
s=s.replace(needle,"uid,n,s=holes[int(j)];distance=shape.distance(s)\n   if axis is not None and L.norm(net)=='/IO_3V3'and uid=='3945a1ae-f8cb-441a-ad9d-21bde31e0e9f'and axis.distance(Point(84.15,24.7))<.000001:continue")
s=s.replace("attempts.append(row)\n  if bad:continue", "attempts.append(row)\n  if len(attempts)%25==0:put(O/'finite-small-rigid-pose-ordinary-return-and-terminal-geometry-attempts.json',attempts)\n  if bad:continue")
needle="row['terminal_stub_count']=len(nt);row['terminal_stub_deficits']=bad;"
assert needle in s
extra="""for t in nt:
   axis=LineString([t['a'],t['b']])
   for np in newpads:
    if L.norm(np['original']['net'])==L.norm(t['net']):continue
    dd=axis.distance(np['shape'])-t['w']/2
    if dd<.175:bad.append({'kind':'new-stub-to-other-actually-moved-pad','UUID':t['uuid'],'pin':np['original']['num'],'actual_gap_mm':dd})
   for tt in nt:
    if L.norm(tt['net'])==L.norm(t['net']):continue
    dd=axis.distance(LineString([tt['a'],tt['b']]))-t['w']/2-tt['w']/2
    if dd<.175:bad.append({'kind':'new-mutual-foreign-stub-Cu','UUID':t['uuid'],'other_UUID':tt['uuid'],'actual_gap_mm':dd})
  """
s=s.replace(needle,extra+needle)
(H/'sbc-power/exact-expanded-small-R7035-rigid-rotation-screen-r383.py').write_text(s,encoding='utf-8')
exec(compile(s,str(__file__),'exec'))
