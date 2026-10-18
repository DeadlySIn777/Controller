from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'b5_conditional_drop_screen_r34.py').read_text().replace('b5-conditional-drop-screen-r34','b5-conditional-drop-screen-r35')
s=s.replace("bridge=q.get('inner_source_bridge_route')", "bridge=q.get('inner_source_bridge_route');bridge=bridge if bridge and not bridge.get('source_escape_initialization') else None")
(P/'b5_conditional_drop_screen_r35.py').write_text(s,encoding='utf-8')
compile(s,'b5_conditional_drop_screen_r35.py','exec')
