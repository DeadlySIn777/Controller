"""Exact C92 placement correction; preserve frozen failed pose proof."""
import copy,json
from inventory import HERE,BOARD,sha
from contact_layout import O,S
from verify_source import parse,child,children,atom
from stage_source import top_spans
OUT=HERE/'board-delta-r4-c92-pose'
def main():
 assert not OUT.exists();OUT.mkdir();oldpath=HERE/'board-delta-r3/C11092.footprint-chunk';text=oldpath.read_text(encoding='utf-8');before=parse(text)
 original=O.C.inventory(BOARD.read_bytes())[3];clone=next(c for c in original.values() if O.C.pcbtext.chunk_kind(c)=='footprint' and S.overlay_tool.base.ref_of(c)=='C11076');cl=parse(clone.decode('utf-8'));clone_ref=next(p for p in children(cl,'property') if p[1]=='Reference');old_ref=next(p for p in children(before,'property') if p[1]=='Reference')
 assert child(before,'at')==['at','42.356','174'];assert child(old_ref,'at')==['at','80.5','210.5','0'];expected=copy.deepcopy(before);child(expected,'at')[1:]=['80.5','210.5'];ref=next(p for p in children(expected,'property') if p[1]=='Reference');child(ref,'at')[:]=copy.deepcopy(child(clone_ref,'at'))
 changes=[]
 for a,b in reversed(top_spans(text)):
  n=parse(text[a:b]);new=None
  if n[0]=='at':assert n==child(before,'at');new='(at 80.5 210.5)'
  if n[0]=='property' and n[1]=='Reference':
   oldat=child(n,'at');newat=child(clone_ref,'at');chunk=text[a:b];oldstr='(at '+' '.join(oldat[1:])+')';newstr='(at '+' '.join(newat[1:])+')';assert chunk.count(oldstr)==1;new=chunk.replace(oldstr,newstr)
  if new is not None:changes.append({'kind':n[0],'before':text[a:b],'after':new});text=text[:a]+new+text[b:]
 assert parse(text)==expected;out=OUT/'C11092.footprint-chunk';out.write_text(text,encoding='utf-8',newline='');assert len(changes)==2
 r={'verdict':'PASS_EXACT_C92_ROOT_POSE_AND_REFERENCE_ANCHOR_CORRECTION','before_chunk_path':str(oldpath.resolve()),'before_sha256':sha(oldpath),'corrected_chunk_path':str(out.resolve()),'corrected_chunk_sha256':sha(out),'footprint_uuid':atom(expected,'uuid'),'exact_root_pose_mm':[80.5,210.5,0],'exact_two_field_changes':changes,'all_pad_UUID_numbers_nets_local_geometries_paths_MPN_Value_and_other_objects_exact':True,'source_export_sha256':sha(HERE/'combined-power-source-r3-hierarchy/source-export/fresh.net'),'source_electrical_delta':0,'native_jobs':0,'whole_board_written':False,'old_C11076_pose_and_footprint_unmodified':True,'cause':'Unanchored first-three-coordinate at substitution skipped root omitted-zero rotation and mutated the Reference local at instead. Correcting exactly both affected fields.'}
 (OUT/'receipt.json').write_text(json.dumps(r,indent=1)+'\n',encoding='utf-8');print(json.dumps(r))
if __name__=='__main__':main()
