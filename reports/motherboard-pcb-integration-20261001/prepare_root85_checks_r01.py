from pathlib import Path
p=Path(__file__).parent;s=(p/'run-root84-checks-r01.py').read_text()
s=s.replace('source26-FPGA-flash-MISO-r84','source26-seven-path-IO3-tip-trial-r85').replace('source26-r84-r01','source26-r85-r01')
start=s.index(" ('FLASH-MISO',");end=s.index('\n]',start)
s=s[:start]+" ('seven-new-ordinary',['reports/motherboard-ordinary-routing-20261001/verify_seven_pair_combined_r15.py',*common,'--out',str(p/'combined-seven-pair-proof')]),\n ('inventory',['tools/motion_card_routing_inventory.py','--board',str(board),'--netlist','hardware/motherboard/netlist.xml','--source-design','hardware/motherboard/design.json','--out',str(p/'independent-connectivity')]),"+s[end:]
needle="common=['--board'"
start=s.index(needle)
s=s[:start]+"with(p/'map-command.log').open('w')as stream:\n result=subprocess.run([py,'tools/hardware_map_motherboard_domains.py','--board',str(board),'--source','hardware/motherboard','--out',str(mp.parent)],cwd=root,stdout=stream,stderr=subprocess.STDOUT)\nassert result.returncode==0\n"+s[start:]
dest=p/'run-root85-checks-r01.py';assert not dest.exists();dest.write_text(s);compile(s,str(dest),'exec');print(dest)
