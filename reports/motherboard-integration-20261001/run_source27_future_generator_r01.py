from pathlib import Path
import sys,importlib.util
ROOT=Path.cwd();OUT=ROOT/'reports/motherboard-integration-20261001/source27-health-parent-staged-r01';T=OUT/'candidate-tools';sys.path.insert(0,str(T));sys.path.insert(1,str(ROOT/'tools'))
s=importlib.util.spec_from_file_location('source27_future_builder',T/'hardware_build_motherboard.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b);b.ROOT=ROOT;b.MC=ROOT/'hardware/motion_card_loading_r03';print('Original MC input',b.MC,flush=True)
b.build(OUT/'future-generated-parent-r01')
