"""Preserve frozen runtime suite; add one isolated transport source overlay."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;OUT=H/'transport-cmd-alignment-r1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    behavior=json.loads((OUT/'behavior-receipt.json').read_bytes())
    assert behavior['status']=='ACTUAL_SPI_OLD_NEW_TRANSPORT_ALIGNMENT_DIFFERENTIAL_PASS'
    source=H/'event-capture-select-r2/run_full_runtime_with_capture.py';text=source.read_text()
    marker=' if args.mutation:\n';assert text.count(marker)==1
    overlay=" shutil.copyfile(Path('C:/Users/Gluis/OneDrive/Documents/ChatGPT/Controller/reports/board-finish-20261017/release-review/transport-cmd-alignment-r1/cnc3_spi_transport_stateful.v'),inputs/'cnc3_spi_transport_stateful.v')\n"
    target=OUT/'run_full_runtime_with_transport.py';assert not target.exists();target.write_text(text.replace(marker,overlay+marker))
    record={'status':'ISOLATED_TRANSPORT_FULL_SUITE_RUNNER_PREPARED','source_runner':str(source),'source_SHA256':sha(source),'derived_runner_SHA256':sha(target),'runner_delta':'one additional isolated transport overlay; registered RAM and capture overlays retained; frozen tests/taskset16,17 controls unchanged','differential_receipt_SHA256':sha(OUT/'behavior-receipt.json'),'adopted':False}
    (OUT/'runtime-runner-derivation.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
if __name__=='__main__':main()
