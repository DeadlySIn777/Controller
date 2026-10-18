from pathlib import Path
p=Path(__file__).parent;s=p/'review_CCK_CORE_cleaned_pair_r02.py';text=s.read_text().replace('CORE-cleaned-CCK-relative-review-r02','CORE-cleaned-CCK-relative-review-r03').replace('antipad-join-baseline-r02','antipad-join-baseline-r03').replace('antipad-join-cck-r02','antipad-join-cck-r03')
(p/'review_CCK_CORE_cleaned_pair_r03.py').write_text(text)
