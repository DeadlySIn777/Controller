"""Preserve R120 and bridge distinct new-only reference pieces in R122."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
src=H/'construct_DI15_extended_ground_handoffs_r120.py';raw=src.read_bytes();s=raw.decode().replace('\r\n','\n')
s=s.replace('r120','r122').replace('R120','R122')
old="extended=max(components,key=lambda q:q.intersection(island).area);shared=line.intersection(ref1.buffer(-.105,quad_segs=128)).intersection(extended.buffer(-.105,quad_segs=128));parts=lines(shared);roles=[];opts=[]"
new="extended=max(components,key=lambda q:q.intersection(island).area);all_new_strip=unary_union(K.pieces(newshape));shared=line.intersection(ref1.buffer(-.105,quad_segs=128)).intersection(all_new_strip.buffer(-.105,quad_segs=128));parts=lines(shared);roles=[];opts=[];ground_bridge_center=legal.buffer(-.155,quad_segs=128)"
assert old in s;s=s.replace(old,new)
old="attach=nearest_points(extended.buffer(-.12,quad_segs=128),pt)[0];direct=LineString([list(attach.coords)[0],at]);branch=Z.bounded_buffer(direct,.175);path=list(direct.coords);search={'method':'exact_direct_full_body'}"
new="""localpieces=[p for p in K.pieces(newshape) if p.covers(station.buffer(.105,quad_segs=128))];assert localpieces;handoff_piece=localpieces[0];link=None;link_search={'method':'same_new_only_reference_piece'}
   if handoff_piece.intersection(extended).area>.004:link=handoff_piece
   else:
    target=handoff_piece.buffer(-.155,quad_segs=128);origin=extended.buffer(-.155,quad_segs=128);bridgeparts=[p for p in K.pieces(ground_bridge_center.intersection(station.buffer(7,quad_segs=128))) if p.intersects(target) and p.intersects(origin)]
    if not bridgeparts:attempt.append({'at_mm':at,'handoff_at_mm':list(station.coords)[0],'reason':'no .30 mm new ground bridge component to central piece'});continue
    start,end=nearest_points(bridgeparts[0].intersection(origin),bridgeparts[0].intersection(target));bridgepoints,link_search=T.route(bridgeparts[0],tuple(start.coords)[0],tuple(end.coords)[0]);bridgepoints=[[round(x,6),round(y,6)] for x,y in bridgepoints];link=Z.bounded_buffer(LineString(bridgepoints),.15).union(handoff_piece)
    if not legal.covers(link) or link.intersection(extended).area<.004:attempt.append({'at_mm':at,'reason':'exact serialized new ground bridge full-body or central contact failed'});continue
   attach=nearest_points(handoff_piece.buffer(-.12,quad_segs=128),pt)[0];direct=LineString([list(attach.coords)[0],at]);branch=Z.bounded_buffer(direct,.175);path=list(direct.coords);search={'method':'exact_direct_full_body'}"""
assert old in s;s=s.replace(old,new)
s=s.replace("q.intersects(extended.buffer(-.18,quad_segs=128))","q.intersects(handoff_piece.buffer(-.18,quad_segs=128))")
s=s.replace("components[0].intersection(extended.buffer(-.18,quad_segs=128))","components[0].intersection(handoff_piece.buffer(-.18,quad_segs=128))")
s=s.replace("if not legal.covers(branch) or branch.intersection(extended).area<.004:continue","if not legal.covers(branch) or branch.intersection(handoff_piece).area<.004:continue\n   branch=branch.union(link);search={'return_branch':search,'new_reference_piece_bridge':link_search};assert branch.intersection(extended).area>.004")
dst=H/'construct_DI15_bridged_ground_handoffs_r122.py';assert not dst.exists();dst.write_text(s,newline='\n');out=H/'prepare-DI15-reference-bridge-r122.json';assert not out.exists();out.write_text(json.dumps({'source_file':str(src),'source_sha256':sha(raw),'derived_file':str(dst),'derived_sha256':sha(dst.read_bytes()),'delta':'Use full physical shared signal locus across separate new ground strip pieces; link selected handoff piece to central piece with exact .30mm covered-chord route. Every old/positive power obstacle and aperture unchanged. No generic union source credit.'},indent=1)+'\n');print(sha(dst.read_bytes()))
