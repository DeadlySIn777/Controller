"""Literal scoped reference qualification; never promotes a whole-board pass.

Every selected native filled component is copied exactly from the complete
resource report and requires a real source-anchor witness. The complete report,
including unrelated unanchored components, stays immutable and linked.
"""
from pathlib import Path
import copy,json,hashlib

ANCHORS=('actual_numbered_through_pad_anchors',
 'actual_source_connected_through_stitch_anchors',
 'actual_source_connected_inner_return_track_anchors')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf8'))
def anchor_check(row):
 if row.get('passed')is not True:raise ValueError('Scoped native reference piece is unanchored')
 found=False
 for name in ANCHORS:
  for a in row.get(name,[]):
   if name==ANCHORS[0]:
    valid=all(a.get(k)for k in ('reference','pin','pad_uuid'))
   else:
    valid=bool(a.get('uuid'))and any(all(p.get(k)for k in ('reference','pin','pad_uuid'))for p in a.get('source_pad_anchors',[]))
   if not valid:raise ValueError('Scoped anchor lacks exact physical source witness')
   found=True
 if not found:raise ValueError('Scoped native reference piece has no physical anchor')
def qualify(full_report,source_map,return_nets):
 full_report,source_map=map(lambda p:Path(p).resolve(),(full_report,source_map))
 full=read(full_report);nets=sorted(set(return_nets));mapping=read(source_map)
 if not nets or not full.get('board_sha256')or full.get('source_map_sha256')!=sha(source_map):
  raise ValueError('Exact full native resource report/source map required')
 if full.get('exact_source_pad_inventory_checked')!=len(mapping.get('pads',[]))or not mapping.get('pads'):
  raise ValueError('Complete actual source pad inventory was not checked')
 rows=[r for r in full.get('filled_components',[])if r.get('net')in nets]
 for n in nets:
  if {r.get('reference_layer')for r in rows if r.get('net')==n}!={'In1.Cu','In4.Cu'}:
   raise ValueError('Both actual per-side references required for selected domain: '+n)
 for r in rows:anchor_check(r)
 return dict(schema_version=1,type='literal_scoped_native_reference_qualification',passed=True,
  scope_only=True,whole_board_reference_qualification=False,manufacturing_ready=False,
  board_sha256=full['board_sha256'],qualified_return_nets=nets,
  reference_layers={'F.Cu':'In1.Cu','B.Cu':'In4.Cu'},
  full_plane_review=dict(path=str(full_report),sha256=sha(full_report),passed=full.get('passed')),
  source_map=dict(path=str(source_map),sha256=sha(source_map)),
  complete_native_unanchored_components_retained=len(full.get('unanchored_components',[])),
  filled_components=copy.deepcopy(rows))
def check(scoped,manifest):
 if scoped.get('type')!='literal_scoped_native_reference_qualification'or scoped.get('scope_only')is not True:
  raise ValueError('Explicit literal scoped reference qualification required')
 if scoped.get('whole_board_reference_qualification')is not False or scoped.get('manufacturing_ready')is not False:
  raise ValueError('Scoped prototype work cannot claim whole-board qualification')
 full=scoped.get('full_plane_review',{});mapping=scoped.get('source_map',{})
 for entry in (full,mapping):
  if not entry.get('path')or sha(entry['path'])!=entry.get('sha256'):
   raise ValueError('Frozen complete plane/source-map evidence changed')
 expected=qualify(full['path'],mapping['path'],scoped.get('qualified_return_nets',[]))
 if scoped!=expected:raise ValueError('Scoped qualification differs from actual complete native report')
 if scoped['board_sha256']!=manifest.get('board_sha256'):
  raise ValueError('Scoped reference qualification belongs to a different native board')
 nets={r['return_net']for r in manifest.get('nets',{}).values()}
 if not nets or not nets<=set(scoped['qualified_return_nets']):
  raise ValueError('Selected critical return domain is not actually qualified')
 if any(r.get('reference_layers')!=scoped['reference_layers']for r in manifest['nets'].values()):
  raise ValueError('Actual route side/reference mapping is outside scoped qualification')
 return dict(scoped_return_nets=sorted(nets),whole_board_reference_qualification=False,
  full_plane_review_sha256=full['sha256'],source_map_sha256=mapping['sha256'])
