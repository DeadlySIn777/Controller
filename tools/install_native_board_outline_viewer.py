"""Install verified native outline rendering, preserving other viewer behavior."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
html=ROOT/'hardware/board_review/index.html'
helper=ROOT/'reports/motherboard-mechanical-20260930/native-outline.js'
out=ROOT/'reports/motherboard-mechanical-20260930/viewer-native-outline-r01'
assert not out.exists();out.mkdir()
original=html.read_bytes();text=original.decode('utf-8')
(out/'input-index.html').write_bytes(original)
anchor='function draw(){';assert text.count(anchor)==1 and 'function nativeOutlinePath('not in text
code=helper.read_text().split('if (typeof module !== "undefined")')[0].strip()
text=text.replace(anchor,code+'\n'+anchor,1)
old='  svgNode("rect",{x:0,y:0,width,height,rx:.8,fill:"#174a3d",stroke:"#70af96","stroke-width":.3},svg);svgNode("rect",{x:0,y:0,width,height,fill:"url(#grid)","pointer-events":"none"},svg);'
new='''  if(board.native_edge_cuts){
    const nativePath=nativeOutlinePath(board.native_edge_cuts,width,height);
    svgNode("path",{d:nativePath,fill:"#174a3d",stroke:"#70af96","stroke-width":.3,"fill-rule":"evenodd"},svg);
    const clip=svgNode("clipPath",{id:"native-board-outline"},defs);svgNode("path",{d:nativePath,"fill-rule":"evenodd"},clip);
    svgNode("rect",{x:0,y:0,width,height,fill:"url(#grid)","clip-path":"url(#native-board-outline)","pointer-events":"none"},svg);
  }else{
    svgNode("rect",{x:0,y:0,width,height,rx:.8,fill:"#174a3d",stroke:"#70af96","stroke-width":.3},svg);svgNode("rect",{x:0,y:0,width,height,fill:"url(#grid)","pointer-events":"none"},svg);
  }'''
assert text.count(old)==1;text=text.replace(old,new,1)
html.write_text(text,encoding='utf-8')
# Reconstruct the exact input from the two permitted substitutions. This
# proves selectors, interactions, polling, pad/copper drawing and older
# revision rendering have no incidental modifications.
reconstructed=text.replace(code+'\n'+anchor,anchor,1).replace(new,old,1)
assert reconstructed==original.decode('utf-8')
script=text.split('<script>')[1].split('</script>')[0];(out/'viewer-script.js').write_text(script)
(out/'updated-index.html').write_bytes(html.read_bytes())
digest=lambda b:hashlib.sha256(b).hexdigest()
report={'input_index_sha256':digest(original),'output_index_sha256':digest(html.read_bytes()),'helper_sha256':digest(helper.read_bytes()),
        'only_helper_and_native_outline_grid_branch_changed':True,'historic_rectangular_appearance_preserved':True,
        'native_grid_clipped_to_actual_profile':True,'physical_CAD_or_publication_manifest_changed':False,
        'scope':'Viewer rendering only; source, native PCB, routing, machine configuration and all historical published JSON unchanged.'}
(out/'receipt.json').write_text(json.dumps(report,indent=2)+chr(10));print(json.dumps(report))
