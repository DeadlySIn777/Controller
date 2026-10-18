"use strict";
(() => {
  const $ = id => document.getElementById(id);
  const token = document.querySelector('meta[name="setup-token"]').content;
  let pending = false, timer, controller;
  const routes = {0:"setup",1:"drives",2:"review",3:"saved",4:"diagnostics",5:"readiness"};
  async function get(path) {
    const response = await fetch("/api/" + path, {headers:{"X-Setup-Token":token}, signal:controller.signal, cache:"no-store"});
    const envelope = await response.json();
    if (!response.ok || envelope.ok !== true) throw Error(envelope.error?.message || "Local service unavailable");
    return envelope.result;
  }
  function coherent(setup, readiness) {
    const binding = readiness.configuration_binding;
    if (!setup.initialized) return binding === null;
    return binding && binding.store_id === setup.store_id && binding.epoch === setup.epoch &&
      binding.revision === setup.current_revision && binding.generation === setup.generation &&
      binding.configuration_sha256 === (setup.active?.configuration_sha256 ?? null) &&
      binding.draft_sha256 === setup.draft_binding?.draft_sha256;
  }
  function paint(context, readiness) {
    if (context.simulation_only !== true || readiness.motion_authorized !== false ||
        readiness.physical_commissioning_complete !== false || readiness.outputs_inhibited !== true) {
      throw Error("Workspace authority does not match this disconnected interface. Inspect the service before continuing.");
    }
    const setup = context.setup;
    if (!coherent(setup, readiness)) throw Error("Settings changed while loading. Refresh to see one consistent configuration.");
    const draft = setup.active?.draft ?? setup.draft;
    const profile = context.profiles[draft?.profile_id];
    $("machine-name").textContent = draft?.machine_name || profile?.title || "Let’s make it yours.";
    $("machine-detail").textContent = setup.active ? "Your reviewed configuration is retained locally. Check readiness before the next independent hardware commissioning step." : "Start with the mechanics you know. The setup service keeps the facts, calculations and review together.";
    $("generation").textContent = setup.active ? `Saved generation ${setup.generation} · revision ${setup.current_revision}` : setup.initialized ? `Draft workspace · revision ${setup.current_revision}` : "No saved generation";
    $("motor-selection").textContent = draft ? `${draft.motors.length} motors selected · simulation profile` : "Machine profile not selected";
    $("setup-action").firstChild.textContent = setup.active ? "Review machine " : setup.initialized ? "Continue setup " : "Set up machine ";
    const next = readiness.next_step;
    $("next-label").textContent = next ? "GUIDED SETUP" : "CONFIGURATION REVIEWED";
    $("next-title").textContent = next?.title || "Configuration checks passed";
    $("next-detail").textContent = next?.action || "Independent physical commissioning is still required. The workspace cannot enable machine motion.";
    $("next-action").href = "/workbench?view=" + (routes[next?.ui_step] || "readiness");
    $("next-action").setAttribute("aria-label", next ? next.action : "Inspect readiness and remaining commissioning");
    const passed = readiness.checks.filter(c => c.required_for_simulation && c.status === "pass").length;
    const required = readiness.checks.filter(c => c.required_for_simulation).length;
    $("readiness-status").textContent = `${passed} of ${required} setup checks passed · physical commissioning required`;
    const record = readiness.checks.find(c => c.id === "recorder");
    $("recorder-status").textContent = record?.status === "unavailable" ? "Recording evidence unavailable" : `${record?.evidence?.record_count ?? 0} retained simulation records · no live acquisition`;
    $("ai-status").textContent = context.paid_ai_enabled ? "Optional paid extraction configured · review required" : "Local guidance · no paid calls from this screen";
    $("connection").textContent = "Local workspace connected";
    $("sampled").textContent = "Updated " + new Date().toLocaleTimeString([], {hour:"2-digit",minute:"2-digit"});
    $("error").hidden = true;
    document.body.classList.remove("stale");
  }
  async function refresh() {
    if (pending || document.hidden) return;
    pending = true;
    $("refresh").disabled = true;
    controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 8000);
    try { const [context, readiness] = await Promise.all([get("context"), get("readiness")]); paint(context, readiness); }
    catch (error) {
      controller.abort();
      document.body.classList.add("stale");
      $("connection").textContent = "Workspace status unavailable";
      $("sampled").textContent = "Data unavailable · refresh to retry";
      $("error").textContent = (error.name === "AbortError" ? "The local service did not respond in time." : error.message) + " Previous values are not current evidence. Open setup or refresh to inspect the workspace.";
      $("error").hidden = false;
      for (const id of ["readiness-status","recorder-status","ai-status"]) $(id).textContent = "Current status unavailable";
    } finally {
      clearTimeout(timeout); pending = false; $("refresh").disabled = false;
      clearTimeout(timer); if (!document.hidden) timer = setTimeout(refresh, 15000);
    }
  }
  $("refresh").addEventListener("click", refresh);
  document.addEventListener("visibilitychange", () => { clearTimeout(timer); if (document.hidden) controller?.abort(); else refresh(); });
  window.addEventListener("pagehide", () => { clearTimeout(timer); controller?.abort(); });
  refresh();
})();
