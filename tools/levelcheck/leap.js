// Branch Leap checker: from each branch, try waiting a while and then holding for every
// length of time, and follow the leaps that land further on. Weakest stats, as check.js.
//   node tools/levelcheck/leap.js   (a few minutes)
const H = require("./check.js"), { G, ctx, STEP, DT } = H;
ctx.__ST = { speed: 3, jump: 1, agility: 1, size: 5 };
G(`mg.game = MG_GAMES.find((g) => g.key === "leap"); mg.species = { slug: "zz", common_name: "Zz" }; mg.taps = []; mgReset("play");`);
const mg = G("mg");
const clone = (r) => { const c = Object.assign({}, r); c.things = r.things.map((o) => Object.assign({}, o)); c.perches = c.things.filter((o) => o.type === "m_perch"); c.fx = []; return c; };
const step = (r, down) => { mg.run = r; mg.down = down; r.acc = 0; STEP(mg.run, DT / mg.run.p.tempo + 1e-9); };
const last = mg.run.perches.length - 1;
let front = [mg.run], far = 0, maxPer = 12;
while (front.length) {
  const next = new Map();
  for (const s of front) {
    for (let w = 0; w <= 120; w += 8) {          // wait up to 1 s
      const base = clone(s); let ok = true;
      for (let i = 0; i < w; i++) { step(base, false); if (base.mode !== "play") { ok = false; break; } }
      if (!ok) continue;
      const hold = clone(base); hold.fresh = true;
      for (let h = 1; h <= 108; h++) {        // hold up to 0.9 s (charge rises)
        step(hold, true); if (h % 2) continue;
        const r = clone(hold);
        let n = 0; step(r, false);
        while (r.mode === "play" && r.on < 0 && n++ < 600) step(r, false);
        if (r.mode === "done" || r.on === last) { console.log(JSON.stringify({ ok: true, perches: last })); process.exit(0); }
        if (r.mode !== "play" || r.on <= s.on) continue;
        far = Math.max(far, r.on);
        const key = r.on + ":" + Math.round(r.off / 4) + ":" + Math.round((r.t % 4) * 10);
        if (!next.has(key)) next.set(key, r);
      }
    }
  }
  // keep the furthest branches, a few timings each
  const by = [...next.values()].sort((a, b) => b.on - a.on);
  const cnt = {}; front = [];
  for (const r of by) { cnt[r.on] = (cnt[r.on] || 0) + 1; if (cnt[r.on] <= maxPer && front.length < 10) front.push(r); }
}
console.log(JSON.stringify({ ok: false, far, perches: last }));
