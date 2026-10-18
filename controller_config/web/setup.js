"use strict";
const token = document.querySelector('meta[name="setup-token"]').content;
const $ = id => document.getElementById(id);
let context, draft, plan, commitPayload, commitRequest, step = 0, revision = 0, dirty = 0, saved = 0, timer, busy = false, savePromise;
let diagnosticReport, diagnosticExample = false;
let readinessReport, selfCheckReceipt, importReview, backupFile, backupSource="active", intakeText="", intakeResult;
let renderedStep;
const fields = [
  ["motor_steps_per_revolution", "Motor full steps / revolution", "200"],
  ["microsteps", "Drive microstep setting", "16"],
  ["gear_motor_revolutions", "Ratio · motor revolutions", "1"],
  ["gear_load_revolutions", "Ratio · load revolutions", "1"],
  ["travel_per_load_revolution", "Travel / load revolution", "5"],
  ["max_velocity_units_per_second", "Maximum velocity / second", "10"]
];
function node(tag, text, className) { const n = document.createElement(tag); if(text !== undefined) n.textContent=text; if(className) n.className=className; return n; }
function button(text, fn, cls="secondary") { const b=node("button",text,cls);b.type="button";b.dataset.focusKey="action:"+text;b.addEventListener("click",()=>guard(fn));return b; }
function scrollBehavior(){return window.matchMedia("(prefers-reduced-motion: reduce)").matches?"auto":"smooth";}
function captureFocus(){const element=document.activeElement;if(!element||element===document.body)return null;return {element,id:element.id,key:element.dataset.focusKey};}
function focusHeading(){ $("page-title").focus({preventScroll:true});window.scrollTo({top:0,behavior:scrollBehavior()}); }
function restoreFocus(savedFocus){
  if(!savedFocus)return;
  const element=savedFocus.element.isConnected?savedFocus.element:savedFocus.id?$(savedFocus.id):savedFocus.key?document.querySelector(`[data-focus-key="${CSS.escape(savedFocus.key)}"]`):null;
  if(element&&!element.disabled&&!element.closest("[hidden]"))element.focus({preventScroll:true});
  else $("page-title").focus({preventScroll:true});
}
function notice(error) { $("notice").hidden=false;$("notice").textContent=error.message||String(error);$("notice").scrollIntoView({behavior:scrollBehavior(),block:"start"}); }
async function request(path, data) {
  const options={headers:{"X-Setup-Token":token}};
  if(data!==undefined){options.method="POST";options.headers["Content-Type"]="application/json";options.body=JSON.stringify(data);}
  const response=await fetch("/api/"+path,options);
  const result=await response.json();
  if(!response.ok||!result.ok) throw Error(`${result.error?.message||"Unable to load setup"}${result.error?.path ? " · "+result.error.path : ""} [${result.error?.code||response.status}]`);
  if(path==="preview"||path==="restore"){if(typeof result.commit_payload!=="string")throw Error("The server must be updated before this review can be saved.");commitPayload=result.commit_payload;}
  return result.result;
}
async function guard(fn){
  if(busy)return;
  const previousFocus=captureFocus(),previousStep=step;
  busy=true;$("notice").hidden=true;$("content").setAttribute("aria-busy","true");
  document.querySelectorAll("button,input,select,textarea").forEach(b=>b.disabled=true);
  try{await fn();}catch(e){notice(e);}finally{
    busy=false;document.querySelectorAll("button,input,select,textarea").forEach(b=>b.disabled=!context);
    $("content").setAttribute("aria-busy","false");
    if(previousStep!==step)focusHeading();else restoreFocus(previousFocus);
  }
}
async function refresh(){
  const fresh=await request("context"),changedBinding=context&&JSON.stringify(context.setup.draft_binding)!==JSON.stringify(fresh.setup.draft_binding);
  if(changedBinding&&dirty>saved)throw Error("Another client changed this setup. Your local answers are preserved; inspect the current saved draft before editing it.");
  if(context&&dirty===saved&&changedBinding){draft=fresh.setup.draft?structuredClone(fresh.setup.draft):null;plan=null;commitPayload=null;commitRequest=null;importReview=null;selfCheckReceipt=null;}
  context=fresh;revision=context.setup.current_revision??context.setup.revision??0;updateMeta();
}
async function refreshBudget(){const fresh=await request("context");for(const key of ["budget","budget_error","paid_ai_enabled","paid_ai"])context[key]=fresh[key];updateMeta();}
function updateMeta(){
  const b=context?.budget,spent=b?.spent_microdollars||0,held=b?.outstanding_microdollars||0,cap=b?.cap_microdollars??15000000;
  $("budget-value").textContent=`$${(spent/1e6).toFixed(2)} / $${(cap/1e6).toFixed(2)}`;
  $("budget-held").textContent=held?`$${(held/1e6).toFixed(4)} reserved pending billing reconciliation`:"No reserved charges";
  $("budget-meter").style.width=`${(cap===0?0:Math.min(100,(spent+held)/cap*100))}%`;
  $("paid-panel").hidden=!context?.paid_ai_enabled;
  $("budget-note").textContent=context?.paid_ai_enabled?"Paid extraction uses the configured bounded request. Reserved amounts stay unavailable until billing is reconciled. Local setup uses no credits.":"Optional paid AI is not connected. Local calculations, saving and recovery use no credits.";
  if(context?.budget_error){$("budget-value").textContent="Unavailable";$("budget-held").textContent="Paid advice is blocked";$("budget-note").textContent="The allowance needs reconciliation. Your offline setup remains available; the budget file was preserved.";}
  $("save-state").textContent=dirty>saved?"Saving changes…":context?.setup.initialized?`Saved · revision ${revision}`:"Not started";
}
function changed(){dirty++;plan=null;commitPayload=null;commitRequest=null;importReview=null;selfCheckReceipt=null;readinessReport=null;updateMeta();updateGuide();updateValidationIssues();clearTimeout(timer);timer=setTimeout(()=>flush().catch(e=>{$("save-state").textContent="Not saved";notice(e);}),650);}
async function flush(){
  clearTimeout(timer);
  if(savePromise)return savePromise;
  if(!draft||dirty===saved)return;
  savePromise=(async()=>{
    while(dirty>saved){
      if(!context.setup.initialized){const initialized=await request("initialize",{});if(initialized.draft)throw Error("Another client started this setup. Your local answers are unchanged; reload to inspect the saved draft before editing it.");context.setup=initialized;revision=initialized.current_revision;await refreshBudget();}
      const version=dirty,value=structuredClone(draft);
      if(!context.setup.draft_binding)throw Error("Reload the updated setup service before saving. Your local answers are preserved.");
      const status=await request("save",{draft:value,expected_revision:revision,expected_binding:context.setup.draft_binding});
      revision=status.current_revision??status.revision;context.setup=status;saved=version;updateMeta();updateGuide();updateValidationIssues();
    }
  })();
  try{await savePromise;}finally{savePromise=null;}
}
function updateGuide(){const validation=dirty===saved?context?.setup.validation:null;const missing=validation?.missing_facts||[],blockers=validation?.blockers||[],issues=[...blockers,...missing];$("guide-summary").textContent=dirty>saved?"Your latest changes are waiting for validation.":!validation?"Choose your starting profile, then enter the mechanics you know. Unknown values stay unanswered.":blockers.length?`${blockers.length} configuration checks need attention before review.`:missing.length?`${missing.length} details still need an answer. We keep the answers you’ve already saved.`:"Your saved details are ready for backend review. Physical wiring and commissioning still need independent verification.";$("guide-items").replaceChildren();issues.slice(0,3).forEach(x=>$("guide-items").append(node("div",x.message||x.path,"missing")));if(issues.length>3)$("guide-items").append(node("small",`+ ${issues.length-3} more in Drive details`));}
function fieldId(path){return "setup-field-"+path.replace(/[^a-zA-Z0-9_-]/g,"-");}
function bindField(input,path){input.id=fieldId(path);input.dataset.fieldPath=path;input.dataset.focusKey="field:"+path;}
function ownerPath(owner){for(const name of ["motors","inputs","outputs","encoders"]){const index=draft?.[name]?.indexOf(owner);if(index>=0)return `$.${name}[${index}]`;}return null;}
function updateValidationIssues(){
  if(step!==1)return;
  document.querySelectorAll("[data-field-path]").forEach(input=>{input.removeAttribute("aria-invalid");input.removeAttribute("aria-describedby");});
  document.querySelectorAll(".field-error").forEach(error=>error.remove());
  let details=$("validation-issues");
  if(!details){const intro=$("content").querySelector(".panel");if(!intro)return;details=node("details",undefined,"optional");details.id="validation-issues";intro.append(details);}
  const wasOpen=details.open;details.replaceChildren();
  if(dirty>saved){details.hidden=false;details.append(node("summary","Latest edits await validation"),node("p","Previous checks are out of date. New checks appear after these edits are saved.","description"));return;}
  const validation=context?.setup.validation,issues=[...(validation?.blockers||[]),...(validation?.missing_facts||[])];
  details.hidden=!issues.length;if(!issues.length)return;
  details.append(node("summary",`Review all ${issues.length} details that need attention`));
  const list=node("ul",undefined,"validation-list");
  for(const [index,issue] of issues.entries()){
    const item=node("li"),input=$(fieldId(issue.path));
    if(input){
      const link=node("a",issue.message);link.href="#"+input.id;link.addEventListener("click",event=>{event.preventDefault();for(let ancestor=input.parentElement;ancestor;ancestor=ancestor.parentElement)if(ancestor.tagName==="DETAILS")ancestor.open=true;input.focus({preventScroll:true});input.scrollIntoView({behavior:scrollBehavior(),block:"center"});});item.append(link);
      const errorId="setup-field-error-"+index,error=node("small",issue.message,"field-error");error.id=errorId;input.parentElement.append(error);input.setAttribute("aria-invalid","true");input.setAttribute("aria-describedby",[input.getAttribute("aria-describedby"),errorId].filter(Boolean).join(" "));
    }else item.append(node("span",issue.message+(issue.path?" · "+issue.path:"")));
    list.append(item);
  }
  details.append(list);details.open=wasOpen||Boolean(validation?.blockers?.length);
}
const titles=["Set up your machine","Tell us about your drives","Review before you save","A setup you can come back to","Understand what happened","Know exactly what’s ready"];
const descriptions=["Choose a starting point. We’ll keep the details together and check every change.","Enter the known mechanics. The service calculates scales and checks timing limits.","See the calculated settings, illustrative wiring and exact changes together.","Your configuration is saved. Position, homing and motion authority are never restored.","Saved observations, useful checks and a portable support report. No AI credits needed.","Evidence for this revision, the next useful step and a configuration self-check. Physical commissioning stays explicit."];
function render(){
  const previousFocus=captureFocus(),pageChanged=renderedStep!==undefined&&renderedStep!==step;
  document.querySelectorAll("[data-step]").forEach(b=>{b.classList.toggle("selected",Number(b.dataset.step)===step);b.setAttribute("aria-current",Number(b.dataset.step)===step?"page":"false");});
  $("workspace-section").textContent=step===4?"DIAGNOSTICS":step===5?"READINESS":"SETUP";
  document.querySelector(".intro .eyebrow").textContent=step===4?"RECORDS WITHOUT GUESSWORK":step===5?"EVIDENCE BEFORE CONFIDENCE":"A GOOD SETUP STARTS HERE";
  $("footer-note").textContent=step>=4?"Configuration checks and records stay local. No machine commands or paid requests are sent.":"Progress is saved locally. Only a reviewed setup becomes a saved generation.";
  $("page-title").textContent=titles[step];$("page-description").textContent=descriptions[step];$("content").replaceChildren();
  document.querySelector(".workspace").classList.toggle("diagnostic-layout",step>=4);
  $("back").hidden=step===0||step>=4;$("next").hidden=step>=3;$("next").textContent=["Continue to drive details →","Check my setup →","Save reviewed setup →","","",""][step];
  [renderMachine,()=>{renderIntake();renderDrives();renderConnections();},renderReview,()=>{renderSaved();renderBackupImport();},renderDiagnostics,renderReadiness][step]();
  updateGuide();updateValidationIssues();renderedStep=step;if(!busy){if(pageChanged)focusHeading();else restoreFocus(previousFocus);}
}

function renderIntake(){
  if(!draft)return;
  const p=panel("Tell it once. Keep the evidence.","Paste explicit motor facts. Supported statements are interpreted locally, without API credits. Unclear or conflicting details stay unanswered.");
  const details=node("details",undefined,"optional");details.open=Boolean(intakeText);details.append(node("summary","Enter facts in your own words · $0.00"));
  const label=node("label","Motor facts"),input=node("textarea");input.id="local-facts";input.rows=6;input.maxLength=12000;input.value=intakeText;input.placeholder="Motor m0 has 200 full steps per revolution\nMotor m0 microsteps = 16\nMotor m0 travel_per_load_revolution = 5 mm";input.addEventListener("input",()=>{intakeText=input.value;intakeResult=null;$("local-intake-result").replaceChildren();});label.append(input);details.append(label);
  details.append(node("p",`Use the logical motor ID: ${draft.motors.map(m=>`${m.id} (${m.axis.toUpperCase()}, ${m.resource}, ${m.unit})`).join(" · ")}. Travel and velocity require each motor’s configured units.`,"description"));
  details.append(button("Interpret facts locally",async()=>{await flush();intakeResult=await request("local_intake",{facts:intakeText,expected_revision:revision});render();}));
  const target=node("div");target.id="local-intake-result";target.setAttribute("role","status");
  if(intakeResult){
    target.append(node("p",`${intakeResult.accepted_facts.length} supported facts · ${intakeResult.conflicts.length} conflicts · ${intakeResult.unknowns.length} unsupported statements. Nothing has been added to your draft.`));
    for(const fact of intakeResult.accepted_facts){const row=node("div",undefined,"intake-fact");row.append(node("strong",`${fact.logical_motor_id} · ${fact.path.split(".").at(-1).replaceAll("_"," ")} = ${fact.value}${fact.unit?" "+fact.unit:""}`),node("p",`Source: “${fact.source_quote}”`,"description"));target.append(row);}
    for(const issue of intakeResult.conflicts)target.append(node("div",`${issue.message}${issue.path?" · "+issue.path:""}`,"missing"));
    if(intakeResult.unknowns.length)showData(target,"Statements that need clarification",intakeResult.unknowns);
    if(intakeResult.accepted_facts.length)target.append(button("Add reviewed local facts to draft",async()=>{
      await flush();await refresh();const binding=intakeResult.configuration_binding;
      if(revision!==binding.revision||context.setup.store_id!==binding.store_id||context.setup.epoch!==binding.epoch)throw Error("The draft changed after interpretation. Your source text is preserved; interpret it again against the current draft.");
      draft=structuredClone(intakeResult.proposed_draft);intakeResult=null;changed();await flush();render();
    },"primary"));
  }
  details.append(target);p.append(details);
}

function renderReadiness(){
  const report=readinessReport;
  if(!report){panel("Readiness is unavailable","Refresh this view to load the checks for your saved configuration.").append(button("Refresh readiness",async()=>{readinessReport=await request("readiness");render();}));return;}
  const p=panel(report.simulation_configuration_ready?"Simulation configuration ready":"Your next setup step",report.next_step?.action||"The current draft matches its reviewed generation. Physical commissioning remains unavailable here.");
  if(report.configuration_binding)p.append(node("span",`Generation ${report.configuration_binding.generation} · revision ${report.configuration_binding.revision}`,"pill"));
  if(report.simulation_configuration_ready)p.append(button("Run configuration self-check",async()=>{await flush();selfCheckReceipt=await request("readiness_rehearsal",{expected_revision:revision});readinessReport=await request("readiness");render();},"primary"));
  if(selfCheckReceipt&&report.configuration_binding&&selfCheckReceipt.configuration_binding.revision===report.configuration_binding.revision&&selfCheckReceipt.configuration_binding.epoch===report.configuration_binding.epoch&&selfCheckReceipt.configuration_binding.store_id===report.configuration_binding.store_id)p.append(node("p",`${selfCheckReceipt.passed?"Configuration self-check passed":"Self-check needs attention"} · ${selfCheckReceipt.motor_count} motors · 0 API calls. Detailed receipt below.`,"description"));
  if(report.next_step?.ui_step!==null&&report.next_step)p.append(button("Continue setup",()=>navigate(report.next_step.ui_step),"primary"));
  p.append(node("div","Physical machine readiness: unverified. There is no live hardware connection, motion test or authority to enable outputs.","info"));
  const labels={pass:"Verified in this scope",pending:"Needs setup",blocked:"Needs attention",unavailable:"Unavailable here"};
  const checklist=node("div",undefined,"readiness-checks");$("content").append(checklist);
  for(const check of report.checks){const card=panel(check.title,check.action);card.classList.add("readiness-card");card.append(node("span",labels[check.status]||check.status,`readiness-status ${check.status}`));if(typeof check.evidence==="string")card.append(node("p",check.evidence,"description"));else showData(card,"Inspect the exact evidence",check.evidence);if(check.ui_step!==null)card.append(button("Open "+check.title,()=>navigate(check.ui_step)));checklist.append(card);}
  const self=panel("Check this saved configuration","Recompute every motor’s settings, exercise rejected timing and current selections, and verify an actual compressed backup roundtrip. This tests configuration and storage; it does not test a motion loop.");
  if(selfCheckReceipt){const binding=selfCheckReceipt.configuration_binding,current=report.configuration_binding;const currentReceipt=current&&binding.revision===current.revision&&binding.epoch===current.epoch&&binding.store_id===current.store_id&&binding.configuration_sha256===current.configuration_sha256;
    self.append(node("p",currentReceipt?`${selfCheckReceipt.passed?"All configuration checks passed":"Some checks need attention"} · ${selfCheckReceipt.motor_count} motors · 0 API calls`:"This result belongs to an older configuration. Run the self-check again.","description"));
    table(self,["Check","Result"],selfCheckReceipt.checks.map(check=>[check.id.replaceAll("_"," "),check.status]));showData(self,"Bound receipt and scope",selfCheckReceipt);
  }
  self.append(button("Refresh readiness",async()=>{await refresh();readinessReport=await request("readiness");render();}));
}

function renderBackupImport(){
  const p=panel("Recover from a compressed backup","Choose a local configuration backup. Inspect its checks and changes before saving a new generation. Importing restores no position or motion permission.");
  const label=node("label","Configuration backup (.tar.zst)"),input=node("input");input.type="file";input.id="backup-file";input.accept=".zst,.tar.zst,application/zstd";input.addEventListener("change",()=>{backupFile=input.files[0]||null;$("backup-selected").textContent=backupFile?`${backupFile.name} · ${(backupFile.size/1024).toFixed(1)} KB`:"No file selected";});label.append(input);p.append(label);
  const name=node("p",backupFile?`${backupFile.name} · ${(backupFile.size/1024).toFixed(1)} KB`:"No file selected","description");name.id="backup-selected";p.append(name);
  const source=node("label","Setup to review"),select=node("select");select.id="backup-source";for(const [value,title] of [["active","Reviewed saved generation"],["draft","Backup’s working draft"]]){const option=node("option",title);option.value=value;option.selected=backupSource===value;select.append(option);}select.addEventListener("change",()=>backupSource=select.value);source.append(select);p.append(source);
  p.append(button("Review backup",async()=>{
    if(!backupFile||backupFile.size===0||backupFile.size>8*1024*1024)throw Error("Choose a nonempty configuration backup no larger than 8 MiB.");
    await flush();const response=await fetch("/api/"+(backupSource==="draft"?"backup-draft-preview":"backup-preview"),{method:"POST",headers:{"X-Setup-Token":token,"Content-Type":"application/zstd"},body:backupFile});const value=await response.json();
    if(!response.ok||!value.ok)throw Error(`${value.error?.message||"Unable to inspect backup"} [${value.error?.code||response.status}]`);
    if(typeof value.commit_payload!=="string")throw Error("The backup review has no original commit payload.");
    plan=value.result;commitPayload=value.commit_payload;commitRequest=null;importReview={filename:backupFile.name,source:backupSource};step=2;render();
  },"primary"));
  p.append(node("small","Maximum upload: 8 MiB. The archive is bounded and checked locally; files are never extracted or executed."));
}
function panel(title,description){const p=node("div",undefined,"panel");p.append(node("h2",title));if(description)p.append(node("p",description,"description"));$("content").append(p);return p;}
function renderMachine(){const p=panel("What are you setting up?","These profiles model the full IS-2 inventory in a disconnected workspace.");const grid=node("div",undefined,"machine-grid");Object.entries(context.profiles).forEach(([id,profile])=>{const chosen=draft?.profile_id===id;const b=button("",async()=>{if(draft?.profile_id===id)return;await flush();const previous=draft,retained=context.setup.retained_profile_drafts?.[id];draft=retained?structuredClone(retained):await request("template",{profile_id:id});if(previous){if(!retained&&previous.machine_name!==context.profiles[previous.profile_id]?.title)draft.machine_name=previous.machine_name;for(const key of ["inputs","outputs","encoders"])if(!retained)draft[key]=structuredClone(previous[key]);draft.motors.forEach((m,i)=>{const old=previous.motors[i];if(old){for(const key of [...fields.map(f=>f[0]),"unit","step_high_ns","step_low_ns","dir_setup_ns","dir_hold_ns","step_active_high","dir_inverted"])if(!retained||m[key]===null)m[key]=old[key];}});}changed();render();},`machine-card ${chosen?"chosen":""}`);b.dataset.focusKey="profile:"+id;b.setAttribute("aria-pressed",String(chosen));const icon=node("div");icon.innerHTML='<svg viewBox="0 0 70 46" aria-hidden="true"><path d="M6 39H64M12 36V8H58V36M12 15H58M26 16V26H44V16M35 26V34M17 36H53M6 40V44M64 40V44"/><path d="M29 7V3H41V7"/></svg>';b.append(icon,node("strong",profile.title.replace(/^Simulation |^Simulated |^Virtual /,"")),node("small",`${profile.motor_axes.length} assigned motors · all 12 remain available`));if(chosen)b.append(node("span","✓","check"));grid.append(b);});p.append(grid);if(draft){const label=node("label","Workspace name");const input=node("input");input.value=draft.machine_name;input.maxLength=120;bindField(input,"$.machine_name");input.addEventListener("input",()=>{draft.machine_name=input.value;changed();});label.style.marginTop="22px";label.append(input);p.append(label);}p.append(node("div","The 12 motors, 4 ABZ encoders, 24 inputs and 16 outputs are represented. Other IS-2 interfaces still need setup support. Connected equipment is not discovered here.","info"));}
function numberField(m,key,title,placeholder){const label=node("label",title);const input=node("input");input.type="number";input.step="any";input.inputMode="decimal";input.value=m[key]??"";input.placeholder=placeholder||"Required";input.setAttribute("aria-label",`${m.id||m.resource} ${title}`);bindField(input,ownerPath(m)+"."+key);input.addEventListener("input",()=>{m[key]=input.value===""?null:Number(input.value);changed();});label.append(input);return label;}
function renderDrives(){if(!draft){panel("Choose a machine first","Return to Machine to select a profile.");return;}const intro=panel("Keep the facts. Calculate the rest.","Use the values on your simulated drive and mechanics. A sample recipe is available to explore the workflow.");const actions=node("div",undefined,"twin");actions.append(button("Fill simulation example",()=>{for(const m of draft.motors){[200,16,1,1,5,10].forEach((v,i)=>m[fields[i][0]]=v);m.unit="mm";}changed();render();}),button("Copy first motor’s mechanics",()=>{const first=draft.motors[0];draft.motors.slice(1).forEach(m=>{fields.forEach(([key])=>m[key]=first[key]);m.unit=first.unit;});changed();render();}));intro.append(actions);draft.motors.forEach((m,index)=>{const p=panel("","");p.firstChild.remove();const head=node("div",undefined,"motor-head"),badge=node("div",undefined,"motor-badge");badge.append(node("div",`M${index+1}`,"motor-icon"));const text=node("div");text.append(node("h3",`${m.axis.toUpperCase()} motor`),node("small",`${m.resource} · ${m.equipment_profile}`));badge.append(text);head.append(badge,node("span","SIMULATION","pill"));p.append(head);const grid=node("div",undefined,"fields");fields.forEach(([key,title,placeholder])=>grid.append(numberField(m,key,title+(key.includes("travel")?` (${m.unit})`:key.includes("velocity")?` (${m.unit}/s)`:""),placeholder)));const unit=node("label","Distance unit"),select=node("select");bindField(select,ownerPath(m)+".unit");["mm","in"].forEach(u=>{const o=node("option",u);o.value=u;o.selected=m.unit===u;select.append(o);});select.addEventListener("change",()=>{const factor=m.unit==="mm"?1/25.4:25.4;for(const key of ["travel_per_load_revolution","max_velocity_units_per_second"])if(m[key]!==null)m[key]=Number((m[key]*factor).toPrecision(12));m.unit=select.value;changed();render();});unit.append(select);grid.append(unit);p.append(grid);const advanced=node("details",undefined,"optional");advanced.append(node("summary","Advanced · pulse and direction timing"));const timing=node("div",undefined,"fields");["step_high_ns","step_low_ns","dir_setup_ns","dir_hold_ns"].forEach(key=>timing.append(numberField(m,key,key.replaceAll("_"," "),"5000")));advanced.append(timing);p.append(advanced);});}
function showData(p,title,value){const details=node("details",undefined,"optional");details.append(node("summary",title));let loaded=false;details.addEventListener("toggle",()=>{if(details.open&&!loaded){details.append(node("pre",JSON.stringify(value,null,2)));loaded=true;}});p.append(details);}
function renderConnections(){
  if(!draft)return;
  const p=panel("Inputs, outputs and feedback","Optional assignments use the same checked resource catalog as the CLI. Unassigned resources remain available.");
  for(const [name,kind,title,equipment] of [["inputs","digital_input","Digital inputs","sim-24v-switch-v1"],["outputs","digital_output","Smart outputs","sim-smart-output-v1"],["encoders","abz","ABZ encoders","sim-abz-5v-v1"]]){
    const details=node("details",undefined,"optional");details.open=draft[name].length>0;details.append(node("summary",`${title} · ${draft[name].length} assigned`));
    const resources=context.capabilities.resources.filter(r=>r.kind===kind);
    draft[name].forEach((item,index)=>{
      const row=node("div",undefined,"connection"),grid=node("div",undefined,"fields");
      const label=node("label","Resource"),select=node("select");select.setAttribute("aria-label",`${title} ${index+1} resource`);bindField(select,`$.${name}[${index}].resource`);
      resources.forEach(r=>{const option=node("option",`${r.label} · ${r.id}`);option.value=r.id;option.selected=item.resource===r.id;select.append(option);});
      select.addEventListener("change",()=>{item.resource=select.value;changed();});label.append(select);grid.append(label);
      const role=node("label","Purpose"),input=node("input");input.value=item.role;input.maxLength=120;input.setAttribute("aria-label",`${title} ${index+1} purpose`);bindField(input,`$.${name}[${index}].role`);input.addEventListener("input",()=>{item.role=input.value;changed();});role.append(input);grid.append(role);
      if(name!=="encoders")grid.append(numberField(item,"voltage_v","Selected voltage (V)","24"));
      if(name==="outputs")grid.append(numberField(item,"current_a","Expected current (A)","0.1"));
      if(name==="encoders")grid.append(numberField(item,"counts_per_revolution","Decoded counts / revolution","Required"));
      const remove=button("Remove assignment",()=>{draft[name].splice(index,1);changed();render();});remove.dataset.focusKey=`remove:${name}:${item.resource}`;row.append(grid,remove);details.append(row);
    });
    details.append(button(`Add ${name==="encoders"?"encoder":name==="outputs"?"output":"input"}`,()=>{
      const resource=resources.find(r=>!draft[name].some(item=>item.resource===r.id));if(!resource)throw Error(`All ${title.toLowerCase()} are already assigned.`);
      const item={resource:resource.id,role:`${title} ${draft[name].length+1}`,equipment_profile:equipment};
      if(name!=="encoders")item.voltage_v=24;
      if(name==="outputs")item.current_a=0;
      if(name==="encoders")item.counts_per_revolution=null;
      draft[name].push(item);changed();render();
    }));p.append(details);
  }
  p.append(node("div","Outputs are limited to 0.5 A per channel and 2 A per group of four. These fields record selections; physical measurements remain pending.","info"));
}
function table(p,headers,rows){const wrap=node("div",undefined,"table-scroll"),t=node("table"),head=node("thead"),tr=node("tr");headers.forEach(h=>tr.append(node("th",h)));head.append(tr);t.append(head);const body=node("tbody");rows.forEach(values=>{const row=node("tr");values.forEach(value=>row.append(node("td",String(value))));body.append(row);});t.append(body);wrap.append(t);p.append(wrap);}
function renderReview(){
  if(!plan){panel("Check your saved drive details","Complete the required facts in Drive details, then choose Check my setup.");return;}
  const restoring=plan.operation==="restore",validation=plan.validation||{},candidate=validation.draft||plan.candidate||draft;
  const p=panel(importReview?"Review the imported backup":restoring?"Review the previous setup":"Configuration checks passed",importReview?`${importReview.filename} · ${importReview.source==="draft"?"working draft":"reviewed generation"}. Saving creates a reviewed generation in this workspace.`:restoring?"Restoring creates a new generation. Inspect the changes before saving.":"This is a configuration review. Physical checks remain pending.");
  const stats=node("div",undefined,"stat-line");[[candidate.motors.length,"assigned motors"],[12,"available motors"],["0","machine commands"]].forEach(([n,label])=>{const d=node("div");d.append(node("strong",String(n)),node("small",label));stats.append(d);});p.append(stats);
  const diff=panel("Changes to save",`${plan.changes?.length||0} changes against the saved generation.`);
  function summarize(value){if(value===null)return "Unspecified";if(typeof value!=="object")return String(value);if(value.motors)return `${value.machine_name} · ${value.motors.length} motors`;if(Array.isArray(value))return `${value.length} assignments`;return "Structured settings (see exact diff)";}
  function label(path){const parts=path.split("/").filter(Boolean);if(parts[0]==="motors"&&candidate.motors[Number(parts[1])])return `${candidate.motors[Number(parts[1])].id} · ${(parts[2]||"settings").replaceAll("_"," ")}`;return parts.join(" · ").replaceAll("_"," ")||"New machine configuration";}
  if(plan.changes?.length)table(diff,["Setting","Before","After"],plan.changes.slice(0,30).map(change=>[label(change.path),summarize(change.before),summarize(change.after)]));else diff.append(node("p","No configuration changes. The saved generation will be retained.","description"));
  if(plan.changes?.length>30)diff.append(node("p",`${plan.changes.length-30} more changes are included in the exact diff below.`));
  showData(diff,"Inspect the exact configuration diff",plan.changes);showData(diff,"All calculated values and checks",validation);
  p.append(node("h3","Calculated motion settings"));table(p,["Motor / axis","Scale","Required rate","Model ceiling"],(validation.calculations||[]).map(c=>[`${context.capabilities.resources.find(r=>r.id===c.resource)?.label||c.motor_id} · ${c.axis.toUpperCase()}`,`${c.steps_per_unit.toLocaleString()} steps/${c.unit}`,`${c.required_step_rate_hz.toLocaleString()} Hz`,`${c.maximum_simulation_rate_hz.toLocaleString()} Hz`]));
  const wiring=panel("Illustrative connections","Every motor keeps its individual enable and alarm. SIM terminals are examples only.");table(wiring,["Assignment","Resource","Terminals"],(validation.wiring||[]).map(w=>[w.owner,w.resource,w.terminals.join(" · ")]));
  p.append(node("div","All terminals begin with SIM. Do not wire physical equipment from these examples. Saving this configuration does not commission, home or arm a machine.","info"));
}
function renderSaved(){const active=context.setup.active;if(!active){panel("No committed setup yet","Complete the review to save a versioned setup. Your draft is retained.");return;}const p=panel("Your reviewed setup is saved",`Generation ${context.setup.generation} · revision ${revision}`);const mark=node("div","✓","saved-mark");p.prepend(mark);p.append(node("p",active.draft.machine_name||"Machine workspace"),node("div","You can close this page and resume later. Physical verification, homing and deliberate restart remain pending.","info"));const actions=node("div",undefined,"twin");actions.append(button("Edit saved setup",()=>{step=1;render();}),button("Export setup",download),button("Download compressed backup",()=>downloadPackage("config")));p.append(actions);const history=panel("Previous generations","Restore creates a new reviewed generation; it never restores machine permission.");(context.setup.history||[]).forEach(h=>{const row=node("div",undefined,"history");row.append(node("span",`Generation ${h.generation}`),button("Review restore",async()=>{plan=await request("restore",{generation:h.generation});commitRequest=null;step=2;render();}));history.append(row);});}
async function downloadPackage(kind,example=false){
  if(context.setup.initialized)await flush();
  const path=kind==="config"?"config-package":example?"example-package":"support-package";
  // Verify errors in the workbench before starting a native browser download.
  // The second GET uses a separate HttpOnly read-only download session;
  // the token stays out of the URL and no Blob download support is required.
  const response=await fetch("/api/"+path,{headers:{"X-Setup-Token":token}});
  if(!response.ok){const value=await response.json();throw Error(`${value.error?.message||"Unable to export package"} [${value.error?.code||response.status}]`);}
  await response.arrayBuffer();const a=node("a");a.href="/api/"+path;a.download=kind==="config"?"controller-setup.tar.zst":example?"controller-example-report.tar.zst":"controller-support-report.tar.zst";document.body.append(a);a.click();a.remove();
}
function renderDiagnostics(){
  const diagnostics=context.diagnostics||{},report=diagnosticReport||diagnostics.report||{},storage=report.storage||diagnostics.recorder||{};
  const p=panel("Your diagnostic recorder",diagnosticExample?"Authored simulation example · separate from your workspace recordings.":"This workspace has no live telemetry connection. Imported simulation observations remain clearly labelled.");
  p.append(node("span",diagnosticExample?"SIMULATION EXAMPLE":"OFFLINE · NO LIVE SOURCE","pill"));
  const stats=node("div",undefined,"stat-line");
  [[report.record_count||0,"saved observations"],[(Number(storage.compressed_bytes||0)/1024).toFixed(1)+" KB","compressed chunks"],["$0.00","API spend for diagnostics"]].forEach(([value,label])=>{const stat=node("div");stat.append(node("strong",String(value)),node("small",label));stats.append(stat);});p.append(stats);
  const actions=node("div",undefined,"twin");
  const progress=node("p","","description");progress.setAttribute("role","status");
  actions.append(button("Try a fault example",async()=>{progress.textContent="Preparing a separate simulation report…";try{diagnosticReport=await request("diagnostic_example",{});diagnosticExample=true;render();}finally{progress.textContent="";}}),button("Workspace recordings",async()=>{diagnosticReport=await request("diagnostic_report",{example:false});diagnosticExample=false;render();}));
  p.append(actions,progress);
  if(diagnostics.error)p.append(node("div",`${diagnostics.error.message} [${diagnostics.error.code}]`,"missing"));
  const fault=report.explanations?.at(-1);
  if(fault){
    const title=fault.code==="MOTOR_DRIVE_ALARM"&&fault.resource?.axis?`${fault.resource.axis} drive alarm`:fault.title;
    const card=panel(title,fault.summary);card.classList.add("fault-card");
    card.append(node("span",fault.resource?.label||fault.resource?.id||"Reported resource","pill"));
    const grid=node("div",undefined,"fault-grid"),observed=node("div"),response=node("div");
    observed.append(node("h3","What the record says"));
    for(const item of fault.observations||[])observed.append(node("p",item.text,"observation"));
    response.append(node("h3","Machine response"),node("p",fault.machine_response?.measured?.length?"Fresh measured signals are listed below. Whole-machine state still needs verification.":"No fresh measured response was recorded.","description"));
    for(const item of fault.machine_response?.observations||[])response.append(node("p",item.text,"observation"));
    response.append(node("div","Whole-machine stop and retained position: unverified. Restart requires independent verification.","missing"));grid.append(observed,response);card.append(grid);
    const checks=node("ol",undefined,"fault-checks");for(const item of fault.checks||[]){const check=node("li");check.append(node("strong",item.title),node("p",item.detail));checks.append(check);}card.append(node("h3","Check next"),checks);
    const wiring=node("details",undefined,"optional");wiring.append(node("summary","Illustrative wiring"),node("p","SIM terminals are examples. Qualified physical wiring is not available in this workspace.","description"));
    const resource=context.capabilities.resources.find(r=>r.id==="SIM."+fault.resource?.logical_id);
    if(resource){const names={"STEP+":"Step +","STEP-":"Step −","DIR+":"Direction +","DIR-":"Direction −","EN":"Individual enable","ALM":"Drive alarm"};table(wiring,["Connection","Illustrative terminal"],resource.terminals.map(terminal=>[names[terminal.split(".").at(-1)]||terminal.split(".").at(-1),terminal]));showData(wiring,"Resource limits and scope",resource);}
    else wiring.append(node("p","No matching simulated terminal map is available."));
    card.append(button("View wiring",()=>{wiring.open=!wiring.open;}),wiring);
    showData(card,"Inspect source observations and provenance",fault);
    $("content").prepend(card);
  }else panel("No interpreted fault available",report.explanation_errors?.length?"The raw fault record is retained in the report. Its format needs an exact matching explanation reference.":diagnosticExample?"No valid fault report is available for this example.":"Record declared simulation events through the CLI, or try the separate example to explore a fault report.");
  const timeline=panel("History around the fault","Capture targets are five minutes before and 30 seconds after. Coverage below reflects retained records and declared simulation time.");
  if(report.window){
    const window=report.window,bar=node("div",undefined,"fault-timeline");
    bar.append(node("div",`${Number(window.pre_observed_seconds||0).toFixed(0)}s before`,window.pre_complete?"covered":"incomplete"),node("span","FAULT"),node("div",`${Number(window.post_observed_seconds||0).toFixed(0)}s after`,window.post_complete?"covered":"incomplete"));timeline.append(bar);
    timeline.append(node("p",`${window.pre_complete?"Pre-fault history covered":"Pre-fault history incomplete"} · ${window.post_complete?"Post-fault history covered":"Post-fault history incomplete"} · ${(window.gaps||[]).length} reported gaps`,"description"));
  }else timeline.append(node("p","Coverage is unavailable until a fault and surrounding records are captured.","description"));
  if(storage.dropped_records)timeline.append(node("div",`${storage.dropped_records} records were dropped. Review the gaps before drawing conclusions.` ,"missing"));
  const support=panel("Keep the evidence together","Download a compressed report containing local setup facts and diagnostic records. Review it before sharing with support.");
  support.append(button(diagnosticExample?"Download example report":"Download support report",()=>downloadPackage("support",diagnosticExample),"primary"));
  showData(support,"Recorder limits, gaps and complete report",report);
  const service=panel("Machine state and service evidence","A shared view of the current configuration and supplied simulation records. No live source is connected.");
  const state=report.machine_state;
  if(state){
    const details=node("details",undefined,"optional");details.append(node("summary","View configuration binding and observed signals"));
    details.append(node("p",state.configuration_binding?`Saved generation ${state.configuration_binding.generation} · revision ${state.configuration_binding.revision}`:"No saved machine definition is bound to these observations.","description"));
    table(details,["Domain","Measured facts","Commanded facts","Reported facts"],Object.entries(state.domains||{}).map(([name,data])=>[name,data.counts.measured,data.counts.commanded,data.counts.reported]));
    details.append(node("p","Missing, stale and differently bound observations stay unavailable. A requested state does not verify the physical response.","description"));
    showData(details,"Inspect typed state, freshness and provenance",state);service.append(details);
  }else service.append(node("p","No typed machine state is available.","description"));
}
async function download(){await flush();const response=await fetch("/api/setup-download",{headers:{"X-Setup-Token":token}});if(!response.ok){const result=await response.json();throw Error(`${result.error?.message||"Unable to export setup"} [${result.error?.code||response.status}]`);}await response.arrayBuffer();const a=node("a");a.href="/api/setup-download";a.download="controller-simulation-setup.json";document.body.append(a);a.click();a.remove();}
$("next").onclick=()=>guard(async()=>{if(!draft)throw Error("Choose a machine profile first.");await flush();if(step===0){step=1;}else if(step===1){plan=await request("preview",{});commitRequest=null;step=2;}else if(step===2){if(!plan)throw Error("Create a fresh preview first.");commitRequest=commitRequest||crypto.randomUUID();await request("commit",{plan:commitPayload,request_id:commitRequest});await refresh();draft=structuredClone(context.setup.draft);step=3;commitRequest=null;}render();});
$("back").onclick=()=>guard(async()=>{await flush();step=Math.max(0,step-1);render();});
async function navigate(destination){if(destination<4||context.setup.initialized)await flush();if(destination===2&&draft){plan=await request("preview",{});importReview=null;commitRequest=null;}if(destination===4)diagnosticReport=await request("diagnostic_report",{example:diagnosticExample});if(destination===5){await refresh();readinessReport=await request("readiness");}step=destination;render();}
document.querySelectorAll("[data-step]").forEach(b=>b.onclick=()=>guard(()=>navigate(Number(b.dataset.step))));
$("export").onclick=()=>guard(download);
$("ask").onclick=()=>guard(async()=>{await flush();const result=await request("guidance",{question:$("question").value||"What remains to complete setup?"});$("answer").textContent=result.message;});
$("paid-ask").onclick=()=>guard(async()=>{
  await flush();$("paid-result").replaceChildren(node("p","Request in progress. No automatic retries will be sent."));let result;try{result=await request("paid_advice",{facts:$("facts").value,expected_revision:revision,allow_paid:true});}catch(error){
    $("paid-result").replaceChildren(node("p","Request failed. No automatic retry was sent. Any uncertain charge remains reserved."));
    try{await refreshBudget();}catch(refreshError){notice(refreshError);}
    throw error;
  }
  if(result.budget)context.budget=result.budget;updateMeta();
  const target=$("paid-result");target.replaceChildren();
  if(result.status!=="proposal"){target.append(node("p",result.error?.message||(result.status==="blocked_configuration"?"Resolve the existing configuration checks before requesting extracted facts.":"There are no missing mechanical facts to extract.")));for(const issue of result.validation?.blockers||[])target.append(node("div",issue.message,"missing"));return;}
  target.append(node("p",result.cached?"Saved advice reused. No new paid request.":"Review these unverified extractions before adding them to your draft."));
  for(const fact of result.model_output.proposals){const block=node("div",undefined,"missing");block.append(node("strong",`${fact.path} = ${fact.value}`),node("p",`Source: “${fact.source_quote}”`));target.append(block);}
  for(const question of result.next_questions||[])target.append(node("p",question));
  showData(target,"Inspect the original model output",result.model_output);
  if(result.validation.blockers.length)target.append(node("p","Some proposed values fail configuration checks. Correct the underlying facts before review."));
  if(result.model_output.proposals.length)target.append(button("Add reviewed facts to draft",async()=>{
    await flush();await refresh();const binding=result.configuration_binding;
    if(!binding||revision!==binding.revision||context.setup.store_id!==binding.store_id||context.setup.epoch!==binding.epoch||context.setup.draft?.profile_id!==binding.profile_id)throw Error("The saved setup changed since this advice. Review the current facts before using the retained proposal.");
    draft=structuredClone(result.proposed_draft);changed();await flush();target.replaceChildren(node("p","Facts saved to the draft. Review the full configuration before committing."));step=1;render();
  }));
});
window.addEventListener("beforeunload",e=>{if(dirty>saved){e.preventDefault();e.returnValue="";}});
guard(async()=>{await refresh();draft=context.setup.draft?structuredClone(context.setup.draft):await request("template",{profile_id:"sim-mill-3axis"});if(!context.setup.draft)dirty=1;if(context.setup.active){step=JSON.stringify(draft)===JSON.stringify(context.setup.active.draft)?5:1;if(step===5)readinessReport=await request("readiness");}render();});
