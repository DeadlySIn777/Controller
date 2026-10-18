"use strict";
(() => {
  const $ = id => document.getElementById(id);
  const token = document.querySelector('meta[name="setup-token"]').content;
  const view = document.querySelector('meta[name="appliance-view"]').content;
  const navigation = document.querySelector(`[data-view="${view}"]`);
  navigation.classList.add("selected"); navigation.setAttribute("aria-current", "page");
  $(view + "-view").hidden = false;
  $("section-name").textContent = view.toUpperCase();
  document.title = "Motion X12 · " + (view === "files" ? "Files" : "Settings");
  $("page-title").textContent = view === "files" ? "Everything worth keeping." : "Your workspace. Your way.";
  $("page-description").textContent = view === "files" ? "Backups and diagnostic exports, without opening a terminal." : "Comfortable controls, deliberate changes and recovery that preserves your machine.";
  let status, pending = false, dirty = false, plan, serializedPlan, requestId;
  const dirtyFields = new Set();
  const preferenceControls = {display_scale:"display-scale",reduced_motion:"reduced-motion",startup_page:"startup-page"};
  function choices() { return {display_scale:Number($("display-scale").value),reduced_motion:$("reduced-motion").checked,startup_page:$("startup-page").value}; }
  function keepChoices(saved) {
    for (const [field,value] of Object.entries(saved)) {
      const control = $(preferenceControls[field]);
      if (field === "reduced_motion") control.checked = value; else control.value = String(value);
      dirtyFields.add(field);
    }
    dirty = dirtyFields.size > 0;
    apply(choices());
    controls(true);
  }
  const controllers = new Set();
  async function api(name, payload, shared = false) {
    const controller = new AbortController(); controllers.add(controller);
    const timeout = setTimeout(() => controller.abort(), 8000);
    try {
      const response = await fetch((shared ? "/api/" : "/api/appliance/") + name, {method:payload === undefined ? "GET" : "POST",
        headers:{"X-Setup-Token":token,...(payload === undefined ? {} : {"Content-Type":"application/json"})},
        ...(payload === undefined ? {} : {body:JSON.stringify(payload)}),cache:"no-store",signal:controller.signal});
      const envelope = await response.json();
      if (!response.ok || envelope.ok !== true) throw Error(envelope.error?.message || "Appliance state unavailable");
      return envelope;
    } finally { clearTimeout(timeout); controllers.delete(controller); }
  }
  function message(text) { $("result").textContent = text; $("result").hidden = false; }
  function error(target, value) {
    target.textContent = value.name === "AbortError" ? "The local service did not respond in time. Keep your choices and retry deliberately." : value.message;
    target.hidden = false;
  }
  function controls(enabled) {
    for (const id of ["display-scale","reduced-motion","startup-page","save-preferences","reset-preferences","undo-preferences","open-service"]) $(id).disabled = !enabled;
    if (enabled) { $("undo-preferences").disabled = !status.undo_available; $("save-preferences").disabled = !dirty; }
  }
  function apply(preferences) { window.dispatchEvent(new CustomEvent("appliance-preferences", {detail:preferences})); }
  function paint(value) {
    if (value.physical_authority !== false || value.motion_authorized !== false || value.api_calls !== 0 || value.terminal_available !== false) throw Error("Appliance service scope changed; inspect the service before continuing.");
    status = value;
    if (view === "settings") {
      $("display-scale").value = String(value.preferences.display_scale);
      $("reduced-motion").checked = value.preferences.reduced_motion;
      $("startup-page").value = value.preferences.startup_page;
      dirty = false; dirtyFields.clear(); controls(true);
    }
    apply(value.preferences);
    $("connection").textContent = "Local appliance connected";
  }
  function exportCapability(available, setupInitialized = false) {
    for (const id of ["config-export","support-export"]) {
      const link = $(id);
      if (!available || id === "config-export" && !setupInitialized) {
        link.removeAttribute("href"); link.setAttribute("aria-disabled", "true");
      } else {
        link.href = id === "config-export" ? "/api/config-package" : "/api/support-package";
        link.removeAttribute("aria-disabled");
      }
    }
    $("compression-status").textContent = available ? "Compressed packages use the installed Zstd backend. " + (setupInitialized ? "Configuration backup is available; " : "Save a setup draft before exporting a configuration backup; ") + "exports do not grant motion permission." : "Compressed packages are unavailable on this host. Setup JSON remains available; the target image still needs its qualified compression dependency.";
  }
  function fileRows(inventory, context) {
    if (context.simulation_only !== true || !context.setup) throw Error("Setup export scope unavailable");
    exportCapability(inventory.archive_capabilities.available === true, context.setup.initialized === true);
    const list = $("package-list"); list.replaceChildren();
    if (!inventory.files.length && !inventory.unavailable.length) {
      const row = document.createElement("li"); row.textContent = "No local packages yet. Use the exports above to keep a copy."; list.append(row);
    }
    for (const item of inventory.files) {
      const row = document.createElement("li"), description = document.createElement("div"), title = document.createElement("strong"), detail = document.createElement("small"), link = document.createElement("a");
      title.textContent = item.filename; detail.textContent = `${item.kind} · ${item.size.toLocaleString()} bytes · integrity checked`;
      description.append(title,detail); link.className = "secondary-action"; link.textContent = "Download ↓";
      link.href = "/api/appliance/download?" + new URLSearchParams({id:item.package_id,sha256:item.sha256});
      row.append(description,link); list.append(row);
    }
    for (const item of inventory.unavailable) {
      const row = document.createElement("li"); row.textContent = item.filename + " · Unavailable: " + item.error.message; list.append(row);
    }
  }
  async function refresh() {
    if (pending) return;
    const savedChoices = view === "settings" && dirty ? Object.fromEntries([...dirtyFields].map(field => [field,choices()[field]])) : null;
    pending = true; $("refresh").disabled = true; controls(false); $("error").hidden = true;
    try {
      const current = await api("status");
      if (view === "files") fileRows((await api("files")).result, (await api("context", undefined, true)).result);
      paint(current.result);
      if (savedChoices) { keepChoices(savedChoices); message("Latest preferences loaded. Your edited choices are kept; review the fresh differences before saving."); }
    } catch (failure) {
      $("connection").textContent = "Appliance state unavailable"; error($("error"), failure);
      if (view === "files") { exportCapability(false); $("package-list").textContent = "Package inventory unavailable. Refresh to retry; previous results are not current evidence."; }
    } finally { pending = false; $("refresh").disabled = false; }
  }
  function edited(event) {
    const field = Object.keys(preferenceControls).find(key => preferenceControls[key] === event.target.id);
    dirtyFields.add(field); dirty = true; controls(!!status);
    message("Interface preview only. Review changes to save them."); apply(choices());
  }
  $("display-scale").addEventListener("change", edited); $("reduced-motion").addEventListener("change", edited); $("startup-page").addEventListener("change", edited);
  window.addEventListener("beforeunload", event => { if (dirty) { event.preventDefault(); event.returnValue = ""; } });
  async function review(name, payload) {
    if (pending) return;
    pending = true; controls(false); $("error").hidden = true;
    try {
      const envelope = await api(name, payload);
      plan = envelope.result; serializedPlan = envelope.commit_payload;
      if (typeof serializedPlan !== "string" || plan.scope !== "appliance_preferences" || plan.physical_authority !== false || plan.motion_authorized !== false) throw Error("Invalid interface review; refresh before retrying.");
      requestId = crypto.randomUUID();
      $("review-title").textContent = plan.operation === "reset" ? "Reset interface preferences" : plan.operation === "undo" ? "Restore previous preferences" : "Save interface preferences";
      $("review-scope").textContent = "Only interface preferences will change. No machine command is sent.";
      $("review-diff").replaceChildren();
      const labels = {display_scale:"Text size",reduced_motion:"Reduced motion",startup_page:"Starting screen"};
      for (const difference of plan.diff) {
        const label = document.createElement("dt"), value = document.createElement("dd");
        label.textContent = labels[difference.field] || difference.field; value.textContent = `${difference.before} → ${difference.after}`;
        $("review-diff").append(label,value);
      }
      if (!plan.diff.length) $("review-diff").textContent = "Preferences already match this choice.";
      $("review-preserved").textContent = "Preserved: machine setup, backups, calibration, licences, AI allowance, diagnostics and jobs.";
      $("review-error").hidden = true; $("confirm-review").disabled = false;
      $("review-dialog").showModal();
    } catch (failure) { error($("error"),failure); }
    finally { pending = false; controls(!!status); }
  }
  $("preferences-form").addEventListener("submit", event => {
    event.preventDefault();
    if (!status) return;
    review("preferences-preview", {patch:Object.fromEntries([...dirtyFields].map(field => [field,choices()[field]])),expected_revision:status.revision});
  });
  $("reset-preferences").addEventListener("click", () => review("reset-preview",{scope:"appliance_preferences"}));
  $("undo-preferences").addEventListener("click", () => review("undo-preview",{}));
  $("cancel-review").addEventListener("click", () => $("review-dialog").close());
  $("confirm-review").addEventListener("click", async () => {
    if (pending || !plan) return;
    pending = true; $("confirm-review").disabled = true; $("review-error").hidden = true;
    $("cancel-review").disabled = true;
    try {
      const response = await api("confirm",{plan:serializedPlan,request_id:requestId,confirmation:plan.confirmation});
      apply(response.result.preferences); dirty = false; dirtyFields.clear(); $("review-dialog").close();
      message("Interface preferences saved. Machine settings and backups are unchanged.");
      status = null;
    } catch (failure) { error($("review-error"),failure); }
    finally { pending = false; $("confirm-review").disabled = false; $("cancel-review").disabled = false; }
    if (!$("review-dialog").open) await refresh();
  });
  $("review-dialog").addEventListener("cancel", event => { if (pending) event.preventDefault(); });
  $("open-service").addEventListener("click", () => { $("service-confirmation").checked = false; $("service-details").hidden = true; $("service-error").hidden = true; $("service-dialog").showModal(); });
  $("enter-service").addEventListener("click", async () => {
    if (pending) return;
    if (!$("service-confirmation").checked) { error($("service-error"), Error("Acknowledge the service-view limits before continuing.")); return; }
    pending = true; $("enter-service").disabled = true;
    $("close-service").disabled = true;
    try {
      const value = (await api("service-mode",{enabled:true,confirmation:"ENTER SERVICE VIEW"})).result;
      if (value.service_mode !== true || value.motion_authorized !== false || value.terminal_available !== false) throw Error("Service view scope changed; close this view.");
      $("service-details").textContent = "Motion X12 development appliance. Local preference service only. No terminal, device control or physical motion backend. Full machine reset blocked. Boot, signed updates, touchscreen timing and actual runtime continuity need target qualification.";
      $("service-details").hidden = false; $("service-error").hidden = true;
    } catch (failure) { error($("service-error"),failure); }
    finally { pending = false; $("enter-service").disabled = false; $("close-service").disabled = false; }
  });
  $("close-service").addEventListener("click", () => $("service-dialog").close());
  $("service-dialog").addEventListener("cancel", event => { if (pending) event.preventDefault(); });
  $("service-dialog").addEventListener("close", () => { api("service-mode",{enabled:false,confirmation:"LEAVE SERVICE VIEW"}).catch(() => {/* Presentation state expires with the service; it grants no authority. */}); });
  $("refresh").addEventListener("click",refresh);
  window.addEventListener("pagehide", () => { for (const controller of controllers) controller.abort(); });
  refresh();
})();
