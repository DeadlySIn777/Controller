from pathlib import Path
p=Path('reports/motherboard-return-zoning-20261001/review-IO3-literal-tip-cleanup-independent-r06.py');q=p.with_name(p.name.replace('r06.py','r07.py'))
if q.exists():raise ValueError('Immutable revision exists')
s=p.read_text().replace("IO3-literal-tip-cleanup-independent-r06'","IO3-literal-tip-cleanup-independent-r07'")
needle="for row in influence['all_literal_outside_loss_polygons']:"
replacement="""second_receipt=Path('reports/motherboard-return-zoning-20261001/IO3-literal-tip-cleanup-independent-r06/full-native-influence-outside-thin-mask.json')
second=json.loads(second_receipt.read_text())
if second['board_sha256']!=sha(candidate)or len(second['all_literal_outside_loss_polygons'])!=1:raise ValueError('Exact additional full native local smoothing contour drift')
frozen[str(second_receipt)]=sha(second_receipt)
literal_influence=influence['all_literal_outside_loss_polygons']+second['all_literal_outside_loss_polygons']
for row in literal_influence:"""
s=s.replace(needle,replacement).replace('<=211.414225','<=211.429813')
s=s.replace("exact_two_native_local_smoothing_contours=influence['all_literal_outside_loss_polygons']","exact_three_native_local_smoothing_contours=literal_influence")
q.write_text(s)
