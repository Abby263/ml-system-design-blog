const menuButton = document.querySelector("[data-menu-button]");
const mobileMenu = document.querySelector("[data-mobile-menu]");
const mobileToc = document.querySelector("[data-mobile-toc]");

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
  if (event.key === "Escape" && mobileToc?.open) mobileToc.open = false;
});

const mobileTocLinks = [...(mobileToc?.querySelectorAll("a[href^='#']") ?? [])];
const mobileTocCurrent = mobileToc?.querySelector("[data-mobile-toc-current]");
const mobileTocNav = mobileToc?.querySelector("nav");
const mobileTocViewport = window.matchMedia("(max-width: 1050px)");
const mobileTocTargets = mobileTocLinks
  .map((link) => ({ link, target: document.querySelector(link.getAttribute("href")) }))
  .filter(({ target }) => target);

const setCurrentSection = (activeLink) => {
  mobileTocLinks.forEach((link) => {
    if (link === activeLink) link.setAttribute("aria-current", "location");
    else link.removeAttribute("aria-current");
  });
  if (mobileTocCurrent) mobileTocCurrent.textContent = activeLink.textContent.trim();
};

mobileTocLinks.forEach((link) => {
  link.addEventListener("click", () => {
    setCurrentSection(link);
    if (mobileToc) mobileToc.open = false;
  });
});

mobileToc?.addEventListener("toggle", () => {
  if (!mobileToc.open || !mobileTocNav) return;
  const activeLink = mobileTocNav.querySelector("[aria-current='location']");
  if (!activeLink) return;

  const linkTop = activeLink.offsetTop - mobileTocNav.offsetTop;
  mobileTocNav.scrollTop = linkTop - (mobileTocNav.clientHeight - activeLink.offsetHeight) / 2;
});

if (mobileTocTargets.length) {
  let sectionTicking = false;
  const updateCurrentSection = () => {
    if (!mobileTocViewport.matches) {
      sectionTicking = false;
      return;
    }

    const activationLine = 132;
    let current = mobileTocTargets[0];

    for (const candidate of mobileTocTargets) {
      if (candidate.target.getBoundingClientRect().top > activationLine) break;
      current = candidate;
    }

    setCurrentSection(current.link);
    sectionTicking = false;
  };

  const requestSectionUpdate = () => {
    if (sectionTicking) return;
    sectionTicking = true;
    requestAnimationFrame(updateCurrentSection);
  };

  updateCurrentSection();
  document.addEventListener("scroll", requestSectionUpdate, { passive: true });
  mobileTocViewport.addEventListener?.("change", requestSectionUpdate);
}

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
