import runpy
from pathlib import Path
H=Path(__file__).resolve().parent;old=H/'diagnose_coupon_native_nets_r4.py';target=H/'diagnose_coupon_native_nets_r5.py';runner=H/'run_coupon_native_diagnostic_r5.py'
if target.exists() or runner.exists():raise ValueError('Fresh native net diagnostic required')
target.write_text(old.read_text(encoding='utf-8').replace('str(t.GetEffectiveNetClass().GetName())','str(t.GetNetClassName())'),encoding='utf-8')
text=(H/'run_coupon_native_diagnostic_r4.py').read_text(encoding='utf-8').replace('net-diagnostic-r4','net-diagnostic-r5').replace('diagnose_coupon_native_nets_r4.py','diagnose_coupon_native_nets_r5.py')
runner.write_text(text,encoding='utf-8');runpy.run_path(str(runner),run_name='__main__')
