"""Apply native offset uncertainty to reconstruction-boundary classification."""
from pathlib import Path
p=Path(__file__).parent
s=(p/'check_io3_backbone_preservation_r06.py').read_text()
old=' narrow=subtract(before,opened);removed=subtract(before,after)'
new=""" # Opening is itself an approximate reconstruction. Nanometre strips
 # at rounded old antipads are not evidence of a thin physical feed.
 # Classify definite thin features outside its declared1um uncertainty.
 classified_opened=duplicate(opened)
 classified_opened.Inflate(pcbnew.FromMM(.001),pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,1)
 narrow=subtract(before,classified_opened);removed=subtract(before,after)"""
assert old in s;s=s.replace(old,new)
s=s.replace('preexisting_sub1mm_features_preserved_within_native_precision=True,','definite_preexisting_sub1mm_features_preserved_within_native_precision=True,morphological_reconstruction_boundary_uncertainty_um=1,')
(p/'check_io3_backbone_preservation_r07.py').write_text(s)
for old,new in [('test_io3_backbone_native_r06.py','test_io3_backbone_native_r07.py'),('test_io3_precision_boundary_r06.py','test_io3_precision_boundary_r07.py')]:
 t=(p/old).read_text().replace('preservation_r06','preservation_r07').replace('screen-native-r06','screen-native-r07').replace('boundary-r06','boundary-r07')
 if old.startswith('test_io3_backbone'):
  t=t.replace('for name,a,b in cases:',"""short=h.box(0,0,10,10);short.BooleanAdd(h.box(10,4.8,10.020,5.2));short.Simplify()
cases.append(('remove actual20um-long400um-wide receiving tab',short,h.box(0,0,10,10)))
brief=h.box(0,0,10,10);brief.BooleanAdd(h.box(10.004,0,20,10));brief.BooleanAdd(h.box(10,4.8,10.004,5.2));brief.Simplify()
cases.append(('actual2nm complete slit in4um-long400um-wide neck',brief,h.subtract(brief,h.box(10.002,-1,10.002002,11))))
for name,a,b in cases:""")
 (p/new).write_text(t)
for old,new in [('verify_OUT_PERMIT_common_In1_r06.py','verify_OUT_PERMIT_common_In1_r07.py'),('verify_OUT_PERMIT_combined_r05.py','verify_OUT_PERMIT_combined_r06.py')]:
 t=(p/old).read_text().replace('preservation_r06','preservation_r07').replace('screen-native-r06','screen-native-r07').replace('boundary-r06','boundary-r07')
 (p/new).write_text(t);compile(t,str(p/new),'exec')
t=(p/'verify_root83_In2_batch_r08.py').read_text().replace('actual-source26-root83-In2-batch-r08','actual-source26-root83-In2-batch-r09').replace('preservation_r06','preservation_r07').replace('screen-native-r06','screen-native-r07').replace('boundary-r06','boundary-r07')
(p/'verify_root83_In2_batch_r09.py').write_text(t)
