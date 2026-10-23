// Minigames: three short games you play as one of your own captured animals, drawn
// with its pixel sprite and animation frames (species/sprites/anim). Shared by the
// website (static/index.html) and the Android app (assets/minigames.html), like
// habitat.js, which it needs loaded first (habRole, habAnimIdx, HAB_FLIERS).
// The page has a #minigames element and calls mgSet(entries) with its collection
// entries ({caught, species: {slug, common_name, category}}) whenever they change.
//
// Each game unlocks once you've captured an animal of its kind: Sky Glide for
// fliers, Trail Run for land animals, River Swim for swimmers. A round lasts a
// minute and never ends early: bumping into something only stuns you for a moment.
// Best scores stay in this browser (localStorage), nothing goes to the server.
const MG_W = 320, MG_H = 200, MG_ROUND = 60;
const MG_GROUND = 172, MG_SURFACE = 34, MG_BED = 186;
const MG_GAMES = [
  { key: "sky", title: "Sky Glide", pose: "fly", kind: "flying animal", thing: ["berry", "berries"],
    how: "Tap to flap. Collect berries and glide around the storm clouds.", tip: "Tap to flap your wings" },
  { key: "trail", title: "Trail Run", pose: "walk", kind: "land animal", thing: ["acorn", "acorns"],
    how: "Tap to jump over logs and rocks, hold for a bigger jump. Collect acorns.", tip: "Tap to jump, hold to jump higher" },
  { key: "river", title: "River Swim", pose: "swim", kind: "water animal", thing: ["point", "points"],
    how: "Hold to swim up, let go to dive. Eat snacks, scoop up litter for 3 points, and dodge the snags.", tip: "Hold to swim up, let go to dive" },
];
const MG_LAND_ROLES = new Set(["walk", "hop", "shore", "beach", "dangle"]);
const MG_WATER_ROLES = new Set(["swim", "jelly", "float", "paddle"]);
const mg = { entries: [], game: null, slug: null, run: null, raf: 0, last: 0, visible: true, down: false, built: false,
             imgs: {}, sheets: {} };

const mgStore = {
  get(k) { try { return localStorage.getItem("mg." + k); } catch { return null; } },
  set(k, v) { try { localStorage.setItem("mg." + k, v); } catch {} },
};

// Which games an animal can play: a duck flies and swims, a roadrunner runs.
function mgKinds(s) {
  const role = habRole(s), acts = (habAnimIdx && habAnimIdx.acts[s.slug]) || [];
  const kinds = [];
  if (HAB_FLIERS.has(role) || acts.includes("fly")) kinds.push("sky");
  if (MG_LAND_ROLES.has(role)) kinds.push("trail");
  if (MG_WATER_ROLES.has(role) || (acts.includes("swim") && (s.category === "marine" || s.category === "fish"))) kinds.push("river");
  return kinds;
}

function mgPlayers(key) {
  return mg.entries.filter((e) => e.caught && mgKinds(e.species).includes(key)).map((e) => e.species);
}

function mgSet(entries) {
  mg.entries = entries || [];
  // The animation index may still be loading; the unlocks depend on it.
  if (!habAnimIdx && (mg.tries = (mg.tries || 0) + 1) < 20) { setTimeout(() => mgSet(mg.entries), 300); return; }
  if (!mg.run) mgList();
}

const mgEl = (tag, cls, text) => { const e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; };

function mgBuild() {
  if (mg.built) return;
  mg.built = true;
  const css = mgEl("style");
  css.textContent = `
  .mg-list { display:grid; gap:10px; }
  .mg-game { border:1px solid var(--line); border-radius:12px; padding:10px 12px; }
  .mg-game h3 { margin:0; font-size:1.05rem; display:flex; justify-content:space-between; align-items:baseline; gap:8px; }
  .mg-best { font-size:.8rem; font-weight:400; color:var(--muted); }
  .mg-how { margin:4px 0 8px; font-size:.85rem; color:var(--muted); }
  .mg-pick { display:flex; gap:4px; overflow-x:auto; padding-bottom:4px; }
  .mg-pick img { width:40px; height:40px; image-rendering:pixelated; border-radius:8px; border:2px solid transparent;
                 cursor:pointer; flex:none; background:rgba(127,127,127,.08); }
  .mg-pick img.on { border-color:var(--accent); background:rgba(127,200,150,.18); }
  .mg-row { display:flex; justify-content:space-between; align-items:center; gap:8px; margin-top:6px; }
  .mg-name { font-size:.85rem; font-weight:600; }
  .mg-play { font:inherit; font-weight:600; padding:6px 16px; border-radius:999px; border:none; background:var(--accent);
             color:#fff; cursor:pointer; }
  .mg-locked { opacity:.6; }
  .mg-list.hidden, .mg-stage.hidden { display:none; }
  .mg-lock { font-size:.85rem; }
  .mg-stage canvas { display:block; width:100%; height:auto; image-rendering:pixelated; border-radius:10px;
                     touch-action:none; user-select:none; -webkit-user-select:none; cursor:pointer; }
  .mg-bar { display:flex; justify-content:space-between; align-items:center; margin-top:6px; font-size:.85rem; }
  .mg-back { font:inherit; font-size:.85rem; padding:4px 12px; border-radius:999px; border:1px solid var(--line);
             background:transparent; color:var(--accent); cursor:pointer; }`;
  document.head.append(css);
  const box = document.getElementById("minigames");
  const list = mgEl("div", "mg-list"), stage = mgEl("div", "mg-stage hidden");
  list.id = "mg-list";
  const cv = mgEl("canvas");
  cv.width = MG_W; cv.height = MG_H; cv.id = "mg-canvas";
  const bar = mgEl("div", "mg-bar"), back = mgEl("button", "mg-back", "← All games"), name = mgEl("span", "muted");
  name.id = "mg-playing";
  back.onclick = mgQuit;
  bar.append(back, name);
  stage.id = "mg-stage";
  stage.append(cv, bar);
  box.append(list, stage);
  const press = (on) => {
    if (on && !mg.down) mgTap();
    mg.down = on;
  };
  cv.addEventListener("pointerdown", (e) => { e.preventDefault(); try { cv.setPointerCapture(e.pointerId); } catch {} press(true); });
  ["pointerup", "pointercancel", "lostpointercapture"].forEach((t) => cv.addEventListener(t, () => press(false)));
  cv.addEventListener("contextmenu", (e) => e.preventDefault());
  const keys = (e) => [" ", "ArrowUp", "w", "W", "Enter"].includes(e.key);
  addEventListener("keydown", (e) => { if (mg.run && mg.visible && keys(e)) { e.preventDefault(); if (!e.repeat) press(true); } });
  addEventListener("keyup", (e) => { if (mg.run && keys(e)) press(false); });
  // Stop when the tab is switched away or the page is hidden; the round waits.
  new IntersectionObserver(([en]) => { mg.visible = en.isIntersecting; mgWake(); }).observe(cv);
  document.addEventListener("visibilitychange", mgWake);
}

function mgList() {
  mgBuild();
  const list = document.getElementById("mg-list");
  list.innerHTML = "";
  for (const g of MG_GAMES) {
    const players = mgPlayers(g.key), card = mgEl("div", "mg-game" + (players.length ? "" : " mg-locked"));
    const h = mgEl("h3", null, g.title), best = +(mgStore.get("best." + g.key) || 0);
    if (best) h.append(mgEl("span", "mg-best", `Best: ${best}`));
    card.append(h, mgEl("div", "mg-how", g.how));
    if (!players.length) {
      card.append(mgEl("div", "mg-lock", `🔒 Capture a ${g.kind} to unlock this game.`));
      list.append(card);
      continue;
    }
    const saved = mgStore.get("pick." + g.key);
    let pick = players.find((s) => s.slug === saved) || players[0];
    const row = mgEl("div", "mg-pick"), foot = mgEl("div", "mg-row"), name = mgEl("span", "mg-name", pick.common_name);
    const play = mgEl("button", "mg-play", "Play");
    for (const s of players) {
      const img = mgEl("img", s === pick ? "on" : "");
      img.src = `/sprites/${encodeURIComponent(s.slug)}.png`;
      img.alt = img.title = s.common_name;
      img.onclick = () => {
        pick = s; name.textContent = s.common_name; mgStore.set("pick." + g.key, s.slug);
        row.querySelectorAll("img").forEach((i) => i.classList.toggle("on", i === img));
      };
      row.append(img);
    }
    play.onclick = () => mgStart(g, pick);
    foot.append(name, play);
    card.append(row, foot);
    list.append(card);
  }
}

function mgImg(cache, url) {
  if (!cache[url]) { cache[url] = new Image(); cache[url].src = url; }
  return cache[url];
}

function mgStart(g, s) {
  mg.game = g; mg.species = s;
  mgImg(mg.imgs, `/sprites/${encodeURIComponent(s.slug)}.png`);
  mgImg(mg.sheets, `/sprites/anim/${encodeURIComponent(s.slug)}.png`);
  document.getElementById("mg-list").classList.add("hidden");
  document.getElementById("mg-stage").classList.remove("hidden");
  document.getElementById("mg-playing").textContent = `Playing as ${s.common_name}`;
  mgReset("ready");
  document.getElementById("mg-stage").scrollIntoView?.({ block: "nearest" });
  mgWake();
}

function mgQuit() {
  cancelAnimationFrame(mg.raf); mg.raf = 0;
  mg.run = null; mg.down = false;
  document.getElementById("mg-stage").classList.add("hidden");
  document.getElementById("mg-list").classList.remove("hidden");
  mgList();
}

// How each animal moves: quick runners go faster, hoppers jump higher, the slow
// ones plod along (and still get there).
function mgTraits(s) {
  const role = habRole(s), slug = s.slug;
  let speed = 1, jump = 1;
  if (/roadrunner|squirrel|chipmunk|lizard|skink|anole|fox|coyote|deer|hare|jackrabbit|pronghorn|horse|pony|dog|cat$/.test(slug)) speed = 1.2;
  if (/tortoise|box_turtle|slug|snail|turtle|millipede|woodlouse|newt|salamander|crab|seal|sea_lion|sloth|porcupine|skunk|armadillo/.test(slug)) speed = .8;
  if (role === "hop" || /rabbit|cottontail|hare|kangaroo|squirrel/.test(slug)) jump = 1.15;
  return { speed, jump };
}

function mgReset(mode) {
  const g = mg.game;
  mg.run = { mode, t: 0, left: MG_ROUND, score: 0, litter: 0, things: [], fx: [], spawn: .6, dist: 0, phase: 0,
             x: g.key === "trail" ? 70 : 72, y: g.key === "trail" ? MG_GROUND : g.key === "sky" ? 90 : 100, vy: 0,
             stun: 0, flap: 0, ground: true, overAt: 0, best: +(mgStore.get("best." + g.key) || 0), newBest: false,
             traits: mgTraits(mg.species) };
}

function mgTap() {
  const r = mg.run;
  if (!r) return;
  if (r.mode === "ready" || r.mode === "paused") { r.mode = "play"; mg.last = 0; mgWake(); }
  else if (r.mode === "over") { if (performance.now() - r.overAt > 700) { mgReset("play"); mgWake(); } return; }
  if (r.mode !== "play") return;
  if (mg.game.key === "sky") { r.vy = -118; r.flap = .35; }
  if (mg.game.key === "trail" && r.ground) { r.vy = -255 * r.traits.jump; r.ground = false; }
}

function mgWake() {
  const r = mg.run;
  const on = r && mg.visible && !document.hidden;
  if (r && !on && r.mode === "play") r.mode = "paused";
  if (on && !mg.raf) { mg.last = 0; mg.raf = requestAnimationFrame(mgLoop); }
  if (!on && mg.raf) { cancelAnimationFrame(mg.raf); mg.raf = 0; mgDraw(); }
}

function mgLoop(now) {
  mg.raf = 0;
  if (!mg.run || !mg.visible || document.hidden) return;
  const dt = mg.last ? Math.min(.05, (now - mg.last) / 1000) : 0;
  mg.last = now;
  const r = mg.run;
  r.phase += dt;
  if (r.mode === "play") mgStep(r, dt);
  mgFxStep(r, dt);
  mgDraw();
  mg.raf = requestAnimationFrame(mgLoop);
}

const mgRnd = (a, b) => a + Math.random() * (b - a);

function mgStep(r, dt) {
  const key = mg.game.key;
  r.t += dt; r.left -= dt;
  r.stun = Math.max(0, r.stun - dt); r.flap = Math.max(0, r.flap - dt);
  // Worlds speed up a little over the minute.
  const base = key === "trail" ? 92 * r.traits.speed : key === "sky" ? 70 : 62;
  const speed = base * (1 + r.t / 90) * (r.stun ? .55 : 1);
  r.speed = speed;
  r.dist += speed * dt;
  if (key === "sky") {
    r.vy = Math.min(150, r.vy + 300 * dt);
    r.y += r.vy * dt;
    if (r.y < 18) { r.y = 18; r.vy = Math.max(0, r.vy); }
    if (r.y > MG_GROUND - 14) { r.y = MG_GROUND - 14; r.vy = 0; }  // glides along the meadow
  } else if (key === "trail") {
    const g = 760;
    if (!r.ground) {
      // Let go early for a small hop.
      r.vy += (r.vy < 0 && !mg.down ? g * 2.2 : g) * dt;
      r.y += r.vy * dt;
      if (r.y >= MG_GROUND) { r.y = MG_GROUND; r.vy = 0; r.ground = true; }
    }
  } else {
    r.vy += (mg.down ? -260 : 200) * dt;
    r.vy = Math.max(-95, Math.min(85, r.vy));
    r.y += r.vy * dt;
    if (r.y < MG_SURFACE + 12) { r.y = MG_SURFACE + 12; r.vy = Math.max(0, r.vy); }
    if (r.y > MG_BED - 12) { r.y = MG_BED - 12; r.vy = Math.min(0, r.vy); }
  }
  // New things come in from the right.
  r.spawn -= dt;
  if (r.spawn <= 0) mgSpawn(r, key);
  for (const o of r.things) {
    o.x -= speed * dt * (o.drift || 1);
    if (o.bob) o.y = o.y0 + Math.sin(r.phase * 3 + o.x * .05) * o.bob;
  }
  // Touching things: pick up the good ones, bump the rest.
  const [px0, py0, px1, py1] = mgBox(r), px = (px0 + px1) / 2, py = (py0 + py1) / 2;
  for (const o of r.things) {
    if (o.gone || o.x + o.w / 2 < px0 || o.x - o.w / 2 > px1 || o.y + o.h / 2 < py0 || o.y - o.h / 2 > py1) continue;
    if (o.good) {
      if (r.stun) continue;
      o.gone = true;
      r.score += o.pts;
      if (o.litter) r.litter++;
      r.fx.push({ kind: "text", x: o.x, y: o.y - 6, text: `+${o.pts}`, life: .8 });
      if (o.litter) r.fx.push({ kind: "text", x: o.x, y: o.y - 16, text: "Cleaned!", life: .9 });
      for (let i = 0; i < 5; i++) r.fx.push({ kind: "spark", x: o.x, y: o.y, vx: mgRnd(-40, 40), vy: mgRnd(-60, -10), life: .5 });
    } else if (!r.stun) {
      r.stun = 1.1;
      if (key === "sky") r.vy = 60;
      for (let i = 0; i < 4; i++) r.fx.push({ kind: "star", x: px, y: py - 12, vx: mgRnd(-30, 30), vy: mgRnd(-40, -10), life: .8 });
    }
  }
  r.things = r.things.filter((o) => !o.gone && o.x > -40);
  if (r.left <= 0) {
    r.left = 0; r.mode = "over"; r.overAt = performance.now(); r.stun = 0; mg.down = false;
    if (r.score > r.best) { r.newBest = r.best > 0 || r.score > 0; r.best = r.score; mgStore.set("best." + key, r.score); }
  }
}

// What of the player touches things: a box around its body, a bit smaller than the
// sprite so near misses count as misses. On the trail r.y is where its feet are.
function mgBox(r) {
  return mg.game.key === "trail" ? [r.x - 9, r.y - 22, r.x + 9, r.y - 1] : [r.x - 9, r.y - 8, r.x + 9, r.y + 8];
}

function mgSpawn(r, key) {
  const add = (o) => r.things.push(Object.assign({ x: MG_W + 20, y0: o.y }, o));
  if (key === "sky") {
    if (Math.random() < .42) add({ type: "cloud", y: mgRnd(26, 140), w: 34, h: 14, bob: 3 });
    const y = mgRnd(24, 150);
    for (let i = 0; i < (Math.random() < .5 ? 3 : 1); i++)
      add({ type: "berry", good: true, pts: 1, x: MG_W + 30 + i * 16, y: y + Math.sin(i) * 8, w: 8, h: 8, bob: 2 });
    r.spawn = mgRnd(.8, 1.2);
  } else if (key === "trail") {
    const roll = Math.random();
    if (roll < .55) add(Math.random() < .5 ? { type: "log", y: MG_GROUND - 5, w: 22, h: 10 } : { type: "rock", y: MG_GROUND - 6, w: 14, h: 12 });
    // Acorns along the trail or up where a jump goes.
    const high = Math.random() < .5, n = 1 + Math.floor(Math.random() * 3);
    for (let i = 0; i < n; i++)
      add({ type: "acorn", good: true, pts: 1, x: MG_W + 50 + i * 14, y: high ? MG_GROUND - 52 - Math.sin(i / (n - 1 || 1) * Math.PI) * 8 : MG_GROUND - 10, w: 8, h: 9 });
    // Room to land between logs, even at full speed.
    r.spawn = mgRnd(1.1, 1.6) * 92 / (r.speed || 92) * (r.traits.speed < 1 ? 1.1 : 1);
  } else {
    const roll = Math.random();
    if (roll < .3) add({ type: "snag", y: mgRnd(MG_SURFACE + 22, MG_BED - 18), w: 26, h: 10, drift: 1.1 });
    else if (roll < .55) add({ type: pickOf(["can", "bottle", "bag"]), good: true, litter: true, pts: 3, y: mgRnd(MG_SURFACE + 16, MG_BED - 14), w: 10, h: 10, bob: 3 });
    const y = mgRnd(MG_SURFACE + 16, MG_BED - 14);
    for (let i = 0; i < 2; i++) add({ type: "snack", good: true, pts: 1, x: MG_W + 40 + i * 14, y: y + i * 6, w: 7, h: 7, bob: 4 });
    r.spawn = mgRnd(.7, 1.1);
  }
}
const pickOf = (a) => a[Math.floor(Math.random() * a.length)];

function mgFxStep(r, dt) {
  for (const f of r.fx) {
    f.life -= dt;
    if (f.kind === "text") f.y -= 18 * dt;
    else { f.x += f.vx * dt; f.y += f.vy * dt; f.vy += 120 * dt; }
  }
  r.fx = r.fx.filter((f) => f.life > 0);
}

// ---- Drawing -------------------------------------------------------------------

function mgDraw() {
  const cv = document.getElementById("mg-canvas"), r = mg.run;
  if (!cv || !r) return;
  const c = cv.getContext("2d");
  c.imageSmoothingEnabled = false;
  const key = mg.game.key;
  if (key === "sky") mgSkyBg(c, r); else if (key === "trail") mgTrailBg(c, r); else mgRiverBg(c, r);
  for (const o of r.things) mgThing(c, o, r);
  mgPlayer(c, r);
  for (const f of r.fx) mgFxDraw(c, f);
  mgHud(c, r);
}

const mgScroll = (r, k, wrap) => Math.floor(((r.dist * k) % wrap + wrap) % wrap);

function mgHills(c, r, k, base, amp, period, color) {
  c.fillStyle = color;
  const off = r.dist * k;
  for (let x = 0; x < MG_W; x += 2) {
    const u = (x + off) / period;
    const h = Math.round(amp * (.6 + .4 * Math.sin(u) + .25 * Math.sin(u * 2.3 + 1)));
    c.fillRect(x, base - h, 2, MG_H - base + h);
  }
}

function mgCloud(c, x, y, s, color) {
  c.fillStyle = color;
  c.fillRect(x, y + 4 * s, 22 * s, 5 * s);
  c.fillRect(x + 4 * s, y + s, 9 * s, 4 * s);
  c.fillRect(x + 11 * s, y + 2 * s, 7 * s, 3 * s);
}

function mgSkyBg(c, r) {
  const sky = c.createLinearGradient(0, 0, 0, MG_H);
  sky.addColorStop(0, "#7cc4e8"); sky.addColorStop(1, "#d6f0f7");
  c.fillStyle = sky; c.fillRect(0, 0, MG_W, MG_H);
  c.fillStyle = "#fff6c8"; c.fillRect(262, 18, 16, 16); c.fillStyle = "#f2c14e"; c.fillRect(264, 20, 12, 12);
  for (let i = 0; i < 4; i++) mgCloud(c, (i * 97 - mgScroll(r, .15, 400) + 400) % 400 - 40, 20 + (i * 37) % 70, 1, "rgba(255,255,255,.85)");
  mgHills(c, r, .25, 150, 26, 60, "#9fcf9a");
  mgHills(c, r, .5, 166, 14, 34, "#6aae6e");
  c.fillStyle = "#58a662"; c.fillRect(0, MG_GROUND, MG_W, MG_H - MG_GROUND);
  c.fillStyle = "#2f7d4f";
  for (let x = -mgScroll(r, 1, 12); x < MG_W; x += 12) c.fillRect(x, MG_GROUND, 2, 2);
}

function mgTrailBg(c, r) {
  const sky = c.createLinearGradient(0, 0, 0, MG_H);
  sky.addColorStop(0, "#9ad3ee"); sky.addColorStop(1, "#e4f4e0");
  c.fillStyle = sky; c.fillRect(0, 0, MG_W, MG_H);
  for (let i = 0; i < 3; i++) mgCloud(c, (i * 131 - mgScroll(r, .08, 420) + 420) % 420 - 40, 14 + i * 16, 1, "rgba(255,255,255,.9)");
  mgHills(c, r, .12, 120, 34, 80, "#8fb9a8");
  // A row of pines, then the trail.
  c.fillStyle = "#2f7d4f";
  const off = mgScroll(r, .45, 30);
  for (let x = -off; x < MG_W + 30; x += 30) {
    const h = 26 + ((Math.floor((x + r.dist * .45) / 30) * 7) % 3) * 6;
    for (let k = 0; k < h; k += 2) { const w = Math.round(k * .45) + 1; c.fillRect(x + 12 - w, MG_GROUND - 14 - h + k, w * 2, 2); }
    c.fillStyle = "#62402a"; c.fillRect(x + 11, MG_GROUND - 14, 3, 4); c.fillStyle = "#2f7d4f";
  }
  c.fillStyle = "#58a662"; c.fillRect(0, MG_GROUND - 10, MG_W, 10);
  c.fillStyle = "#c79a64"; c.fillRect(0, MG_GROUND, MG_W, MG_H - MG_GROUND);
  c.fillStyle = "#a87c4c";
  for (let x = -mgScroll(r, 1, 18); x < MG_W; x += 18) { c.fillRect(x, MG_GROUND + 6, 3, 1); c.fillRect(x + 9, MG_GROUND + 14, 2, 1); }
  c.fillStyle = "#3f8d58";
  for (let x = -mgScroll(r, 1, 10); x < MG_W; x += 10) c.fillRect(x, MG_GROUND - 12, 1, 2);
}

function mgRiverBg(c, r) {
  c.fillStyle = "#a9dcf0"; c.fillRect(0, 0, MG_W, MG_SURFACE);
  mgHills(c, r, .1, MG_SURFACE - 4, 8, 50, "#6aae6e");
  const w = c.createLinearGradient(0, MG_SURFACE, 0, MG_H);
  w.addColorStop(0, "#3d9cc9"); w.addColorStop(1, "#1d5d86");
  c.fillStyle = w; c.fillRect(0, MG_SURFACE, MG_W, MG_H - MG_SURFACE);
  c.fillStyle = "rgba(255,255,255,.55)";
  for (let x = -mgScroll(r, .7, 16); x < MG_W; x += 16) c.fillRect(x, MG_SURFACE, 8, 1);
  // Light from above, and bubbles drifting up.
  c.fillStyle = "rgba(255,255,255,.06)";
  for (let i = 0; i < 4; i++) { const x = (i * 90 - mgScroll(r, .2, 360) + 360) % 360 - 20; c.beginPath(); c.moveTo(x, MG_SURFACE); c.lineTo(x + 18, MG_SURFACE); c.lineTo(x + 50, MG_BED); c.lineTo(x + 26, MG_BED); c.fill(); }
  c.fillStyle = "rgba(255,255,255,.35)";
  for (let i = 0; i < 8; i++) {
    const x = (i * 47 - mgScroll(r, .5, 380) + 380) % 380 - 30, y = MG_BED - ((r.phase * 18 + i * 29) % (MG_BED - MG_SURFACE - 6));
    c.fillRect(x, y, 2, 2);
  }
  c.fillStyle = "#d9c18a"; c.fillRect(0, MG_BED, MG_W, MG_H - MG_BED);
  c.fillStyle = "#3f8d58";
  const off = mgScroll(r, 1, 40);
  for (let x = -off; x < MG_W + 40; x += 40) {
    for (let k = 0; k < 16; k += 2) c.fillRect(x + Math.round(Math.sin(r.phase * 2 + k * .4 + x) * 2), MG_BED - k, 2, 2);
    for (let k = 0; k < 10; k += 2) c.fillRect(x + 12 + Math.round(Math.sin(r.phase * 2 + k * .5) * 2), MG_BED - k, 2, 2);
  }
}

function mgThing(c, o, r) {
  const x = Math.round(o.x), y = Math.round(o.y);
  const box = (dx, dy, w, h, col) => { c.fillStyle = col; c.fillRect(x + dx, y + dy, w, h); };
  switch (o.type) {
    case "berry":
      box(-3, -2, 3, 3, "#d9534f"); box(0, -3, 3, 3, "#c0392b"); box(-1, 0, 3, 3, "#e0605a"); box(-1, -4, 1, 2, "#2f7d4f");
      box(-2, -1, 1, 1, "#ffb3ad"); break;
    case "cloud":
      mgCloud(c, x - 17, y - 9, 1.6, "#7a7f92");
      box(-14, 4, 24, 2, "#5f6378");
      if (Math.sin(r.phase * 5 + o.x) > .9) { box(-2, 7, 2, 4, "#f2c14e"); box(-1, 11, 2, 3, "#f2c14e"); }
      break;
    case "acorn":
      box(-3, -4, 7, 3, "#62402a"); box(0, -6, 1, 2, "#62402a"); box(-2, -1, 5, 4, "#c78a3e"); box(-1, 3, 3, 1, "#c78a3e");
      box(-1, 0, 1, 1, "#e6b46a"); break;
    case "log":
      box(-11, -5, 22, 10, "#8a5a35"); box(-11, -5, 22, 2, "#a8744a"); box(-11, 3, 22, 2, "#62402a");
      box(8, -5, 4, 10, "#d8b07a"); box(9, -2, 2, 4, "#a8744a"); break;
    case "rock":
      box(-6, -3, 12, 9, "#8a8f9e"); box(-4, -6, 8, 4, "#9fa4b2"); box(-3, -5, 3, 2, "#c4c8d2"); box(-6, 4, 12, 2, "#606476"); break;
    case "snack":
      box(-2, -2, 5, 5, "#f2a541"); box(-1, -1, 2, 2, "#ffd28a"); break;
    case "can":
      box(-3, -5, 7, 10, "#c9ced8"); box(-3, -2, 7, 4, "#d9534f"); box(-2, -5, 5, 1, "#9aa0ad"); break;
    case "bottle":
      box(-2, -6, 5, 11, "rgba(150,220,180,.85)"); box(-1, -8, 3, 2, "#6aa8d8"); box(-1, -4, 1, 6, "rgba(255,255,255,.7)"); break;
    case "bag":
      box(-5, -4, 10, 8, "rgba(240,240,240,.75)"); box(-4, -6, 2, 2, "rgba(240,240,240,.75)"); box(2, -6, 2, 2, "rgba(240,240,240,.75)"); break;
    case "snag":
      box(-13, -3, 26, 6, "#5b4030"); box(-13, -3, 26, 1, "#7a5a40"); box(-6, -8, 2, 5, "#5b4030"); box(4, 3, 2, 5, "#5b4030");
      box(-8, -9, 4, 2, "#5b4030"); break;
  }
}

function mgPlayer(c, r) {
  const s = mg.species, key = mg.game.key;
  const raw = mg.imgs[`/sprites/${encodeURIComponent(s.slug)}.png`], sheet = mg.sheets[`/sprites/anim/${encodeURIComponent(s.slug)}.png`];
  const acts = (habAnimIdx && habAnimIdx.acts[s.slug]) || [];
  const framed = sheet && sheet.complete && sheet.naturalWidth && acts.length;
  const cyc = (t) => ((Math.floor(t) % 4) + 4) % 4;
  // The game's own pose when the animal draws one (fly, walk, swim), else standing.
  let pose = acts.includes(mg.game.pose) ? mg.game.pose : key === "river" && acts.includes("walk") ? "walk" : "idle";
  let frame = 0;
  const moving = r.mode === "play";
  if (pose === "fly") frame = !moving ? cyc(r.phase * 4) : r.flap > 0 || r.vy < 20 ? cyc(r.phase * 14) : HAB_GLIDERS.test(s.slug) ? 0 : cyc(r.phase * 6);
  else if (pose === "walk") frame = key === "trail" && !r.ground ? 1 : cyc((moving ? r.dist : r.phase * 20) / 9);
  else if (pose === "swim") frame = cyc(r.phase * (mg.down ? 5 : 2.5));
  if (r.mode === "over" && acts.includes("idle")) { pose = "idle"; frame = 0; }
  const img = framed ? sheet : raw;
  if (!img || !img.complete || !img.naturalWidth) return;
  const F = framed ? sheet.naturalWidth / habAnimIdx.frames : raw.naturalWidth;
  if (r.stun && Math.floor(r.phase * 12) % 3 === 0) return;  // blink while dizzy
  let x = Math.round(r.x), y = Math.round(r.y), bob = 0;
  if (!framed) bob = Math.round(Math.sin(r.phase * 8) * 2);
  if (key === "trail" && r.ground) {
    c.fillStyle = "rgba(20,32,10,.25)"; c.fillRect(x - 9, MG_GROUND - 1, 18, 2);
  }
  c.save();
  // Sprites face left; the games run to the right.
  if (key === "trail") c.translate(x, y + 2);  // feet on the trail
  else c.translate(x, y + F * .4);
  c.scale(-1, 1);
  if (key === "sky" && moving) c.rotate(Math.max(-.35, Math.min(.35, r.vy / 400)));
  if (key === "river" && moving) c.rotate(Math.max(-.3, Math.min(.3, r.vy / 350)));
  if (framed) c.drawImage(sheet, frame * F, habAnimIdx.rows.indexOf(pose) * F, F, F, -F / 2, -F + bob, F, F);
  else c.drawImage(raw, -F / 2, -F + bob);
  c.restore();
}

function mgFxDraw(c, f) {
  if (f.kind === "text") {
    c.font = "bold 9px system-ui, sans-serif"; c.textAlign = "center";
    c.fillStyle = "rgba(0,0,0,.4)"; c.fillText(f.text, f.x + 1, f.y + 1);
    c.fillStyle = "#fff"; c.fillText(f.text, f.x, f.y);
  } else {
    c.fillStyle = f.kind === "star" ? "#f2c14e" : "#fff6c8";
    c.fillRect(Math.round(f.x), Math.round(f.y), 2, 2);
    if (f.kind === "star") { c.fillRect(Math.round(f.x) - 1, Math.round(f.y) + 0.5, 4, 1); }
  }
}

function mgPanel(c, lines, y0) {
  const h = lines.length * 16 + 14;
  c.fillStyle = "rgba(20,30,24,.72)";
  c.fillRect(40, y0, MG_W - 80, h);
  c.textAlign = "center";
  lines.forEach(([text, size, color], i) => {
    c.font = `bold ${size}px system-ui, sans-serif`;
    c.fillStyle = color || "#fff";
    c.fillText(text, MG_W / 2, y0 + 20 + i * 16);
  });
}

function mgHud(c, r) {
  const g = mg.game, top = g.key === "trail" ? 34 : 104;  // clear of the animal
  c.textAlign = "left"; c.font = "bold 11px system-ui, sans-serif";
  const label = g.key === "river" ? `Score ${r.score}` : `${g.key === "sky" ? "Berries" : "Acorns"} ${r.score}`;
  c.fillStyle = "rgba(0,0,0,.35)"; c.fillRect(4, 4, c.measureText(label).width + 10, 16);
  c.fillStyle = "#fff"; c.fillText(label, 9, 16);
  const secs = `${Math.ceil(r.left)}s`;
  c.textAlign = "right";
  c.fillStyle = "rgba(0,0,0,.35)"; c.fillRect(MG_W - 14 - c.measureText(secs).width, 4, c.measureText(secs).width + 10, 16);
  c.fillStyle = r.left < 10 ? "#ffd28a" : "#fff"; c.fillText(secs, MG_W - 9, 16);
  if (r.mode === "ready") mgPanel(c, [[g.title, 15], [g.tip, 11], ["Tap to start", 11, "#ffd28a"]], top);
  else if (r.mode === "paused") mgPanel(c, [["Paused", 15], ["Tap to keep going", 11, "#ffd28a"]], top);
  else if (r.mode === "over") {
    const what = `${r.score} ${g.thing[r.score === 1 ? 0 : 1]}`;
    const lines = [["Time's up!", 15], [what, 13, "#ffd28a"]];
    if (g.key === "river" && r.litter) lines.push([`You cleaned up ${r.litter} piece${r.litter === 1 ? "" : "s"} of litter`, 10]);
    lines.push([r.newBest ? "New best score!" : `Best: ${r.best}`, 11, r.newBest ? "#9be59b" : "#fff"]);
    lines.push(["Tap to play again", 10, "#cfe"]);
    mgPanel(c, lines, Math.min(top, MG_H - 8 - (lines.length * 16 + 14)));
  }
}
