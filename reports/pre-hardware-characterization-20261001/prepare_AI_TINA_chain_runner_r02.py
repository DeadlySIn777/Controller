"""Use the original TI TINA release with its own exact top-level pin order."""
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent
src=HERE/'run_AI_chain_SPICE_r01.py';dst=HERE/'run_AI_chain_SPICE_r02.py'
model=HERE/'INA149-active-model-discovery-r01/SBOM668/INA149_TINA_AIO/INA149.lib'
assert not dst.exists()
t=src.read_text()
def swap(a,b):
    global t
    assert t.count(a)==1,(a,t.count(a))
    t=t.replace(a,b)
swap("INA149-active-model-discovery-r01/SBOMC47/ina149.lib","INA149-active-model-discovery-r01/SBOM668/INA149_TINA_AIO/INA149.lib")
swap('7adccaf61abbb093980aa6fe6604bea72068541cf4112141e22aaaa79a463c8b',hashlib.sha256(model.read_bytes()).hexdigest())
swap("'INA149': ['3','2','5','1','7','4','6']","'INA149': ['3','5','7','6','4','1','2']")
swap('XINA{i} P{i} N{i} REF REF VCC AGND SHIFT{i} INA149','XINA{i} P{i} REF VCC SHIFT{i} AGND REF N{i} INA149')
swap('Unmodified INA149 and OPAx197 models under ngspice PSA compatibility, actual AGND=0.',
     'Unmodified TI INA149 TINA v1.0 and OPAx197 models under ngspice PSA compatibility, actual AGND=0. TINA top-level order is +IN,REF_A,V+,VOUT,V-,REF_B,-IN; PSpice order is different and is not reused.')
dst.write_text(t,encoding='utf8')
(HERE/'prepare-AI-TINA-chain-r02.json').write_text(json.dumps({'old_runner_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),
    'new_runner_sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'original_TINA_model_sha256':hashlib.sha256(model.read_bytes()).hexdigest(),
    'model_modified':False,'executed':False},indent=2)+'\n')
