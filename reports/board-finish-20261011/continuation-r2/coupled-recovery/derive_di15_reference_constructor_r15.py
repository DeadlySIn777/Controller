from pathlib import Path
HERE=Path(__file__).resolve().parent
src=HERE/'construct_di15_reference_escape_r12.py';dst=HERE/'construct_di15_reference_escape_r15.py';assert not dst.exists();t=src.read_text()
t=t.replace("import tri_route as T", "import tri_route as T\n+import di15_current_base_r13 as BIND".replace('\n+','\n'))
t=t.replace("out=HERE/'di15-reference-escape-nomination-r12.json'", "out=HERE/'di15-reference-escape-nomination-r15.json'")
t=t.replace("h=cp['h2'];zones=cp['zones'];before=cp['after'];refs=cp['refs'];source=A.read(cp['binding']['exact_native_discrete_board_file']);", "current=BIND.bind(r11,cp);h=current['h'];zones=current['zones'];before=current['after'];refs=current['refs'];source=A.read(current['binding']['exact_native_discrete_board_file']);")
t=t.replace("'source_parent_sha256':C.sha(source),", "'source_parent_sha256':C.sha(source),'current_R78_model_sha256':current['R78_model_sha256'],'exact_DI6_delta_only_current_checkpoint_sha256':current['checkpoint_sha256'],'latest_ground_snapshot4_hard_only_sha256':current['ground_snapshot4_hard_only_sha256'],'latest_ground_snapshot4_no_reference_credit':True,")
t=t.replace("A.read(__file__)", "A.read(__file__);A.read(BIND.__file__)")
assert t!=src.read_text();dst.write_text(t);print(dst)
