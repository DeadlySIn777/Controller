"""Continue preserved REG feeds on exact current root geometry/ownership."""
from pathlib import Path
p=Path(__file__).resolve().parent
s=(p/'construct_regulated_lazy_feeds_r105.py').read_text().replace('regulated-lazy-source-feeds-r105','regulated-native-bound-lazy-source-feeds-r112').replace('corrected-regulated-joint-search-base-r106','corrected-regulated-native-bound-search-base-r111').replace('controller-regulated-r105/','controller-regulated-r112/')
exec(compile(s,str(p/'construct_regulated_lazy_feeds_r105.py'),'exec'))
