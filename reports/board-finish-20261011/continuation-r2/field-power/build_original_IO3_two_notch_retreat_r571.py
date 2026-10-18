"""Preserve failed three-point trial; derive the two attributed notch repair."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent
old=H/'nominate_original_IO3_TMR_exact_local_outline_retreat_r569.py'
text=old.read_text(encoding='utf-8')
(H/'original-IO3-TMR-exact-local-three-vertex-negative-outline-nominee-r569/failure.json').write_text(json.dumps({'status':'FAIL_DECLARED_025_MARGIN_NOT_REACHED_AT_OTHER_EXISTING_DIAGONAL_NOTCH','script_SHA256':hashlib.sha256(old.read_bytes()).hexdigest(),'preserved_before_native_or_packet_emission':True,'cause':'The lower touching edge was cleared; a separate original diagonal follows the AREA within approximately one nanometre, so complete AREA distance remained below .025. No margin waiver.','successor':'Two separately attributed notch edits; preserve all other original ring points.'},indent=1)+'\n',encoding='utf-8')
text=text.replace('r569','r571').replace('three-vertex','two-notch').replace("new=[[323972900,130375100],[339800000,130375100]];rings[0][idx:idx+3]=new", "new=[[323972900,130375100],[339800000,130375100]];rings[0][idx:idx+3]=new\n upper_old=[[334400000,123679066],[325246423,119253576]];upper_new=[[334400000,123651178],[325265219,119234781]];assert rings[0][3013:3015]==upper_old;rings[0][3013:3015]=upper_new")
text=text.replace("assert locality.is_valid;outside=loss.difference(locality);assert outside.is_empty", "upper_local=Polygon([(x/1e6,y/1e6)for x,y in upper_old+upper_new+[[334400000,122500000],[325400000,119100000]]]).convex_hull;locality=unary_union([locality,upper_local]);assert locality.is_valid;outside=loss.difference(locality);assert outside.is_empty")
text=text.replace("newchunk=(oldtext[:mat.start()]+replacement+oldtext[mat.end():]).encode();olda=", "newtext=oldtext[:mat.start()]+replacement+oldtext[mat.end():];upperpattern=r'(?P<indent>[ \\t]+)\\(xy 334\\.4 123\\.679066\\)\\r?\\n[ \\t]+\\(xy 325\\.246423 119\\.253576\\)';um=list(re.finditer(upperpattern,newtext));assert len(um)==1;um=um[0];ui=um.group('indent');ur=ui+'(xy 334.4 123.651178)'+nl+ui+'(xy 325.265219 119.234781)';newchunk=(newtext[:um.start()]+ur+newtext[um.end():]).encode();olda=")
text=text.replace("assert oldpts[1:1+idx]==newpts[1:1+idx]and oldpts[1+idx+3:]==newpts[1+idx+2:]", "assert oldpts[1:3014]==newpts[1:3014]and oldpts[3016:1+idx]==newpts[3016:1+idx]and oldpts[1+idx+3:]==newpts[1+idx+2:]")
text=text.replace("'declared_new_vertices_IU':new,", "'declared_new_vertices_IU':new,'second_declared_old_vertices_IU':upper_old,'second_declared_new_vertices_IU':upper_new,")
text=text.replace("'old_outer_vertices_before_3160_and_after_3162_exact':True", "'all_old_outer_vertices_exact_except_only_indices3013_3014_3160_3161_3162':True")
text=text.replace("'new_original_vertices_IU':new,", "'new_original_vertices_IU':new,'second_changed_original_vertices_IU':upper_old,'second_new_original_vertices_IU':upper_new,")
new=H/'nominate_original_IO3_TMR_exact_local_outline_retreat_r571.py';assert not new.exists();new.write_text(text,encoding='utf-8')
print('R571 derived',hashlib.sha256(new.read_bytes()).hexdigest())
