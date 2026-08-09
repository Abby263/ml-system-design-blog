const menuButton = document.querySelector("[data-menu-button]");
const mobileMenu = document.querySelector("[data-mobile-menu]");

menuButton?.addEventListener("click", () => {
  const isOpen = menuButton.getAttribute("aria-expanded") === "true";
  menuButton.setAttribute("aria-expanded", String(!isOpen));
  mobileMenu?.toggleAttribute("data-open", !isOpen);
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
