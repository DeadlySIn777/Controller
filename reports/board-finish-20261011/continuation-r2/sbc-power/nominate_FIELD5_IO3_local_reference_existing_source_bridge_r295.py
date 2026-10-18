"""Bound actual reference erosion to each declared local routing window."""
from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'nominate_FIELD5_IO3_no_hole_existing_source_bridge_r293.py').read_text()
s=s.replace('FIELD5-R393-IO3-no-hole-actual-source-strict-reference-bridge-r293','FIELD5-R393-IO3-no-hole-local-actual-reference-bridge-r295')
s=s.replace("rawfree=free(layer,width,clip);f=rawfree.intersection(refs[layer].buffer(-width/2-.000004,quad_segs=128));faces=[]", "print('R295_ATTEMPT',radius,width,layer,flush=True);rawfree=free(layer,width,clip);localref=refs[layer].intersection(clip.buffer(1));f=rawfree.intersection(localref.buffer(-width/2-.000004,quad_segs=128));faces=[]")
s=s.replace('R293','R295')
exec(compile(s,str(__file__),'exec'))
