"""The narrow first notch relocated the cusp and remains failed.
This proposal replaces it with the complete bounding collar of the two actual
existing .20 mm-clearance antipads, plus .10 mm native-minimum-feature half
width. It is an actual changed rule polygon, not an expanded acceptance mask.
"""
from pathlib import Path
p=Path(__file__).parent;src=p/'propose_CORE_literal_antipad_join_r01.py';text=src.read_text()
old="CORE='/CORE_1V2';BOUNDS=(40.63,49.43,40.77,49.73)";new="CORE='/CORE_1V2';BOUNDS=(39.912499,48.775,41.175,50.6)"
assert text.count(old)==1;text=text.replace(old,new).replace("'-r02'","'-r03'")
text=text.replace("UID='2bfc40b8-8d35-4887-939a-a660cb92e0c9'","UID='c052f4ee-df74-43b5-9147-fb73d1f5a408'")
text=text.replace("literal_bounds_mm=BOUNDS,","literal_bounds_mm=BOUNDS,actual_existing_antipad_bounding_box_mm=[40.012499,48.875,41.075,50.5],actual_added_collar_mm=.10,native_zone_minimum_feature_width_mm=.20,")
(p/'propose_CORE_complete_two_barrel_collar_r03.py').write_text(text)
