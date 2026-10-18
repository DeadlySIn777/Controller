from pathlib import Path
p=Path(__file__).parent
s=(p/'reconcile-root78-validation-r01.py').read_text()
s=s.replace("rows=lambda r:collections.Counter(json.dumps(dict(sheet=s['path'],uuid_path=s['uuid_path'],violation=v),sort_keys=True)for s in r['sheets']for v in s['violations'])\nassert rows(erc)==rows(prior) and not erc['ignored_checks']",'''repeat=read(h/'native-erc-repeat.json')
def rows(report):
 out=[]
 for sheet in report['sheets']:
  for original in sheet['violations']:
   v=json.loads(json.dumps(original))
   if v['type']in ['ground_pin_not_ground','pin_to_pin']:
    for item in v['items']:
     assert re.match(r'Symbol \\S+ Pin \\S+ \\[',item['description'])
     item.pop('uuid')
   out.append(json.dumps(dict(sheet=sheet['path'],uuid_path=sheet['uuid_path'],violation=v),sort_keys=True))
 return collections.Counter(out)
raw=lambda r:collections.Counter(json.dumps(v,sort_keys=True)for sheet in r['sheets']for v in sheet['violations'])
assert len(raw(erc)-raw(repeat))==26
assert rows(erc)==rows(repeat)==rows(prior) and not erc['ignored_checks']and not repeat['ignored_checks']''')
s=s.replace("h/'native-erc.json',priorpath", "h/'native-erc.json',h/'native-erc-repeat.json',priorpath")
s=s.replace('exact_prior_source26_warning_dispositions_preserved=True,','exact_prior_source26_warning_dispositions_preserved=True,transient_pin_UUIDs_reissued_in_26_violations_on_identical_source_repeat=True,all_sheet_ids_pin_identities_positions_descriptions_types_and_severities_retained=True,')
(p/'reconcile-root78-validation-r02.py').write_text(s)
