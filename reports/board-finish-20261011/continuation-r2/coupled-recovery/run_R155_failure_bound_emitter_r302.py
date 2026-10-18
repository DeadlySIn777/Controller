from pathlib import Path
import sys
import emit_known_failed_reference_native_recipe_r298 as E
H=Path(__file__).resolve().parent
sys.argv=[E.__file__,str(H/'R155-known-failed-reference-diagnostic-manifest-r300/immutable-diagnostic-manifest.json'),str(H/'R155-known-failed-reference-native-recipe-r302')]
E.main()
