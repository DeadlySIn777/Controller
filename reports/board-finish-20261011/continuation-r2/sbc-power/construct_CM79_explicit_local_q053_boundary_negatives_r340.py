"""R338 successor with individually bound q053 owned-boundary negatives."""
from pathlib import Path
P=Path(__file__).resolve().parent
t=(P/'construct_CM79_exact_R333_larger_port_q053_local_current_r338.py').read_text(encoding='utf-8').replace('diagnostic-r338','diagnostic-explicit-owner-boundary-r340').replace('R338','R340')
needle="exec(compile(s,str(__file__),'exec'))"
assert t.count(needle)==1
extra='''diagnosis=H/'sbc-power/q053-R338-raw-gain-controlling-edge-and-declared-corridor-attribution-r339/receipt.json';assert sha(diagnosis)=='c9d0fac1b6e01d61b7c732952c12557b4fe3e8ff1bcb95a7d3ddba4e7ee5bf91';diag=json.loads(diagnosis.read_text());assert diag['reserve_outside_declared_owner_corridor']['empty'];put(O/'q053-exact-controlling-intersection-negative-scope-authority.json',{'frozen_R339_readonly_receipt_sha256':sha(diagnosis),'raw_gain_bounds_mm':diag['q053_failed_nm_grid_raw_gain']['bounds'],'only_owned_q053_local_boundary_redesign':True,'entire_explicit_negative_source_scope_mm':[116,169,139,208],'no_native_or_electrical_clearance_or_magnitude_waiver':True,'full_old_source_contact_reference_current_mesh_native':'OPEN'});'''
# Install that authority after O is created, before any geometry is changed.
replacement="""s=s.replace("scope=normalScopes.get(key);assert scope is not None;outsideReserve=zero(reserve).difference(zero(Z.bounded_buffer(scope,.0002)));", "scope=normalScopes.get(key);assert scope is not None;ownedBoundary=key.startswith('053e747d-d229-5488-b123-0bd7612fb8ef-');allowedNegativeScope=localCorridor if ownedBoundary else zero(Z.bounded_buffer(scope,.0002));outsideReserve=zero(reserve).difference(allowedNegativeScope);")
s=s.replace("negativeScope=zero(Z.bounded_buffer(normal,.0002));", "negativeScope=localCorridor if z['uuid']=='053e747d-d229-5488-b123-0bd7612fb8ef'else zero(Z.bounded_buffer(normal,.0002));")
s=s.replace("outsideMask=zero(mask).difference(zero(Z.bounded_buffer(normalScopes[z['uuid']+'-inside-intent-'+str(it)],.0002)));", "allowedInsideScope=localCorridor if z['uuid']=='053e747d-d229-5488-b123-0bd7612fb8ef'else zero(Z.bounded_buffer(normalScopes[z['uuid']+'-inside-intent-'+str(it)],.0002));outsideMask=zero(mask).difference(allowedInsideScope);")
s=s.replace("sourceScope=zero(Z.bounded_buffer(zero(unary_union(cuts)),.0002));", "sourceScope=localCorridor if z['uuid']=='053e747d-d229-5488-b123-0bd7612fb8ef'and l=='In2.Cu'else zero(Z.bounded_buffer(zero(unary_union(cuts)),.0002));")
s=s.replace("oldq={z['uuid']:z for z in q};", "oldq={z['uuid']:z for z in q};originalSettings={z['uuid']:{k:v for k,v in z.items()if k not in('shape','zone_outline_shape')}for z in q0};")
s=s.replace("{k:v for k,v in oldq[z['uuid']].items()if k not in('shape','zone_outline_shape')}", "originalSettings[z['uuid']]")
s=s.replace("roles=[];masks=[];changed=set()", "AUTHORITYroles=[];masks=[];changed=set()".replace('AUTHORITY',AUTHORITY))
exec(compile(s,str(__file__),'exec'))""".replace('AUTHORITY',repr(extra)[1:-1])
# Preserve actual newlines in the inserted executable block, not literal \n.
replacement=replacement.replace("repr(extra)[1:-1]",'') if False else replacement
# Inject authority as a separate exact source splice; repr is source quoting,
# never shell quoting or an executed command string.
replacement=replacement.replace("s=s.replace(\"roles=[];masks=[];changed=set()\", \""+repr(extra)[1:-1]+"roles=[];masks=[];changed=set()\".replace('"+repr(extra)[1:-1]+"',"+repr(extra)[1:-1]+"))\n", "s=s.replace('roles=[];masks=[];changed=set()',"+repr(extra+'roles=[];masks=[];changed=set()')+")\n")
t=t.replace(needle,replacement)
exec(compile(t,str(__file__),'exec'))
