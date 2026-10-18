from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;p=H/'construct_AO1_old_COM_barrel_same_profile_escape_move_r688.py';s=p.read_text()
replacements=[('exact-profile-controlled-escape-r688','exact-profile-controlled-detour-escape-r690'),('R688_','R690_'),("Bfree=win.difference(unary_union(stub_obs));pad=", "Bfree=win.difference(unary_union(stub_obs));Bfaces=[s for s in parts(Bfree)if s.covers(Point(stub['a']))];Bconnected=unary_union(Bfaces);pad="),("if not Bfree.covers(line):continue","if not Bconnected.covers(pt):continue"),("for pos in opts:\n   face=", "for pos in opts:\n   bface=next((s for s in Bfaces if s.covers(pt)),None)\n   if bface is None:continue\n   bpath,bsearch=T.route(bface,tuple(stub['a']),tuple(at));bpath=[[round(x,6),round(y,6)]for x,y in bpath]\n   if len(bpath)<2 or not bface.covers(LineString(bpath)):continue\n   face="),("'entry_route_search':search","'entry_route_search':search,'owned_B_stub_detour_mm':bpath,'owned_B_stub_search':bsearch")]
for a,b in replacements:
 assert a in s,a;s=s.replace(a,b)
start=s.index("  at=selected['old_COM_move_mm'];text=");end=s.index('\n packet=OUT/',start)
new="""  at=selected['old_COM_move_mm'];text=' '.join(format(x,'.6f').rstrip('0').rstrip('.')for x in at).encode();oldat=b'376.772997 127.45';assert raw[UID].count(b'(at '+oldat+b')')==1;chunks={UID:raw[UID].replace(b'(at '+oldat+b')',b'(at '+text+b')')};identity=K.A.N.SourceNets(sp.read_bytes());newtracks=[]
  for ix,(a,b1)in enumerate(zip(selected['owned_B_stub_detour_mm'],selected['owned_B_stub_detour_mm'][1:])):
   tid,ch=identity.serial_segment(COM,'B.Cu',a,b1,.2)
   if ix==0:ch=ch.replace(tid.encode(),STUB.encode());tid=STUB
   chunks[tid]=ch;newtracks.append({'uuid':tid,'net':identity.raw(COM),'layer':'B.Cu','a':a,'b':b1,'w':.2})
  identity.assert_chunks(chunks);newvia={**v,'x':at[0],'y':at[1]};packetdata.update({'original_deletes':{UID:raw[UID],STUB:raw[STUB]},'new_chunks':chunks,'tracks':newtracks,'vias':[newvia]});after={**before,'tracks':[t for t in before['tracks']if t['uuid']!=STUB]+newtracks,'vias':[newvia if q['uuid']==UID else q for q in before['vias']]};ng=K.physical(after,COM,K.hole_context(after))[1];newroot=K.root(ng,'U14619','7');oldkeys=K.keys(root);newkeys=K.keys(newroot);lost=sorted(oldkeys-newkeys);groupbad=K.contact_losses(bg,ng)[1];assert not lost and not groupbad,(lost,groupbad);packetdata['prospective_old_COM_source_keys_lost']=lost;packetdata['prospective_old_COM_groups_lost']=groupbad;packetdata['prospective_source_group_keys']=len(newkeys)"""
s=s[:start]+new+s[end:]
marker=" trials=[];selected=None"
assert s.count(marker)==1
s=s.replace(marker," (OUT/'bounded-source-COM-SG-stub-axis-regions.pkl').write_bytes(pickle.dumps({'COMfree':COMfree,'SGfree':SGfree,'Ffree':Ffree,'Bfree':Bfree,'Bconnected':Bconnected,'SGsites':SGsites,'SOURCEcenters':sourcecenters},protocol=5))\n"+marker)
s=s.replace("'same_stub_width_layer_fixed_other_endpoint_mm':", "'same_stub_width_layer_fixed_other_endpoint_owned_detour_mm':")
out=H/'construct_AO1_old_COM_barrel_owned_stub_detour_escape_r690.generated.py';assert not out.exists();out.write_text(s)
(H/'derive-AO1-owned-COM-barrel-detour-r690.json').write_text(json.dumps({'source':str(p.resolve()),'source_SHA256':hashlib.sha256(p.read_bytes()).hexdigest(),'generated':str(out.resolve()),'generated_SHA256':hashlib.sha256(out.read_bytes()).hexdigest(),'changes':'use only original stub’s free source-connected B face for finite detour; retain .20 width, fixed original pad endpoint, same old stub UUID on first segment; additional owned segments NEW'},indent=1)+'\n')
