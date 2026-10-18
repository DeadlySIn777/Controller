from pathlib import Path
import importlib.util,json
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('public_stateful_bench',ROOT/'tools/validate_controller.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
out=b.fresh_output(ROOT/'reports/cnc3-stateful-implementation-20261001/public-stateful-stage-r01')
inputs=('tools/validate_controller.py','tests/test_validate_controller.py',*b.stateful_inputs(),*b.SPI_PLANT_INPUTS)
bound={p:b.sha(ROOT/p) for p in inputs}
caps=b.capability_inventory(out,'GarciaMechBuilder')
stage=b.run_stateful_stage(out,caps,'GarciaMechBuilder')
unchanged=bound=={p:b.sha(ROOT/p) for p in bound}
receipt={'passed':stage['status']=='PASS'and unchanged,'stage':stage,'source_unchanged':unchanged,'input_sha256':bound,
         'whole_controller_passed':False,'physical_qualified':False,'manufacturing_ready':False}
b.write(out/'receipt.json',receipt)
print(json.dumps({'passed':receipt['passed'],'stage_status':stage['status']}))
raise SystemExit(0 if receipt['passed']else 1)
