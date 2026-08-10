const menuButton = document.querySelector("[data-menu-button]");
const mobileMenu = document.querySelector("[data-mobile-menu]");

const closeMenu = () => {
  menuButton?.setAttribute("aria-expanded", "false");
  menuButton?.setAttribute("aria-label", "Open navigation");
  mobileMenu?.removeAttribute("data-open");
};

menuButton?.addEventListener("click", () => {
  const isOpen = menuButton.getAttribute("aria-expanded") === "true";
  menuButton.setAttribute("aria-expanded", String(!isOpen));
  menuButton.setAttribute("aria-label", isOpen ? "Open navigation" : "Close navigation");
  mobileMenu?.toggleAttribute("data-open", !isOpen);
});

mobileMenu?.querySelectorAll("a").forEach((link) => link.addEventListener("click", closeMenu));
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") closeMenu();
});

const themeButtons = document.querySelectorAll("[data-theme-toggle]");
const themeColor = document.querySelector("[data-theme-color]");
const systemTheme = window.matchMedia("(prefers-color-scheme: dark)");

const setTheme = (theme, persist = false) => {
  const isDark = theme === "dark";
  document.documentElement.dataset.theme = theme;
  document.documentElement.style.colorScheme = theme;
  themeColor?.setAttribute("content", isDark ? "#10120f" : "#f0f0e9");

  themeButtons.forEach((button) => {
    button.setAttribute("aria-pressed", String(isDark));
    button.setAttribute("aria-label", `Switch to ${isDark ? "light" : "dark"} theme`);
    const label = button.querySelector("[data-theme-label]");
    const icon = button.querySelector("[data-theme-icon]");
    if (label) label.textContent = isDark ? "Light" : "Dark";
    if (icon) icon.textContent = isDark ? "☀" : "◐";
  });

  if (persist) {
    try {
      localStorage.setItem("dml-theme", theme);
    } catch (_) {}
  }
};

setTheme(document.documentElement.dataset.theme === "dark" ? "dark" : "light");

themeButtons.forEach((button) => {
  button.addEventListener("click", () => {
    setTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark", true);
  });
});

systemTheme.addEventListener?.("change", (event) => {
  try {
    if (localStorage.getItem("dml-theme")) return;
  } catch (_) {}
  setTheme(event.matches ? "dark" : "light");
});

document.querySelectorAll("[data-copy]").forEach((button) => {
  button.addEventListener("click", async () => {
    const target = document.getElementById(button.dataset.copy);
    if (!target) return;

    await navigator.clipboard.writeText(target.textContent ?? "");
    const original = button.textContent;
    button.textContent = "Copied";
    setTimeout(() => {
      button.textContent = original;
    }, 1500);
  });
});

const readingBar = document.querySelector("[data-reading-progress]");
if (readingBar) {
  const updateProgress = () => {
    const max = document.documentElement.scrollHeight - window.innerHeight;
    const progress = max > 0 ? window.scrollY / max : 0;
    readingBar.style.transform = `scaleX(${Math.min(1, Math.max(0, progress))})`;
  };

  updateProgress();
  document.addEventListener("scroll", updateProgress, { passive: true });
}
