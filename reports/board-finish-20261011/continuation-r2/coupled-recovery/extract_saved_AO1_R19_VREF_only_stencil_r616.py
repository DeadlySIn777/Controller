"""Extract four saved VREF add chunks for root's fresh current audit only.

The coupled R19 audit remains OPEN. Its monitor correction, source cuts,
fill retreat and invalid .873212 SDI pair are not silently replayed.
"""
from pathlib import Path
import json,hashlib,re,math
H=Path(__file__).resolve().parent;OUT=H/'AO1-R19-VREF-only-four-chunk-current-requalification-handoff-r616';assert not OUT.exists();OUT.mkdir()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
src=H/'ao1-reference-coupled-r19.json';ap=H/'ao1-reference-coupled-r19-independent-native-bound-r19.json';nr=H/'ao1-native-com-reference-independent-r4.json';r=json.loads(src.read_bytes());a=json.loads(ap.read_bytes())
assert sha(src)=='203f9f36ec4979ba2715139a16058a38f40f4d9fdcb4ec9f95fad07c4c6526b7';assert sha(ap)=='f664d851a31e2ce65a2f0bd979a8d851bd67c3efd3d20099c4cb3f210a7bb3bd'
uids=['85c9e9fa-8501-5e8b-b7c6-41abc60300bb','da16ac1d-640e-5454-a300-69a8f8f12c45','d0f11d7f-bfce-5400-8455-c5864e23647e','c35ca6b4-426d-5180-9a66-cc78537275f6'];chunks={u:r['exact_new_chunks'][u]for u in uids};paths={}
for uid,ch in chunks.items():
 f=OUT/(uid+('.via.chunk'if '(via' in ch else'.segment.chunk'));f.write_bytes(ch.encode());paths[uid]={'file':str(f.resolve()),'SHA256':sha(f)}
pair=next(p for p in a['paired_returns']if p['signal_net']=='/motherboard_analog_output/AO1_VREF');assert pair['choices'][0]['uuid']==uids[3]and math.isclose(pair['choices'][0]['distance_mm'],.9178779875342458)
packet={'schema':'SAVED_AO1_VREF_ADD_ONLY_STENCIL_CURRENT_REQUALIFICATION_REQUIRED','exact_new_chunks':paths,'original_deletes':{},'old_coupled_recipe_deletion_UUIDs_DIAGNOSTIC_ONLY':r['removed_owned_items'],'old_coupled_exact_removed_chunks_DIAGNOSTIC_ONLY':r['exact_removed_chunks'],'saved_VREF_return_pair':pair,'source_root_selector':{'ref':'U14619','pin':'7','UUID':'ba8a438e-2bdd-4f29-9cf0-fe1f66d3471e','net':'/motherboard_analog_output/AO1_COM','saved_at_mm':[342.438,122.55]},'signal_endpoints':{'B':'C14643.1','F':'U14626.9','saved_at_mm':[375.498,129]},'explicit_dependencies_open':['R19 was coupled to old AO1_MON_12V correction; recheck all current MON geometry rather than replaying its removals','Raw net spellings and exact 1nm serialized geometry must bind current R753/native source','Fresh all-drill source-rooted In1/In4 annuli, literal old contacts/references, new body references and current native DRC/SI','Original .525 mm own-signal cap must be rederived from current normal source antipad; no neighbor cap or drill borrowing'],'DAC_SDI_or_second_COM_stitch_included':False,'coupled_R19_verdict':a['verdict'],'guard_policy':'Two .20 mm F/B tracks; .5/.2 mm SG and COM ordinary vias; .917878 mm real return pair. Prior native proof was selected COM and old source context only; not current qualification.'}
f=OUT/'saved-VREF-only-add-stencil.json';f.write_text(json.dumps(packet,indent=1)+'\n');receipt={'verdict':'FOUR_SAVED_VREF_ADD_CHUNKS_EXTRACTED_CURRENT_ALL_GATES_OPEN','input_SHA256':{str(p.resolve()):sha(p)for p in(src,ap,nr)},'packet_file':str(f.resolve()),'packet_SHA256':sha(f),'new_chunk_count':4,'old_items_deleted':0,'native_jobs':0,'adopted':False,'current_native_requalification':'OPEN'};(OUT/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n');print('R616_COMPLETE',sha(OUT/'receipt.json'),'packet',sha(f))
