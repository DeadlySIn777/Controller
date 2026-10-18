import json
import core_lane_r2 as R
def main():
    g,h,*_=R.model();refs={'U11012','C11061','C11062','C11063','C15001','C15002','R11022','C11088'}
    for ref in sorted(refs):print(ref,json.dumps([{'num':r['num'],'net':r['net'],'at':[r['x'],r['y']]} for r in h['pads'] if r['ref']==ref]))
if __name__=='__main__':main()
