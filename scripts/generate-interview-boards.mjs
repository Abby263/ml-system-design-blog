import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';

const ROOT = process.cwd();
const COLORS = {
  ink: '#1f2937', muted: '#53606f', paper: '#fffdf6', blue: '#dbeafe',
  yellow: '#fef3c7', green: '#dcfce7', pink: '#fce7f3', purple: '#ede9fe', red: '#dc2626',
};
let serial = 0;
const uid = (prefix = 'el') => `${prefix}-${++serial}`;
const esc = (s) => String(s).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;');

function box(x, y, w, h, label, opts = {}) {
  return { kind: 'box', x, y, w, h, label, fill: opts.fill ?? COLORS.paper, stroke: opts.stroke ?? COLORS.ink,
    size: opts.size ?? 25, sub: opts.sub ?? '', dashed: opts.dashed ?? false, align: opts.align ?? 'center' };
}
function note(x, y, w, h, title, lines, opts = {}) {
  return { kind: 'note', x, y, w, h, title, lines, fill: opts.fill ?? COLORS.yellow, stroke: opts.stroke ?? COLORS.ink };
}
function textOp(x, y, text, size = 24, opts = {}) {
  return { kind: 'text', x, y, text, size, color: opts.color ?? COLORS.ink, weight: opts.weight ?? 600,
    anchor: opts.anchor ?? 'start', family: opts.family ?? 'Virgil, Comic Sans MS, cursive' };
}
function arrow(x1, y1, x2, y2, opts = {}) {
  return { kind: 'arrow', x1, y1, x2, y2, dashed: opts.dashed ?? false, color: opts.color ?? COLORS.ink,
    label: opts.label ?? '', bend: opts.bend ?? 0 };
}
function scribble(x1, y1, x2, y2, opts = {}) {
  return { kind: 'scribble', x1, y1, x2, y2, color: opts.color ?? COLORS.red, width: opts.width ?? 4 };
}

const recFrames = [
  {
    slug: '01-scope-and-v0', title: '01 · CLARIFY BEFORE DRAWING', subtitle: 'Recommendation system interview — assumptions create the first architecture',
    ops: [
      note(55, 120, 330, 245, 'PRODUCT CONTRACT', ['Home feed · 20 videos', '10M+ active items', 'Fresh upload < 15 min', 'Hard policy eligibility'], { fill: COLORS.yellow }),
      note(55, 405, 330, 215, 'NFR / SCALE', ['p99 < 200 ms', '~58K peak feed RPS', 'Session signal < 1 min', 'Safe fallback required'], { fill: COLORS.blue }),
      note(55, 660, 330, 155, 'MEASURE', ['Quality watch + retention', 'Hide/report guardrails', 'Recall@K · NDCG · latency'], { fill: COLORS.green }),
      textOp(455, 120, 'Intelligence boundary', 27),
      box(455, 170, 260, 105, 'Learned', { fill: COLORS.purple, sub: 'retrieve + predict outcomes' }),
      box(770, 170, 280, 105, 'Deterministic', { fill: COLORS.green, sub: 'eligibility + slate policy' }),
      arrow(715, 222, 770, 222, { label: 'bounded by' }),
      textOp(455, 350, 'HLD V0 — smallest credible loop', 29),
      box(455, 420, 200, 105, 'Feed request', { sub: 'user · session' }),
      box(735, 420, 265, 105, 'Modular feed service', { fill: COLORS.blue, sub: 'heuristics + GBDT + slate' }),
      box(1080, 420, 210, 105, '20 videos', { fill: COLORS.green, sub: 'request_id' }),
      arrow(655, 472, 735, 472), arrow(1000, 472, 1080, 472),
      box(735, 625, 265, 95, 'Exposure log', { fill: COLORS.yellow, sub: 'shown + position + versions' }),
      box(1080, 625, 210, 95, 'Daily retrain', { fill: COLORS.purple, sub: 'point-in-time data' }),
      arrow(1185, 525, 1185, 625, { dashed: true, label: 'async outcomes' }),
      arrow(1080, 672, 1000, 672, { dashed: true }),
      textOp(455, 785, 'Rejected:', 22, { color: COLORS.red }),
      textOp(575, 785, 'score every item with one heavy model', 22, { color: COLORS.muted }),
      scribble(570, 800, 1015, 775),
      textOp(1110, 780, 'Why? 10M × request ≫ 200 ms', 20, { color: COLORS.red }),
    ],
  },
  {
    slug: '02-critical-path-and-learning', title: '02 · V1 EARNS A MULTI-STAGE FUNNEL', subtitle: 'Solid arrows are on the request deadline; dashed arrows are background work',
    ops: [
      textOp(55, 120, 'SYNC · USER WAITS · p99 200 ms', 23, { color: COLORS.red }),
      box(55, 195, 170, 105, 'Request', { sub: 'deadline tree' }),
      box(300, 145, 245, 205, 'Parallel retrieval', { fill: COLORS.blue, sub: 'ANN · follows · co-watch\ntrending · fresh · explore' }),
      box(620, 195, 190, 105, 'Merge + gate', { fill: COLORS.green, sub: '≈5K eligible' }),
      box(880, 195, 180, 105, 'Pre-rank', { fill: COLORS.yellow, sub: '5K → 1K' }),
      box(1130, 195, 180, 105, 'Heavy rank', { fill: COLORS.purple, sub: '1K → 200' }),
      box(1375, 195, 170, 105, 'Slate', { fill: COLORS.green, sub: '200 → 20' }),
      arrow(225, 247, 300, 247), arrow(545, 247, 620, 247), arrow(810, 247, 880, 247),
      arrow(1060, 247, 1130, 247), arrow(1310, 247, 1375, 247),
      textOp(325, 390, '45 ms', 21, { color: COLORS.red }), textOp(675, 390, 'gate first', 21),
      textOp(915, 390, '20 ms', 21, { color: COLORS.red }), textOp(1170, 390, '55 ms batched', 21, { color: COLORS.red }),
      note(55, 455, 310, 190, 'TAIL-LATENCY RULE', ['Per-source child deadline', 'Accept partial candidates', 'Never wait 300 ms for one source'], { fill: COLORS.pink }),
      note(55, 680, 310, 145, 'FALLBACK', ['Trending + subscriptions', 'Cached policy-safe inventory'], { fill: COLORS.green }),
      textOp(435, 485, 'ASYNC · LEARNING LOOP', 23, { color: '#2563eb' }),
      box(435, 550, 210, 100, 'Exposure events', { fill: COLORS.blue, sub: 'candidates + shown' }),
      box(720, 550, 210, 100, 'Point-in-time set', { fill: COLORS.yellow, sub: 'outcomes + propensity' }),
      box(1005, 550, 210, 100, 'Train + evaluate', { fill: COLORS.purple, sub: 'chronological replay' }),
      box(1290, 550, 210, 100, 'Versioned bundle', { fill: COLORS.green, sub: 'shadow → canary' }),
      arrow(1455, 300, 1455, 550, { dashed: true, color: '#2563eb', label: 'log' }),
      arrow(645, 600, 720, 600, { dashed: true, color: '#2563eb' }),
      arrow(930, 600, 1005, 600, { dashed: true, color: '#2563eb' }),
      arrow(1215, 600, 1290, 600, { dashed: true, color: '#2563eb' }),
      arrow(1395, 550, 1200, 350, { dashed: true, color: '#2563eb', label: 'immutable release' }),
      textOp(435, 755, 'Interview checkpoint:', 22),
      textOp(675, 755, 'retrieval owns recall; ranker owns precision; policy owns the product decision.', 21, { color: COLORS.muted }),
    ],
  },
  {
    slug: '03-global-and-degraded', title: '03 · V2 ADDS CELLS ONLY WHEN SCALE DEMANDS THEM', subtitle: 'Region-local serving, globally coordinated releases, explicit degraded modes',
    ops: [
      box(55, 165, 220, 105, 'Global router', { fill: COLORS.blue, sub: 'home / healthy region' }),
      box(365, 125, 400, 245, 'Regional cell · NA', { fill: COLORS.green, sub: 'candidate shards\nfeature KV + cache\nCPU pre-rank · GPU rank\nlocal exposure log' }),
      box(835, 125, 400, 245, 'Regional cell · EU', { fill: COLORS.green, sub: 'candidate shards\nfeature KV + cache\nCPU pre-rank · GPU rank\nlocal exposure log' }),
      arrow(275, 217, 365, 217), arrow(275, 217, 835, 217),
      scribble(790, 115, 790, 385, { color: COLORS.red, width: 3 }),
      textOp(745, 405, 'failure boundary', 19, { color: COLORS.red }),
      note(1280, 125, 270, 245, 'DEGRADE LADDER', ['1. Full personalized', '2. Skip slow source', '3. Smaller ranker', '4. Cached baseline', '5. Safe trending feed'], { fill: COLORS.yellow }),
      textOp(55, 465, 'GLOBAL CONTROL / LEARNING PLANE', 23, { color: '#2563eb' }),
      box(55, 535, 225, 105, 'Event lake', { fill: COLORS.blue, sub: 'exposure + outcomes' }),
      box(355, 535, 225, 105, 'Train + evaluate', { fill: COLORS.purple, sub: 'quality + guardrails' }),
      box(655, 535, 225, 105, 'Model registry', { fill: COLORS.yellow, sub: 'immutable artifacts' }),
      box(955, 535, 225, 105, 'Rollout control', { fill: COLORS.green, sub: 'shadow · canary · rollback' }),
      arrow(280, 587, 355, 587, { dashed: true, color: '#2563eb' }), arrow(580, 587, 655, 587, { dashed: true, color: '#2563eb' }),
      arrow(880, 587, 955, 587, { dashed: true, color: '#2563eb' }),
      arrow(1065, 535, 565, 370, { dashed: true, color: '#2563eb', label: 'bundle' }),
      arrow(1065, 535, 1035, 370, { dashed: true, color: '#2563eb', label: 'bundle' }),
      note(1245, 500, 305, 175, 'WHY MICROSERVICES NOW?', ['Different bottlenecks / owners', 'CPU retrieval vs GPU ranking', 'Fault isolation is measurable'], { fill: COLORS.pink }),
      textOp(55, 760, '10× trigger:', 23, { color: COLORS.red }),
      textOp(195, 760, 'shard ANN + batch inference; do not add synchronous hops to look “distributed.”', 22),
    ],
  },
];

const fraudFrames = [
  {
    slug: '01-decision-and-v0', title: '01 · CLARIFY THE DECISION, NOT “THE MODEL”', subtitle: 'Fraud interview — business actions and deadline define the intelligence boundary',
    ops: [
      note(55, 120, 320, 220, 'BUSINESS DECISION', ['Who: payment customer', 'Protect: money + trust', 'When: before authorization', 'Actions: allow · challenge', 'review · block'], { fill: COLORS.yellow }),
      note(55, 385, 320, 200, 'NFR / SCALE', ['p99 risk budget < 80 ms', '20K peak decisions/s', '99.99% · regional', 'Audit acknowledged decisions'], { fill: COLORS.blue }),
      note(55, 630, 320, 175, 'COST, NOT ACCURACY', ['Fraud loss + false declines', 'Challenge friction', 'Analyst queue capacity'], { fill: COLORS.pink }),
      textOp(445, 120, 'Separate prediction from policy', 28),
      box(445, 175, 245, 105, 'ML model', { fill: COLORS.purple, sub: 'P(fraud | evidence)' }),
      box(765, 175, 285, 105, 'Decision policy', { fill: COLORS.green, sub: 'cost + capacity + rules' }),
      box(1125, 175, 250, 105, 'Action', { fill: COLORS.yellow, sub: 'allow / friction / stop' }),
      arrow(690, 227, 765, 227), arrow(1050, 227, 1125, 227),
      textOp(445, 355, 'HLD V0 — one auditable boundary', 28),
      box(445, 425, 175, 105, 'Pay request', { sub: 'idempotency key' }),
      box(690, 425, 255, 105, 'Fraud service', { fill: COLORS.blue, sub: 'features + rules + GBDT' }),
      box(1015, 425, 190, 105, 'Policy', { fill: COLORS.green, sub: 'action + reasons' }),
      box(1275, 425, 210, 105, 'Ledger', { fill: COLORS.yellow, sub: 'immutable decision' }),
      arrow(620, 477, 690, 477), arrow(945, 477, 1015, 477), arrow(1205, 477, 1275, 477),
      box(1015, 665, 210, 95, 'Labels arrive later', { fill: COLORS.pink, sub: 'review · dispute · appeal' }),
      box(690, 665, 255, 95, 'Chronological train', { fill: COLORS.purple, sub: 'mature outcomes only' }),
      arrow(1380, 530, 1380, 712, { dashed: true, color: '#2563eb', label: 'outcomes' }),
      arrow(1015, 712, 945, 712, { dashed: true, color: '#2563eb' }),
      textOp(445, 815, 'Hard controls remain deterministic. The model may be wrong; the audit trail may not disappear.', 21, { color: COLORS.muted }),
    ],
  },
  {
    slug: '02-critical-path-and-streaming', title: '02 · V1 ADDS FRESH MEMORY WITHOUT LENGTHENING CHECKOUT', subtitle: 'The payment waits for a bounded decision; streaming and learning continue asynchronously',
    ops: [
      textOp(55, 115, 'SYNC · 80 ms INTERNAL DEADLINE', 23, { color: COLORS.red }),
      box(55, 190, 175, 105, 'Request', { sub: 'normalize + dedupe' }),
      box(305, 150, 250, 185, 'Parallel evidence', { fill: COLORS.blue, sub: 'feature batch-get\nhard rules\nexternal snapshots' }),
      box(630, 190, 190, 105, 'GBDT', { fill: COLORS.purple, sub: 'calibrated risk' }),
      box(895, 190, 205, 105, 'Policy', { fill: COLORS.green, sub: 'action + reasons' }),
      box(1175, 190, 190, 105, 'Ledger', { fill: COLORS.yellow, sub: 'append decision' }),
      box(1430, 190, 120, 105, 'Return', { fill: COLORS.green, sub: '<80 ms' }),
      arrow(230, 242, 305, 242), arrow(555, 242, 630, 242), arrow(820, 242, 895, 242),
      arrow(1100, 242, 1175, 242), arrow(1365, 242, 1430, 242),
      textOp(55, 390, 'ASYNC · REPLAYABLE MEMORY + DELAYED TRUTH', 23, { color: '#2563eb' }),
      box(55, 470, 215, 105, 'Canonical log', { fill: COLORS.blue, sub: 'attempts + outcomes' }),
      box(345, 470, 215, 105, 'Stream windows', { fill: COLORS.green, sub: 'event time + dedupe' }),
      box(635, 470, 215, 105, 'Online state', { fill: COLORS.yellow, sub: 'velocity + freshness' }),
      box(925, 470, 215, 105, 'Label join', { fill: COLORS.pink, sub: 'maturity + source' }),
      box(1215, 470, 215, 105, 'Train + replay', { fill: COLORS.purple, sub: 'shadow → canary' }),
      arrow(270, 522, 345, 522, { dashed: true, color: '#2563eb' }), arrow(560, 522, 635, 522, { dashed: true, color: '#2563eb' }),
      arrow(850, 522, 925, 522, { dashed: true, color: '#2563eb' }), arrow(1140, 522, 1215, 522, { dashed: true, color: '#2563eb' }),
      arrow(1270, 295, 165, 470, { dashed: true, color: '#2563eb', label: 'outbox' }),
      arrow(742, 470, 430, 335, { dashed: true, color: '#2563eb', label: 'fresh view' }),
      note(55, 655, 325, 155, 'RETRY RACE', ['Same key + same body → replay', 'Changed body → reject key reuse', 'Dedupe state by event_id'], { fill: COLORS.yellow }),
      note(445, 655, 325, 155, 'STALE FEATURES', ['Carry freshness metadata', 'High-value + ambiguous → challenge', 'Missing is never silently zero'], { fill: COLORS.pink }),
      note(835, 655, 325, 155, 'WHY NOT GRAPH RPC?', ['Unbounded fan-out breaks p99', 'Serve precomputed graph signals', 'Deep traversal stays async'], { fill: COLORS.blue }),
      note(1225, 655, 325, 155, 'MODEL DOWN', ['Hard rules + cached baseline', 'Mark degraded=true', 'Track fallback policy version'], { fill: COLORS.green }),
    ],
  },
  {
    slug: '03-regional-and-failure', title: '03 · V2 MAKES FAILURE AND GLOBAL EVIDENCE EXPLICIT', subtitle: 'Regional cells decide locally; compact risk evidence converges in the background',
    ops: [
      box(55, 155, 220, 105, 'Global router', { fill: COLORS.blue, sub: 'tenant + home region' }),
      box(350, 115, 380, 250, 'Regional risk cell · NA', { fill: COLORS.green, sub: 'gateway + local features\nmodel + policy cache\ndecision ledger\nlast-known-good bundle' }),
      box(805, 115, 380, 250, 'Regional risk cell · EU', { fill: COLORS.green, sub: 'gateway + local features\nmodel + policy cache\ndecision ledger\nlast-known-good bundle' }),
      arrow(275, 207, 350, 207), arrow(275, 207, 805, 207),
      arrow(730, 300, 805, 300, { dashed: true, color: '#2563eb', label: 'compact risk signals' }),
      arrow(805, 335, 730, 335, { dashed: true, color: '#2563eb' }),
      scribble(765, 105, 765, 380, { color: COLORS.red, width: 3 }),
      textOp(720, 405, 'WAN is not on checkout', 20, { color: COLORS.red }),
      note(1260, 115, 290, 250, 'DEGRADED POLICY', ['Features stale → challenge', 'Model down → rules + baseline', 'Review full → cost-aware action', 'Region lost → healthy cell', 'Preserve data residency'], { fill: COLORS.yellow }),
      textOp(55, 480, 'GLOBAL CONTROL + INVESTIGATION (NOT ON THE DEADLINE)', 23, { color: '#2563eb' }),
      box(55, 555, 215, 105, 'Event lake', { fill: COLORS.blue, sub: 'jurisdiction-aware' }),
      box(345, 555, 215, 105, 'Graph + cases', { fill: COLORS.pink, sub: 'rings + analyst evidence' }),
      box(635, 555, 215, 105, 'Train + replay', { fill: COLORS.purple, sub: 'chronological' }),
      box(925, 555, 215, 105, 'Registry', { fill: COLORS.yellow, sub: 'model + policy + features' }),
      box(1215, 555, 215, 105, 'Rollout', { fill: COLORS.green, sub: 'shadow · canary · rollback' }),
      arrow(270, 607, 345, 607, { dashed: true, color: '#2563eb' }), arrow(560, 607, 635, 607, { dashed: true, color: '#2563eb' }),
      arrow(850, 607, 925, 607, { dashed: true, color: '#2563eb' }), arrow(1140, 607, 1215, 607, { dashed: true, color: '#2563eb' }),
      arrow(1322, 555, 995, 365, { dashed: true, color: '#2563eb', label: 'immutable bundle' }),
      note(55, 720, 420, 115, 'STRONG CONSISTENCY — TINY ONLY', ['Confirmed bad token: maybe. Ordinary velocity: no.'], { fill: COLORS.pink }),
      note(540, 720, 420, 115, 'FIRST 10× BOTTLENECK', ['Hot keys → stream partitions → model replicas.'], { fill: COLORS.blue }),
      note(1025, 720, 525, 115, 'RECOVERY PROOF', ['Evacuate · replay · checksum · residency.'], { fill: COLORS.green }),
    ],
  },
];

function svgFor(frame) {
  const body = frame.ops.map((op) => {
    if (op.kind === 'text') return `<text x="${op.x}" y="${op.y}" fill="${op.color}" font-family="${op.family}" font-size="${op.size}" font-weight="${op.weight}" text-anchor="${op.anchor}">${esc(op.text)}</text>`;
    if (op.kind === 'scribble') return `<path d="M ${op.x1} ${op.y1} C ${(op.x1 + op.x2) / 2 - 15} ${op.y1 + 7}, ${(op.x1 + op.x2) / 2 + 15} ${op.y2 - 7}, ${op.x2} ${op.y2}" fill="none" stroke="${op.color}" stroke-width="${op.width}" stroke-linecap="round"/>`;
    if (op.kind === 'arrow') {
      const cx = (op.x1 + op.x2) / 2 + op.bend, cy = (op.y1 + op.y2) / 2 - op.bend;
      const label = op.label ? `<text x="${cx}" y="${cy - 12}" fill="${op.color}" font-family="Virgil, Comic Sans MS, cursive" font-size="17" text-anchor="middle">${esc(op.label)}</text>` : '';
      return `<path d="M ${op.x1} ${op.y1} Q ${cx} ${cy} ${op.x2} ${op.y2}" fill="none" stroke="${op.color}" stroke-width="3" stroke-linecap="round" ${op.dashed ? 'stroke-dasharray="11 9"' : ''} marker-end="url(#arrow)"/>${label}`;
    }
    const x = op.x, y = op.y, w = op.w, h = op.h;
    if (op.kind === 'box') {
      const labelY = y + (op.sub ? h / 2 - 5 : h / 2 + 8);
      const subs = op.sub ? op.sub.split('\n').map((line, i) => `<tspan x="${x + w / 2}" dy="${i === 0 ? 31 : 25}" font-size="17" font-weight="400" fill="${COLORS.muted}">${esc(line)}</tspan>`).join('') : '';
      return `<g><rect x="${x}" y="${y}" width="${w}" height="${h}" rx="13" fill="${op.fill}" stroke="${op.stroke}" stroke-width="3" ${op.dashed ? 'stroke-dasharray="10 8"' : ''}/><path d="M ${x + 7} ${y + 4} Q ${x + w / 2} ${y - 3}, ${x + w - 5} ${y + 5}" fill="none" stroke="${op.stroke}" stroke-width="1.4" opacity=".3"/><text x="${x + w / 2}" y="${labelY}" fill="${COLORS.ink}" font-family="Virgil, Comic Sans MS, cursive" font-size="${op.size}" font-weight="700" text-anchor="middle">${esc(op.label)}${subs}</text></g>`;
    }
    const lines = op.lines.map((line, i) => `<text x="${x + 22}" y="${y + 74 + i * 30}" fill="${COLORS.ink}" font-family="Virgil, Comic Sans MS, cursive" font-size="19">${esc(line)}</text>`).join('');
    return `<g transform="rotate(-0.7 ${x + w / 2} ${y + h / 2})"><rect x="${x}" y="${y}" width="${w}" height="${h}" rx="4" fill="${op.fill}" stroke="${op.stroke}" stroke-width="2.5"/><path d="M ${x + w / 2 - 42} ${y - 7} h84 v18 h-84z" fill="#ffffff" opacity=".62"/><text x="${x + 22}" y="${y + 40}" fill="${COLORS.ink}" font-family="Virgil, Comic Sans MS, cursive" font-size="22" font-weight="700">${esc(op.title)}</text>${lines}</g>`;
  }).join('\n');
  return `<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="900" viewBox="0 0 1600 900" role="img" aria-labelledby="title desc"><title id="title">${esc(frame.title)}</title><desc id="desc">${esc(frame.subtitle)}</desc><defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="context-stroke"/></marker><filter id="paper"><feTurbulence baseFrequency=".8" numOctaves="2" seed="7" type="fractalNoise" result="n"/><feBlend in="SourceGraphic" in2="n" mode="multiply"/></filter></defs><rect width="1600" height="900" fill="${COLORS.paper}"/><path d="M 35 78 Q 780 71 1565 80" fill="none" stroke="${COLORS.ink}" stroke-width="2" opacity=".25"/><text x="45" y="50" fill="${COLORS.ink}" font-family="Virgil, Comic Sans MS, cursive" font-size="31" font-weight="700">${esc(frame.title)}</text><text x="45" y="82" fill="${COLORS.muted}" font-family="Virgil, Comic Sans MS, cursive" font-size="18">${esc(frame.subtitle)}</text>${body}<text x="1548" y="870" fill="${COLORS.muted}" font-family="Virgil, Comic Sans MS, cursive" font-size="16" text-anchor="end">candidate whiteboard · editable board linked below</text></svg>`;
}

function base(type, x, y, w, h, extra = {}) {
  const id = uid(type);
  return { id, type, x, y, width: w, height: h, angle: 0, strokeColor: COLORS.ink,
    backgroundColor: 'transparent', fillStyle: 'solid', strokeWidth: 2, strokeStyle: 'solid',
    roughness: 1, opacity: 100, groupIds: [], frameId: null, index: `a${serial.toString(36)}`,
    roundness: type === 'rectangle' ? { type: 3 } : null, seed: 1000 + serial * 97, version: 1,
    versionNonce: 9000 + serial * 131, isDeleted: false, boundElements: [], updated: 1770000000000,
    link: null, locked: false, ...extra };
}
function exText(x, y, text, size = 24, opts = {}) {
  const lines = String(text).split('\n');
  const width = Math.max(...lines.map((line) => line.length)) * size * 0.58 + 10;
  const height = lines.length * size * 1.25;
  return base('text', x, y, width, height, { strokeColor: opts.color ?? COLORS.ink, fontSize: size, fontFamily: 1,
    text, textAlign: opts.align ?? 'left', verticalAlign: 'top', containerId: null, originalText: text,
    autoResize: true, lineHeight: 1.25, roundness: null, backgroundColor: 'transparent' });
}
function exRect(x, y, w, h, fill, dashed = false) {
  return base('rectangle', x, y, w, h, { backgroundColor: fill, strokeStyle: dashed ? 'dashed' : 'solid' });
}
function exArrow(x1, y1, x2, y2, dashed = false, color = COLORS.ink) {
  return base('arrow', x1, y1, x2 - x1, y2 - y1, { strokeColor: color, strokeStyle: dashed ? 'dashed' : 'solid',
    points: [[0, 0], [x2 - x1, y2 - y1]], lastCommittedPoint: null, startBinding: null, endBinding: null,
    startArrowhead: null, endArrowhead: 'arrow', elbowed: false, roundness: { type: 2 } });
}
function elementsForFrame(frame, offsetX) {
  const out = [exText(offsetX + 45, 28, frame.title, 31), exText(offsetX + 45, 67, frame.subtitle, 18, { color: COLORS.muted })];
  for (const op of frame.ops) {
    if (op.kind === 'text') out.push(exText(offsetX + op.x, op.y - op.size, op.text, op.size, { color: op.color }));
    else if (op.kind === 'scribble') out.push(exArrow(offsetX + op.x1, op.y1, offsetX + op.x2, op.y2, false, op.color));
    else if (op.kind === 'arrow') {
      out.push(exArrow(offsetX + op.x1, op.y1, offsetX + op.x2, op.y2, op.dashed, op.color));
      if (op.label) out.push(exText(offsetX + (op.x1 + op.x2) / 2 - op.label.length * 4, (op.y1 + op.y2) / 2 - 30, op.label, 16, { color: op.color }));
    } else if (op.kind === 'box') {
      out.push(exRect(offsetX + op.x, op.y, op.w, op.h, op.fill, op.dashed));
      out.push(exText(offsetX + op.x + 14, op.y + 15, op.label, Math.min(op.size, 22)));
      if (op.sub) out.push(exText(offsetX + op.x + 14, op.y + 50, op.sub, 15, { color: COLORS.muted }));
    } else if (op.kind === 'note') {
      out.push(exRect(offsetX + op.x, op.y, op.w, op.h, op.fill));
      out.push(exText(offsetX + op.x + 18, op.y + 15, op.title, 19));
      out.push(exText(offsetX + op.x + 18, op.y + 49, op.lines.join('\n'), 16));
    }
  }
  out.push(exText(offsetX + 1220, 860, 'candidate whiteboard · use solid vs dashed paths', 16, { color: COLORS.muted }));
  return out;
}
function sceneFor(frames) {
  serial = 0;
  const elements = [];
  frames.forEach((frame, i) => {
    const ox = i * 1700;
    elements.push(exRect(ox + 15, 10, 1570, 875, COLORS.paper));
    elements.push(...elementsForFrame(frame, ox));
  });
  return { type: 'excalidraw', version: 2, source: 'https://excalidraw.com', elements,
    appState: { gridSize: null, viewBackgroundColor: '#f4f1e8' }, files: {} };
}

async function writeSet(folder, prefix, frames) {
  const dir = path.join(ROOT, folder, 'assets');
  await mkdir(dir, { recursive: true });
  for (const frame of frames) await writeFile(path.join(dir, `interview-board-${frame.slug}.svg`), svgFor(frame));
  await writeFile(path.join(dir, `${prefix}-interview-board.excalidraw`), `${JSON.stringify(sceneFor(frames), null, 2)}\n`);
}

await writeSet('blogs/21-recommendation-system', 'recommendation-system', recFrames);
await writeSet('blogs/22-real-time-fraud-detection', 'fraud-detection', fraudFrames);
console.log('Generated two editable boards and six interview-stage SVGs.');
