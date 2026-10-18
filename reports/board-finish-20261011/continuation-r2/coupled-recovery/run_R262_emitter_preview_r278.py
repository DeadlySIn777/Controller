import sys
from pathlib import Path
H=Path(__file__).resolve().parent
import emit_current_owned_native_recipe_r274 as E
sys.argv=[E.__file__,str(H/'R262-native-emitter-preview-manifest-r278.json'),str(H/'R262-current-owned-native-emitter-preview-r278')]
E.main()
