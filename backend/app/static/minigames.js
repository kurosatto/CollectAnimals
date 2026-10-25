// Minigames: three short games you play as one of your own captured animals, drawn
// with its pixel sprite and animation frames (species/sprites/anim). Shared by the
// website (static/index.html) and the Android app (assets/minigames.html), like
// habitat.js, which it needs loaded first (habRole, habAnimIdx, HAB_FLIERS).
// The page has a #minigames element and calls mgSet(entries) with its collection
// entries ({caught, species: {slug, common_name, category}}) whenever they change.
//
// Each game unlocks once you've captured an animal of its kind: Sky Glide for
// fliers, Trail Run for land animals, River Swim for swimmers. Every game has
// hand-made levels that are the same on every try, each with its own song: the
// hazards sit on the beat. A bump ends the try, and the next one starts right away,
// so you get further by learning the course. Finishing a level unlocks the next.
// Progress stays in this browser (localStorage), nothing goes to the server.
const MG_W = 320, MG_H = 200;
// The canvas has 4 real pixels per game pixel, so text stays sharp when it's scaled up.
const MG_RES = 4;
const MG_GROUND = 172, MG_SURFACE = 34, MG_BED = 186;
const MG_GAMES = [
  { key: "sky", title: "Sky Glide", pose: "fly", kind: "flying animal", thing: ["berry", "berries"],
    how: "Tap to flap through the gaps in the storm clouds, and grab the berries on the way.", tip: "Tap to flap your wings" },
  { key: "trail", title: "Trail Run", pose: "walk", kind: "land animal", thing: ["acorn", "acorns"],
    how: "Tap to hop over rocks and logs, hold for a big jump over stumps, and stay low under branches.", tip: "Tap to jump, hold to jump higher" },
  { key: "river", title: "River Swim", pose: "swim", kind: "water animal", thing: ["point", "points"],
    how: "Hold to swim up, let go to dive. Slip between the rocks and roots, eat snacks and scoop up litter.", tip: "Hold to swim up, let go to dive" },
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
  // Anything drawn swimming can swim: seals, ducks, frogs, turtles. Not tortoises.
  if (MG_WATER_ROLES.has(role) || (acts.includes("swim") && !/tortoise|box_turtle/.test(s.slug))) kinds.push("river");
  return kinds;
}

function mgPlayers(key) {
  return mg.entries.filter((e) => e.caught && mgKinds(e.species).includes(key)).map((e) => e.species);
}

function mgSet(entries) {
  mg.entries = entries || [];
  // The animation index and stats may still be loading; the unlocks depend on them.
  if ((!habAnimIdx || !mgStatsIdx) && (mg.waits = (mg.waits || 0) + 1) < 20) { setTimeout(() => mgSet(mg.entries), 300); return; }
  if (!mg.run) mgList();
}

// ---- Leaderboards ----------------------------------------------------------------
// Finished runs go to the game server (app/games.py), which keeps everyone's best per
// level and shows the top 10, or you and your friends. The website calls it with its
// own api(); the Android app passes calls through its AndroidMinigames bridge. Offline
// or logged out, the games work the same without the boards.
const mgCalls = {};
let mgCallN = 0;
function mgApi(method, path, body) {
  const json = body ? JSON.stringify(body) : null;
  if (window.AndroidMinigames && window.AndroidMinigames.api) {
    return new Promise((ok, fail) => { const id = ++mgCallN; mgCalls[id] = [ok, fail]; window.AndroidMinigames.api(id, method, path, json); });
  }
  if (typeof api === "function" && typeof token !== "undefined" && token) {
    return api(path, { method, headers: json ? { "Content-Type": "application/json" } : {}, body: json });
  }
  return Promise.reject(new Error("offline"));
}
// The Android bridge answers here.
function mgApiDone(id, ok, text) {
  const cb = mgCalls[id];
  delete mgCalls[id];
  if (!cb) return;
  if (ok) { try { cb[0](JSON.parse(text)); } catch (e) { cb[1](e); } } else cb[1](new Error(text));
}

function mgBoard(box, level, scope) {
  box.innerHTML = "";
  const tabs = mgEl("div", "mg-tabs"), rows = mgEl("ol", "mg-rows");
  for (const [s, label] of [["all", "Everyone"], ["friends", "Friends"]]) {
    const b = mgEl("button", "mg-tab" + (s === scope ? " on" : ""), label);
    b.onclick = () => { mgStore.set("board", s); mgBoard(box, level, s); };
    tabs.append(b);
  }
  box.append(mgEl("b", null, "Top scores"), tabs, rows);
  const row = (e) => {
    const li = mgEl("li", e.you ? "you" : "");
    li.append(mgEl("span", "mg-rank", `${e.rank}.`));
    const img = mgEl("img");
    if (e.species.slug) { img.src = `/sprites/${encodeURIComponent(e.species.slug)}.png`; img.alt = e.species.common_name; }
    else img.style.visibility = "hidden";
    li.append(img, mgEl("span", "mg-who", `${e.you ? "You" : e.username} as ${e.species.common_name}`), mgEl("span", "mg-pts", e.points));
    return li;
  };
  Promise.resolve(mg.posting).then(() => mgApi("GET", `/games/scores/${level}?scope=${scope}`)).then((d) => {
    if (!d.top.length) rows.append(mgEl("li", "muted", scope === "friends" ? "No scores from you or your friends yet." : "No scores yet. Finish the level to be first!"));
    d.top.forEach((e) => rows.append(row(e)));
    if (d.you && !d.top.some((e) => e.you)) rows.append(row(d.you));
  }).catch(() => { box.classList.add("hidden"); });
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
  .mg-stats { display:flex; gap:10px; flex-wrap:wrap; margin-top:4px; font-size:.75rem; }
  .mg-stat { display:flex; gap:4px; align-items:baseline; }
  .mg-stat i { font-style:normal; color:var(--muted); }
  .mg-stat b { color:var(--accent); letter-spacing:-1px; font-weight:400; }
  .mg-levels { display:flex; gap:6px; margin-top:6px; flex-wrap:wrap; }
  .mg-lv { font:inherit; font-size:.78rem; text-align:left; padding:5px 10px; border-radius:10px; border:2px solid var(--line);
           background:transparent; color:inherit; cursor:pointer; display:flex; flex-direction:column; gap:1px; }
  .mg-lv span { color:var(--muted); font-size:.72rem; }
  .mg-lv.on { border-color:var(--accent); background:rgba(127,200,150,.14); }
  .mg-lv:disabled { opacity:.55; cursor:default; }
  .mg-board { margin-top:8px; font-size:.8rem; }
  .mg-board.hidden { display:none; }
  .mg-tabs { display:inline-flex; gap:4px; margin-left:8px; }
  .mg-tab { font:inherit; font-size:.72rem; padding:1px 8px; border-radius:999px; border:1px solid var(--line);
            background:transparent; color:var(--muted); cursor:pointer; }
  .mg-tab.on { border-color:var(--accent); color:var(--accent); }
  .mg-rows { list-style:none; margin:4px 0 0; padding:0; display:grid; gap:2px; }
  .mg-rows li { display:flex; align-items:center; gap:6px; }
  .mg-rows li.you { font-weight:600; }
  .mg-rows img { width:20px; height:20px; image-rendering:pixelated; }
  .mg-rank { width:2.2em; color:var(--muted); text-align:right; }
  .mg-who { flex:1; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
  .mg-pts { color:var(--accent); font-variant-numeric:tabular-nums; }
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
  cv.width = MG_W * MG_RES; cv.height = MG_H * MG_RES; cv.id = "mg-canvas";
  const bar = mgEl("div", "mg-bar"), back = mgEl("button", "mg-back", "← All games"), name = mgEl("span", "muted");
  name.id = "mg-playing";
  back.onclick = mgQuit;
  const mute = mgEl("button", "mg-back");
  const label = () => { mute.textContent = mgAudio.muted ? "🔇 Music off" : "🔊 Music on"; };
  mute.onclick = () => {
    mgAudio.muted = !mgAudio.muted; mgStore.set("muted", mgAudio.muted ? "1" : "0"); label();
    if (mgAudio.muted) mgMusicStop(mg.run); else if (mg.run && mg.run.mode === "play") mgMusicStart(mg.run);
  };
  label();
  bar.append(back, name, mute);
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
    const h = mgEl("h3", null, g.title), lvls = MG_LEVELS[g.key];
    const cleared = lvls.filter((_, i) => mgRec(g.key, i).pct >= 100).length;
    if (cleared) h.append(mgEl("span", "mg-best", `${cleared} of ${lvls.length} levels cleared`));
    card.append(h, mgEl("div", "mg-how", g.how));
    if (!players.length) {
      card.append(mgEl("div", "mg-lock", `🔒 Capture a ${g.kind} to unlock this game.`));
      list.append(card);
      continue;
    }
    const saved = mgStore.get("pick." + g.key);
    let pick = players.find((s) => s.slug === saved) || players[0];
    const row = mgEl("div", "mg-pick"), foot = mgEl("div", "mg-row"), name = mgEl("span", "mg-name", pick.common_name);
    const stats = mgEl("div", "mg-stats");
    const showStats = () => {
      const st = mgStats(pick.slug);
      stats.innerHTML = "";
      [st.speed, st.jump, st.agility, st.size].forEach((v, i) => {
        const cell = mgEl("span", "mg-stat");
        cell.append(mgEl("i", null, MG_STAT_NAMES[i]), mgEl("b", null, "●".repeat(v) + "○".repeat(5 - v)));
        stats.append(cell);
      });
    };
    const play = mgEl("button", "mg-play", "Play");
    for (const s of players) {
      const img = mgEl("img", s === pick ? "on" : "");
      img.src = `/sprites/${encodeURIComponent(s.slug)}.png`;
      img.alt = img.title = s.common_name;
      img.onclick = () => {
        pick = s; name.textContent = s.common_name; mgStore.set("pick." + g.key, s.slug); showStats();
        row.querySelectorAll("img").forEach((i) => i.classList.toggle("on", i === img));
      };
      row.append(img);
    }
    // Levels: the next one unlocks when you finish the one before.
    const levels = mgEl("div", "mg-levels");
    let lv = Math.min(+(mgStore.get("lvl." + g.key) || 0), lvls.length - 1);
    const open = (i) => i === 0 || mgRec(g.key, i - 1).pct >= 100;
    if (!open(lv)) lv = 0;
    lvls.forEach((L, i) => {
      const rec = mgRec(g.key, i), b = mgEl("button", "mg-lv" + (i === lv ? " on" : ""));
      b.append(mgEl("b", null, `${i + 1}. ${L.name}`),
               mgEl("span", null, !open(i) ? `🔒 Finish level ${i} first` : rec.pct >= 100 ? `✓ Best ${rec.points || rec.got} points` : rec.pct ? `Best ${rec.pct}%` : "New"));
      b.disabled = !open(i);
      b.onclick = () => {
        lv = i; mgStore.set("lvl." + g.key, i); levels.querySelectorAll(".mg-lv").forEach((e, j) => e.classList.toggle("on", j === i));
        mgBoard(board, `${g.key}.${i}`, mgStore.get("board") || "all");
      };
      levels.append(b);
    });
    play.onclick = () => mgStart(g, pick, lv);
    foot.append(name, play);
    showStats();
    const board = mgEl("div", "mg-board");
    mgBoard(board, `${g.key}.${lv}`, mgStore.get("board") || "all");
    card.append(row, stats, levels, foot, board);
    list.append(card);
  }
}

function mgImg(cache, url) {
  if (!cache[url]) { cache[url] = new Image(); cache[url].src = url; }
  return cache[url];
}

function mgStart(g, s, level) {
  mg.game = g; mg.species = s; mg.level = level || 0; mg.tries = 0;
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
  mgMusicStop(mg.run);
  mg.run = null; mg.down = false;
  document.getElementById("mg-stage").classList.add("hidden");
  document.getElementById("mg-list").classList.remove("hidden");
  mgList();
}

// ---- Levels --------------------------------------------------------------------
// Every game has fixed levels, the same on every try, like Geometry Dash: you get
// better by learning the course, not by luck. Bumping into anything ends the try,
// and you start again right away from the beginning. A level is a list of things
// placed by distance along the course (wx: how far you've travelled when it
// reaches you).
const MG_DT = 1 / 120;  // fixed physics steps, so a course plays the same every time
const MG_SPEED = { sky: 75, trail: 100, river: 70 };
const MG_TOP = 18;      // how high a flier can go

// A gap to fly or swim through: a wall above it and a wall below it.
function mgGate(key, wx, c, gap, w) {
  const top = key === "sky" ? 0 : MG_SURFACE, bot = key === "sky" ? MG_GROUND + 6 : MG_BED;
  const a = c - gap / 2, b = c + gap / 2;
  const up = key === "sky" ? "storm" : "roots", down = key === "sky" ? "storm" : "boulder";
  return [{ type: up, wx, y: (top + a) / 2, w: w || 26, h: a - top },
          { type: down, wx, y: (b + bot) / 2, w: w || 26, h: bot - b }];
}

// Treats along a line, so the safe way through is also the tasty one.
function mgTrail(type, wx0, y0, wx1, y1, n, pts) {
  const out = [];
  for (let i = 0; i < n; i++) {
    const u = n > 1 ? i / (n - 1) : .5;
    out.push({ type, good: true, pts: pts || 1, wx: wx0 + (wx1 - wx0) * u, y: y0 + (y1 - y0) * u });
  }
  return out;
}

const MG_SIZES = { berry: [8, 8], acorn: [8, 9], snack: [7, 7], can: [10, 10], bottle: [10, 10], bag: [10, 10],
                   rock: [12, 10], log: [20, 8], stump: [10, 20], branch: [34, 10], snag: [24, 8], cloud: [30, 12] };

function mgSkyLevel(k, gates, extra) {
  const out = [];
  for (const [b, c, gap] of gates) {
    const wx = b * k;
    out.push(...mgGate("sky", wx, c, gap));
    out.push(...mgTrail("berry", wx - 30, c, wx + 30, c, 3));
  }
  for (const [b, y] of extra || []) out.push({ type: "cloud", wx: b * k, y });
  return out;
}

function mgRiverLevel(k, gates, snags, litter) {
  const out = [];
  for (const [b, c, gap] of gates) {
    const wx = b * k;
    out.push(...mgGate("river", wx, c, gap, 22));
    out.push(...mgTrail("snack", wx - 22, c, wx + 22, c, 2));
  }
  for (const [b, y] of snags) out.push({ type: "snag", wx: b * k, y });
  litter.forEach(([b, y], i) => out.push({ type: ["can", "bottle", "bag"][i % 3], good: true, litter: true, pts: 3, wx: b * k, y }));
  return out;
}

// Trail obstacles: rocks and logs to hop, tall stumps that need a big jump (hold),
// and low branches you must stay under (don't jump!).
function mgTrailLevel(k, list) {
  const out = [], g = MG_GROUND;
  for (const [type, b] of list) {
    const wx = b * k;
    if (type === "rock") out.push({ type, wx, y: g - 5 }, ...mgTrail("acorn", wx - 18, g - 34, wx + 18, g - 34, 3));
    else if (type === "log") out.push({ type, wx, y: g - 4 }, ...mgTrail("acorn", wx - 20, g - 36, wx + 20, g - 36, 3));
    else if (type === "stump") out.push({ type, wx, y: g - 10 }, ...mgTrail("acorn", wx - 14, g - 48, wx + 14, g - 48, 2));
    else if (type === "branch") out.push({ type, wx, y: g - 35 }, ...mgTrail("acorn", wx - 12, g - 8, wx + 12, g - 8, 2));
    else if (type === "acorns") out.push(...mgTrail("acorn", wx - 20, g - 8, wx + 20, g - 8, 3));
  }
  return out;
}

// Levels are written in beats of their song, so every hazard lands on the music:
// the tempo is the difficulty. [beat, gap middle, gap size] for gates.
const MG_LEVELS = {
  sky: [
    { name: "Meadow Breeze", bpm: 112, song: 0, items: (k) => mgSkyLevel(k, [
      [8, 100, 72], [12, 85, 72], [16, 110, 72], [20, 95, 72],
      [24, 70, 72], [28, 60, 70], [32, 75, 70],
      [38, 120, 70], [42, 130, 70], [46, 115, 70],
      [52, 90, 68], [55, 80, 68], [58, 70, 68], [61, 60, 68],
      [66, 100, 68], [70, 130, 68], [74, 95, 68], [78, 60, 68], [82, 100, 68], [86, 110, 68], [90, 80, 68],
    ], [[14, 145], [26, 140], [40, 52], [64, 140], [76, 140]]) },
    { name: "Storm Front", bpm: 128, song: 1, items: (k) => mgSkyLevel(k, [
      [8, 100, 62], [12, 70, 62], [16, 110, 62], [20, 70, 62], [24, 110, 62],
      [28, 130, 60], [30, 114, 60], [32, 98, 60], [34, 82, 60], [36, 66, 60],
      [40, 60, 60], [43, 100, 60], [46, 60, 60], [49, 100, 60], [52, 60, 60],
      [56, 140, 58], [58, 130, 58], [60, 120, 58], [62, 110, 58],
      [66, 50, 58], [69, 90, 58], [72, 130, 58], [75, 90, 58], [78, 50, 58],
      [82, 100, 58], [84, 100, 58], [86, 100, 58], [90, 70, 58], [94, 120, 58], [98, 95, 58], [102, 95, 58],
    ], [[38, 100], [54, 100], [64, 75], [80, 120], [88, 50]]) },
  ],
  trail: [
    { name: "Forest Path", bpm: 120, song: 2, items: (k) => mgTrailLevel(k, [
      ["acorns", 4], ["rock", 8], ["rock", 12], ["log", 16], ["acorns", 19],
      ["rock", 22], ["log", 26], ["branch", 30], ["acorns", 33], ["rock", 36],
      ["stump", 40], ["rock", 44], ["rock", 47], ["branch", 52], ["log", 56],
      ["stump", 60], ["acorns", 63], ["rock", 66], ["log", 70], ["branch", 74], ["rock", 78],
      ["log", 82], ["rock", 85], ["rock", 88],
    ]) },
    { name: "Rocky Ridge", bpm: 132, song: 3, items: (k) => mgTrailLevel(k, [
      ["rock", 8], ["rock", 11], ["rock", 14], ["log", 18], ["branch", 22],
      ["stump", 26], ["rock", 30], ["branch", 33], ["log", 37], ["rock", 40],
      ["stump", 44], ["stump", 48], ["branch", 52], ["rock", 56], ["rock", 59], ["rock", 62],
      ["branch", 66], ["log", 69], ["stump", 73], ["branch", 77], ["rock", 81], ["log", 84],
      ["stump", 88], ["rock", 92], ["branch", 95], ["rock", 99], ["stump", 103], ["log", 107], ["rock", 110],
    ]) },
  ],
  river: [
    { name: "Lazy Creek", bpm: 100, song: 4, items: (k) => mgRiverLevel(k,
      [[8, 110, 74], [13, 90, 74], [18, 130, 74], [24, 110, 74], [30, 80, 74],
       [36, 120, 74], [42, 140, 74], [48, 100, 72], [53, 70, 72], [59, 110, 72],
       [65, 140, 72], [71, 100, 72], [76, 120, 72]],
      [[10.5, 70], [15.5, 150], [21, 80], [33, 150], [39, 70], [50.5, 150], [62, 70], [68, 80]],
      [[15.5, 100], [27, 90], [45, 120], [56, 90], [73.5, 110]]) },
    { name: "Rapids", bpm: 116, song: 5, items: (k) => mgRiverLevel(k,
      [[8, 110, 64], [12, 80, 64], [16, 120, 64], [20, 150, 64], [24, 120, 64], [28, 80, 64],
       [33, 60, 62], [36, 90, 62], [39, 120, 62], [42, 150, 62],
       [47, 110, 62], [50, 110, 62], [53, 70, 62], [56, 110, 62], [59, 150, 62],
       [64, 100, 60], [67, 70, 60], [70, 100, 60], [73, 130, 60], [76, 100, 60]],
      [[10, 150], [14, 60], [22, 60], [30.5, 150], [44.5, 70], [61.5, 70], [74.5, 60]],
      [[18, 140], [34.5, 150], [48.5, 150], [68.5, 130], [79, 90]]) },
  ],
};

// A level's things, placed in pixels, and how long it is: a few beats past the last thing.
function mgLevelOf(key, n) {
  const lvl = MG_LEVELS[key][Math.min(n, MG_LEVELS[key].length - 1)];
  if (!lvl.things) {
    lvl.spb = 60 / lvl.bpm;
    const k = MG_SPEED[key] * lvl.spb;
    lvl.things = lvl.items(k).sort((a, b) => a.wx - b.wx);
    for (const o of lvl.things) if (MG_SIZES[o.type]) [o.w, o.h] = MG_SIZES[o.type];
    lvl.len = lvl.things[lvl.things.length - 1].wx + 4 * k;
  }
  return lvl;
}

function mgRec(key, n) {
  const k = `lv.${key}.${n}`;
  return { pct: +(mgStore.get(k + ".pct") || 0), got: +(mgStore.get(k + ".got") || 0), points: +(mgStore.get(k + ".points") || 0),
           who: mgStore.get(k + ".who") || "", k };
}
const mgTreats = (lvl) => lvl.things.reduce((s, o) => s + (o.good ? o.pts : 0), 0);

// ---- Music ------------------------------------------------------------------------
// Each level has its own little chiptune, made right here with Web Audio (no sound
// files). Hazards sit on its beats, so you can feel when to flap or jump. The song
// follows the level's own clock: it stops when you bump into something and starts
// over with your next try.
const MG_SONGS = [
  // root note (MIDI), chord roots in the key, lead pattern (scale steps, -1 = rest)
  { root: 60, prog: [0, 5, 3, 4], lead: [0, 2, 4, 2, 7, 4, 2, -1], scale: [0, 2, 4, 5, 7, 9, 11] },
  { root: 57, prog: [0, 5, 3, 6], lead: [4, -1, 4, 2, 0, 2, 4, 6], scale: [0, 2, 3, 5, 7, 8, 10] },
  { root: 62, prog: [0, 3, 4, 3], lead: [0, 4, 7, 4, 9, 7, 4, 2], scale: [0, 2, 4, 5, 7, 9, 11] },
  { root: 59, prog: [0, 6, 5, 4], lead: [7, 6, 4, -1, 4, 6, 7, 9], scale: [0, 2, 3, 5, 7, 8, 10] },
  { root: 65, prog: [0, 4, 5, 3], lead: [2, -1, 4, -1, 7, -1, 4, 2], scale: [0, 2, 4, 5, 7, 9, 11] },
  { root: 55, prog: [0, 3, 6, 4], lead: [0, 3, 4, 7, 4, 3, 0, 3], scale: [0, 2, 3, 5, 7, 8, 10] },
];
const mgAudio = { ctx: null, out: null, noise: null, muted: mgStore.get("muted") === "1" };

function mgAudioOn() {
  if (mgAudio.muted) return null;
  try {
    if (!mgAudio.ctx) {
      const C = window.AudioContext || window.webkitAudioContext;
      if (!C) return null;
      const ctx = mgAudio.ctx = new C();
      const buf = ctx.createBuffer(1, ctx.sampleRate * .2, ctx.sampleRate), d = buf.getChannelData(0);
      for (let i = 0; i < d.length; i++) d[i] = Math.sin(i * 12.9898) * 43758.5453 % 1;  // fixed noise, no Math.random
      mgAudio.noise = buf;
    }
    if (mgAudio.ctx.state === "suspended") mgAudio.ctx.resume();
    return mgAudio.ctx;
  } catch { return null; }
}

// Starts a fresh bus for this try, so stopping is just fading it out.
function mgMusicStart(r) {
  mgMusicStop(r);
  const ctx = mgAudioOn();
  if (!ctx) return;
  const out = ctx.createGain();
  out.gain.value = .16;
  out.connect(ctx.destination);
  r.music = { out, at: ctx.currentTime + .05 - r.rt, next: Math.ceil(r.rt / (r.lvl.spb / 4 / r.p.tempo)) };
}

function mgMusicStop(r) {
  if (!r || !r.music) return;
  const { out } = r.music, ctx = mgAudio.ctx;
  try { out.gain.setTargetAtTime(0, ctx.currentTime, .03); setTimeout(() => out.disconnect(), 400); } catch {}
  r.music = null;
}

const mgHz = (m) => 440 * Math.pow(2, (m - 69) / 12);

function mgNote(ctx, out, type, freq, at, len, vol, slide) {
  const o = ctx.createOscillator(), g = ctx.createGain();
  o.type = type; o.frequency.setValueAtTime(freq, at);
  if (slide) o.frequency.exponentialRampToValueAtTime(slide, at + len);
  g.gain.setValueAtTime(vol, at); g.gain.exponentialRampToValueAtTime(.001, at + len);
  o.connect(g); g.connect(out); o.start(at); o.stop(at + len + .02);
}

function mgHit16(ctx, out, at, len, vol, hp) {
  const s = ctx.createBufferSource(), f = ctx.createBiquadFilter(), g = ctx.createGain();
  s.buffer = mgAudio.noise; f.type = "highpass"; f.frequency.value = hp;
  g.gain.setValueAtTime(vol, at); g.gain.exponentialRampToValueAtTime(.001, at + len);
  s.connect(f); f.connect(g); g.connect(out); s.start(at); s.stop(at + len + .02);
}

// Schedules the next bit of the song, a little ahead of the level's clock. The
// level gets busier as it goes: drums first, then bass, then the tune.
function mgMusicTick(r) {
  const m = r.music, ctx = mgAudio.ctx;
  if (!m || !ctx) return;
  // Stay locked to the level's clock if the page stuttered.
  const want = ctx.currentTime - r.rt;
  if (Math.abs(want - m.at) > .08) m.at = want;
  // A faster animal plays the song faster, a slower one slower.
  const song = MG_SONGS[r.lvl.song % MG_SONGS.length], step = r.lvl.spb / 4 / r.p.tempo;
  while (m.next * step < r.rt + .25) {
    const i = m.next++, at = m.at + i * step;
    if (at < ctx.currentTime - .01) continue;
    const beat = Math.floor(i / 4), sub = i % 4, bar = Math.floor(beat / 4);
    const chord = song.prog[bar % 4], deg = (n) => song.root + song.scale[(n % 7 + 7) % 7] + 12 * Math.floor(n / 7);
    if (sub === 0 && beat % 2 === 0) mgNote(ctx, m.out, "sine", 150, at, .14, .9, 45);  // kick
    if (sub === 0 && beat % 2 === 1) mgHit16(ctx, m.out, at, .12, .35, 1200);            // snare
    if (sub === 2) mgHit16(ctx, m.out, at, .04, .18, 6000);                               // hi-hat
    if (bar >= 2 && sub % 2 === 0) mgNote(ctx, m.out, "triangle", mgHz(deg(chord) - 24), at, step * 1.8, .5);
    if (bar >= 4) {
      const n = song.lead[(i / 2 | 0) % song.lead.length];
      if (sub % 2 === 0 && n >= 0) mgNote(ctx, m.out, "square", mgHz(deg(chord + n)), at, step * 1.6, .09);
    }
  }
}

// A short sound for a bump, a treat and a cleared level.
function mgSfx(kind) {
  const ctx = mgAudio.ctx;
  if (!ctx || mgAudio.muted) return;
  const out = ctx.destination, at = ctx.currentTime;
  if (kind === "bump") mgNote(ctx, out, "square", 300, at, .25, .12, 60);
  else if (kind === "treat") mgNote(ctx, out, "square", 1320, at, .07, .05);
  else if (kind === "done") [0, 4, 7, 12].forEach((n, i) => mgNote(ctx, out, "square", mgHz(72 + n), at + i * .1, .2, .07));
}

// ---- Animal stats ----------------------------------------------------------------
// Every animal has Speed, Jump, Agility and Size from 1 to 5, from the real animal
// (tools/make_game_stats.py). Speed plays the whole level faster or slower, music
// and all, like changing a song's tempo: the course stays the same, a fast animal
// just gets less time to react and a better time. The others only ever make a
// level more forgiving, so every level is built for the weakest animal and every
// animal can finish it.
let mgStatsIdx = null;
fetch("/sprites/game_stats.json").then((r) => (r.ok ? r.json() : null)).then((j) => { mgStatsIdx = j; }).catch(() => {});
const MG_STAT_NAMES = ["Speed", "Jump", "Agility", "Size"];

function mgStats(slug) {
  const v = (mgStatsIdx && mgStatsIdx.stats[slug]) || [3, 3, 3, 3];
  return { speed: v[0], jump: v[1], agility: v[2], size: v[3] };
}

// What the stats do in a game. Level 1 of every stat is the baseline the levels are
// built (and checked) for.
function mgPhysOf(st) {
  return { tempo: [.75, .88, 1, 1.15, 1.3][st.speed - 1], jump: 1 + (st.jump - 1) * .04,
           power: 1 + (st.agility - 1) * .03, shrink: (5 - st.size) * .75 };
}

const mgPoints = (treats, p) => Math.round(treats * 10 * p.tempo);

// ---- Playing --------------------------------------------------------------------

function mgReset(mode) {
  const g = mg.game, lvl = mgLevelOf(g.key, mg.level);
  const rec = mgRec(g.key, mg.level);
  mg.tries = mode === "play" ? (mg.tries || 0) + 1 : mg.tries || 0;
  const st = mgStats(mg.species.slug);
  mg.run = { mode, t: 0, rt: 0, acc: 0, st, p: mgPhysOf(st), score: 0, litter: 0, fx: [], dist: 0, phase: 0, len: lvl.len, lvl,
             things: lvl.things.map((o) => Object.assign({ x: MG_W + 99 }, o)),
             x: g.key === "trail" ? 70 : 72, y: g.key === "trail" ? MG_GROUND : g.key === "sky" ? 90 : 110, vy: 0,
             flap: 0, ground: true, held: false, overAt: 0, rec, newBest: false, total: mgTreats(lvl) };
}

// A press: flap, jump or start swimming up. Shared by touch, keys and the level checker.
function mgPress(r, key, on) {
  if (on && !r.held) {
    if (key === "sky") { r.vy = -118 * r.p.power; r.flap = .35; }
    if (key === "trail" && r.ground) { r.vy = -255 * r.p.jump; r.ground = false; }
  }
  r.held = on;
}

function mgTap() {
  const r = mg.run;
  if (!r) return;
  if (r.mode === "ready" || r.mode === "paused") { r.mode = "play"; mg.last = 0; mgMusicStart(r); mgWake(); }
  else if (r.mode === "over" || r.mode === "done") {
    if (performance.now() - r.overAt > (r.mode === "done" ? 900 : 350)) { mgReset("play"); mgMusicStart(mg.run); mgWake(); }
  }
}

function mgWake() {
  const r = mg.run;
  const on = r && mg.visible && !document.hidden;
  if (r && !on && r.mode === "play") { r.mode = "paused"; mgMusicStop(r); }
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
  if (r.mode === "play") { mgStep(r, dt); mgMusicTick(r); }
  mgFxStep(r, dt);
  mgDraw();
  mg.raf = requestAnimationFrame(mgLoop);
}

// The animal's movement for one step. Pure, so it can be replayed exactly.
function mgPhys(r, key, dt) {
  r.t += dt; r.flap = Math.max(0, r.flap - dt);
  r.dist += MG_SPEED[key] * dt;
  if (key === "sky") {
    r.vy = Math.min(150, r.vy + 300 * dt);
    r.y += r.vy * dt;
    if (r.y < MG_TOP) { r.y = MG_TOP; r.vy = Math.max(0, r.vy); }
    if (r.y > MG_GROUND - 14) { r.y = MG_GROUND - 14; r.vy = 0; }  // glides along the meadow
  } else if (key === "trail") {
    if (!r.ground) {
      // Let go early for a small hop.
      r.vy += (r.vy < 0 && !r.held ? 760 * 2.2 : 760) * dt;
      r.y += r.vy * dt;
      if (r.y >= MG_GROUND) { r.y = MG_GROUND; r.vy = 0; r.ground = true; }
    }
  } else {
    r.vy += (r.held ? -260 * r.p.power : 200) * dt;
    r.vy = Math.max(-95, Math.min(85, r.vy));
    r.y += r.vy * dt;
    if (r.y < MG_SURFACE + 12) { r.y = MG_SURFACE + 12; r.vy = Math.max(0, r.vy); }
    if (r.y > MG_BED - 12) { r.y = MG_BED - 12; r.vy = Math.min(0, r.vy); }
  }
}

// What of the player touches things: a box around its body, a bit smaller than the
// sprite so near misses count as misses. On the trail r.y is where its feet are.
function mgBox(key, r, pad) {
  const p = (pad || 0) - r.p.shrink;
  return key === "trail" ? [r.x - 8 - p, r.y - 21 - p, r.x + 8 + p, r.y - 1 + p] : [r.x - 8 - p, r.y - 7 - p, r.x + 8 + p, r.y + 7 + p];
}
const mgTouches = (b, o, x) => !(x + o.w / 2 < b[0] || x - o.w / 2 > b[2] || o.y + o.h / 2 < b[1] || o.y - o.h / 2 > b[3]);

// Does the animal hit a hazard right now? (Used by the game and the level checker.)
function mgHit(r, key, things, pad) {
  const b = mgBox(key, r, pad);
  for (const o of things) {
    if (o.good) continue;
    const x = o.wx - r.dist + r.x;
    if (x > b[2] + 40) break;  // things are in course order
    if (mgTouches(b, o, x)) return true;
  }
  return false;
}

function mgStep(r, dt) {
  const key = mg.game.key;
  // Fixed steps: the same presses always give the same flight.
  r.rt += dt;
  r.acc += dt * r.p.tempo;
  while (r.acc >= MG_DT && r.mode === "play") {
    r.acc -= MG_DT;
    mgPress(r, key, mg.down);
    mgPhys(r, key, MG_DT);
    for (const o of r.things) o.x = o.wx - r.dist + r.x;
    const b = mgBox(key, r);
    for (const o of r.things) {
      if (!o.good || o.gone || o.x > b[2] + 20 || !mgTouches(b, o, o.x)) continue;
      o.gone = true;
      r.score += o.pts;
      mgSfx("treat");
      if (o.litter) r.litter++;
      r.fx.push({ kind: "text", x: o.x, y: o.y - 6, text: `+${o.pts}`, life: .8 });
      if (o.litter) r.fx.push({ kind: "text", x: o.x, y: o.y - 16, text: "Cleaned!", life: .9 });
      for (let i = 0; i < 5; i++) r.fx.push({ kind: "spark", x: o.x, y: o.y, vx: (i - 2) * 18, vy: -20 - (i % 3) * 18, life: .5 });
    }
    if (mgHit(r, key, r.hazards || (r.hazards = r.things.filter((o) => !o.good).sort((a, b) => a.wx - b.wx)))) mgEnd(r, false);
    else if (r.dist >= r.len) mgEnd(r, true);
  }
}

function mgEnd(r, cleared) {
  const pct = cleared ? 100 : Math.min(99, Math.floor(r.dist / r.len * 100));
  r.mode = cleared ? "done" : "over"; r.overAt = performance.now(); r.pct = pct; mg.down = false;
  mgMusicStop(r);
  mgSfx(cleared ? "done" : "bump");
  const rec = r.rec;
  r.newBest = pct > rec.pct || (cleared && r.score > rec.got);
  if (pct > rec.pct) { rec.pct = pct; mgStore.set(rec.k + ".pct", pct); }
  if (cleared && r.score > rec.got) { rec.got = r.score; mgStore.set(rec.k + ".got", r.score); }
  if (cleared) {
    // Points for a finished run: every treat counts, times the animal's speed. A fast
    // animal is harder to steer through, so it earns more. Best overall, and per animal.
    const pts = mgPoints(r.score, r.p), slug = mg.species.slug, mine = +(mgStore.get(`${rec.k}.p.${slug}`) || 0);
    r.points = pts;
    r.animalBest = pts > mine;
    if (r.animalBest) mgStore.set(`${rec.k}.p.${slug}`, pts);
    // The server works the points out again from the treats and the animal.
    mg.posting = mgApi("POST", "/games/scores", { level: `${mg.game.key}.${mg.level}`, species: slug, treats: r.score }).catch(() => {});
    if (pts > rec.points) { r.newBest = true; rec.points = pts; mgStore.set(rec.k + ".points", pts); mgStore.set(rec.k + ".who", mg.species.common_name); }
    else r.newBest = false;
  }
  if (!cleared) {
    const [x0, y0, x1, y1] = mgBox(mg.game.key, r);
    for (let i = 0; i < 6; i++) r.fx.push({ kind: "star", x: (x0 + x1) / 2, y: (y0 + y1) / 2, vx: (i - 2.5) * 16, vy: -30 - (i % 2) * 20, life: .8 });
  }
}

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
  c.setTransform(MG_RES, 0, 0, MG_RES, 0, 0);
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
    case "storm": {
      // A wall of storm cloud, puffy at the end that faces the gap.
      const t0 = Math.round(o.y - o.h / 2), t1 = Math.round(o.y + o.h / 2), up = t0 <= 2;
      c.fillStyle = "#6f7488"; c.fillRect(x - 13, t0, 26, t1 - t0);
      // Puffs down both sides so it reads as cloud, not a pillar.
      for (let yy = t0 + 5; yy < t1 - 3; yy += 9) {
        const k = Math.floor((yy + o.wx) / 9) % 3;
        c.fillStyle = "#7a7f92"; c.beginPath(); c.arc(x - 12 + k, yy, 4, 0, Math.PI * 2); c.arc(x + 12 - k, yy + 4, 4, 0, Math.PI * 2); c.fill();
        c.fillStyle = "#5f6378"; c.fillRect(x - 5 + k * 2, yy + 2, 8, 2);
      }
      c.fillStyle = "#8a8fa2"; c.fillRect(x - 13, t0, 3, t1 - t0);
      const end = up ? t1 : t0;
      c.fillStyle = "#7a7f92";
      for (const [dx, r0] of [[-10, 5], [0, 7], [10, 5]]) { c.beginPath(); c.arc(x + dx, end, r0, 0, Math.PI * 2); c.fill(); }
      if (Math.sin(r.phase * 4 + o.wx) > .93) { box(-1, up ? 6 + (t1 - y) : -(y - t0) - 12, 2, 5, "#f2c14e"); }
      break;
    }
    case "roots": {
      const t1 = Math.round(o.y + o.h / 2);
      c.fillStyle = "#5b4030"; c.fillRect(x - 11, MG_SURFACE, 22, t1 - MG_SURFACE);
      c.fillStyle = "#7a5a40"; c.fillRect(x - 11, MG_SURFACE, 4, t1 - MG_SURFACE);
      c.fillStyle = "#5b4030";
      for (const dx of [-8, -2, 5]) c.fillRect(x + dx, t1, 2, 4 + ((dx + 9) % 4));
      break;
    }
    case "boulder": {
      const t0 = Math.round(o.y - o.h / 2);
      c.fillStyle = "#6e7380"; c.fillRect(x - 11, t0 + 3, 22, MG_BED - t0);
      c.fillStyle = "#8a8f9e"; c.fillRect(x - 9, t0, 18, 5); c.fillRect(x - 11, t0 + 3, 5, MG_BED - t0 - 3);
      c.fillStyle = "#3f8d58"; c.fillRect(x - 7, t0, 6, 2);
      break;
    }
    case "stump":
      box(-5, -10, 10, 20, "#7a5232"); box(-5, -10, 10, 3, "#d8b07a"); box(-3, -9, 6, 1, "#a8744a"); box(-5, -10, 2, 20, "#946640");
      box(-7, 8, 14, 2, "#62402a"); break;
    case "branch":
      // Vines from the leafy canopy above hold the branch up.
      c.fillStyle = "#3f8d58"; c.fillRect(x - 12, 0, 1, y); c.fillRect(x + 11, 0, 1, y);
      c.fillStyle = "#2f7d4f";
      for (let dx = -22; dx <= 22; dx += 8) { c.beginPath(); c.arc(x + dx, 2, 7, 0, Math.PI * 2); c.fill(); }
      box(-17, -2, 34, 4, "#7a5232"); box(-17, -2, 34, 1, "#a8744a");
      box(-15, -6, 8, 4, "#3f8d58"); box(-3, -7, 8, 5, "#2f7d4f"); box(9, -6, 7, 4, "#3f8d58"); box(-10, 2, 6, 3, "#2f7d4f");
      break;
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
  else if (pose === "swim") frame = cyc(r.phase * (r.held ? 5 : 2.5));
  if (r.mode === "over" && acts.includes("idle")) { pose = "idle"; frame = 0; }
  const img = framed ? sheet : raw;
  if (!img || !img.complete || !img.naturalWidth) return;
  const F = framed ? sheet.naturalWidth / habAnimIdx.frames : raw.naturalWidth;
  if (r.mode === "over" && Math.floor(r.phase * 12) % 3 === 0) return;  // blink after a bump
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
  // How far along the course you are, with your best try marked.
  const p = Math.min(1, r.dist / r.len), bw = MG_W - 120;
  c.fillStyle = "rgba(0,0,0,.35)"; c.fillRect(60, 7, bw, 6);
  c.fillStyle = "#9be59b"; c.fillRect(60, 7, Math.round(bw * p), 6);
  if (r.rec.pct) { c.fillStyle = "#ffd28a"; c.fillRect(60 + Math.round(bw * r.rec.pct / 100) - 1, 5, 2, 10); }
  c.textAlign = "left"; c.font = "bold 11px system-ui, sans-serif";
  const label = `${g.key === "river" ? "Score" : g.key === "sky" ? "Berries" : "Acorns"} ${r.score}`;
  c.fillStyle = "rgba(0,0,0,.35)"; c.fillRect(4, 18, c.measureText(label).width + 10, 16);
  c.fillStyle = "#fff"; c.fillText(label, 9, 30);
  c.font = "bold 10px system-ui, sans-serif"; c.textAlign = "right";
  c.fillStyle = "#fff"; c.fillText(`${Math.floor(p * 100)}%`, MG_W - 8, 15);
  if (r.p.tempo !== 1) {
    const sp = `Speed ×${r.p.tempo}`;
    c.fillStyle = "rgba(0,0,0,.35)"; c.fillRect(MG_W - 14 - c.measureText(sp).width, 18, c.measureText(sp).width + 10, 16);
    c.fillStyle = r.p.tempo > 1 ? "#ffd28a" : "#cfe"; c.fillText(sp, MG_W - 9, 30);
  }
  c.textAlign = "left"; c.fillText(`Try ${mg.tries || 1}`, 8, 15);
  const lvl = r.lvl;
  if (r.mode === "ready") mgPanel(c, [[`Level ${mg.level + 1}: ${lvl.name}`, 14], [g.tip, 11], ["The course is the same every time. Learn it!", 10, "#cfe"], ["Tap to start", 11, "#ffd28a"]], top);
  else if (r.mode === "paused") mgPanel(c, [["Paused", 15], ["Tap to keep going", 11, "#ffd28a"]], top);
  else if (r.mode === "over") {
    const lines = [["Bump!", 15], [`You made it ${r.pct}% of the way`, 12, "#ffd28a"]];
    lines.push([r.newBest ? "That's your best yet!" : `Best: ${r.rec.pct}%`, 11, r.newBest ? "#9be59b" : "#fff"]);
    lines.push(["Tap to try again", 10, "#cfe"]);
    mgPanel(c, lines, Math.min(top, MG_H - 8 - (lines.length * 16 + 14)));
  } else if (r.mode === "done") {
    const lines = [["Level complete!", 15, "#9be59b"], [`${r.points} points as a ${mg.species.common_name}`, 12, "#ffd28a"],
                   [`${r.score} of ${r.total} ${g.thing[1]} × ${r.p.tempo} speed bonus`, 10]];
    if (g.key === "river" && r.litter) lines.push([`You cleaned up ${r.litter} piece${r.litter === 1 ? "" : "s"} of litter`, 10]);
    if (r.score >= r.total) lines.push(["You got every one!", 11, "#9be59b"]);
    if (r.newBest) lines.push(["Your best score yet!", 11, "#9be59b"]);
    else if (r.animalBest) lines.push([`Your best with this animal! (Best ever: ${r.rec.points})`, 10, "#9be59b"]);
    else lines.push([`Best: ${r.rec.points} as a ${r.rec.who}`, 10]);
    if (mg.level + 1 < MG_LEVELS[g.key].length) lines.push([`Level ${mg.level + 2} is unlocked!`, 10, "#cfe"]);
    lines.push(["Tap to play again", 10, "#cfe"]);
    mgPanel(c, lines, Math.min(top, MG_H - 8 - (lines.length * 16 + 14)));
  }
}
