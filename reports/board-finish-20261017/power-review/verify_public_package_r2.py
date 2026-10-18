"""Independent read-only review of the explicitly authorized public CAD package."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
psutil.Process().cpu_affinity([16,17])
from pathlib import Path
from datetime import datetime,timezone
import hashlib,importlib.util,json,re,zipfile
ROOT=Path(__file__).resolve().parents[3];PKG=ROOT/'tmp/github-controller-public-20261018';OUT=Path(__file__).resolve().parent/'public-package-independent-review-r2';HP=ROOT/'reports/board-finish-20261011/parity-repair/root106/tools/pcbtext.py';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();dig=lambda b:hashlib.sha256(b).hexdigest();sp=importlib.util.spec_from_file_location('pcbtext',HP);H=importlib.util.module_from_spec(sp);sp.loader.exec_module(H)
SENSITIVE=[('private_key',rb'-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----'),('github_token',rb'(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})'),('OpenAI_key',rb'sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{32,}'),('AWS_access_key',rb'AKIA[0-9A-Z]{16}')]
def secrets(name,data):return[{'file':name,'pattern':label,'matches':len(re.findall(pattern,data))}for label,pattern in SENSITIVE if re.search(pattern,data)]
def main():
 assert not OUT.exists();OUT.mkdir();mp=PKG/'MANIFEST.json';mraw=mp.read_bytes();manifest=json.loads(mraw);results=[];fail=[];secret_hits=[];archive_names=[]
 for which,p in manifest['project_provenance'].items():
  folder=PKG/'board'/which;source=ROOT/p['workspace_source'];archive=PKG/'archives'/f'{which}-full-cached-project.zip';z=zipfile.ZipFile(archive);names=z.namelist();archive_names+=names;assert len(names)==len(set(names));assert all(not n.startswith(('/','\\'))and'..'not in Path(n.replace('\\','/')).parts and not re.match(r'^[A-Za-z]:',n)for n in names);boardnames=[n for n in names if n.endswith('/board.kicad_pcb')or n=='board.kicad_pcb'];assert len(boardnames)==1;name=boardnames[0];prefix=name[:-len('board.kicad_pcb')];original=z.read(name);loose=(folder/'board.kicad_pcb').read_bytes();assert dig(original)==p['original_cached_board_SHA256']==sha(source/'board.kicad_pcb');assert dig(loose)==p['editable_cache_free_board_SHA256'];assert len(original)==p['original_cached_board_bytes']and len(loose)==p['editable_cache_free_board_bytes'];cache=re.compile(rb'(?m)\(filled_polygon\b.*?^\t\t\)',re.S);stripped,n=cache.subn(b'',original);assert n>0 and stripped==loose,'Non-cache byte delta or unexpected cache serialization';assert b'(filled_polygon'not in loose
  oh,oc,ot=H.split(original);lh,lc,lt=H.split(loose);assert oh==lh and ot==lt and len(oc)==len(lc);nonzones=0;zones=0
  for a,b in zip(oc,lc):
   assert H.chunk_kind(a)==H.chunk_kind(b)and H.chunk_uuid(a)==H.chunk_uuid(b)
   if H.chunk_kind(a)=='zone':assert cache.sub(b'',a)==b;zones+=1
   else:assert a==b;nonzones+=1
  local_tables=[];libmap={}
  for tab in('fp-lib-table','sym-lib-table'):
   txt=(folder/tab).read_text();uris=re.findall(r'\(uri "([^"]+)"\)',txt);assert uris and all(x.startswith('${KIPRJMOD}/')for x in uris);resolved=[]
   for x in uris:
    q=folder/x.removeprefix('${KIPRJMOD}/');assert q.exists()and q.resolve().is_relative_to(folder.resolve());resolved.append(str(q.relative_to(folder)))
   local_tables.append({'table':tab,'relative_URIs_resolved':len(resolved)})
   if tab=='fp-lib-table':libmap=dict(re.findall(r'\(lib \(name "([^"]+)"\).*?\(uri "\$\{KIPRJMOD\}/([^"]+)"\)',txt))
  fps=set(re.findall(rb'\(footprint "([^"\r\n]+)"',loose));missing=[]
  for f in fps:
   text=f.decode();lib,part=text.split(':',1)
   if lib not in libmap or not(folder/libmap[lib]/(part+'.kicad_mod')).exists():missing.append(text)
  assert not missing,missing
  sheets=[]
  for f in folder.glob('*.kicad_sch'):
   for n in re.findall(r'\(property "Sheetfile" "([^"]+)"',f.read_text()):assert(folder/n).is_file();sheets.append(n)
  for f in folder.rglob('*'):
   if not f.is_file():continue
   rel=f.relative_to(folder).as_posix();expected=p['source_files'].get(rel)
   if rel!='board.kicad_pcb'and expected:assert sha(f)==expected
  for n in names:
   if n.endswith('/'):continue
   data=z.read(n);rel=n[len(prefix):]if n.startswith(prefix)else n;expected=p['source_files'].get(rel)
   if expected:assert dig(data)==expected
   if rel in('board.kicad_pro','board.kicad_dru'):assert data==(folder/rel).read_bytes()==(source/rel).read_bytes()
   secret_hits+=secrets(which+' archive/'+n,data)
  results.append({'project':which,'archive_SHA256':sha(archive),'archive_original_board_SHA256':dig(original),'loose_board_SHA256':dig(loose),'removed_filled_polygon_cache_nodes':len(cache.findall(original)),'all_source_and_noncache_bytes_exact':True,'all_nonzone_chunks_exact':nonzones,'all_source_zone_chunks_exact_after_cache_removal':zones,'all_library_table_paths_project_relative_and_present':local_tables,'unique_board_footprint_ids_with_local_lands':len(fps),'all_referenced_child_schematic_sheets_present':len(sheets),'pro_dru_exact_source_and_archive':True,'zip_entries':len(names)})
 suspicious=[];textfiles=0
 for f in PKG.rglob('*'):
  if not f.is_file():continue
  rel=f.relative_to(PKG).as_posix()
  if re.search(r'(^|/)(\.env(?:\.|$)|\.ssh|\.aws|\.git)(/|$)|(?:id_rsa|id_ed25519|credentials|automation\.toml)|\.(?:pem|key|ini|hal|var|kicad_prl)$',rel,re.I):suspicious.append(rel)
  if f.suffix.lower()!='.zip':secret_hits+=secrets(rel,f.read_bytes());textfiles+=1
 for n in archive_names:
  if re.search(r'(^|/)(\.env(?:\.|$)|\.ssh|\.aws|\.git)(/|$)|(?:id_rsa|id_ed25519|credentials|automation\.toml)|\.(?:pem|key|ini|hal|var|kicad_prl)$',n,re.I):suspicious.append('archive/'+n)
 assert not secret_hits and not suspicious;listed=manifest['files_excluding_this_manifest'];checked=0
 for rel,entry in listed.items():
  p=PKG/rel
  if not p.is_file():fail.append({'missing_manifest_file':rel});continue
  if p.stat().st_size!=entry['bytes']or sha(p)!=entry['SHA256']:fail.append({'manifest_hash_mismatch':rel})
  checked+=1
 # Root may add reports and regenerate MANIFEST while this read-only review runs.
 r={'utc':datetime.now(timezone.utc).isoformat(),'status':'READ_ONLY_PUBLIC_SOURCE_ARCHIVE_PORTABILITY_AND_SECRET_SCREEN_PASS'if not fail else'PUBLIC_PACKAGE_MANIFEST_SNAPSHOT_CHANGED_OR_FAILED','manifest_snapshot_SHA256':dig(mraw),'manifest_still_same_at_end':mp.read_bytes()==mraw,'manifest_snapshot_files_checked':checked,'manifest_snapshot_failures':fail,'projects':results,'high_confidence_credential_pattern_hits':secret_hits,'private_machine_or_account_file_paths':suspicious,'loose_text_files_scanned':textfiles,'archive_entries_scanned':len(archive_names),'absolute_workspace_paths_in_selected_evidence':'Present as provenance; no credentials or runtime machine configurations observed. Not redacted by this read-only review.','package_not_modified':True,'native_readback':'Separate bounded load-only receipt will be linked; no Fill/Save.','full_native_DRC_current_or_manufacturing_qualification_claimed':False,'manufacturing_ready':False};(OUT/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'status':r['status'],'projects':len(results),'manifest_files_checked':checked,'credential_hits':len(secret_hits),'private_file_paths':len(suspicious)}),flush=True)
if __name__=='__main__':main()
