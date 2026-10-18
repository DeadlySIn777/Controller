"""Differential check: indexing may never omit an exhaustive geometric hit."""
import json,random,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from hardware_route_local_signals import GeometryIndex
from hardware_route_logic_return import segment_hits_box
rng=random.Random(927461)
boxes=[(0,0,.35,.35),(4.99,4.99,5.01,5.01),(-5,-5,0,0)]
for _ in range(500):
    x,y=rng.uniform(-10,470),rng.uniform(-10,350)
    boxes.append((x,y,x+rng.uniform(.01,8),y+rng.uniform(.01,8)))
index=GeometryIndex()
for i,box in enumerate(boxes):index.add(i,box)
for _ in range(2000):
    s=(rng.uniform(-10,470),rng.uniform(-10,350));e=(rng.uniform(-10,470),rng.uniform(-10,350));margin=rng.choice((0,.251,.401,.451))
    exhaustive={i for i,box in enumerate(boxes) if segment_hits_box(s,e,box,margin)}
    indexed=set(index.candidates(s,e,margin))
    assert exhaustive<=indexed, (s,e,margin,sorted(exhaustive-indexed))
    assert len(list(index.candidates(s,e,margin)))==len(indexed)
print(json.dumps({'randomized_segments':2000,'obstacles':len(boxes),'false_negative_collisions':0,'deterministic_seed':927461,'native_DRC_still_required':True}))
