"""Prepare a fresh combined-board check; never reuse a donor's filled proof."""
from pathlib import Path
p=Path(__file__).parent
s=(p/'verify_OUT_PERMIT_common_In1_r02.py').read_text()
s=s.replace("BASE=Path('reports/motherboard-pcb-integration-20261001/source26-C19042-local-bypass-r81/motherboard-bounded-merged-candidate.kicad_pcb')", "MANIFEST_BASE=Path('reports/motherboard-pcb-integration-20261001/source26-C19042-local-bypass-r81/motherboard-bounded-merged-candidate.kicad_pcb')\nBASE=Path('reports/motherboard-pcb-integration-20261001/source26-reference-closure-and-spurs-r83/motherboard-bounded-merged-candidate.kicad_pcb')")
s=s.replace("OUT=Path('reports/motherboard-ordinary-routing-20261001/actual-source26-root81-OUT-PERMIT-r06')", "DONOR=Path('reports/motherboard-ordinary-routing-20261001/actual-source26-root81-OUT-PERMIT-r06')\nimport argparse\nap=argparse.ArgumentParser()\nfor n in ('board','map','drc','out'):ap.add_argument('--'+n,type=Path,required=True)\na=ap.parse_args();OUT=a.out;OUT.mkdir(exist_ok=False)")
s=s.replace("DEST=OUT/'motherboard-OUT-PERMIT-common-In1-candidate.kicad_pcb'", "DEST=a.board")
s=s.replace("MAP=Path('reports/motherboard-domains-20261001/source26-OUT-PERMIT-r06-r01/domain-map.json')", "MAP=a.map")
s=s.replace("OUT/'proposed-groups.json'", "DONOR/'proposed-groups.json'").replace("OUT/'manifest.json'", "DONOR/'manifest.json'").replace("OUT/'native.json'", "a.drc")
s=s.replace('o.INPUT_BOARD=BASE;', 'o.INPUT_BOARD=MANIFEST_BASE;')
s=s.replace('BASE,DEST,MAP,CONTROL,', 'BASE,DEST,MAP,CONTROL,MANIFEST_BASE,')
s=s.replace("native['ignored_checks']", "native['ignored_checks']")
s=s.replace("board_sha256=e.sha(DEST),source_scope=source", "board_sha256=e.sha(DEST),map_sha256=e.sha(MAP),source_scope=source")
s=s.replace("powerproof=power.review(before,after);", "precision=e.read(Path(__file__).parent/'io3-precision-boundary-r02/receipt.json');assert precision['passed']and precision['helper_sha256']==e.sha(power.__file__)\npowerproof=power.review(before,after);")
(p/'verify_OUT_PERMIT_combined_r01.py').write_text(s)
compile(s,str(p/'verify_OUT_PERMIT_combined_r01.py'),'exec')
