"""Use a genuinely assigned IMP_50 net for the other-literal negative control."""
import hashlib,json,runpy
from pathlib import Path
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    source=HERE/'check_cm_terminal_native_rules_r2.py';target=HERE/'check_cm_terminal_native_rules_r3.py'
    if target.exists():raise ValueError('Fresh negative-control correction required')
    project=HERE/'coupled-recovery/cm-terminal-profile-r1/board.kicad_pro.proposed';p=json.loads(project.read_bytes())
    selected='/motherboard_compute/CM_HOST_SPI_SCLK';assignment=p['net_settings']['netclass_assignments'][selected]
    if 'IMP_50' not in assignment:raise ValueError('Native other-net control lacks actual controlled class')
    text=source.read_text(encoding='utf-8');anchor="'/motherboard_compute/CM_CAN_SPI_MISO'"
    if text.count(anchor)!=1:raise ValueError('Exact other-net control edit anchor differs')
    text=text.replace(anchor,repr(selected)).replace("OUT=HERE/'cm-terminal-native-rule-coupons-r2'","OUT=HERE/'cm-terminal-native-rule-coupons-r3'")
    target.write_text(text,encoding='utf-8')
    (HERE/'cm-terminal-native-rule-coupons-r2/control-correction.json').write_text(json.dumps({'source_sha256':sha(source),'corrected_sha256':sha(target),'project_sha256':sha(project),'cause':'Original other-literal negative control chose CM_CAN_SPI_MISO, which has no IMP_50 assignment. Its .20mm width was correctly permitted by general rule, so that expectation was invalid.','selected_raw_net':selected,'actual_project_assignment':assignment,'rule_board_or_project_modified':False},indent=1)+'\n',encoding='utf-8')
    runpy.run_path(str(target),run_name='__main__')
if __name__=='__main__':main()
