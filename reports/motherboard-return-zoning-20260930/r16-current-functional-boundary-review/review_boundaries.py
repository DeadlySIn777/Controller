"""Read-only native copper crossing review on the combined current freeze."""
from pathlib import Path
import json,sys,hashlib,collections
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT/'tools'))
import pcbnew
from hardware_zone_motherboard_returns import functional_barrier

OUT=Path(__file__).resolve().parent
BOARD=ROOT/'reports/motherboard-bypass-owners-20260930/usb-bulk-local-r05/motherboard-local-capacitors-candidate.kicad_pcb'
MAP=ROOT/'reports/motherboard-return-zoning-20260930/r15-combined-current-domain-map/domain-map.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
mapping=json.loads(MAP.read_text(encoding='utf-8'))
assert mapping['input_sha256'][str(BOARD)]==sha(BOARD)
b=pcbnew.LoadBoard(str(BOARD))
domains={p['net']:p['domain'] for p in mapping['pads']}
tracks=list(b.GetTracks());pads=[(fp.GetReference(),p)for fp in b.GetFootprints()for p in fp.Pads()if p.GetNumber() and p.GetLayerSet().CuStack()]
rows=[]
for r in mapping['barriers']:
 band=functional_barrier(r)
 if not band.OutlineCount():continue
 box=band.BBox();cu=[];lands=[]
 for t in tracks:
  if box.Intersects(t.GetBoundingBox()) and band.Collide(t.GetEffectiveShape()):
   cu.append(dict(uuid=t.m_Uuid.AsString(),net=t.GetNetname(),domain=domains.get(t.GetNetname()),
    type=t.GetClass(),position_mm=[pcbnew.ToMM(v)for v in t.GetPosition()],layer=b.GetLayerName(t.GetLayer())))
 for ref,p in pads:
  if box.Intersects(p.GetBoundingBox()) and any(band.Collide(p.GetEffectiveShape(layer))for layer in p.GetLayerSet().CuStack()):
   lands.append(dict(reference=ref,pin=p.GetNumber(),uuid=p.m_Uuid.AsString(),net=p.GetNetname(),domain=domains.get(p.GetNetname())))
 rows.append(dict(reference=r['reference'],mpn=r['mpn'],side_domains=r['side_domains'],
  functional_strip_width_mm=.6,native_copper_crossings=cu,native_pad_crossings=lands))
review=dict(schema_version=1,input_sha256={str(BOARD):sha(BOARD),str(MAP):sha(MAP),str(Path(__file__)):sha(Path(__file__))},
 no_source_or_pcb_mutation=True,board_track_via_count=len(tracks),grounded_domain_barriers_reviewed=len(rows),
 native_copper_crossing_count=sum(len(r['native_copper_crossings'])for r in rows),
 native_pad_crossing_count=sum(len(r['native_pad_crossings'])for r in rows),barriers=rows,
 width_is_provisional_selv_functional_separation_not_certified_package_isolation_rating=True,
 manufacturer_specific_raw_secondary_emi_exclusions_not_replaced_by_this_strip=True,
 planes_not_generated=True,manufacturing_ready=False)
(OUT/'review.json').write_text(json.dumps(review,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in review.items()if k in ['grounded_domain_barriers_reviewed','native_copper_crossing_count','native_pad_crossing_count','board_track_via_count']}))
