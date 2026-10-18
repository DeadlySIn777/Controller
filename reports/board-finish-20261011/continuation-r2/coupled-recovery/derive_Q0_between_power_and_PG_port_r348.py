from pathlib import Path
H=Path(__file__).resolve().parent;dst=H/'screen_Q0_four_coupled_blockers_two_ports_r348.py';assert not dst.exists();s=(H/'screen_Q0_four_coupled_blockers_two_ports_r344.py').read_text().replace('[228.65,163.78]','[228.35,163.98]').replace('two-port-preflight-r344','two-port-preflight-r348');dst.write_text(s,encoding='utf-8',newline='\n')
