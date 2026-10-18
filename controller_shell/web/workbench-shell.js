"use strict";
(() => {
  const home = document.createElement("a");
  home.href = "/"; home.className = "shell-home"; home.textContent = "⌂ Machine";
  const content = document.getElementById("content");
  let fallback, captured = false;
  function untouchedFallback() {
    return fallback !== undefined && !context.setup.initialized && dirty === 1 && saved === 0 &&
      JSON.stringify(draft) === fallback;
  }
  function leave(destination, event) {
    event.preventDefault();
    // Honor the workbench's guarded autosave before leaving. A failed or
    // stale save keeps the operator's answers on screen for recovery.
    guard(async () => {
      // The original workbench marks its initial blank fallback as dirty.
      // Browsing alone must not create a machine or an AI allowance. Only
      // dismiss that exact untouched provisional template; real edits still
      // pass through the ordinary guarded save and stale-binding checks.
      if (untouchedFallback()) dirty = saved;
      else await flush();
      window.location.assign(destination);
    });
  }
  home.addEventListener("click", event => leave("/", event));
  const navigation = document.createElement("nav");
  navigation.className = "appliance-nav";
  navigation.setAttribute("aria-label", "Appliance navigation");
  navigation.append(home);
  const requestedView = new URLSearchParams(window.location.search).get("view");
  for (const [label, path] of [["◇ Setup","/workbench?view=setup"],["◎ Diagnostics","/workbench?view=diagnostics"],["▤ Files","/files"],["⚙ Settings","/settings"]]) {
    const link = document.createElement("a");
    link.textContent = label; link.href = path;
    if (path === "/workbench?view=setup" && requestedView !== "diagnostics" || path === "/workbench?view=diagnostics" && requestedView === "diagnostics") {
      link.className = "selected"; link.setAttribute("aria-current", "page");
    }
    link.addEventListener("click", event => leave(path, event));
    navigation.append(link);
  }
  for (const link of navigation.querySelectorAll("a")) {
    const icon = document.createElement("span"), text = document.createElement("span");
    const label = link.textContent;
    icon.className = "appliance-nav-icon"; icon.textContent = label.slice(0,1); icon.setAttribute("aria-hidden", "true");
    text.textContent = label.slice(2); link.replaceChildren(icon,text);
  }
  const brand = document.querySelector(".brand");
  brand.after(navigation);
  document.querySelector(".brandmark").textContent = "M";
  brand.querySelector("div").firstChild.textContent = "MOTION X12";
  brand.querySelector("small").textContent = "BY GARCIAMECH";
  document.querySelector(".rail-label").textContent = "SETUP STEPS";
  document.title = "Motion X12 · Setup workspace";
  const requested = new URLSearchParams(window.location.search).get("view");
  const destination = {setup:0,drives:1,review:2,saved:3,readiness:5,diagnostics:4}[requested];
  const button = document.querySelector(`[data-step="${destination}"]`);
  let complete = false;
  function navigateIfReady() {
    if (complete || content.getAttribute("aria-busy") !== "false" || !context) return;
    if (!captured) {
      captured = true;
      if (!context.setup.initialized && dirty === 1 && saved === 0) fallback = JSON.stringify(draft);
    }
    if (destination === undefined || destination === 0 && untouchedFallback()) {
      complete = true; observer.disconnect(); return;
    }
    if (button.disabled) return;
    complete = true; observer.disconnect(); button.click();
  }
  const observer = new MutationObserver(navigateIfReady);
  observer.observe(content, {attributes:true,attributeFilter:["aria-busy"]});
  window.addEventListener("pagehide", () => observer.disconnect(), {once:true});
  navigateIfReady();
})();
