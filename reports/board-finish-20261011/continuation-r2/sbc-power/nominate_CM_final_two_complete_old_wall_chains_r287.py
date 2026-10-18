"""Complete .20 native wall-chain restoration, retain real terminal contacts."""
from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'nominate_CM_final_two_coupled_actual_old_walls_r285.py').read_text()
s=s.replace('CM-final-two-coupled-actual-old-wall-fullwidth-nominations-r285','CM-final-two-complete-actual-old-wall-chain-fullwidth-nominations-r287')
old="rm={t['uuid']for t in walls};anchors=[(pt,max(t['w'],.2)/2)for t in walls for pt in(t['a'],t['b'])];candidate="
new="""rm={t['uuid']for t in walls};degree=__import__('collections').Counter(tuple(pt)for t in walls for pt in(t['a'],t['b']));ends=[list(pt)for pt,n in degree.items()if n==1];anchors=[(pt,.1)for pt in ends];candidate="""
assert s.count(old)==1;s=s.replace(old,new)
s=s.replace("attempts.append(candidate)\n    if any", "attempts.append(candidate)\n    if len(ends)!=2 or any(n>2 for n in degree.values()):candidate['failure']='Selected native walls are not one complete two-terminal chain';continue\n    if any")
old="sf=free(net,clip,rm,extra=extras);replacements=[];errors=[]\n       for old in walls:"
new="""replacements=[];errors=[];sf=None
       for wr in(8.,16.,25.,40.):
        wc=box(ps.x-wr,ps.y-wr,ps.x+wr,ps.y+wr);test=free(net,wc,rm,extra=extras)
        if any(f.covers(Point(ends[0]))and f.covers(Point(ends[1]))for f in RF.parts(test)):sf=test;break
       if sf is None:candidate['paired_chain_failure']='No exact .20 complete-chain F face in8/16/25/40mm';continue
       chain={'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'CM-R287-complete-wall-chain:'+','.join(sorted(rm)))),'net':net,'w':.2,'layer':'F.Cu','a':ends[0],'b':ends[1]}
       for old in[chain]:"""
assert s.count(old)==1;s=s.replace(old,new)
s=s.replace("'all_retained_old_signal_physical_layer_contacts_loss_count':len(loss)", "'all_retained_old_signal_physical_layer_contacts_loss_count':len(loss),'only_deleted_chain_internal_nodes_need_not_be_recreated':True,'complete_old_chain_real_terminal_coords_mm':ends")
s=s.replace('R285','R287')
exec(compile(s,str(__file__),'exec'))
