// Claw Catch checker: plays the real game code with a greedy swiper at the smallest
// reach (Size 1). Each step it swipes a tiny stroke on the food closest to getting
// away, as long as no bee is within the bee hit distance of that spot. Reports whether
// the level was finished, how many got away, the tightest food-to-bee gap it had to
// swipe through, and the busiest half-second (foods that had to be swiped in it).
//   node tools/levelcheck/claw.js
const { G, STEP, DT, ctx } = require("./check.js");
ctx.__ST = { speed: 3, jump: 1, agility: 1, size: 1 };
G(`mg.game = MG_GAMES.find((g) => g.key === "claw"); mg.species = { slug: "zz", common_name: "Zz" }; mg.taps = []; mg.down = false; mgReset("play");`);
const mg = G("mg"), at = G("mgClawAt"), BEE = 6, SAFE = 14;
const r = mg.run;
let tight = Infinity, steps = 0;
const swipedAt = [];
while (r.mode === "play" && steps < 200000) {
  steps++;
  let best = null;
  for (const o of r.things) {
    if (o.gone || !o.good) continue;
    const p = at(o, r);
    if (!p || p[1] > 230 || p[2] > 0.6) continue;  // still far below, or not up yet
    let gap = Infinity;
    for (const b of r.things) {
      if (b.good || b.gone) continue;
      const q = at(b, r);
      if (q) gap = Math.min(gap, Math.hypot(q[0] - p[0], q[1] - p[1]));
    }
    if (gap <= BEE + 1) continue;
    // the one that leaves soonest: past its peak and lowest on screen
    const urgency = -p[2] * 100 + p[1];
    if (!best || urgency > best.u) best = { o, p, gap, u: urgency };
  }
  if (best) {
    mg.down = true; mg.swipe = [[best.p[0], best.p[1]], [best.p[0] + 1, best.p[1]]];
    // only count it if this stroke really takes the food
    if (best.gap < SAFE) tight = Math.min(tight, best.gap);
  } else { mg.down = false; mg.swipe = null; }
  const before = r.score;
  r.acc = 0; STEP(r, DT / r.p.tempo + 1e-9);
  if (r.score > before) swipedAt.push(r.rt);
}
let busy = 0;
for (let i = 0; i < swipedAt.length; i++) { let j = i; while (j < swipedAt.length && swipedAt[j] - swipedAt[i] < 0.5) j++; busy = Math.max(busy, j - i); }
console.log(JSON.stringify({ ok: r.mode === "done", why: r.why || null, pct: r.pct, caught: r.score, total: r.total,
  missed: r.missed, tightestGap: tight === Infinity ? null : +tight.toFixed(1), busiestHalfSecond: busy }));
