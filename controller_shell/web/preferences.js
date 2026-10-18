"use strict";
(() => {
  const token = document.querySelector('meta[name="setup-token"]').content;
  const apply = preferences => {
    if (!preferences || ![1,1.25,1.5].includes(preferences.display_scale) || typeof preferences.reduced_motion !== "boolean") return;
    document.documentElement.style.setProperty("--text-scale", preferences.display_scale);
    document.body.classList.toggle("reduce-motion", preferences.reduced_motion);
  };
  window.addEventListener("appliance-preferences", event => apply(event.detail));
  if (document.querySelector('meta[name="appliance-view"]')) return;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 8000);
  window.addEventListener("pagehide", () => controller.abort(), {once:true});
  fetch("/api/appliance/status", {headers:{"X-Setup-Token":token},cache:"no-store",signal:controller.signal})
    .then(async response => {
      const value = await response.json();
      if (!response.ok || value.ok !== true) throw Error("Preferences unavailable");
      apply(value.result.preferences);
      if (document.querySelector('meta[name="appliance-launch"]')) {
        const page = value.result.preferences.startup_page;
        window.location.replace(page === "files" || page === "settings" ? "/" + page : "/");
      }
    })
    .catch(() => { document.body.classList.remove("launching"); /* Navigation remains usable when preferences are unavailable. */ })
    .finally(() => clearTimeout(timeout));
})();
