"""Isolated CMD RX alignment; retain full RX/completed-frame/TX snapshots."""
from pathlib import Path
import hashlib,json,difflib
H=Path(__file__).resolve().parent;ROOT=H.parents[2];OUT=H/'transport-cmd-alignment-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    assert not OUT.exists();OUT.mkdir()
    source=ROOT/'gateware/v3/runtime/cnc3_spi_transport_stateful.v';old=source.read_text();new=old
    replacements={
     'rx_crc==rx_shift[15:0]':'rx_crc==(selected_fb?rx_shift[15:0]:rx_shift[655:640])',
     "frame<=selected_fb?rx_shift:{rx_shift[767:0],640'b0};":'frame<=rx_shift;',
     'rx_rate_word<={rx_shift[30:0],mosi_sync[2]};':'rx_rate_word<={rx_shift[670:640],mosi_sync[2]};',
     'rx_shift<={rx_shift[1406:0],mosi_sync[2]};':'''// Collect CMD directly in the same upper768-bit alignment used by
      // the public completed frame. FB still uses the full1408-bit shift.
      if(selected_fb)rx_shift<={rx_shift[1406:0],mosi_sync[2]};
      else rx_shift<={rx_shift[1406:640],mosi_sync[2],640'd0};'''
    }
    for oldtext,newtext in replacements.items():
        assert new.count(oldtext)==1,oldtext;new=new.replace(oldtext,newtext)
    (OUT/'cnc3_spi_transport_stateful.v').write_text(new)
    (OUT/'original.v').write_bytes(source.read_bytes())
    (OUT/'original_diff.v').write_text(old.replace('module cnc3_spi_transport_stateful (','module cnc3_spi_transport_stateful_original ('))
    (OUT/'candidate_diff.v').write_text(new.replace('module cnc3_spi_transport_stateful (','module cnc3_spi_transport_stateful_candidate ('))
    (OUT/'candidate.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='canonical/cnc3_spi_transport_stateful.v',tofile='isolated/cnc3_spi_transport_stateful.v')))
    record={'status':'ISOLATED_CMD_ALIGNMENT_CANDIDATE_PREPARED_QUALIFICATION_REQUIRED','source':str(source),'canonical_SHA256':sha(source),'candidate_SHA256':sha(OUT/'cnc3_spi_transport_stateful.v'),'buffers_retained':{'rx_shift':1408,'completed_frame':1408,'tx_snapshot':1392,'first_six_byte_header':48},'delta':['CMD incoming bits shift within upper768bits and lower640bits stay0','CMD trailer compare uses655:640','CMD streamed rate-word tap uses670:640','completed frame commit directly copies aligned RX; FB path unchanged'],'unchanged':['SPI synchronizers','CS/timing/overlap guards','RX/TXCRC16 algorithms and update cycles','FB innerCRC32C taps','first48bitrejection header','TX snapshot/MISO','completed frame hold/valid cycle','reset'],'adopted':False,'physical_fit_timing':'OPEN'}
    (OUT/'preparation-receipt.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
if __name__=='__main__':main()
