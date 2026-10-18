"""Frozen exact R353 independent qualification; all failures remain diagnostic."""
from pathlib import Path
H=Path(__file__).resolve().parent.parent
p=H/'sbc-power/audit_CM79_R350_fresh_all_source_contact_native_reference_r351.py'
s=p.read_text(encoding='utf-8').replace('r350','r353').replace('R350','R353').replace('r351','r354').replace('R351','R354')
s=s.replace("boundReceipt=sha(p/'receipt.json');", "boundReceipt=sha(p/'receipt.json');assert boundReceipt=='d3319ca84f15cfd10f74a69623466e6ffdae0a65a5a6051dcf80af80718f6477';assert sha(p/'model.pkl')=='de8e2af4143fe43491773e0e0339c39efb17cb1660072bf37ffc6a22c155255e';")
# Let the generated inner audit reuse each exact bank union after it is computed.
s=s.replace("exec(compile(s,str(__file__),'exec'))", "s=s.replace('sources=[];refs=[];literal=[]','sources=[];refs=[];literal=[];refBanks={}').replace(\"nr={ly:zero(sh)for ly,sh in K.source_refs(nn).items()};ll,pf=RF.audit\",\"nr={ly:zero(sh)for ly,sh in K.source_refs(nn).items()};refBanks[net]=(ar,nr);ll,pf=RF.audit\").replace(\"ab=K.root(oldgroups[bank],rootref,pin);an=K.root(groups[bank],rootref,pin);ar={ly:zero(sh)for ly,sh in K.source_refs(ab).items()};nr={ly:zero(sh)for ly,sh in K.source_refs(an).items()}\",\"ar,nr=refBanks[bank]\").replace(\"lgrefs={ly:zero(sh)for ly,sh in K.source_refs(lg).items()}\",\"lgrefs=refBanks['/LOGIC_GND'][1]\")\nexec(compile(s,str(__file__),'exec'))")
exec(compile(s,str(__file__),'exec'))
