from pathlib import Path
HERE=Path(__file__).resolve().parent
p=HERE/'cnc3_motion_spi.v'
t=p.read_text(encoding='utf8')
for old,new in [
 ('wire alarm_valid,stop,consumed,sync_clear,io,effective;','wire alarm_valid,stop,sync_clear,io,effective,request_ready;'),
 ('.request_ready(),','.request_ready(request_ready),')]:
 if t.count(old)!=1:raise RuntimeError('Expected exact single old text '+old)
 t=t.replace(old,new)
p.write_text(t,encoding='utf8',newline='\n')
