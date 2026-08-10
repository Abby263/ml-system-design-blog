import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";

const ROOT = process.cwd();
const OUT = path.join(ROOT, "blogs/20-ml-system-design-prerequisites/assets");
const C = {
  ink: "#172033",
  muted: "#596579",
  paper: "#fffdf6",
  blue: "#dbeafe",
  purple: "#ede9fe",
  green: "#dcfce7",
  yellow: "#fef3c7",
  pink: "#fce7f3",
  orange: "#ffedd5",
  red: "#b91c1c",
  line: "#94a3b8",
};

const esc = (value) => String(value)
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;");

const text = (x, y, value, size = 22, options = {}) => {
  const lines = String(value).split("\n");
  const anchor = options.anchor ?? "start";
  const weight = options.weight ?? 600;
  const color = options.color ?? C.ink;
  const family = options.mono ? "ui-monospace, SFMono-Regular, Menlo, monospace" : "Inter, Arial, sans-serif";
  return `<text x="${x}" y="${y}" text-anchor="${anchor}" fill="${color}" font-family="${family}" font-size="${size}" font-weight="${weight}">${lines.map((line, index) => `<tspan x="${x}" dy="${index ? size * 1.28 : 0}">${esc(line)}</tspan>`).join("")}</text>`;
};

const box = (x, y, width, height, title, subtitle = "", fill = C.paper, options = {}) => {
  const titleSize = options.titleSize ?? 21;
  const titleLineCount = String(title).split("\n").length;
  const titleY = y + (subtitle ? 32 : height / 2 + 7);
  const subtitleY = y + 32 + titleLineCount * titleSize * 1.28 + 12;
  const subtitleLines = subtitle ? text(x + width / 2, subtitleY, subtitle, options.subtitleSize ?? 16, { anchor: "middle", color: C.muted, weight: 500 }) : "";
  return `<g><rect x="${x}" y="${y}" width="${width}" height="${height}" rx="${options.radius ?? 14}" fill="${fill}" stroke="${options.stroke ?? C.ink}" stroke-width="${options.strokeWidth ?? 2}" ${options.dashed ? 'stroke-dasharray="9 7"' : ""}/>${text(x + width / 2, titleY, title, titleSize, { anchor: "middle", weight: 750 })}${subtitleLines}</g>`;
};

const arrow = (x1, y1, x2, y2, options = {}) => {
  const color = options.color ?? C.ink;
  const label = options.label ? text((x1 + x2) / 2, (y1 + y2) / 2 - 10, options.label, 14, { anchor: "middle", color, weight: 650, mono: true }) : "";
  return `<path d="M${x1} ${y1} L${x2} ${y2}" fill="none" stroke="${color}" stroke-width="${options.width ?? 2.5}" stroke-linecap="round" ${options.dashed ? 'stroke-dasharray="9 8"' : ""} marker-end="url(#arrow)"/>${label}`;
};

const base = (titleValue, description, body, width = 1400, height = 820) => `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" role="img" aria-labelledby="title desc">
  <title id="title">${esc(titleValue)}</title>
  <desc id="desc">${esc(description)}</desc>
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M0 0 10 5 0 10Z" fill="context-stroke"/></marker>
    <pattern id="grid" width="28" height="28" patternUnits="userSpaceOnUse"><path d="M28 0H0V28" fill="none" stroke="#dbe1e8" stroke-width="1"/></pattern>
  </defs>
  <rect width="100%" height="100%" fill="${C.paper}"/>
  <rect x="18" y="18" width="${width - 36}" height="${height - 36}" rx="18" fill="none" stroke="${C.ink}" stroke-width="2"/>
  ${body}
</svg>`;

const prerequisiteMap = () => {
  const branches = [
    [60, 150, "Software +\ndistributed systems", "APIs · caches · queues\npartitioning · deadlines", C.blue],
    [325, 150, "Data\nengineering", "batch · streaming\nevent time · backfills", C.green],
    [590, 150, "Machine learning\nfundamentals", "targets · losses · ranking\ncalibration · embeddings", C.purple],
    [855, 150, "Evaluation +\nexperimentation", "temporal splits · slices\nshadow · A/B tests", C.yellow],
    [1120, 150, "Production\noperations", "lineage · rollback · drift\nprivacy · cost", C.pink],
  ];
  const cards = branches.map(([x, y, titleValue, subtitle, fill]) => box(x, y, 220, 165, titleValue, subtitle, fill, { titleSize: 20, subtitleSize: 15 })).join("");
  const links = branches.map(([x]) => arrow(x + 110, 315, 700, 510, { dashed: true, color: C.muted })).join("");
  return base(
    "ML system design prerequisite dependency map",
    "Five prerequisite branches converge into interview readiness and production decision reasoning.",
    `${text(60, 78, "PREREQUISITES ARE DEPENDENCIES, NOT A CHECKLIST", 27, { weight: 800 })}${text(60, 112, "Each branch answers a different class of interviewer follow-up.", 17, { color: C.muted, weight: 500 })}${cards}${links}${box(470, 510, 460, 145, "ML system design readiness", "decision → data → model → serving → learning\nwith explicit trade-offs and failure behavior", C.orange, { titleSize: 28, subtitleSize: 18 })}${arrow(700, 655, 700, 724, { color: C.red })}${text(700, 760, "Can you explain what changes the design?", 22, { anchor: "middle", color: C.red, weight: 750 })}`,
  );
};

const interviewRoadmap = () => {
  const phases = [
    [55, 155, 245, 145, "1 · CONTRACT", "decision · scope\nFR / NFR", C.yellow, "0–8 min"],
    [330, 155, 245, 145, "2 · MEASURE", "metrics · scale\nlatency budget", C.blue, "8–15 min"],
    [605, 155, 245, 145, "3 · HLD V0", "smallest full loop\nbaseline first", C.green, "15–25 min"],
    [880, 155, 245, 145, "4 · DEEP DIVE", "data · model\nserving path", C.purple, "25–43 min"],
    [1155, 155, 190, 145, "5 · PROVE", "failure · release\nsummary", C.pink, "43–60 min"],
  ];
  const top = phases.map(([x, y, w, h, titleValue, subtitle, fill, timing]) => `${box(x, y, w, h, titleValue, subtitle, fill, { titleSize: 19, subtitleSize: 16 })}${text(x + w / 2, y - 22, timing, 14, { anchor: "middle", color: C.muted, mono: true })}`).join("");
  const phaseArrows = phases.slice(0, -1).map((phase, i) => arrow(phase[0] + phase[2], 228, phases[i + 1][0], 228)).join("");
  const canonical = [
    [70, 410, "Prompt", "Business + scope", "FR / NFR", C.yellow],
    [290, 410, "Intelligence", "Success metrics", "Estimation", C.blue],
    [510, 410, "HLD V0", "Evolution", "Data + labels", C.green],
    [730, 410, "Features + models", "Online path", "Reliability", C.purple],
    [950, 410, "LLD", "Final board", "References + next", C.pink],
  ].map(([x, y, a, b, c, fill]) => box(x, y, 185, 165, a, `${b}\n${c}`, fill, { titleSize: 18, subtitleSize: 15 })).join("");
  return base(
    "ML system design interview roadmap",
    "A sixty-minute sequence maps the canonical headings to five interview phases.",
    `${text(55, 78, "THE CANONICAL TEMPLATE IS ALSO A CLOCK", 27, { weight: 800 })}${text(55, 112, "Spend the most time where requirements create a real trade-off.", 17, { color: C.muted, weight: 500 })}${top}${phaseArrows}${text(70, 375, "CANONICAL H2 SPINE", 15, { color: C.muted, mono: true, weight: 750 })}${canonical}${box(1160, 410, 180, 165, "FOLLOW-UPS", "Why this model?\nWhy synchronous?\nWhat fails?", C.orange, { titleSize: 18, subtitleSize: 15 })}${text(700, 690, "The board should evolve; do not erase the assumptions that earned each box.", 21, { anchor: "middle", color: C.red, weight: 700 })}`,
  );
};

const decisionLearningLoop = () => {
  const nodes = [
    [540, 100, 320, 100, "Product decision", "recipient · deadline · action", C.yellow],
    [940, 230, 300, 100, "Decision + exposure log", "candidates · versions · action", C.blue],
    [940, 475, 300, 100, "Outcomes + labels", "delay · source · confidence", C.pink],
    [540, 625, 320, 100, "Point-in-time dataset", "features as known at decision", C.green],
    [150, 475, 300, 100, "Train + evaluate", "baseline · slices · guardrails", C.purple],
    [150, 230, 300, 100, "Versioned release", "artifact · policy · rollback", C.orange],
  ];
  const nodeMarkup = nodes.map(([x, y, w, h, t, s, f]) => box(x, y, w, h, t, s, f)).join("");
  const edges = [
    [860, 150, 940, 280, "exposes"], [1090, 330, 1090, 475, "observes"], [940, 525, 860, 675, "joins"],
    [540, 675, 450, 525, "builds"], [300, 475, 300, 330, "promotes"], [450, 280, 540, 150, "serves"],
  ].map(([a,b,c,d,l]) => arrow(a,b,c,d,{label:l,dashed:l==="observes",color:l==="observes"?"#2563eb":C.ink})).join("");
  return base(
    "Decision-to-learning loop",
    "A closed lifecycle connects product decisions to exposure, outcomes, point-in-time data, training, release, and the next decision.",
    `${text(55, 76, "THE PRODUCT ACTION CREATES THE NEXT TRAINING DISTRIBUTION", 26, { weight: 800 })}${text(55, 110, "Log what was considered, not only what was clicked or approved.", 17, { color: C.muted, weight: 500 })}${nodeMarkup}${edges}${box(515, 340, 370, 135, "Feedback-loop checkpoint", "What outcomes became unobservable\nbecause the current policy acted?", C.paper, { dashed: true, stroke: C.red, titleSize: 23 })}`,
  );
};

const estimationWhiteboard = () => {
  const formulas = [
    [55, 155, "TRAFFIC", "100M decisions/day\n÷ 86,400 = 1,157 avg RPS\n× 5 peak = 5,800 RPS", C.blue],
    [365, 155, "EVENTS", "100M × 3 KB\n≈ 300 GB/day\nbefore replicas + indexes", C.green],
    [675, 155, "CONCURRENCY", "5,800 RPS × 0.040 s\n≈ 232 requests\nin flight", C.yellow],
    [985, 155, "REPLICAS", "5,800 ÷ 250 safe RPS\n× headroom\n≈ 24 replicas", C.purple],
  ];
  const cards = formulas.map(([x, y, titleValue, subtitle, fill]) => box(x, y, 270, 195, titleValue, subtitle, fill, { titleSize: 20, subtitleSize: 17 })).join("");
  const waterfall = [
    [75, 535, 85, "5 ms", "validate", C.blue], [160, 535, 280, "20 ms", "features", C.green],
    [440, 535, 140, "10 ms", "rules", C.yellow], [580, 535, 210, "15 ms", "model", C.purple],
    [790, 535, 140, "10 ms", "ledger", C.orange], [930, 535, 345, "20 ms", "network + tail reserve", C.pink],
  ].map(([x, y, w, label, sub, fill]) => `<g><rect x="${x}" y="${y}" width="${w}" height="90" fill="${fill}" stroke="${C.ink}" stroke-width="2"/>${text(x + w/2, y + 38, label, 20, {anchor:"middle",weight:800})}${text(x + w/2, y + 67, sub, 13, {anchor:"middle",color:C.muted,weight:600})}</g>`).join("");
  return base(
    "Back-of-the-envelope estimation whiteboard",
    "Traffic, event storage, concurrency, replica count, and latency budget calculations drive architecture choices.",
    `${text(55, 78, "ESTIMATE UNTIL A NUMBER CHANGES THE DESIGN", 27, { weight: 800 })}${text(55, 112, "Write assumptions beside results so the interviewer can change either.", 17, { color: C.muted, weight: 500 })}${cards}${arrow(325, 253, 365, 253)}${arrow(635, 253, 675, 253)}${arrow(945, 253, 985, 253)}${text(75, 485, "80 MS INTERNAL DECISION BUDGET", 17, { color: C.red, mono: true, weight: 800 })}${waterfall}${text(75, 685, "Forces: batch feature reads · preloaded model · child deadlines · explicit reserve", 20, { color: C.red, weight: 700 })}`,
  );
};

const twoPlaneArchitecture = () => {
  const online = [
    [55, 150, 160, "Request", "deadline", C.paper], [275, 150, 245, "Decision service", "validate · orchestrate", C.blue],
    [580, 150, 210, "Online features", "batch-get · freshness", C.green], [850, 150, 190, "Model", "preloaded artifact", C.purple],
    [1100, 150, 210, "Policy + response", "constraints · action", C.yellow],
  ].map(([x,y,w,t,s,f]) => box(x,y,w,115,t,s,f,{titleSize:19,subtitleSize:15})).join("");
  const onlineArrows = [[215,207,275,207],[520,207,580,207],[790,207,850,207],[1040,207,1100,207]].map(v=>arrow(...v)).join("");
  const asyncNodes = [
    [55, 510, 195, "Event log", "durable + replayable", C.blue], [300, 510, 195, "Point-in-time data", "backfill + validate", C.green],
    [545, 510, 195, "Train + evaluate", "baseline + slices", C.purple], [790, 510, 195, "Registry", "lineage + compatibility", C.orange],
    [1035, 510, 195, "Rollout control", "shadow · canary", C.yellow], [1260, 510, 90, "Next", "bundle", C.pink],
  ].map(([x,y,w,t,s,f]) => box(x,y,w,115,t,s,f,{titleSize:18,subtitleSize:14})).join("");
  const asyncArrows = [[250,567,300,567],[495,567,545,567],[740,567,790,567],[985,567,1035,567],[1230,567,1260,567]].map(v=>arrow(...v,{dashed:true,color:"#2563eb"})).join("");
  return base(
    "Synchronous prediction path and asynchronous learning plane",
    "The bounded online decision path is separated from replayable data, training, registry, rollout, and feedback workflows.",
    `${text(55, 78, "TWO PLANES, TWO FAILURE CONTRACTS", 27, { weight: 800 })}${text(55, 112, "Solid arrows spend the caller’s deadline. Dashed arrows improve a future decision.", 17, { color: C.muted, weight: 500 })}${text(55, 136, "SYNC · CALLER WAITS", 14, { color: C.red, mono: true, weight: 800 })}${online}${onlineArrows}${text(55, 480, "ASYNC · DURABLE, RETRYABLE, IDEMPOTENT", 14, { color: "#2563eb", mono: true, weight: 800 })}${asyncNodes}${asyncArrows}<path d="M1205 265V455H152V510" fill="none" stroke="#2563eb" stroke-width="2.5" stroke-dasharray="9 8" marker-end="url(#arrow)"/>${text(865, 447, "decision + exposure", 14, { anchor: "middle", color: "#2563eb", mono: true, weight: 700 })}<path d="M1140 510V445H1035L945 265" fill="none" stroke="#2563eb" stroke-width="2.5" stroke-dasharray="9 8" marker-end="url(#arrow)"/>${text(1115, 395, "immutable bundle", 14, { anchor: "middle", color: "#2563eb", mono: true, weight: 700 })}${box(430, 335, 540, 90, "Control-plane outage must not stop a healthy prediction path", "Serve the last-known-good compatible bundle.", C.paper, { dashed: true, stroke: C.red, titleSize: 20, subtitleSize: 15 })}`,
  );
};

const failureMatrix = () => {
  const rows = [
    ["FEATURES", "freshness / timeout", "default or smaller model", "parity + age recover", C.green],
    ["MODEL", "load / schema error", "last-known-good", "shadow + checksum", C.purple],
    ["STREAM", "lag / hot partition", "bounded stale state", "drain without duplicates", C.blue],
    ["LABELS", "source / rate shift", "pause promotion", "mature cohort audit", C.pink],
    ["REGION", "health / RTO breach", "allowed healthy cell", "replay + residency proof", C.orange],
  ];
  const header = [
    [55, "DEPENDENCY", 185], [240, "DETECT", 285], [525, "SAFE BEHAVIOR", 350], [875, "RECOVERY PROOF", 470],
  ].map(([x,t,w]) => `<rect x="${x}" y="145" width="${w}" height="70" fill="${C.ink}"/>${text(x+18,188,t,15,{color:C.paper,mono:true,weight:800})}`).join("");
  const body = rows.map(([dep,detect,safe,proof,fill],i) => {
    const y=215+i*105;
    return `<rect x="55" y="${y}" width="185" height="105" fill="${fill}" stroke="${C.ink}" stroke-width="1.5"/>${text(74,y+60,dep,17,{mono:true,weight:800})}<rect x="240" y="${y}" width="285" height="105" fill="${C.paper}" stroke="${C.ink}" stroke-width="1.5"/>${text(258,y+60,detect,17,{weight:600})}<rect x="525" y="${y}" width="350" height="105" fill="${C.paper}" stroke="${C.ink}" stroke-width="1.5"/>${text(543,y+60,safe,17,{weight:600})}<rect x="875" y="${y}" width="470" height="105" fill="${C.paper}" stroke="${C.ink}" stroke-width="1.5"/>${text(893,y+60,proof,17,{weight:600})}`;
  }).join("");
  return base(
    "ML failure and recovery matrix",
    "A matrix maps feature, model, stream, label, and regional failures to detection, safe behavior, and recovery evidence.",
    `${text(55, 78, "A FALLBACK IS INCOMPLETE WITHOUT RECOVERY EVIDENCE", 27, { weight: 800 })}${text(55, 112, "Monitor software health, data health, and decision health together.", 17, { color: C.muted, weight: 500 })}${header}${body}${text(700, 776, "Never turn missing or stale evidence silently into a valid zero.", 20, { anchor: "middle", color: C.red, weight: 750 })}`,
  );
};

await mkdir(OUT, { recursive: true });
const diagrams = {
  "prerequisite-map.svg": prerequisiteMap(),
  "interview-roadmap.svg": interviewRoadmap(),
  "decision-learning-loop.svg": decisionLearningLoop(),
  "estimation-whiteboard.svg": estimationWhiteboard(),
  "two-plane-architecture.svg": twoPlaneArchitecture(),
  "failure-matrix.svg": failureMatrix(),
};

for (const [name, svg] of Object.entries(diagrams)) {
  await writeFile(path.join(OUT, name), `${svg}\n`);
}

console.log(`Generated ${Object.keys(diagrams).length} ML primer diagrams.`);
