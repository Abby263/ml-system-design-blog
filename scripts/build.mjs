import { readFile, readdir, rm, mkdir, writeFile, copyFile, stat } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { marked } from "marked";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const BLOGS_DIR = path.join(ROOT, "blogs");
const DIST_DIR = path.join(ROOT, "dist");
const GITHUB_URL = "https://github.com/Abby263/ml-system-design-blog";
const SITE_NAME = "Designing ML Systems";

const escapeHtml = (value = "") =>
  value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");

const stripMarkdown = (value = "") =>
  value
    .replace(/```[\s\S]*?```/g, "")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/!\[[^\]]*\]\([^)]*\)/g, "")
    .replace(/\[([^\]]+)\]\([^)]*\)/g, "$1")
    .replace(/[*_>#]/g, "")
    .replace(/\s+/g, " ")
    .trim();

const decodeHtmlEntities = (value = "") =>
  value
    .replace(/&(?:#39|apos);/g, "'")
    .replace(/&quot;/g, '"')
    .replace(/&gt;/g, ">")
    .replace(/&lt;/g, "<")
    .replace(/&amp;/g, "&");

const slugify = (value = "") =>
  stripMarkdown(value)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");

const humanFileSize = (bytes) => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

const writePage = async (route, html) => {
  const target = path.join(DIST_DIR, route, "index.html");
  await mkdir(path.dirname(target), { recursive: true });
  await writeFile(target, html, "utf8");
};

const GENERATED_DIRECTORY_NAMES = new Set([
  ".mypy_cache",
  ".pytest_cache",
  ".ruff_cache",
  ".venv",
  "__pycache__",
  "artifacts",
  "build",
  "dist",
  "node_modules",
]);

const walkFiles = async (directory, prefix = "") => {
  const entries = await readdir(directory, { withFileTypes: true });
  const files = [];

  for (const entry of entries.sort((a, b) => a.name.localeCompare(b.name))) {
    if (entry.name === ".DS_Store") continue;
    if (
      entry.isDirectory() &&
      (GENERATED_DIRECTORY_NAMES.has(entry.name) || entry.name.endsWith(".egg-info"))
    ) {
      continue;
    }
    const absolute = path.join(directory, entry.name);
    const relative = path.join(prefix, entry.name);

    if (entry.isDirectory()) files.push(...(await walkFiles(absolute, relative)));
    if (entry.isFile()) files.push({ absolute, relative });
  }

  return files;
};

const loadBlogs = async () => {
  const entries = await readdir(BLOGS_DIR, { withFileTypes: true });
  const blogs = [];

  for (const entry of entries) {
    if (!entry.isDirectory() || !/^\d{2,}-/.test(entry.name)) continue;

    const articlePath = path.join(BLOGS_DIR, entry.name, "README.md");
    const source = await readFile(articlePath, "utf8");
    const title = source.match(/^#\s+(.+)$/m)?.[1]?.trim() ?? entry.name;
    const subtitle = source.match(/^\*([^\n]+)\*$/m)?.[1]?.trim() ?? "A practical system design case study.";
    const number = Number(entry.name.match(/^(\d+)/)?.[1] ?? blogs.length + 1);
    const codeDirectory = path.join(BLOGS_DIR, entry.name, "code");
    const assetsDirectory = path.join(BLOGS_DIR, entry.name, "assets");
    let codeFiles = [];
    let assetFiles = [];

    try {
      codeFiles = await walkFiles(codeDirectory);
    } catch {
      codeFiles = [];
    }

    try {
      assetFiles = await walkFiles(assetsDirectory);
    } catch {
      assetFiles = [];
    }

    const words = stripMarkdown(source).split(/\s+/).filter(Boolean).length;
    blogs.push({
      slug: entry.name,
      number,
      title,
      shortTitle: title.replace(/^Designing ML Systems:\s*/i, ""),
      subtitle,
      source,
      articlePath,
      codeDirectory,
      codeFiles,
      assetsDirectory,
      assetFiles,
      readTime: Math.max(1, Math.ceil(words / 220)),
    });
  }

  return blogs.sort((a, b) => a.number - b.number);
};

const nav = (active = "") => `
  <header class="site-header">
    <a class="brand" href="/" aria-label="Designing ML Systems home">
      <span class="brand-mark">D/ML</span>
      <span class="brand-name">Designing ML Systems</span>
    </a>
    <nav class="desktop-nav" aria-label="Primary navigation">
      <a ${active === "blogs" ? 'aria-current="page"' : ""} href="/blogs/">Writing</a>
      <a ${active === "about" ? 'aria-current="page"' : ""} href="/about/">About</a>
      <a class="nav-source" href="${GITHUB_URL}" target="_blank" rel="noreferrer">GitHub <span>↗</span></a>
    </nav>
    <button class="menu-button" type="button" aria-label="Open navigation" aria-expanded="false" data-menu-button>
      <span></span><span></span>
    </button>
    <nav class="mobile-menu" aria-label="Mobile navigation" data-mobile-menu>
      <a href="/blogs/">Writing</a>
      <a href="/about/">About</a>
      <a href="${GITHUB_URL}" target="_blank" rel="noreferrer">GitHub ↗</a>
    </nav>
  </header>`;

const footer = () => `
  <footer class="site-footer">
    <div>
      <span class="eyebrow">BUILD · BREAK · UNDERSTAND</span>
      <p>Systems are easier to understand once you have watched them fail.</p>
    </div>
    <div class="footer-links">
      <a href="/blogs/">All writing</a>
      <a href="${GITHUB_URL}" target="_blank" rel="noreferrer">Source on GitHub ↗</a>
    </div>
    <p class="footer-note">Designed and built alongside the systems it explains.</p>
  </footer>`;

const page = ({ title, description, active = "", body, article = false }) => `<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="description" content="${escapeHtml(description)}">
    <meta name="theme-color" content="#0d0e0c">
    <meta property="og:type" content="${article ? "article" : "website"}">
    <meta property="og:title" content="${escapeHtml(title)}">
    <meta property="og:description" content="${escapeHtml(description)}">
    <meta property="og:site_name" content="${SITE_NAME}">
    <title>${escapeHtml(title)}</title>
    <link rel="icon" href="/favicon.svg" type="image/svg+xml">
    <link rel="stylesheet" href="/styles.css">
  </head>
  <body>
    <div class="reading-progress" data-reading-progress></div>
    ${nav(active)}
    <main>${body}</main>
    ${footer()}
    <script src="/site.js" defer></script>
  </body>
</html>`;

const extractHeadings = (markdown) => {
  const seen = new Map();
  return [...markdown.matchAll(/^(#{2,3})\s+(.+)$/gm)].map((match) => {
    const text = stripMarkdown(match[2]);
    const base = slugify(text);
    const count = seen.get(base) ?? 0;
    seen.set(base, count + 1);
    return { level: match[1].length, text, id: count ? `${base}-${count + 1}` : base };
  });
};

const renderMarkdown = (markdown) => {
  const seen = new Map();
  let html = marked.parse(markdown, { gfm: true });

  html = html.replace(/<h([2-3])>([\s\S]*?)<\/h\1>/g, (_, level, content) => {
    const text = decodeHtmlEntities(content.replace(/<[^>]+>/g, ""));
    const base = slugify(text);
    const count = seen.get(base) ?? 0;
    seen.set(base, count + 1);
    const id = count ? `${base}-${count + 1}` : base;
    return `<h${level} id="${id}">${content}<a class="heading-anchor" href="#${id}" aria-label="Link to ${escapeHtml(text)}">#</a></h${level}>`;
  });

  return html;
};

const articleMarkdown = (source) =>
  source
    .replace(/^#\s+.+\n+/, "")
    .replace(/^\*([^\n]+)\*\n+/, "")
    .replace(/^## Table of Contents[\s\S]*?(?=^##\s)/m, "");

const fileIcon = (file) => {
  const extension = path.extname(file).toLowerCase();
  if ([".md", ".mdx"].includes(extension)) return "MD";
  if ([".py", ".ipynb"].includes(extension)) return "PY";
  if ([".js", ".mjs", ".ts", ".tsx", ".jsx"].includes(extension)) return "JS";
  if ([".yml", ".yaml", ".json", ".toml"].includes(extension)) return "CFG";
  if ([".sql"].includes(extension)) return "SQL";
  if (["Dockerfile", "Containerfile"].includes(path.basename(file))) return "CTR";
  return "FILE";
};

const codeRoute = (blog, relative) =>
  `/blogs/${blog.slug}/code/${relative.split(path.sep).map(encodeURIComponent).join("/")}/`;

const blogCard = (blog, featured = false) => `
  <article class="blog-card ${featured ? "featured" : ""}">
    <div class="blog-card-topline">
      <span>Essay ${String(blog.number).padStart(2, "0")}</span>
      <span>${blog.readTime} min read</span>
    </div>
    <div>
      <h3><a href="/blogs/${blog.slug}/">${escapeHtml(blog.shortTitle)}</a></h3>
      <p>${escapeHtml(blog.subtitle)}</p>
    </div>
    <div class="blog-card-footer">
      <a class="text-link" href="/blogs/${blog.slug}/">Read the essay <span>→</span></a>
      <a class="code-count" href="/blogs/${blog.slug}/code/">${blog.codeFiles.length} companion ${blog.codeFiles.length === 1 ? "file" : "files"}</a>
    </div>
  </article>`;

const homePage = (blogs) => {
  const latest = blogs.at(-1);
  return page({
    title: `${SITE_NAME} — From first principles to production`,
    description: "Learn software, machine learning, and AI system design by building real systems and evolving them under production constraints.",
    body: `
      <section class="hero shell">
        <div class="hero-copy">
          <span class="eyebrow"><i></i> A BUILD-FIRST SYSTEM DESIGN SERIES</span>
          <h1>Architecture makes sense<br>once the system <em>breaks.</em></h1>
          <p class="hero-lede">A practical path from software foundations to production ML and AI platforms—one real system, one constraint, and one hard trade-off at a time.</p>
          <div class="hero-actions">
            <a class="button button-primary" href="/blogs/${latest.slug}/">Read the latest essay <span>→</span></a>
            <a class="button button-secondary" href="${GITHUB_URL}" target="_blank" rel="noreferrer">Explore the code <span>↗</span></a>
          </div>
        </div>
        <div class="hero-system" aria-label="The series progression from software systems to AI platforms">
          <div class="system-grid"></div>
          <div class="system-node node-input"><small>START HERE</small><strong>Software<br>systems</strong></div>
          <div class="system-line line-one"><span></span></div>
          <div class="system-node node-middle"><small>EVOLVE</small><strong>ML<br>platforms</strong></div>
          <div class="system-line line-two"><span></span></div>
          <div class="system-node node-output"><small>SCALE</small><strong>AI<br>infrastructure</strong></div>
          <div class="pulse pulse-one"></div><div class="pulse pulse-two"></div>
        </div>
      </section>
      <section class="manifesto">
        <div class="shell manifesto-grid">
          <p class="section-number">01 / THE METHOD</p>
          <div>
            <h2>Not a catalog of technology.<br><span>A record of decisions.</span></h2>
            <div class="manifesto-copy">
              <p>We start with the smallest architecture that can honestly work. Then traffic spikes, requirements move, dependencies fail, and the design has to earn every new component.</p>
              <p>Redis, Kafka, Kubernetes, feature stores, and GPUs appear only when the system creates a reason for them—not because an architecture diagram looked empty.</p>
            </div>
          </div>
        </div>
      </section>
      <section class="path-section shell">
        <div class="section-heading">
          <div><p class="section-number">02 / THE PATH</p><h2>From one service<br>to the whole platform.</h2></div>
          <p>Five stages, fifty systems, and a steadily rising level of complexity.</p>
        </div>
        <div class="path-grid">
          <article><span>01</span><div><h3>Software foundations</h3><p>APIs, data models, caching, queues, concurrency, reliability.</p></div><b>10 systems</b></article>
          <article><span>02</span><div><h3>Distributed systems</h3><p>Streaming, coordination, multi-tenancy, and multi-region design.</p></div><b>10 systems</b></article>
          <article><span>03</span><div><h3>ML system design</h3><p>Features, training, serving, ranking, experimentation, and drift.</p></div><b>10 systems</b></article>
          <article><span>04</span><div><h3>Generative AI</h3><p>RAG, LLM inference, gateways, agents, and enterprise copilots.</p></div><b>10 systems</b></article>
          <article><span>05</span><div><h3>AI platforms</h3><p>Control planes, evaluation, governance, global serving, and cost.</p></div><b>10 systems</b></article>
        </div>
      </section>
      <section class="latest-section">
        <div class="shell">
          <div class="section-heading compact"><div><p class="section-number">03 / NOW PUBLISHING</p><h2>Read. Build. Break. Repeat.</h2></div><a class="text-link" href="/blogs/">View all writing <span>→</span></a></div>
          ${blogCard(latest, true)}
        </div>
      </section>
      <section class="principles shell">
        <p class="section-number">04 / WHAT EVERY DESIGN ANSWERS</p>
        <div class="principle-grid">
          <article><span>Q1</span><h3>What are we actually building?</h3><p>Requirements and constraints come before components.</p></article>
          <article><span>Q2</span><h3>Why this architecture?</h3><p>Every box must solve a specific, visible problem.</p></article>
          <article><span>Q3</span><h3>What changes at scale?</h3><p>The design evolves when the workload earns it.</p></article>
          <article><span>Q4</span><h3>How does it fail?</h3><p>Reliability and observability are part of the design.</p></article>
        </div>
      </section>`,
  });
};

const blogsPage = (blogs) =>
  page({
    title: `Writing — ${SITE_NAME}`,
    description: "All published essays and companion code from the Designing ML Systems series.",
    active: "blogs",
    body: `
      <section class="page-hero shell">
        <span class="eyebrow"><i></i> THE SERIES</span>
        <h1>Systems, explained<br>from the inside out.</h1>
        <p>Every essay starts with a plain requirement and follows the architecture as new constraints force it to grow.</p>
      </section>
      <section class="writing-list shell">
        <div class="list-header"><span>${String(blogs.length).padStart(2, "0")} published</span><span>Newest first</span></div>
        ${blogs.slice().reverse().map((blog) => blogCard(blog)).join("")}
      </section>`,
  });

const articlePage = (blog, previous, next) => {
  const content = articleMarkdown(blog.source);
  const headings = extractHeadings(content);
  const sourceUrl = `${GITHUB_URL}/blob/main/blogs/${blog.slug}/README.md`;
  const toc = headings
    .filter((heading) => heading.level === 2)
    .map((heading) => `<a href="#${heading.id}">${escapeHtml(heading.text)}</a>`)
    .join("");

  return page({
    title: `${blog.title} — ${SITE_NAME}`,
    description: blog.subtitle,
    active: "blogs",
    article: true,
    body: `
      <article class="article-shell shell">
        <header class="article-hero">
          <div class="breadcrumbs"><a href="/blogs/">Writing</a><span>/</span><span>Essay ${String(blog.number).padStart(2, "0")}</span></div>
          <h1>${escapeHtml(blog.shortTitle)}</h1>
          <p>${escapeHtml(blog.subtitle)}</p>
          <div class="article-meta"><span>${blog.readTime} min read</span><span>${blog.codeFiles.length} companion ${blog.codeFiles.length === 1 ? "file" : "files"}</span><a href="${sourceUrl}" target="_blank" rel="noreferrer">Edit on GitHub ↗</a></div>
        </header>
        <div class="article-layout">
          <aside class="article-toc"><p>On this page</p>${toc}</aside>
          <div class="article-content prose">${renderMarkdown(content)}</div>
          <aside class="article-aside">
            <div class="aside-card"><span class="eyebrow">COMPANION REPO</span><h3>Read the source.</h3><p>Browse runnable code, configuration, tests, and notes for this essay.</p><a class="button button-primary" href="/blogs/${blog.slug}/code/">Open code <span>→</span></a></div>
          </aside>
        </div>
        <nav class="article-pagination" aria-label="Article pagination">
          ${previous ? `<a href="/blogs/${previous.slug}/"><small>← Previous</small><strong>${escapeHtml(previous.shortTitle)}</strong></a>` : `<span></span>`}
          ${next ? `<a class="next" href="/blogs/${next.slug}/"><small>Next →</small><strong>${escapeHtml(next.shortTitle)}</strong></a>` : `<a class="next" href="/blogs/"><small>Continue</small><strong>All writing →</strong></a>`}
        </nav>
      </article>`,
  });
};

const codeIndexPage = (blog) => {
  const sourceUrl = `${GITHUB_URL}/tree/main/blogs/${blog.slug}/code`;
  const fileRows = blog.codeFiles.length
    ? blog.codeFiles.map((file) => `
      <a class="file-row" href="${codeRoute(blog, file.relative)}">
        <span class="file-type">${fileIcon(file.relative)}</span>
        <span><strong>${escapeHtml(file.relative)}</strong><small>View rendered source</small></span>
        <span>→</span>
      </a>`).join("")
    : `<div class="empty-state"><p>No companion code has been published for this essay yet.</p></div>`;

  return page({
    title: `Code for ${blog.shortTitle} — ${SITE_NAME}`,
    description: `Companion code and implementation notes for ${blog.title}.`,
    active: "blogs",
    body: `
      <section class="code-hero shell">
        <div class="breadcrumbs"><a href="/blogs/">Writing</a><span>/</span><a href="/blogs/${blog.slug}/">${escapeHtml(blog.shortTitle)}</a><span>/</span><span>Code</span></div>
        <span class="eyebrow"><i></i> COMPANION CODE</span>
        <h1>${escapeHtml(blog.shortTitle)}</h1>
        <p>Source files, runnable services, tests, configuration, and implementation notes that accompany the design.</p>
        <div class="hero-actions"><a class="button button-primary" href="${sourceUrl}" target="_blank" rel="noreferrer">Open on GitHub <span>↗</span></a><a class="button button-secondary" href="/blogs/${blog.slug}/">Read the essay <span>→</span></a></div>
      </section>
      <section class="code-browser shell">
        <div class="browser-header"><div><span></span><span></span><span></span></div><p>blogs / ${escapeHtml(blog.slug)} / code</p><small>${blog.codeFiles.length} ${blog.codeFiles.length === 1 ? "file" : "files"}</small></div>
        <div class="file-list">${fileRows}</div>
      </section>`,
  });
};

const renderCodeFile = async (blog, file) => {
  const fileStats = await stat(file.absolute);
  const isText = fileStats.size < 300_000;
  const source = isText ? await readFile(file.absolute, "utf8") : "This file is too large to render in the browser.";
  const id = `source-${slugify(file.relative)}`;
  const githubUrl = `${GITHUB_URL}/blob/main/blogs/${blog.slug}/code/${file.relative.split(path.sep).map(encodeURIComponent).join("/")}`;
  const markdownPreview = [".md", ".mdx"].includes(path.extname(file.relative).toLowerCase())
    ? `<section class="rendered-file prose"><div class="source-label"><span>Rendered preview</span></div>${renderMarkdown(source)}</section>`
    : "";

  return page({
    title: `${file.relative} — ${blog.shortTitle}`,
    description: `${file.relative}, companion source for ${blog.title}.`,
    active: "blogs",
    body: `
      <section class="file-page shell">
        <div class="breadcrumbs"><a href="/blogs/">Writing</a><span>/</span><a href="/blogs/${blog.slug}/">${escapeHtml(blog.shortTitle)}</a><span>/</span><a href="/blogs/${blog.slug}/code/">Code</a></div>
        <div class="file-title-row"><div><span class="file-type">${fileIcon(file.relative)}</span><h1>${escapeHtml(file.relative)}</h1></div><a class="button button-secondary" href="${githubUrl}" target="_blank" rel="noreferrer">GitHub <span>↗</span></a></div>
        <div class="file-stats"><span>${source.split("\n").length} lines</span><span>${humanFileSize(fileStats.size)}</span></div>
        ${markdownPreview}
        <section class="source-view">
          <div class="source-label"><span>Raw source</span><button type="button" data-copy="${id}">Copy</button></div>
          <pre><code id="${id}">${escapeHtml(source)}</code></pre>
        </section>
      </section>`,
  });
};

const aboutPage = () =>
  page({
    title: `About — ${SITE_NAME}`,
    description: "Why Designing ML Systems teaches architecture through real systems, changing constraints, and working code.",
    active: "about",
    body: `
      <section class="page-hero about-hero shell">
        <span class="eyebrow"><i></i> ABOUT THE SERIES</span>
        <h1>Learn the decision,<br>not the diagram.</h1>
        <p>Designing ML Systems is a public, build-first curriculum for developing architectural judgment—from software fundamentals to global AI platforms.</p>
      </section>
      <section class="about-body shell">
        <div class="about-statement"><p class="section-number">THE PREMISE</p><h2>A finished architecture hides the most useful part: how it got there.</h2></div>
        <div class="about-columns"><p>Each system begins small. We clarify requirements, estimate scale, define APIs and data models, and build the first version we can defend. Then the conditions change.</p><p>Traffic spikes. Two requests race. A region fails. A tenant becomes noisy. Latency budgets shrink. The architecture evolves, and every new component has to justify its operational cost.</p></div>
      </section>
      <section class="values-section">
        <div class="shell value-grid">
          <article><span>01</span><h3>First principles</h3><p>Start with the workload, access patterns, and guarantees—not a familiar stack.</p></article>
          <article><span>02</span><h3>Working systems</h3><p>Code, deployment, load tests, and failure behavior make the architecture concrete.</p></article>
          <article><span>03</span><h3>Visible trade-offs</h3><p>There is rarely one correct design. The useful answer explains what would change it.</p></article>
        </div>
      </section>
      <section class="about-cta shell"><p class="section-number">START HERE</p><h2>One long URL.<br>Then a few million clicks.</h2><div class="hero-actions"><a class="button button-primary" href="/blogs/01-introduction/">Read the introduction <span>→</span></a><a class="button button-secondary" href="${GITHUB_URL}" target="_blank" rel="noreferrer">Follow on GitHub <span>↗</span></a></div></section>`,
  });

const build = async () => {
  await rm(DIST_DIR, { recursive: true, force: true });
  await mkdir(DIST_DIR, { recursive: true });
  await Promise.all([
    copyFile(path.join(ROOT, "site", "styles.css"), path.join(DIST_DIR, "styles.css")),
    copyFile(path.join(ROOT, "site", "site.js"), path.join(DIST_DIR, "site.js")),
    copyFile(path.join(ROOT, "site", "favicon.svg"), path.join(DIST_DIR, "favicon.svg")),
  ]);

  const blogs = await loadBlogs();
  if (!blogs.length) throw new Error("No blog folders were found in blogs/.");

  await writePage("", homePage(blogs));
  await writePage("blogs", blogsPage(blogs));
  await writePage("about", aboutPage());

  for (const [index, blog] of blogs.entries()) {
    await writePage(`blogs/${blog.slug}`, articlePage(blog, blogs[index - 1], blogs[index + 1]));
    await writePage(`blogs/${blog.slug}/code`, codeIndexPage(blog));

    for (const asset of blog.assetFiles) {
      const target = path.join(DIST_DIR, "blogs", blog.slug, "assets", asset.relative);
      await mkdir(path.dirname(target), { recursive: true });
      await copyFile(asset.absolute, target);
    }

    for (const file of blog.codeFiles) {
      await writePage(
        `blogs/${blog.slug}/code/${file.relative.split(path.sep).map(encodeURIComponent).join("/")}`,
        await renderCodeFile(blog, file),
      );
    }
  }

  console.log(`Built ${blogs.length} blog${blogs.length === 1 ? "" : "s"} into dist/.`);
};

await build();
