"""Correct the new bridge's top-level indentation, retaining R242 compile FAIL."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;wrapper=H/'nominate_U10003_shared_return_explicit_In1_source_bridge_r242.py';prefix=wrapper.read_text().split("compile(code,str(source),'exec');receipt=")[0];exec(compile(prefix,str(wrapper),'exec'))
for token in ['source_bridge_xy=','source_bridge=','assert oldref[','desired=desired.union(source_bridge)','in1_central_rooted=False','win=desired.envelope.buffer(1);']:
 needle='\n '+token;assert code.count(needle)==1,token;code=code.replace(needle,'\n'+token)
code=code.replace('nomination-r242','nomination-r243').replace('R242','R243');compile(code,str(source),'exec')
receipt=H/'U10003-source-bridge-r243-derivation.json';assert not receipt.exists();receipt.write_text(json.dumps({'failed_wrapper_sha256':hashlib.sha256(wrapper.read_bytes()).hexdigest(),'executed_script_sha256':hashlib.sha256(code.encode()).hexdigest(),'correction':'new top-level bridge declarations were indented one extra space in R242; source geometry and strong old-source seeding unchanged','R242_IndentationError_preserved_before_any_native_model_emission':True,'native_jobs':0,'adopted':False},indent=1)+'\n');exec(compile(code,str(source),'exec'))
