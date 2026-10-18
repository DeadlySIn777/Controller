"""Independent native-flag DSN keepout scopes; does not mutate a DSN or CAD source."""
from pathlib import Path
import json,re,sys,hashlib
ROOT=Path(__file__).resolve().parents[3];BASE=ROOT/'reports/board-finish-20261017'
sys.path.insert(0,str(ROOT/'tools'))
from hardware_build_assembly import parse,child,children,value,q
RULES=BASE/'routing/parent-audit-review/read-only-native-R299-rule-areas-r2/exact-native-rule-areas.json'
DRU=BASE/'combined-route-stage-r4/native/board.kicad_dru'

def polygon(ring,layer):
 return ['polygon',layer,'0',*[format(v/1000,'.3f').rstrip('0').rstrip('.')or'0'for x,y in ring for v in(x,-y)]]

def build_manifest():
 rows=json.loads(RULES.read_text());flag_scopes=[];flag_owners=[];conditional=[];allow=[]
 for r in rows:
  kind='keepout'if r['GetDoNotAllowTracks']else'via_keepout'if r['GetDoNotAllowVias']else None
  if kind:
   assert not r['GetDoNotAllowTracks']or r['GetDoNotAllowVias'],'Track-only prohibition needs explicit unsupported-case review'
   for layer in r['layers']:
    for i,p in enumerate(r['outlines']):
     flag_scopes.append([kind,q(r['UUID']+':'+str(i)),polygon(p['outer_IU'],layer),*([['window',polygon(h,layer)]for h in p['holes_IU']])])
     flag_owners.append({'UUID':r['UUID'],'name':r['name'],'owner':r['owner'],'layer':layer,'kind':kind,'outline_index':i})
  else:allow.append({'UUID':r['UUID'],'name':r['name'],'layers':r['layers']})
 # DRU disallow conditions have literal area/name and exempt own component/nets.
 for condition in re.findall(r'\(condition "([^"\n]*)"\)\s*\(constraint disallow track via zone\)',DRU.read_text()):
  names=re.findall(r"A\.intersectsArea\('([^']+)'\)",condition)
  for name in names:
   hits=[r for r in rows if r['name']==name];assert len(hits)==1
   r=hits[0];scopes=[]
   for layer in r['layers']:
    for i,p in enumerate(r['outlines']):scopes.append(['keepout',q('CONSERVATIVE_DONOR_ONLY:'+r['UUID']+':'+str(i)),polygon(p['outer_IU'],layer),*([['window',polygon(h,layer)]for h in p['holes_IU']])])
   conditional.append({'name':name,'UUID':r['UUID'],'condition':condition,'exempt_raw_net_names':re.findall(r"A\.NetName != '([^']+)'",condition),'exempt_footprints':re.findall(r"!A\.memberOfFootprint\('([^']+)'\)",condition),'actual_outlines':r['outlines'],'layers':r['layers'],'conservative_all_net_scopes':scopes,'conservative_all_net_warning':'DSN keepout parser has no own-net exemption. These extra scopes restrict otherwise lawful own-net routes; do not label them a faithful translation or relax native DRU afterwards.'})
 return {'status':'NATIVE_FLAG_SCOPES_AND_SEPARATE_CONDITIONAL_DRU_MANIFEST_NOT_ADOPTED','input_SHA256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest()for p in(RULES,DRU)},'native_rule_area_count':len(rows),'native_flag_scopes':flag_scopes,'native_flag_scope_owners':flag_owners,'native_flag_allowed_areas':allow,'conditional_DRU_areas':conditional,'replacement_instruction':'Replace raw structure keepout/via_keepout scopes only after checking separately exported image mechanical obstacles. Add native_flag_scopes; hold conditional_DRU_areas explicitly. Never remove pads, holes, library geometry or placement obstacles. Preserve per-layer polygons and holes; do not assume rectangular bounds.','source_modified':False,'router_jobs':0}

if __name__=='__main__':
 out=BASE/'release-review/global-routability-review/native-DSN-keepout-manifest-r2.json';assert not out.exists();d=build_manifest();out.write_text(json.dumps(d,indent=1)+'\n');print(json.dumps({'output':str(out),'native_flag_scopes':len(d['native_flag_scopes']),'native_BOARD_flag_scopes':sum(r['owner']['kind']=='board'for r in d['native_flag_scope_owners']),'DRU_conditional_areas':len(d['conditional_DRU_areas']),'areas_with_no_native_track_or_via_prohibition':len(d['native_flag_allowed_areas'])}))
