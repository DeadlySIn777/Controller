"""Make discovery probe independently rebuild its exact frozen RTL inputs."""
from pathlib import Path
import hashlib,json
here=Path(__file__).resolve().parent
source=here/'probe_actual_C_driver_SPI_r01.py'
text=source.read_text()
text=text.replace("OUT=HERE/'actual-C-driver-SPI-probe-r01'", "OUT=HERE/'actual-C-driver-SPI-probe-r02'")
old="""    # Reuse exact already compiled model sources, not its executable or responses.
    generated=sorted((ACTUAL/'obj').glob('*.cpp'))
    assert generated"""
new="""    # Fresh translation from the hashed copied HDL makes this replay independent
    # of an earlier generated model or simulation executable.
    obj=OUT/'obj'
    rtl=sorted(copied.glob('*.v'));assert len(rtl)==8
    run('verilate-real-inputs',['wsl','-d','GarciaMechBuilder','--','verilator','--cc',
        '--compiler','clang','--top-module','cnc3_motion_spi','--Mdir',unix(obj),
        '-Wall','-Wno-fatal',*[unix(p)for p in rtl]])
    generated=sorted(obj.glob('*.cpp'));assert generated
    generated_before={str(p):sha(p)for p in obj.iterdir()if p.suffix in ['.cpp','.h']}
"""
assert text.count(old)==1;text=text.replace(old,new).replace("unix(ACTUAL/'obj')","unix(obj)")
text=text.replace("unchanged=all(sha(Path(p))==h for p,h in before.items())", "unchanged=all(sha(Path(p))==h for p,h in before.items())\ngenerated_unchanged=all(sha(Path(p))==h for p,h in generated_before.items())\nunchanged=unchanged and generated_unchanged")
text=text.replace("error=error,input_sha256=before,input_unchanged=unchanged,", "error=error,input_sha256=before,input_unchanged=unchanged,generated_model_sha256=generated_before,generated_model_unchanged=generated_unchanged,")
text=text.replace("executions=[]", "executions=[];generated_before={}")
dest=here/'probe_actual_C_driver_SPI_r02.py';assert not dest.exists()
dest.write_text(text,encoding='utf8',newline='\n')
(here/'C-driver-probe-r02-derivation.json').write_text(json.dumps(dict(source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
    derived_sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),fresh_generated_model=True,prior_probe_preserved=True),indent=2)+'\n')
