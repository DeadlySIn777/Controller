from pathlib import Path
import importlib.util
import json

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('actual_public_bench',ROOT/'tools/validate_controller.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
out=b.fresh_output(ROOT/'reports/controller-plant-20261001/public-SPI-bench-stage-r01')
bound={p:b.sha(ROOT/p) for p in ('tools/validate_controller.py','tests/test_validate_controller.py',*b.SPI_PLANT_INPUTS)}
caps=b.capability_inventory(out,'GarciaMechBuilder')
value=b.run_spi_plant_stage(out,caps,'GarciaMechBuilder')
unchanged=bound=={p:b.sha(ROOT/p) for p in bound}
receipt={'passed':value['status']=='PASS' and unchanged,'stage':value,'input_sha256':bound,
         'source_unchanged':unchanged,'complete_controller_passed':False,'physical_qualified':False,'manufacturing_ready':False}
b.write(out/'receipt.json',receipt)
print(json.dumps({'passed':receipt['passed'],'stage_status':value['status']}))
raise SystemExit(0 if receipt['passed'] else 1)
