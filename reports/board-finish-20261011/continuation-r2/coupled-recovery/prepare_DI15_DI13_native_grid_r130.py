"""Native-IU new-zone quantization with inward margin; preserve R128 failure."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent
def sha(b):return hashlib.sha256(b).hexdigest()
src=H/'construct_DI15_DI13_coupled_reference_r128.py';raw=src.read_bytes();s=raw.decode().replace('\r\n','\n').replace('r128','r130').replace('R128','R130')
s=s.replace('from shapely.geometry import Point,LineString,box','from shapely import set_precision\nfrom shapely.geometry import Point,LineString,box')
s=s.replace('island=island.intersection(legal);new_only_outward_trim=',"island=set_precision(island.intersection(legal).buffer(-.000010,quad_segs=64),Z.GRID);new_only_outward_trim=")
s=s.replace("'original_native_or_power_Cu_trimmed':0","'original_native_or_power_Cu_trimmed':0,'explicit_new_only_inward_margin_mm':.000010,'native_serialization_grid_mm':Z.GRID,'new_only_quantization_added_mm2':island.difference(original_new_island).area,'final_new_shape_area_mm2':island.area,'actual_remaining_outside_legal_mm2':island.difference(legal).area,'strict_legal_covers_new_shape':legal.covers(island)")
s=s.replace("branch=Z.bounded_buffer(LineString([list(attach.coords)[0],pos]),.175)","branch=Z.bounded_buffer(LineString([list(attach.coords)[0],pos]),.15)").replace("'branch_width_mm':.35","'branch_width_mm':.30")
dst=H/'construct_DI15_DI13_coupled_reference_r130.py';assert not dst.exists();dst.write_text(s,newline='\n');out=H/'prepare-DI15-DI13-native-grid-r130.json';assert not out.exists();out.write_text(json.dumps({'source_file':str(src),'source_sha256':sha(raw),'derived_file':str(dst),'derived_sha256':sha(dst.read_bytes()),'delta':'New-only reference island explicitly insets10nm then quantizes1nm native IU, all shape deltas ledgered, no original/power edits. Ground branches .30mm over .25mm minimum profile. Strict source/body/contact/legal gates unchanged; no tolerance or waiver.'},indent=1)+'\n');print(sha(dst.read_bytes()))
