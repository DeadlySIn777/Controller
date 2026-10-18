"""One global-area2 map of qualified RAM/capture/transport overlays."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent;OUT=H/'transport-cmd-alignment-r1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    packet=OUT/'reviewable-transport-overlay-packet.json';p=json.loads(packet.read_bytes())
    assert p['status']=='ISOLATED_CMD_ALIGNMENT_ACTUAL_SPI_DIFFERENTIAL_AND_FULL_SIM2_REGRESSION_PASS_NATIVE_RESOURCE_UNEXECUTED'
    source=H/'map_global_area2_r7.py';text=source.read_text()
    text=text.replace("OUT=HERE/'event-capture-global-area2-r7/native-full-map'", "OUT=HERE/'transport-cmd-alignment-r1/native-full-map'")
    marker="    inventory=[]"
    addition="    overlay['cnc3_spi_transport_stateful.v']=HERE/'transport-cmd-alignment-r1/cnc3_spi_transport_stateful.v'\n    assert sha(overlay['cnc3_spi_transport_stateful.v'])=='c909378cb28cf87c7113b1b92c6cdd82f71e166c64eb87548a8880ba85c9d4cc'\n"
    assert text.count(marker)==1;text=text.replace(marker,addition+marker)
    text=text.replace('full-SIM2-global-area2-map','full-SIM2-transport-area2-map').replace('EXPLORATORY_NATIVE_SIM2_GLOBAL_AREA2_MAP_COMPLETE_BEHAVIOR_AND_FIT_SEPARATE','EXPLORATORY_NATIVE_SIM2_TRANSPORT_AREA2_MAP_COMPLETE_BEHAVIOR_AND_FIT_SEPARATE')
    target=H/'map_transport_full_r1.py';assert not target.exists();target.write_text(text)
    record={'status':'ONE_NATIVE_FULL_CORE_TRANSPORT_OVERLAY_MAP_PREPARED','source_runner':str(source),'source_runner_SHA256':sha(source),'derived_runner_SHA256':sha(target),'transport_packet_SHA256':sha(packet),'baseline_global_area2_receipt_SHA256':sha(H/'event-capture-global-area2-r7/independent-review-receipt.json'),'source_overlays':['registered RAM bank6f034','literal capture4a42','transport CMD alignmentc909'],'setting':'global modearea2; two CPUs/max_threads2; no settings sweep','adopted':False}
    (OUT/'native-map-preparation-receipt.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
if __name__=='__main__':main()
