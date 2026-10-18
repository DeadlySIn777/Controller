"""Conservatively retain the quiet branch's first junction track as well."""
from pathlib import Path
import ast,hashlib,json
P=Path(__file__).resolve().parent;old=P/'review_remaining_power_shadow_source_types_r202.py';s=old.read_text()
s=s.replace('remaining84-power-shadow-source-and-quiet-branch-review-r202','remaining84-power-shadow-quiet-boundary-review-r203').replace('R202_COMPLETE','R203_COMPLETE')
needle="""   if k not in seed and (len(graph[k])>=3 or(k[0]=='pad' and k not in seed)):
    stops.append({'node_kind':k[0],'UUID':k[1],'potential_neighbor_count':len(graph[k]),'stop_at_possible_distribution_junction':True});continue
   if k[0]=='track':walk.append(k[1]);quiet_traces[k[1]].append({'ref':role['ref'],'pin':role['pin'],'role':role['role']})"""
replace="""   if k[0]=='track':walk.append(k[1]);quiet_traces[k[1]].append({'ref':role['ref'],'pin':role['pin'],'role':role['role'],'includes_first_distribution_junction_track_conservatively':True})
   if k not in seed and (len(graph[k])>=3 or(k[0]=='pad' and k not in seed)):
    stops.append({'node_kind':k[0],'UUID':k[1],'potential_neighbor_count':len(graph[k]),'stop_at_possible_distribution_junction':True,'boundary_track_if_any_kept_hard':k[0]=='track'});continue"""
assert needle in s;s=s.replace(needle,replace)
ast.parse(s)
(P/'power-quiet-boundary-conservative-r203-derivation.json').write_text(json.dumps({'original_R202_script_sha256':hashlib.sha256(old.read_bytes()).hexdigest(),'R202_first_junction_track_stop_preserved':'R202 has no exemptions or geometry changes; R203 additionally nominates the first junction track as quiet-hard conservatively.','derived_source_sha256':hashlib.sha256(s.encode()).hexdigest(),'no_legacy_checker_change_or_waiver':True},indent=1)+'\n')
exec(compile(s,str(old),'exec'))
