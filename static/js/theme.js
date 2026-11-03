(() => {
  const themes = new Set(["day", "night", "sign"]);
  const key = "capacity-connect-theme";
  const preference = window.matchMedia("(prefers-color-scheme: dark)");
  const root = document.documentElement;

  function readTheme() {
    try {
      return localStorage.getItem(key);
    } catch {
      return null;
    }
  }

  const stored = readTheme();
  let selected = themes.has(stored) ? stored : null;
  const systemTheme = () => preference.matches ? "night" : "day";
  root.dataset.theme = selected ?? systemTheme();

  document.addEventListener("DOMContentLoaded", () => {
    const control = document.querySelector("[data-theme-control]");
    if (!control) return;
    const select = control.querySelector("select");
    select.value = root.dataset.theme;
    control.hidden = false;
    select.addEventListener("change", () => {
      if (!themes.has(select.value)) return;
      selected = select.value;
      root.dataset.theme = selected;
      try {
        localStorage.setItem(key, selected);
      } catch {
        // The active page still reflects the choice.
      }
    });
    preference.addEventListener("change", () => {
      if (selected === null) root.dataset.theme = systemTheme();
      select.value = root.dataset.theme;
    });
  });
})();
