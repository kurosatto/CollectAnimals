// Minigame level checker: loads habitat.js + minigames.js in a sandbox with a dummy page
// and beam-searches button presses, playing the real game code at the weakest stats
// (Jump 1, Agility 1, Size 5; Speed only changes the clock, not the course). "ok": true
// means the level was finished, so it can be. "ok": false may still be finishable (the
// search can miss), but try a wider beam or another seed first.
//   node tools/levelcheck/check.js <game> [beam width, default 300]
// Branch Leap needs its own search: node tools/levelcheck/leap.js, and Claw Catch
// (swipes) its own greedy player: node tools/levelcheck/claw.js. The search has some randomness, so a miss is worth a second run.
// TMPL=file.js swaps in another minigames.js, with SEEDS='{"SKY": 29}'
// filling in SKYSEED-style placeholders, to try seeds for a new level.
const vm = require("vm"), fs = require("fs");
const S = process.env.STATIC || require("path").join(__dirname, "../../backend/app/static");
function stub() {
  const f = function () { return P; };
  const P = new Proxy(f, { get: (t, k) => k === Symbol.toPrimitive ? () => 0 : k === "then" ? undefined : k === "length" ? 0 : P,
                           set: () => true, apply: () => P, construct: () => P });
  return P;
}
const ctx = { console, Math, JSON, Object, Array, Set, Map, Number, String, Boolean, Symbol, Promise, Proxy, Infinity, NaN, isFinite, parseInt, parseFloat, Date, RegExp, Error };
const st = stub();
Object.assign(ctx, { document: st, localStorage: { getItem: () => null, setItem() {} }, navigator: st, location: st, Image: function () { return st; },
  fetch: () => new Promise(() => {}), addEventListener() {}, setTimeout: () => 0, clearTimeout() {}, requestAnimationFrame: () => 0, cancelAnimationFrame() {},
  performance: { now: () => 0 }, devicePixelRatio: 1, matchMedia: () => st, getComputedStyle: () => st, OffscreenCanvas: function () { return st; }, structuredClone });
ctx.window = ctx; ctx.self = ctx; ctx.globalThis = ctx;
vm.createContext(ctx);
const SEEDS = Object.assign({ SKY: 29, RIVER: 47, POOL: 5, SLIDE: 12, LEAP: 82, DIG: 42, NECTAR: 22, PLUNGE: 62, SPLASH: 72, CALL: 32, ECHO: 52, FEEDER: 92, SCHOOL: 94, FREEZE: 96 }, JSON.parse(process.env.SEEDS || "{}"));
module.exports.SEEDS = SEEDS;
for (const f of ["habitat.js", "decor.js", "minigames.js"]) {
  let src = process.env.TMPL && f === "minigames.js" ? fs.readFileSync(process.env.TMPL, "utf8") : fs.existsSync(`${S}/${f}`) ? fs.readFileSync(`${S}/${f}`, "utf8") : null;
  if (src === null) continue;
  src = src.replace(/\b([A-Z]+)SEED\b/g, (m, n) => SEEDS[n]);
  vm.runInContext(src, ctx, { filename: f });
}
vm.runInContext(`mgSfx = () => {}; mgCallSfx = () => {}; mgMusicStop = () => {}; mgMusicStart = () => {}; mgApi = () => new Promise(() => {});
  mgStats = () => (globalThis.__ST);`, ctx);
const G = (s) => vm.runInContext(s, ctx);
const STEP = G("mgStep"), DT = G("MG_DT");

const T = (x, y) => ({ taps: [[x, y]] });
const ACTIONS = {
  sky: [{ down: 0 }, { down: 1 }], trail: [{ down: 0 }, { down: 1 }], river: [{ down: 0 }, { down: 1 }],
  plunge: [{ down: 0 }, { down: 1 }], splash: [{ down: 0 }, { down: 1 }], school: [{ down: 0 }, { down: 1 }],
  freeze: [{ down: 0 }, { down: 1 }], leap: [{ down: 0 }, { down: 1 }], echo: [{ down: 0 }, { down: 1 }],
  pool: [{ down: 0 }, { down: 1, dir: -1 }, { down: 1, dir: 1 }],
  dig: [{ down: 0 }, ...[48, 80, 117, 150, 186].map((py) => ({ down: 1, py }))],
  slide: [{}, T(160, 20), T(160, 180)],
  nectar: [{}, T(40, 100), T(120, 100), T(200, 100), T(280, 100)],
  feeder: [{}, T(40, 100), T(160, 100), T(280, 100)],
  call: [{}, T(160, 100)],
};
const SKIP = new Set(["dist", "t", "rt", "acc", "phase", "overAt", "flap", "score", "total", "len", "points", "coins", "x"]);
function clone(r) {
  const c = Object.assign({}, r);
  c.things = r.things.map((o) => Object.assign({}, o));
  delete c.plats; delete c.hazards; c.fx = [];
  for (const k in c) if (Array.isArray(c[k]) && k !== "things" && k !== "fx") c[k] = c[k].map((v) => (Array.isArray(v) ? v.slice() : v && typeof v === "object" ? Object.assign({}, v) : v));
  if (r.rec) c.rec = Object.assign({}, r.rec);
  return c;
}
function keyOf(r) {
  let s = "";
  for (const k in r) { const v = r[k]; if (SKIP.has(k)) continue;
    if (typeof v === "number") s += k + (Math.abs(v) > 10 ? Math.round(v / 3) : Math.round(v * 5)) + ","; else if (typeof v === "boolean") s += k + (v ? 1 : 0) + ","; }
  return s;
}
// Returns {ok, pct, treats, total}
function check(key, n, opts = {}) {
  const W = opts.width || 48, D = opts.every || 6, stats = opts.stats || { speed: 3, jump: 1, agility: 1, size: 5 };
  ctx.__ST = stats;
  G(`mg.game = MG_GAMES.find((g) => g.key === ${JSON.stringify(key)}); mg.species = { slug: "zz", common_name: "Zz" }; mg.taps = []; mg.down = false; mgReset("play");`);
  const mg = G("mg"), acts = ACTIONS[key];
  let beam = [{ r: mg.run, held: 0 }], best = 0, bestT = 0, total = mg.run.total, len = mg.run.len, rounds = 0;
  while (beam.length) {
    rounds++;
    const next = new Map();
    for (const node of beam) for (const a of acts) {
      const r = clone(node.r);
      mg.run = r; mg.down = !!a.down; mg.dir = a.dir || 0; if (a.py !== undefined) mg.py = a.py;
      for (let i = 0; i < D && r.mode === "play"; i++) {
        mg.taps = i === 0 && a.taps ? a.taps.map((t) => t.slice()) : [];
        r.acc = 0; STEP(mg.run, DT / mg.run.p.tempo + 1e-9);
      }
      if (r.mode === "done") { return { ok: true, pct: 100, treats: r.score, total, len, rounds }; }
      if (r.mode !== "play") { const p = r.dist / len; if (p > best) best = p; continue; }
      const k = keyOf(r), old = next.get(k);
      if (!old || old.r.score < r.score) next.set(k, { r });
      if (r.dist / len > best) best = r.dist / len;
    }
    beam = [...next.values()];
    for (const b of beam) b.rk = Math.random();
    beam.sort((a, b) => Math.round(b.r.dist) - Math.round(a.r.dist) || b.rk - a.rk);
    if (beam.length > W) beam = beam.slice(0, W);
  }
  return { ok: false, pct: Math.floor(best * 100), total, len };
}
Object.assign(module.exports, { check, G, ctx, STEP, DT });
if (require.main === module) {
  const [key, w] = process.argv.slice(2), keys = key ? [key] : Object.keys(ACTIONS).filter((k) => k !== "leap");
  for (const k of keys) {
    const t0 = Date.now(), res = check(k, 0, { width: +(w || 300) });
    delete res.len;
    console.log(k, JSON.stringify(res), ((Date.now() - t0) / 1000).toFixed(1) + "s");
  }
}
