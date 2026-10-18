"""Distinct back-layer transport using exact original all-layer terminals."""
from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'exact-expanded-existing-LOAD-to-SOURCE-In3-r411.py').read_text(encoding='utf-8')
assert "CORE5-existing-LOAD-to-existing-SOURCE-fullwidth-In3-side-annulus-r411" in s
s=s.replace('CORE5-existing-LOAD-to-existing-SOURCE-fullwidth-In3-side-annulus-r411','CORE5-existing-LOAD-to-existing-SOURCE-fullwidth-B-side-annulus-r412')
s=s.replace('In3.Cu','B.Cu').replace('In3-body.wkb','B-body.wkb').replace('R411_PAIR','R412_PAIR').replace('R411_COMPLETE','R412_COMPLETE')
s=s.replace('two-existing-LOAD-to-21-actual-SOURCE','two-existing-LOAD-to-actual-SOURCE')
s=s.replace("'only_original_LG_In3_native_retreat_pending_local_source_oldrefs':True","'only_original_LG_B_native_retreat_pending_local_source_oldrefs':True")
s=s.replace('width_mm\':1.25,','width_mm\':1.25,\'layer\':\'B.Cu\',')
old="faces=[face for face in RF.parts(free)if not face.intersection(startContact).is_empty and not face.intersection(targetContact).is_empty];row="
new="parts=RF.parts(free);startFaces=[i for i,face in enumerate(parts)if not face.intersection(startContact).is_empty];targetFaces=[i for i,face in enumerate(parts)if not face.intersection(targetContact).is_empty];faces=[face for i,face in enumerate(parts)if i in startFaces and i in targetFaces];row="
assert s.count(old)==1;s=s.replace(old,new)
s=s.replace("'route':None}","'LOAD_contact_face_ids':startFaces,'SOURCE_contact_face_ids':targetFaces,'route':None}")
E=P/'exact-expanded-existing-LOAD-to-SOURCE-B-r412.py';assert not E.exists();E.write_text(s,encoding='utf-8')
exec(compile(s,str(E),'exec'),{'__name__':'__main__','__file__':str(E)})
