from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,sys
HERE=Path(__file__).resolve().parent
BASE=HERE.parent/'actual-target-acquisition-r04'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main(out):
 if out.exists():raise RuntimeError('fresh equivalence directory required')
 out.mkdir(parents=True);candidate=out/'inputs';shutil.copytree(HERE,candidate,ignore=shutil.ignore_patterns('__pycache__'))
 exact={str(p):sha(p) for p in [BASE/'cnc_iol1_acquisition_master.v',BASE/'cnc_iol1_diagnostic_acquisition.v',HERE/'cnc_iol1_acquisition_master.v',HERE/'cnc_iol1_diagnostic_acquisition.v']}
 for name in ['cnc_iol1_acquisition_master.v','cnc_iol1_diagnostic_acquisition.v']:
  s=(BASE/name).read_text().replace('cnc_iol1_acquisition_master','prior_iol1_acquisition_master').replace('cnc_iol1_diagnostic_acquisition','prior_iol1_diagnostic_acquisition')
  (candidate/('prior_'+name)).write_text(s,encoding='utf8',newline='\n')
 p=candidate/'tb_iol1_acquisition.sv';s=p.read_text();insert='''
 wire[3:0]pcs,pclk,pcmd,pfault,paccept,pvalid,pseen,pactive,pfactory,pai;
 wire[511:0]psamples,pintegrity;wire[63:0]pages,pseq,panalog;wire[11:0]pstates;wire[23:0]pfiltered,praw;wire[15:0]papplied;
 prior_iol1_diagnostic_acquisition prior(.clk(clk),.reset_n(reset_n),.enable(enable),.miso(miso),.cs_n(pcs),.sclk(pclk),.mosi(pcmd),.fault_latched(pfault),.accepted(paccept),.diagnostic_sample_valid(pvalid),.diagnostic_transport_seen(pseen),.commercial_active(pactive),.factory_identity_verified(pfactory),.last_valid_realtime(psamples),.last_integrity_realtime(pintegrity),.sample_age_us(pages),.last_reply_sequence(pseq),.last_reply_state(pstates),.diagnostic_filtered_di(pfiltered),.diagnostic_raw_di(praw),.diagnostic_do_applied(papplied),.analog_valid(pai),.analog_codes(panalog));
 integer equivalence_checks=0;
 always @(posedge clk)begin #2;
 if({cs,sclk,mosi,fault,accepted,valid,seen,active,factory,samples,integrity,ages,sequences,states,filtered,raw,applied,ai_valid,analog_codes}!=={pcs,pclk,pcmd,pfault,paccept,pvalid,pseen,pactive,pfactory,psamples,pintegrity,pages,pseq,pstates,pfiltered,praw,papplied,pai,panalog})$fatal(1,"exact optimization equivalence mismatch at%0t",$time);
 equivalence_checks++;
 end
'''
 s=s.replace(' genvar g;',insert+'\n genvar g;')
 s=s.replace('$iol1_reachable_sequence_fixture(0,65534);','prior.lane[0].master.tx_sequence=16\'hffff;prior.lane[0].master.expected_sequence=16\'hfffe;\n  $iol1_reachable_sequence_fixture(0,65534);')
 s=s.replace('$display("PASS acquisition checks=', '$display("OPTIMIZATION_EQUIVALENCE_PASS cycles=%0d",equivalence_checks);\n  $display("PASS acquisition checks=')
 p.write_text(s,encoding='utf8',newline='\n')
 p=candidate/'run_acquisition_proof.py';s=p.read_text().replace("sources=[HERE/'cnc_iol1_acquisition_master.v'","sources=[HERE/'prior_cnc_iol1_acquisition_master.v',HERE/'prior_cnc_iol1_diagnostic_acquisition.v',HERE/'cnc_iol1_acquisition_master.v'")
 s=s.replace('cnc_iol1_acquisition_master.v cnc_iol1_diagnostic_acquisition.v peer.sv','cnc_iol1_acquisition_master.v cnc_iol1_diagnostic_acquisition.v prior_cnc_iol1_acquisition_master.v prior_cnc_iol1_diagnostic_acquisition.v peer.sv')
 p.write_text(s,encoding='utf8',newline='\n')
 q=out/'actual-proof';r=subprocess.run([sys.executable,'-X','utf8',str(p),'--out',str(q)],capture_output=True,text=True,encoding='utf8',errors='replace',timeout=300)
 (out/'command.log').write_text(r.stdout+r.stderr,encoding='utf8',newline='\n')
 log=(q/'simulation.log').read_text() if(q/'simulation.log').is_file() else ''
 receipt={'status':'PASS' if r.returncode==0 and 'OPTIMIZATION_EQUIVALENCE_PASS' in log else 'FAIL','exact_input_hashes':exact,'exact_inputs_unchanged':all(sha(Path(p))==h for p,h in exact.items()),'full_four_lane_cycle_equivalence':'all SPI pins, accepted/fault, diagnostic validity, both sample images, age, header/sequence/class state and decoded data every core clock including CRC/request corruption/wrap/reset','actual_proof_receipt_sha256':sha(q/'receipt.json') if(q/'receipt.json').is_file() else None,'tail':log[-1600:]}
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(receipt['status']);return 0 if receipt['status']=='PASS' else 1
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',required=True,type=Path);raise SystemExit(main(p.parse_args().out.resolve()))
