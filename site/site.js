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

const quizzes = [...document.querySelectorAll("[data-quiz]")];
const quizSummary = document.querySelector("[data-quiz-summary]");

if (quizzes.length && quizSummary) {
  const storageKey = quizSummary.dataset.quizStorage;
  const answeredCount = quizSummary.querySelector("[data-quiz-answered]");
  const correctCount = quizSummary.querySelector("[data-quiz-correct]");
  const progressBar = quizSummary.querySelector("[data-quiz-progress]");
  const resetAllButton = quizSummary.querySelector("[data-quiz-reset]");
  let savedAnswers = {};

  try {
    savedAnswers = JSON.parse(localStorage.getItem(storageKey) ?? "{}") ?? {};
  } catch (_) {
    savedAnswers = {};
  }

  const saveAnswers = () => {
    try {
      localStorage.setItem(storageKey, JSON.stringify(savedAnswers));
    } catch (_) {}
  };

  const updateQuizSummary = () => {
    const answered = quizzes.filter((quiz) => quiz.classList.contains("is-answered")).length;
    const correct = quizzes.filter((quiz) => quiz.classList.contains("is-correct")).length;
    if (answeredCount) answeredCount.textContent = String(answered);
    if (correctCount) correctCount.textContent = String(correct);
    if (progressBar) progressBar.style.width = `${(answered / quizzes.length) * 100}%`;
    if (resetAllButton) resetAllButton.disabled = answered === 0;
  };

  const resetQuiz = (quiz, { persist = true, focus = true } = {}) => {
    quiz.classList.remove("is-answered", "is-correct", "is-incorrect");
    quiz.querySelectorAll("[data-quiz-option]").forEach((option) => {
      option.classList.remove("is-selected", "is-correct-answer");
    });
    quiz.querySelectorAll("input[type='radio']").forEach((input) => {
      input.checked = false;
      input.disabled = false;
    });
    const feedback = quiz.querySelector("[data-quiz-feedback]");
    if (feedback) feedback.hidden = true;
    delete savedAnswers[quiz.dataset.quizId];
    if (persist) saveAnswers();
    updateQuizSummary();
    if (focus) quiz.querySelector("input[type='radio']")?.focus();
  };

  const gradeQuiz = (quiz, selectedIndex, { persist = true, focus = true } = {}) => {
    const inputs = [...quiz.querySelectorAll("input[type='radio']")];
    const answerIndex = Number(quiz.dataset.answer);
    const selected = inputs[selectedIndex];
    const correct = inputs[answerIndex];
    if (!selected || !correct) return;

    const isCorrect = selectedIndex === answerIndex;
    quiz.classList.add("is-answered", isCorrect ? "is-correct" : "is-incorrect");
    selected.checked = true;
    selected.closest("[data-quiz-option]")?.classList.add("is-selected");
    correct.closest("[data-quiz-option]")?.classList.add("is-correct-answer");
    inputs.forEach((input) => {
      input.disabled = true;
    });

    const feedback = quiz.querySelector("[data-quiz-feedback]");
    const result = quiz.querySelector("[data-quiz-result]");
    const optionFeedback = quiz.querySelector("[data-quiz-option-feedback]");
    const bestAnswer = quiz.querySelector("[data-quiz-best-answer]");
    if (result) result.textContent = isCorrect ? "Correct." : "Not quite.";
    if (optionFeedback) optionFeedback.textContent = selected.dataset.feedback;
    if (bestAnswer) {
      bestAnswer.textContent = correct.closest("[data-quiz-option]")?.querySelector(".quiz-option-text")?.textContent ?? "";
    }
    if (feedback) feedback.hidden = false;

    savedAnswers[quiz.dataset.quizId] = selectedIndex;
    if (persist) saveAnswers();
    updateQuizSummary();
    if (focus) feedback?.focus({ preventScroll: true });
  };

  quizzes.forEach((quiz) => {
    quiz.querySelector("form")?.addEventListener("submit", (event) => event.preventDefault());
    quiz.addEventListener("change", (event) => {
      if (!(event.target instanceof HTMLInputElement) || event.target.type !== "radio") return;
      gradeQuiz(quiz, Number(event.target.value));
    });
    quiz.querySelector("[data-quiz-retry]")?.addEventListener("click", () => resetQuiz(quiz));

    const restoredAnswer = savedAnswers[quiz.dataset.quizId];
    if (Number.isInteger(restoredAnswer)) gradeQuiz(quiz, restoredAnswer, { persist: false, focus: false });
  });

  resetAllButton?.addEventListener("click", () => {
    quizzes.forEach((quiz) => resetQuiz(quiz, { persist: false, focus: false }));
    savedAnswers = {};
    saveAnswers();
    quizzes[0]?.scrollIntoView({ behavior: "smooth", block: "center" });
  });

  updateQuizSummary();
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
    if (label) label.textContent = isDark ? "Light" : "Dark";
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

const figureLinks = [...document.querySelectorAll(".technical-figure > a")];
if (figureLinks.length) {
  const lightbox = document.createElement("div");
  lightbox.className = "lightbox-overlay";
  lightbox.hidden = true;
  lightbox.innerHTML = `
    <figure class="lightbox-figure" role="dialog" aria-modal="true" aria-label="Expanded diagram">
      <button type="button" class="lightbox-close" aria-label="Close diagram">&times;</button>
      <div class="lightbox-figure-scroll"><img alt=""></div>
      <figcaption></figcaption>
    </figure>`;
  document.body.appendChild(lightbox);

  const lightboxImg = lightbox.querySelector("img");
  const lightboxCaption = lightbox.querySelector("figcaption");
  const lightboxClose = lightbox.querySelector(".lightbox-close");
  let lastFocused = null;

  const openLightbox = (link) => {
    const img = link.querySelector("img");
    if (!img) return;
    lightboxImg.src = link.getAttribute("href");
    lightboxImg.alt = img.getAttribute("alt") ?? "";
    lightboxCaption.textContent = link.closest("figure")?.querySelector("figcaption")?.textContent.trim() ?? "";
    lastFocused = document.activeElement;
    lightbox.hidden = false;
    document.body.style.overflow = "hidden";
    lightboxClose.focus();
  };

  const closeLightbox = () => {
    if (lightbox.hidden) return;
    lightbox.hidden = true;
    lightboxImg.src = "";
    document.body.style.overflow = "";
    lastFocused?.focus?.();
  };

  figureLinks.forEach((link) => {
    link.addEventListener("click", (event) => {
      event.preventDefault();
      openLightbox(link);
    });
  });

  lightbox.addEventListener("click", (event) => {
    if (event.target === lightbox) closeLightbox();
  });
  lightboxClose.addEventListener("click", closeLightbox);
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape") closeLightbox();
  });
}

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
