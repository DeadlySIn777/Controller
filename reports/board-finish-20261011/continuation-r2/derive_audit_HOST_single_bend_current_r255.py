"""Fresh new bend audit; exact unchanged field graphs may be rebound."""
import hashlib,json,pickle,runpy
from pathlib import Path
H=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
source=H/'audit_U10003_HOST_joint_actual_fresh_r248.py';code=source.read_text();mp=H/'U10003-HOST-field-joint-current-exact-raw-precision-bound-r253/model.pkl';assert sha(mp)=='765ce30b24ed3109b7c938f964775690a99f08504c464313bcf712b078421440'
code=code.replace('refs-r248','refs-r255').replace('bound-r247','bound-r253').replace('diagnostic-r246','diagnostic-r252').replace('9b5ce5fcc6fcf741f73ba48cd15ab396a022115ba7110ee3d4c7fc27459cbf86',sha(mp)).replace('R248','R255')
needle="ns={**globals(),**locals(),'O':OUT};exec";assert code.count(needle)==1;code=code.replace(needle,"ns={**globals(),**locals(),'O':OUT,'nt':nt+[oldt['06f5b2a7-dc39-4a5d-9309-5badd13a2347']]};exec")
needle="contexts=[K.hole_context(x)for x in(before,after)];groups={};contacts=[];direct=[];sources=[]";assert code.count(needle)==1
addition="""
 cachemodel=H/'U10003-HOST-field-joint-current-exact-raw-precision-bound-r247/model.pkl';assert sha(cachemodel)=='9b5ce5fcc6fcf741f73ba48cd15ab396a022115ba7110ee3d4c7fc27459cbf86';cached=pickle.loads(cachemodel.read_bytes())[4]
 cachefile=H/'U10003-HOST-joint-independent-actual-source-contacts-oldrefs-r248/fresh-actual-drilled-affected-groups.pkl';assert sha(cachefile)=='642a32fe670eb21b4675a3d898a1ee56e6afb73e6921b16a43804f5a4f5edfc1';cache=pickle.loads(cachefile.read_bytes());reuse={FG,FLT}
 assert after['vias']==cached['vias'] and after['pads']==cached['pads']
 for net in reuse:
  for kind in('tracks','vias','pads','zones'):assert [x for x in after[kind]if L.norm(x['net'])==net]==[x for x in cached[kind]if L.norm(x['net'])==net],(net,kind)
 put(OUT/'exact-unchanged-field-graph-cache-binding.json',{'exact_R248_source_model_SHA256':sha(cachemodel),'exact_fresh_R248_groups_SHA256':sha(cachefile),'new_current_SHA256':sha(MP),'reused_nets':sorted(reuse),'all_net_physical_records_and_ALL_drills_exact':True,'other_three_nets_rebuilt_fresh':True})
"""
code=code.replace(needle,needle+addition)
needle="_,old=K.physical(before,net,contexts[0]);_,new=K.physical(after,net,contexts[1]);groups[net]=(old,new);";assert code.count(needle)==1
code=code.replace(needle,"\n  if net in reuse:old,new=cache[net]\n  else:\n   _,old=K.physical(before,net,contexts[0]);_,new=K.physical(after,net,contexts[1])\n  groups[net]=(old,new);")
needle="oldmetal={};newmetal=collections.defaultdict(list)";assert code.count(needle)==1;code=code.replace(needle,needle+"\n   if oldfill.is_empty:continue")
target=H/'audit_U10003_HOST_single_bend_actual_fresh_r255.py';assert not target.exists();compile(code,str(target),'exec');target.write_text(code)
der=H/'HOST-r253-independent-current-auditor-derivation-r255.json';assert not der.exists();der.write_text(json.dumps({'source_SHA256':sha(source),'derived_SHA256':sha(target),'before_empty_fill_excluded_from_actual_contact_obligation':True,'prior_R248_1750_empty_fill_false_rows_retained':True,'restored_original_CLOCK_now_geometry_checked':True,'exact_unchanged_field_graph_cache_rebinding_requires_net_record_and_ALL_drill_identity':True,'native_or_current_acceptance':False},indent=1)+'\n');runpy.run_path(str(target),run_name='__main__')
