"""Exact native review of the one-hole source-outline successor."""
from pathlib import Path
import hashlib
H=Path(__file__).resolve().parent.parent
s=(H/'audit_core1v2_selected_native_r133.py').read_text()
s=s.replace("d=H/'core1v2-native-diagnostic-r132';out=d/'independent-selected-CORE1V2-r133.json'","d=H/'core1v2-native-diagnostic-r138';out=d/'independent-selected-CORE1V2-r139.json'")
s=s.replace('65e55826c5b925fdcfb98114b1f6d04f0ca49e67b3025db21157436cee71f6eb','fb672ddca7cf02a92d28b112bb7d79c189a7f1b58230e928c86a335c4a96646f').replace('13571e6204e78f9aab1f2858ff123b6ef72f3aab766edb2587bc8155954f8ec7','96bc0aac793c2aa42a76be9946ff87c3148a35e3418980e8c7122b8b798c087a')
s=s.replace("mp=H/'sbc-power/frozen-regional-source-exit-replay-r129/model.pkl'","mp=H/'sbc-power/CORE1V2-source-native-outline-correction-r135/model.pkl'").replace('8f4db80497693186388d622a45508cdf39eb5e0f51a9ee359061bb7d6428ad93','729c76b8ef0ec7ec8af92ca287f3e8663741e9303bc5dcf3e10fb9b4af3bceca')
out=H/'audit_core1v2_selected_native_r139.py';assert not out.exists();out.write_text(s);compile(s,str(out),'exec');print('CORRECTED_NATIVE_INDEPENDENT_DERIVED',hashlib.sha256(out.read_bytes()).hexdigest())
