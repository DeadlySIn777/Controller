"""Replay named q053 wedges and two literal raw-gain-controlled fill intersections."""
from pathlib import Path
H=Path(__file__).resolve().parent.parent
p=H/'sbc-power/CM79-exact-R333-larger-power-port-local-q053-sparse-current-diagnostic-original-vertex-splice-r346/exact-expanded-sparse-constructor.py'
s=p.read_text(encoding='utf-8').replace('r346','r350').replace('R346','R350')
needle='inherited_outside=[];filled=[];out=[];affected='
assert needle in s
replacement="""fillSpliceDir=H/'sbc-power/CM79-original-IO3-record47-only-two-raw-gain-controlling-intersection-splice-proposal-r349';assert sha(fillSpliceDir/'receipt.json')=='e15c41e4cfb28543c575827b1ba80f0f6b89e3c58b73a3369a0843beb78e2587';fillSplice=json.loads((fillSpliceDir/'receipt.json').read_text());assert fillSplice['literal_no_gain']['empty']and fillSplice['outside_original_declared_corridor']['empty'];fillWedges=[zero(__import__('shapely',fromlist=['from_wkb']).from_wkb(Path(w['file']).read_bytes()))for row in fillSplice['rows']for w in row['exact_two_incident_wedges']];assert all(sha(w['file'])==w['sha256']for row in fillSplice['rows']for w in row['exact_two_incident_wedges']);originalSubtract=IM.subtract
 def exactScopedSubtract(rs,cuts,folder,key):
  if key!='54921f4b-0308-4821-9549-ff9360bf05ca-In2.Cu-new-CM-local-negative':return originalSubtract(rs,cuts,folder,key)
  cut=zero(unary_union(cuts));assert dig(cut)==sha(H/'sbc-power/CM79-R346-original-IO3-record47-exact-raw-gain-controlling-edge-attribution-r347/normal-new-primitives-only-cutter.wkb');out=[];rows=[];ps=L.poly(rs)
  for i,(rec,p)in enumerate(zip(rs,ps)):
   if i!=47:
    rr,led=originalSubtract([rec],cuts,folder,key+'-other-original-'+str(i));out+=rr
    for row in led['per_original_record_operations']:row['record']=i;rows.append(row)
    continue
   p=zero(p);assert dig(p)==fillSplice['before_WKB_sha256'];raw=p.difference(cut);moves={tuple(row['new_raw_cut_intersection']):tuple(row['new_native_inward_intersection'])for row in fillSplice['rows']}
   def rc(r):return[moves.get(tuple(v),tuple(v))for v in r.coords]
   pp=list(raw.geoms)if raw.geom_type=='MultiPolygon'else[raw];newpolys=[Polygon(rc(v.exterior),[rc(r)for r in v.interiors])for v in pp];rebuilt=MultiPolygon(newpolys)if len(newpolys)>1 else newpolys[0];assert rebuilt.is_valid;serialized=IM.records(rebuilt);actual=zero(unary_union(L.poly(serialized)));assert dig(actual)==fillSplice['after']['sha256'];assert actual.difference(p).is_empty;removed=p.difference(actual);explicitScope=zero(Z.bounded_buffer(unary_union([cut,*fillWedges]),.0002));assert removed.difference(explicitScope).is_empty,('native original record extra loss outside exact named intersection wedges',i);out+=serialized;af=save(key+'-47-exact-new-intersection-replay',actual);xf=save(key+'-47-exact-new-intersection-negative-wedges',removed.difference(cut));rows.append({'record':47,'before_WKB_sha256':dig(p),'after_WKB_sha256':dig(actual),'actual_final_record_file':af['file'],'strict_no_reclaimed_Cu':True,'reserves':[],'only_two_bound_raw_gain_controlled_new_intersection_splice':fillSplice['rows'],'exact_R349_splice_receipt_sha256':sha(fillSpliceDir/'receipt.json'),'all_other_old_coordinate_tokens_preserved':True,'explicit_additional_negative_file':xf['file'],'explicit_additional_negative_sha256':xf['sha256'],'explicit_additional_negative_area_mm2':xf['area_mm2'],'no_original_coordinate_snap':True})
  old=zero(unary_union(ps));new=zero(unary_union(L.poly(out)));assert new.difference(old).is_empty;return out,{'per_original_record_operations':rows,'before_WKB_sha256':dig(old),'after_WKB_sha256':dig(new),'strict_complete_fill_subset':True,'exact_removed_mm2':old.difference(new).area,'actual_polygonal_piece_count':len(out),'only_two_bound_record47_intersection_splices_no_original_native_definition_change':True}
 IM.subtract=exactScopedSubtract
 inherited_outside=[];filled=[];out=[];affected="""
s=s.replace(needle,replacement)
s=s.replace("'q053_only_new_native_intersection_and_exact_named_controlling_wedge_replay':True","'q053_only_new_native_intersection_and_exact_named_controlling_wedge_replay':True,'native_IO3_record47_only_two_bound_new_intersection_replay_R349':True,'R346_raw_fill_gain_and_scope_FAILURE_retained':True")
EXACT_EXPANDED_SOURCE=s
exec(compile(s,str(__file__),'exec'))
