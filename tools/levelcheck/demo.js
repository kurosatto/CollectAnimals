// "How to play" demos: for every game, the first few seconds of its level played well
// by a beam search (the real game code, as check.js), recorded as the presses made.
// The game plays them back on its start screen with a ghost finger showing each press,
// so you see how the game is played before you try it.
//   node tools/levelcheck/demo.js [game]   -> writes species/sprites/game/demos.json
// Run it again whenever a level changes (a recorded demo of an old level would crash
// into the new one). Claw Catch has no recording: its demo is a live greedy swiper.
// Every demo plays at middling stats (DEMO_STATS), whatever animal you picked.
const fs = require("fs"), path = require("path");
const { G, ctx, STEP, DT } = require("./check.js");
// Same state key as check.js: near-identical tries are kept once (the calmer one).
const SKIP = new Set(["dist", "t", "rt", "acc", "phase", "overAt", "flap", "score", "total", "len", "points", "coins", "x", "anims"]);
function keyOf(r) {
  let s = "";
  for (const k in r) { const v = r[k]; if (SKIP.has(k)) continue;
    if (typeof v === "number") s += k + (Math.abs(v) > 10 ? Math.round(v / 3) : Math.round(v * 5)) + ","; else if (typeof v === "boolean") s += k + (v ? 1 : 0) + ","; }
  return s + Math.round(r.dist / 4);
}
const OUT = path.join(__dirname, "../../species/sprites/game/demos.json");
const DEMO_STATS = { speed: 3, jump: 3, agility: 3, size: 3 };
const SECONDS = { call: 11 }, DEFAULT_SECONDS = 7, EVERY = 6;  // decide every 6 steps (1/20 s)
// The presses a demo can make: [held, side or spot]. Taps are by place (lane, flower,
// perch) and turned into a spot on the screen when played back.
const ACTS = {
  sky: [[0], [1]], trail: [[0], [1]], river: [[0], [1]], plunge: [[0], [1]], splash: [[0], [1]], school: [[0], [1]],
  freeze: [[0], [1]], leap: [[0], [1]], echo: [[0], [1]],
  pool: [[0], [1, -1], [1, 1]],
  dig: [[0], [1, 48], [1, 80], [1, 117], [1, 150], [1, 186]],
  slide: [[0], [0, "up"], [0, "down"]],
  nectar: [[0], [0, 0], [0, 1], [0, 2], [0, 3]],
  feeder: [[0], [0, 0], [0, 1], [0, 2]],
  call: [[0], [0, "sing"]],
};
const tapOf = (key, a) => G(`mgDemoTap(${JSON.stringify(key)}, ${JSON.stringify(a)})`);
function clone(r) {
  const c = Object.assign({}, r);
  c.things = r.things.map((o) => Object.assign({}, o));
  delete c.plats; delete c.hazards; c.fx = [];
  for (const k in c) if (Array.isArray(c[k]) && k !== "things" && k !== "fx") c[k] = c[k].map((v) => (Array.isArray(v) ? v.slice() : v && typeof v === "object" ? Object.assign({}, v) : v));
  if (r.rec) c.rec = Object.assign({}, r.rec);
  return c;
}
function record(key, width = 160) {
  ctx.__ST = DEMO_STATS;
  G(`mg.game = MG_GAMES.find((g) => g.key === ${JSON.stringify(key)}); mg.species = { slug: "zz", common_name: "Zz" }; mg.taps = []; mg.down = false; mgReset("play");`);
  const mg = G("mg"), acts = ACTS[key], tap = !["sky", "trail", "river", "plunge", "splash", "school", "freeze", "leap", "echo", "pool", "dig"].includes(key);
  const rounds = Math.round((SECONDS[key] || DEFAULT_SECONDS) / (DT * EVERY));
  let beam = [{ r: mg.run, hist: null, moves: 0, last: 0 }];
  for (let round = 0; round < rounds && beam.length; round++) {
    const seen = new Map();
    for (const node of beam) acts.forEach((a, ai) => {
      const r = clone(node.r);
      mg.run = r; mg.down = !!a[0]; mg.dir = typeof a[1] === "number" && key === "pool" ? a[1] : 0;
      if (key === "dig" && a[0]) mg.py = a[1];
      for (let i = 0; i < EVERY && r.mode === "play"; i++) {
        mg.taps = i === 0 && tap && a.length > 1 ? [tapOf(key, a[1])] : [];
        r.acc = 0; STEP(mg.run, DT / mg.run.p.tempo + 1e-9);
      }
      if (r.mode !== "play") return;
      // Fewer, calmer presses look more like a person playing.
      const moves = node.moves + (ai !== node.last ? 1 : 0) + (tap && ai ? 2 : 0);
      const n = { r, hist: { a: ai, prev: node.hist }, moves, last: ai, rk: Math.random() }, k = keyOf(r), old = seen.get(k);
      if (!old || old.r.score < r.score || (old.r.score === r.score && old.moves > moves)) seen.set(k, n);
    });
    const next = [...seen.values()];
    next.sort((a, b) => Math.round(b.r.dist) - Math.round(a.r.dist) || b.r.score - a.r.score || a.rk - b.rk);
    beam = next.slice(0, width);
    if (process.env.DEBUG) console.log(round, beam.length, beam[0] && Math.round(beam[0].r.y));
  }
  if (!beam.length) return null;
  const best = beam.reduce((a, b) => (b.r.score > a.r.score || (b.r.score === a.r.score && b.moves < a.moves) ? b : a));
  const seq = [];
  for (let h = best.hist; h; h = h.prev) seq.unshift(h.a);
  // Run-length: [decisions, action] pairs.
  const runs = [];
  for (const a of seq) { const l = runs[runs.length - 1]; if (l && l[1] === a && !(ACTS[key][a].length > 1 && ACTS[key][a][0] === 0)) l[0]++; else runs.push([1, a]); }
  return { every: EVERY, acts: ACTS[key], runs, score: best.r.score };
}
if (require.main === module) {
  const only = process.argv[2], out = fs.existsSync(OUT) ? JSON.parse(fs.readFileSync(OUT, "utf8")) : {};
  out.stats = DEMO_STATS; out.games = out.games || {};
  for (const key of Object.keys(ACTS)) {
    if (only && key !== only) continue;
    const t0 = Date.now(), d = record(key);
    console.log(key, d ? `${d.runs.length} presses, ${d.score} treats` : "no demo found", ((Date.now() - t0) / 1000).toFixed(1) + "s");
    if (d) out.games[key] = d;
  }
  fs.writeFileSync(OUT, JSON.stringify(out) + "\n");
}
