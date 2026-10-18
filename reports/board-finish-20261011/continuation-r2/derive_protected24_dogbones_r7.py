"""Cache the small endpoint-intersection mask before the corrected-overlay run."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    src=H/'construct_protected24_dogbones_r6.py';dst=H/'construct_protected24_dogbones_r7.py';assert not dst.exists()
    code=src.read_text(encoding='utf-8')
    changes={"OUT=ROOT/'protected24-dogbones-r6'":"OUT=ROOT/'protected24-dogbones-r7'","controller-protected24-dogbone-r6/":"controller-protected24-dogbone-r7/","goal=part.buffer(-.00002).intersection(source[l])":"reachable=part.buffer(-.00002);goal=reachable.intersection(source[l])","'part':part,'goal':goal":"'part':part,'reachable':reachable,'goal':goal","startshape=q['part'].buffer(-.00002).intersection(annulus)":"if not q['reachable'].intersects(annulus):continue\n                startshape=q['reachable'].intersection(annulus)"}
    for a,b in changes.items():
        assert code.count(a)==1,(a,code.count(a));code=code.replace(a,b)
    compile(code,str(dst),'exec');dst.write_text(code,encoding='utf-8')
    (H/'protected24-dogbones-r7-derivation.json').write_text(json.dumps({'source_helper_sha256':sha(src),'new_helper_sha256':sha(dst),'only_exact_reachable_mask_cache_added':True,'corrected_r19_overlay_retained':True,'source_annulus_and_all_aperture_margins_unchanged':True,'full_combined_contact_current_native_gates':'OPEN','native_jobs':0,'board_written':False},indent=1)+'\n',encoding='utf-8')
if __name__=='__main__':main()
