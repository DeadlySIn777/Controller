from pathlib import Path
H=Path(__file__).resolve().parent
t=(H/'prepare_timing_width_r01.py').read_text()
for key in ['timing-width-stage-r01','timing-width-formal-r01','timing-width-proof-r01','timing-width-{kind}-candidate-r01']:
 t=t.replace(key,key.replace('r01','r02'))
t=t.replace("new=new.replace('reg[15:0] delay_left,hold_left;','reg[TIMER_BITS-1:0] delay_left,hold_left;')", "new=new.replace('reg[15:0] delay_left,hold_left;','reg[TIMER_BITS-1:0] delay_left,hold_left;')\nnew=new.replace(\"?delay_left:16'd0\",\"?{{(16-TIMER_BITS){1'b0}},delay_left}:16'd0\")")
exec(compile(t,str(H/'prepare_timing_width_r02.py'),'exec'))
