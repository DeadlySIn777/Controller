"""Keep withdrawn FIELD5 In4 separate from the new In2 source branch."""
from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent;old=H/'freeze_FIELD_ROOT_priority_interaction_and_sparse_role_handoff_r739.generated.py'
failed=H/'FIELD-ROOT-distinct-priority-exact-native-ownership-and-sparse-role-handoff-r739'
assert failed.exists() and not (failed/'failure.json').exists()
(failed/'failure.json').write_text(json.dumps({'status':'FAILED_BEFORE_EMISSION','assertion':'Withdrawn FIELD5 61cb In4 has no same-layer successor; do not infer a scope translation to In2',
 'script_SHA256':hashlib.sha256(old.read_bytes()).hexdigest(),'no_model_or_board_emitted':True},indent=1)+'\n',encoding='utf-8')
text=old.read_text(encoding='utf-8').replace('FIELD-ROOT-distinct-priority-exact-native-ownership-and-sparse-role-handoff-r739','FIELD-ROOT-distinct-priority-exact-native-ownership-and-sparse-role-handoff-r741')
text=text.replace("        assert len(targets)==1\n        current=targets[0]", """        if not targets:
            assert member=='61cb8179-7754-5031-bbea-0da464bf816f' and prior['layer']=='In4.Cu'
            renames.append({'prior_owned_UUID':member,'current_canonical_UUID':None,'raw_net':prior['net'],'layer':prior['layer'],
                'scope_translation_allowed':False,'reason':'Withdrawn failed In4 FIELD5 branch; R543 constructs a distinct source-qualified In2 branch'})
            continue
        assert len(targets)==1
        current=targets[0]""")
text=text.replace('R739_COMPLETE','R741_COMPLETE')
generated=H/'freeze_FIELD_ROOT_priority_interaction_and_sparse_role_handoff_r741.generated.py';assert not generated.exists();generated.write_text(text,encoding='utf-8')
exec(compile(text,str(generated),'exec'),{'__file__':str(generated),'__name__':'__main__'})
