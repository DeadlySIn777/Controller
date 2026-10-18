from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]
evidence=ROOT/'reports/cnc3-stateful-implementation-20261001/serial-replay-full-r02/report.json'
assert json.loads(evidence.read_text())['counts']=={'PASS':11,'FAIL':0,'BLOCKED':0,'NOT_RUN':0}
updates={
 'PROJECT_MEMORY.md':(
  'Incoming MAX_RATE and per-channel timing enforcement in the stateful candidate requires corrective implementation and boundary tests.',
  'The report-local stateful candidate now enforces incoming MAX_RATE and per-channel timing, with 365 endpoint boundary cases, 570 serial/parallel equivalence frames and actual SPI rejection/reset/mutation tests. Its complete eleven-stage replay passes; real CNC3 HAL and all I/O providers remain unfinished.'),
 'reports/ENGINEERING_STATUS.md':(
  'Incoming MAX_RATE/channel timing enforcement in the new stateful candidate is being corrected and tested.',
  'The report-local stateful candidate now passes all eleven replay stages, including incoming global/timing admission, 365 endpoint cases, 570 equivalence frames and actual SPI fault/mutation checks. Nine actual SPI/STEP/DIR/ABZ/ideal-mechanics scenarios also pass; real CNC3 HAL and complete I/O providers remain unfinished.'),
 'docs/CURRENT_ACCEPTANCE_GATES.md':(
  'Incoming rate and per-channel timing enforcement in the new stateful candidate is under correction and adversarial test.',
  'Incoming global and per-channel timing admission now passes in the report-local stateful candidate, including all eleven replay stages and compiled negative controls. This does not close the actual HAL, full I/O, vendor timing or physical qualification gates.')}
changes=[]
for name,(old,new) in updates.items():
    p=ROOT/name;before=p.read_bytes();text=before.decode('utf8')
    assert text.count(old)==1
    text=text.replace(old,new)
    text=text.replace('characterization-register-r02/','characterization-register-r03/')
    marker='**Latest verified increment — Source26/ROOT102:**'
    assert text.count(marker)==1
    prefix=''if name=='PROJECT_MEMORY.md'else'../'
    paragraph=(f'**Bounded simulation evidence:** [reproducible stateful FPGA bundle]({prefix}reports/cnc3-stateful-implementation-20261001/serial-admission-handoff-r01/receipt.json) '
      f'and [nine actual serial-to-mechanics cases]({prefix}reports/controller-plant-20261001/actual-spi-edge-plant-r03/receipt.json) use the same frozen RTL bytes. '
      'Twelve emitted STEP/DIR outputs and four actual quadrature algorithms are exercised with explicit ideal external power/permission fixtures. '
      'The 1,114-check isolated mechanics fixture also has twelve compiled negative controls. The one-command bench now includes separate fresh stateful and serial/mechanics stages; this is not a physical controller or a complete LinuxCNC/CNC3 machine.\n\n')
    text=text.replace(marker,paragraph+marker)
    p.write_text(text,encoding='utf8')
    changes.append(dict(path=name,before_sha256=hashlib.sha256(before).hexdigest(),after_sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
out=ROOT/'reports/pre-hardware-characterization-20261001/characterization-register-r03/status-binding.json'
out.write_text(json.dumps(dict(changes=changes,stateful_report_sha256=hashlib.sha256(evidence.read_bytes()).hexdigest(),electrical_source_or_PCB_modified=False,manufacturing_ready=False),indent=2)+'\n')
