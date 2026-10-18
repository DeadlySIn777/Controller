"""Keep Q0 on In3 while moving only unaccepted SENSE transport to In2."""
from pathlib import Path
H=Path(__file__).resolve().parent;base=H/'construct_Q0_separated_ports_actual_source_coupled_r424.py'
code=base.read_text().replace('Q0-separated-ports-actual-source-coupled-r424','Q0-SENSE-In2-Q0-In3-coupled-r426')
old="exec(compile(code,str(base),'exec'))"
new="""oldSenseLine="senseIn3=route_attachments('SENSE-In3-transport-to-retained-barrel-new-natural-In3-annulus',SENSE,'In3.Cu',senseRef,Point(senseSrc['x'],senseSrc['y']),Point(oldSense['x'],oldSense['y']),tracks,qualified_new_own=senseOwn.union(oldSenseOwn))"
newSenseLine="oldSenseIn1Own,oldSenseIn1Ledger=namespace['support_SENSE'](K,current,{**h,'vias':h['vias']+newvias},trueRoot,iv,oldSense,GND,SENSE,'In1.Cu');put(out/'retained-SENSE-In2-identity-bound-own-support.json',oldSenseIn1Ledger)\\nsenseIn1Own=newOwn(senseSrc,'In1.Cu');senseIn1Ref=refs['In1.Cu'].union(senseIn1Own).union(oldSenseIn1Own)\\nsenseIn3=route_attachments('SENSE-In2-transport-to-retained-barrel-new-natural-In2-annulus',SENSE,'In2.Cu',senseIn1Ref,Point(senseSrc['x'],senseSrc['y']),Point(oldSense['x'],oldSense['y']),tracks,qualified_new_own=senseIn1Own.union(oldSenseIn1Own))"
assert oldSenseLine in code;code=code.replace(oldSenseLine,newSenseLine).replace("'SENSE_In3':senseIn3","'SENSE_In2':senseIn3").replace("'retained_SENSE_prospective_additional_mask':['In3.Cu']","'retained_SENSE_prospective_additional_mask':['In2.Cu']").replace("'new_natural_flash_to_attest':['In3.Cu']","'new_natural_flash_to_attest':['In2.Cu']").replace('natural_required_old_F_B_plus_new_In3_annuli','natural_required_old_F_B_plus_new_In2_annuli')
exec(compile(code,str(base),'exec'))"""
assert old in code;code=code.replace(old,new,1);exec(compile(code,str(base),'exec'))
