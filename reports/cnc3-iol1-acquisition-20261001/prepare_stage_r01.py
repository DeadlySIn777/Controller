"""Stage only: preserve the real target and earlier gateware byte-for-byte."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent/'stage-r01'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 if OUT.exists():raise RuntimeError('fresh staging directory required')
 OUT.mkdir();(OUT/'originals').mkdir()
 names=['gateware/motherboard_iol1_target_bringup/cnc_iol1_readonly_target_master.v','gateware/motherboard_iol1_target_bringup/tb_iol1_target_c.sv','firmware/motherboard_iol1_readonly/iol1.c','firmware/motherboard_iol1_readonly/iol1.h','firmware/motherboard_iol1_readonly/peer_vpi.c','firmware/motherboard_iol1_readonly/target.c','gateware/v3/frozen/spec/protocol.json']
 rows={}
 for name in names:
  p=ROOT/name;q=OUT/'originals'/p.name;q.write_bytes(p.read_bytes());rows[name]=sha(p)
 text=(OUT/'originals/cnc_iol1_readonly_target_master.v').read_text()
 text=text.replace('cnc_iol1_readonly_target_master','cnc_iol1_acquisition_master')
 text=text.replace('output reg accepted, output reg fault_latched','output reg accepted, output reg fault_latched,\n    output reg frame_seen, output reg header_crc_good, output reg [319:0] checked_frame,\n    output wire link_synced, output wire [1:0] failed_polls')
 text=text.replace('reg response_good;','assign link_synced = synced;\n    assign failed_polls = failures;\n    reg header_good;\n    reg response_good;')
 text=text.replace('response_good = (EPOCH != 0) &&','header_good = (EPOCH != 0) &&')
 text=text.replace('rx_shift[303:296] == CLASS_ID && rx_shift[291:288] == SLOT_ID &&','rx_shift[303:296] == CLASS_ID && rx_shift[295:288] == {4\'b0,SLOT_ID} &&')
 text=text.replace("rx_shift[31:0] == (rx_crc ^ 32'hffffffff) &&","rx_shift[31:0] == (rx_crc ^ 32'hffffffff);\n        response_good = header_good &&")
 text=text.replace('failures <= 0; fault_latched <= 0; accepted <= 0;','failures <= 0; fault_latched <= 0; accepted <= 0;\n            frame_seen <= 0; header_crc_good <= 0; checked_frame <= 0;')
 text=text.replace('accepted <= 0;\n            if(!enable','accepted <= 0; frame_seen <= 0; header_crc_good <= 0;\n            if(!enable')
 text=text.replace('CHECK: begin\n                    if(response_good)','CHECK: begin\n                    frame_seen <= 1; header_crc_good <= header_good; checked_frame <= rx_shift;\n                    if(response_good)')
 (OUT/'cnc_iol1_acquisition_master.v').write_text(text,encoding='utf8',newline='\n')
 (OUT/'source-manifest.json').write_text(json.dumps({'scope':'four soldered motherboard regions, read-only diagnostic acquisition; no factory/ACTIVE/output authority','original_sources':rows},indent=2)+'\n')
 print(OUT)
if __name__=='__main__':main()
