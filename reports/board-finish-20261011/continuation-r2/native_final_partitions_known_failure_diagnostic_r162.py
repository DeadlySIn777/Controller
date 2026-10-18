"""Full native diagnostic, preserving every original retained via's actual mask.

The exact R2 fill/Cu/partition/geometry algorithm remains frozen. Flash failures
are recorded as failures and permit the separate full CLI DRC to finish; a
discrete-Cu mismatch still aborts. This is never an adoption or production gate.
"""
from pathlib import Path
import hashlib
H=Path(__file__).resolve().parent
source=H/'native_final_partitions_contract_r2.py'
code=source.read_text()
needle="manager=pcbnew.GetSettingsManager();assert manager.LoadProject(str(board_path.with_suffix('.kicad_pro')))"
extra="""parent=Path('"""+str(H/'sbc-native-contract-r1/copy/board.kicad_pcb').replace('\\','/')+"""')
assert sha(parent)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a'
pins[str(parent.resolve())]=sha(parent)
pins[str(Path('"""+str(source).replace('\\','/')+"""').resolve())]=sha(Path('"""+str(source).replace('\\','/')+"""'))
old=pcbnew.LoadBoard(str(parent));oldstack=list(old.GetEnabledLayers().CuStack())
oldmasks={str(t.m_Uuid.AsString()):[str(old.GetLayerName(l))for l in oldstack if t.FlashLayer(l)]for t in old.GetTracks()if isinstance(t,pcbnew.PCB_VIA)and str(t.m_Uuid.AsString())in e['copper']}
assert oldmasks and all(e['copper'][uid]['kind']=='via'for uid in oldmasks)
oldmaskfile=out.parent/'original-parent-retained-via-actual-flash-masks.json'
assert not oldmaskfile.exists()
put(oldmaskfile,{'parent_sha256':sha(parent),'candidate_sha256':sha(board_path),'retained_original_via_masks':oldmasks,'read_only_original_cached_native_mask_no_fill':True,'no_removed_original_is_credited':True})
del old
"""
assert code.count(needle)==1;code=code.replace(needle,extra+needle)
needle="all6=[str(b.GetLayerName(l))for l in stack]"
extra="""for uid,required in oldmasks.items():
 missing=set(required)-set(flashes[uid])
 if missing:errors.append({'uuid':uid,'missing_original_parent_actual_flashes':sorted(missing),'actual_flashes':flashes[uid]})
"""
assert code.count(needle)==1;code=code.replace(needle,extra+needle)
needle="put(out.parent/'actual-full-refill-contract.json',r);print"
extra="""r.update(original_parent_retained_via_mask_count=len(oldmasks),original_parent_retained_via_mask_file=str(oldmaskfile),original_parent_retained_via_mask_sha256=sha(oldmaskfile),explicit_known_failed_reference_diagnostic_only=True,manufacturing_ready=False)
"""
assert code.count(needle)==1;code=code.replace(needle,extra+needle)
needle="raise SystemExit(1 if errors else 0)"
replacement="""# All raw failures stay in the contract. A diagnostic continues to full DRC
# only if every failure is a mask failure and exact discrete Cu still matches.
flash_only=all(any(k in row for k in ('missing_required_old_native_flashes','new_ordinary_actual_all6_flash_fail','missing_original_parent_actual_flashes'))for row in errors)
raise SystemExit(0 if flash_only else 1)"""
assert code.count(needle)==1;code=code.replace(needle,replacement)
compile(code,str(source),'exec');exec(compile(code,str(source),'exec'))
