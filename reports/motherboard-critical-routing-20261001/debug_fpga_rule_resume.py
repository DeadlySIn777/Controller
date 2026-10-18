from pathlib import Path
import sys,traceback
source=Path('reports/motherboard-critical-routing-20261001/prepare_fpga_neck_rule_r03.py')
log=Path('reports/motherboard-critical-routing-20261001/fpga-rule-debug-r05.log')
def trace(frame,event,arg):
 if event=='line'and frame.f_code.co_filename==str(source):
  with log.open('a',encoding='utf8')as f:f.write(str(frame.f_lineno)+'\n')
 return trace
sys.argv=[str(source),'reports/motherboard-critical-routing-20261001/source26-root71-BGA-neck-rule-r05']
sys.settrace(trace)
try:exec(compile(source.read_text(),str(source),'exec'),{'__name__':'__main__','__file__':str(source)})
except BaseException:
 with log.open('a',encoding='utf8')as f:f.write(traceback.format_exc())
 raise
