// Decorations from the minigame shop in your own habitat, and the animals that visit them.
//
// species/decor.json (written by tools/make_decor.py, which also draws the sprites in
// species/sprites/decor/) lists each decoration: where it goes (the meadow's back, middle
// or front row, the pond, the beach, the sea or the sky), its frames, its effect (a glow
// at night, bubbles, a spinning pinwheel...) and its visits: which animals come, what
// they do there and where, in the drawing's grid (32 wide, feet on row 31). Only the
// animals you've caught visit, and only in your own habitat, never a friend's.
//
// habitat.js calls in here from habLoop (habDecorTick), habStep (habDecorStep: a visiting
// animal goes there, stays a while and leaves), habRestSpot (habDecorRest: homes and beds
// for sleeping animals), habPose/habAnim (perched or riding), and habDraw (the sprites in
// depth order with the animals, then the glows and particles).

let habDecorCat = null;
fetch("/decor.json").then((r) => (r.ok ? r.json() : null)).then((j) => {
  if (j) { habDecorCat = Object.fromEntries(j.map((d) => [d.key, d])); hab.decorKey = ""; }
}).catch(() => {});
const habDecorImgs = {};
function habDecorImg(key) {
  if (!habDecorImgs[key]) { habDecorImgs[key] = new Image(); habDecorImgs[key].src = `/sprites/decor/${key}.png`; }
  return habDecorImgs[key];
}
hab.decor = [];
hab.dfx = [];

// How many can stand in each part of the scene at once (app/games.py has the same numbers).
const HAB_DECOR_ROOM = { ground: 12, pond: 3, sand: 3, sea: 2, sky: 2 };

// The spots decorations stand on, for this layout.
function habDecorSlots(L) {
  const g = (f, y, row) => ({ x: Math.round(L.land * f), y, row });
  const p = L.pond, sand = (y) => ({ x: Math.round((L.shore[y] + L.surf[y]) / 2), y });
  return {
    // Three rows of four: behind the pond, either side of it, and in front.
    ground: [g(.27, 188, "back"), g(.47, 188, "back"), g(.67, 188, "back"), g(.87, 188, "back"),
             g(.09, 227, "mid"), g(.26, 228, "mid"), g(.82, 228, "mid"), g(.96, 227, "mid"),
             g(.17, 266, "front"), g(.39, 266, "front"), g(.61, 266, "front"), g(.83, 266, "front")],
    pond: [{ x: p.x - Math.round(p.rx * .55), y: p.y + 5 }, { x: p.x, y: p.y + 8 }, { x: p.x + Math.round(p.rx * .55), y: p.y + 5 }],
    sand: [sand(206), sand(234), sand(262)],
    sea: [{ x: Math.round((L.sea + L.w) / 2), y: L.water + 16 }, { x: L.w - 22, y: L.water + 44 }],
    sky: [{ x: Math.round(L.w / 2), y: 84 }, { x: Math.round(L.w / 2), y: 60 }],
  };
}

// Puts the decorations you're showing on their spots: the meadow fills tall ones from
// the back row, low ones from the front. Re-run when the look or the layout changes.
function habDecorPlace() {
  const L = hab.L;
  const keys = L && habMine() && habDecorCat ? habLook.decor.filter((k) => habDecorCat[k]) : [];
  const key = `${L ? L.w : 0}|${keys.join(",")}`;
  if (hab.decorKey === key) return;
  hab.decorKey = key;
  for (const a of hab.animals) { a.dv = null; a.home = null; }
  const slots = L ? habDecorSlots(L) : {}, used = new Set(), out = [];
  const order = { back: ["back", "mid", "front"], front: ["front", "mid", "back"], any: ["mid", "front", "back"] };
  for (const k of keys) {
    const it = habDecorCat[k], list = slots[it.area] || [];
    let i = -1;
    if (it.area === "ground") {
      for (const row of order[it.row] || order.any) {
        i = list.findIndex((s, j) => s.row === row && !used.has("ground" + j));
        if (i >= 0) break;
      }
    } else i = list.findIndex((s, j) => !used.has(it.area + j));
    if (i < 0) continue;
    used.add(it.area + i);
    out.push({ key: k, it, x: list[i].x, y: list[i].y, ox: 0, oy: 0, frame: 0, flip: false, busy: {}, t: rnd(0, 30), st: {} });
  }
  hab.decor = out;
  hab.dfx = [];
}

// ---- Who's who -------------------------------------------------------------------------
const habSlug = (re) => (a) => re.test(a.s.slug);
const habBird = (a) => a.s.category === "bird";
const habMammal = (re) => (a) => a.s.category === "mammal" && re.test(a.s.slug);
const HAB_WHO = {
  owl: habSlug(/(^|_)owl$/),
  nightbird: habSlug(/(^|_)owl$|nighthawk|poorwill|whip_poor_will|chuck_will|night_heron/),
  bat: habSlug(/_bat$/),
  moth: habSlug(/moth$|firefly/),
  bee: habSlug(/_bee$|bumble_bee/),
  beetle: habSlug(/beetle$/),
  hummingbird: (a) => a.role === "hover",
  butterfly: (a) => a.role === "flutter" && a.s.category === "invertebrate" &&
    !/moth$|firefly|_bee$|beetle|skimmer|pondhawk|dasher|pennant|whitetail|lanternfly|darner|dragonfly|damselfly/.test(a.s.slug),
  bug: (a) => a.role === "flutter" && a.s.category === "invertebrate" && !/firefly|moth$/.test(a.s.slug),
  raptor: (a) => habBird(a) && (a.role === "soar" || /hawk|eagle|osprey|falcon|kestrel|merlin|harrier/.test(a.s.slug)),
  seabird: (a) => HAB_SEABIRDS.test(a.s.slug) && HAB_FLIERS.has(a.role),
  jay: habSlug(/(^|_)jay$|(^|_)crow$|raven|magpie|nutcracker/),
  songbird: (a) => habBird(a) && a.role === "fly" && !HAB_SEABIRDS.test(a.s.slug) && !HAB_GLIDERS.test(a.s.slug) &&
    !/(^|_)owl$|nighthawk|poorwill|night_heron|albatross|shearwater|petrel/.test(a.s.slug),
  smallbird: (a) => HAB_WHO.songbird(a),
  bird: (a) => habBird(a) && HAB_FLIERS.has(a.role) && a.role !== "hover" && !/(^|_)owl$|albatross/.test(a.s.slug),
  flier: (a) => habBird(a) && ["fly", "soar", "dive"].includes(a.role),
  duck: (a) => habBird(a) && a.role === "paddle",
  wader: (a) => a.role === "wade",
  shorebird: (a) => habBird(a) && (a.role === "beach" || /plover|sandpiper|sanderling|willet|turnstone|killdeer/.test(a.s.slug)),
  groundbird: habSlug(/quail|_dove$|(^|_)turkey$|grouse|pheasant|bobwhite|roadrunner|prairie_chicken|ptarmigan|chachalaca/),
  frog: habSlug(/frog|toad|peeper/),
  salamander: habSlug(/salamander|newt|ensatina|hellbender|mudpuppy|siren$/),
  turtle: (a) => a.s.category === "reptile" && /turtle|tortoise|cooter|slider$|terrapin|softshell|snapping/.test(a.s.slug),
  lizard: (a) => a.s.category === "reptile" && /lizard|skink|anole|gecko|whiptail|iguana|chuckwalla|horned|gila|racerunner/.test(a.s.slug),
  snake: (a) => a.s.category === "reptile" && /snake|racer|rattle|kingsnake|garter|boa|python|copperhead|cottonmouth|coachwhip|massasauga|ribbon/.test(a.s.slug),
  reptile: (a) => HAB_WHO.lizard(a) || HAB_WHO.snake(a),
  crab: (a) => /crab$/.test(a.s.slug) && (a.role === "beach" || a.role === "walk"),
  seal: habSlug(/seal$|sea_lion|walrus/),
  snail: (a) => a.s.category === "invertebrate" && /snail|(^|_)slug$/.test(a.s.slug),
  spider: (a) => a.role === "dangle",
  squirrel: habSlug(/squirrel|chipmunk/),
  rabbit: habMammal(/rabbit|(^|_)hare$|cottontail|jackrabbit|pika/),
  mouse: habMammal(/mouse|vole|woodrat|kangaroo_rat|(^|_)rat$|shrew|lemming/),
  smallmammal: (a) => a.s.category === "mammal" && a.role === "walk" &&
    (HAB_WHO.squirrel(a) || HAB_WHO.rabbit(a) || HAB_WHO.mouse(a) || /marmot|woodchuck|prairie_dog|gopher|weasel|mink|ferret|stoat|ermine|armadillo|hedgehog/.test(a.s.slug)),
  lookout: habSlug(/chipmunk|pika|marmot|woodchuck|prairie_dog|ground_squirrel|antelope_squirrel|rock_squirrel/),
  raccoon: habMammal(/raccoon|opossum|ringtail|coati|skunk/),
  napper: (a) => HAB_WHO.raccoon(a) || HAB_WHO.squirrel(a),
  slider: (a) => /otter/.test(a.s.slug) && a.role !== "float" || HAB_WHO.squirrel(a) || HAB_WHO.raccoon(a),
  fox: habMammal(/fox$|coyote|bobcat|lynx|(^|_)wolf$/),
  bear: habMammal(/(^|_)bear$/),
  deer: habMammal(/(^|_)deer$|(^|_)elk$|moose|pronghorn|sheep$|mountain_goat|bison|caribou|javelina/),
  walker: (a) => ["walk", "hop", "shore"].includes(a.role) && !HAB_FLIERS.has(a.role),
};
const habIs = (a, who) => !!HAB_WHO[who] && HAB_WHO[who](a);

// Visits where a flier lands and sits still, rather than flying around the spot.
const HAB_LANDS = new Set(["perch", "ride", "bathe", "home"]);
// Visits that walk a path through or across the decoration: [gx, gy] points.
const HAB_DECOR_PATHS = {
  through: [[0, 31], [32, 31]],
  cross: [[-4, 31], [3, 26], [9, 23], [16, 22], [23, 23], [29, 26], [36, 31]],
  slide: [[6, 3], [11, 7], [16, 12], [20, 18], [24, 25], [31, 29], [36, 31]],
  hopacross: [[-2, 31], [3, 30], [11, 28], [20, 30], [28, 28], [34, 31]],
};
// How long each kind of visit lasts, in seconds [min, max].
const HAB_STAY = { perch: [6, 14], ride: [8, 16], bathe: [5, 9], home: [8, 14], hover: [5, 10], eat: [5, 10], drink: [4, 8],
                   fish: [6, 12], sit: [8, 16], bask: [10, 20], hide: [5, 10], watch: [4, 8], dig: [4, 8], swim: [6, 12],
                   escort: [6, 10], bump: [1, 2], chase: [5, 9], pose: [3, 5], shelter: [8, 14], dangle: [10, 20] };

// A point of a decoration's drawing in the scene, as it stands now (it may drift, bob or roll).
function habDecorAt(d, gx, gy) {
  if (d.kite && gy < -30) return [d.kite[0] + gx, d.kite[1] + 8];
  const x = d.x + d.ox + (d.flip ? 16 - gx : gx - 16);
  return [x, d.y + d.oy + gy - 31];
}
const habDecorDay = (phase) => phase !== "night";

// ---- Each frame: drifting, bobbing, rolling, spinning, and the little particles ----------
function habDecorTick(dt) {
  habDecorPlace();
  if (!hab.decor.length) return;
  const L = hab.L, phase = habPhase(), gust = habGust();
  for (const d of hab.decor) {
    d.t += dt;
    const t = d.t, fx = d.it.fx, riders = Object.values(d.busy).some((a) => a.dv && a.dv.d === d && a.dv.stage === "stay");
    d.gone = false;
    if (d.it.frames > 1) {
      if (d.key === "pinwheel") d.frame = Math.floor(t * (5 + Math.abs(gust))) % 4;
      else if (d.key === "windsock") { d.frame = Math.abs(gust) >= 14 ? 3 : gust ? 2 : 0; d.flip = gust < 0; }
      else if (d.key === "weathervane") { d.frame = gust ? 0 : Math.floor(t * .2) % 4; d.flip = gust < 0; }
      else if (d.key === "wind_chimes") d.frame = gust ? Math.floor(t * (Math.abs(gust) / 3)) % 4 : 0;
      else if (d.key === "sunflowers") d.frame = Math.floor(t * 1.5) % 4;
      else if (d.key === "kite") d.frame = d.kite ? 1 : 0;  // frame 0 has the kite resting on the ground
      else if (d.key === "beach_ball") d.frame = ((Math.floor((d.st.roll || 0) / 4) % 4) + 4) % 4;
      else d.frame = riders ? Math.floor(t * 2.4) % 4 : 0;  // swings, hammock, seesaw: move when ridden
    }
    if (fx === "bob") {
      d.oy = Math.round(Math.sin(t * 1.6));
      if (d.key === "rubber_duck") { d.ox = Math.round(Math.sin(t * .23) * L.pond.rx * .3); d.flip = Math.cos(t * .23) > 0; }
    } else if (fx === "drift" && d.it.area === "sea") {
      const span = (L.w - L.sea) / 2 - 24;
      d.ox = Math.round(Math.sin(t * .04) * span); d.oy = Math.round(Math.sin(t * 1.3)); d.flip = Math.cos(t * .04) > 0;
    } else if (fx === "drift") {  // the balloon crosses the sky by day
      d.gone = phase === "night";
      d.ox = Math.round(((t * 3) % (L.w + 80)) - 40 - d.x); d.oy = Math.round(Math.sin(t * .3) * 6);
    } else if (fx === "glide") {  // a paper airplane every 30 seconds
      const k = (t % 30) / 7;
      d.gone = k > 1 || phase === "night";
      d.ox = Math.round(-30 + k * (L.w + 60) - d.x); d.oy = Math.round(k * 26 + Math.sin(k * 9) * 4); d.flip = true;
    } else if (fx === "ball") {
      const s = d.st;
      s.vx = (s.vx || 0) * Math.pow(.35, dt);
      if (Math.abs(s.vx) < 1) s.vx = 0;
      let nx = d.ox + s.vx * dt;
      if (d.x + nx < 12 || d.x + nx > L.land - 12 || Math.abs(nx) > 46) { s.vx = -s.vx * .6; nx = d.ox; }
      s.roll = (s.roll || 0) + (nx - d.ox);
      d.ox = nx;
      d.oy = s.vx ? -Math.round(Math.abs(Math.sin((s.roll || 0) / 6)) * 2) : 0;
    } else if (fx === "soccer") {
      const s = d.st;
      if (s.bx === undefined) s.bx = 12;
      s.vx = (s.vx || 0) * Math.pow(.4, dt);
      s.bx += (s.vx || 0) * dt;
      if (s.goal > 0 && (s.goal -= dt) <= 0) { s.bx = 12; s.vx = 0; }
      if (s.bx > 16) { s.bx = 16; s.vx = -Math.abs(s.vx || 0) * .5; }
      if (s.bx < -4 && !s.goal) {  // in the net: a little sparkle
        s.goal = 2.2; s.vx = 0;
        for (let i = 0; i < 8; i++) hab.dfx.push({ x: d.x - 8, y: d.y - 12, vx: rnd(-20, 20), vy: rnd(-34, -10), g: 40, life: .9, col: "#ffe27a" });
      }
    } else if (fx === "kite") {
      d.kite = habDecorDay(phase) ? [Math.round(d.x + 18 + Math.sin(t * .6) * 8), Math.round(Math.max(40, d.y - 120) + Math.sin(t * 1.1) * 5)] : null;
    }
    habDecorParticles(d, dt, phase, gust);
  }
  for (const p of hab.dfx) { p.life -= dt; p.vy += (p.g || 0) * dt; p.x += p.vx * dt; p.y += p.vy * dt; }
  hab.dfx = hab.dfx.filter((p) => p.life > 0);
  if (hab.dfx.length > 160) hab.dfx.splice(0, hab.dfx.length - 160);
}

function habDecorParticles(d, dt, phase, gust) {
  const fx = d.it.fx, at = (gx, gy) => habDecorAt(d, gx, gy), chance = (perSec) => Math.random() < perSec * dt;
  const day = habDecorDay(phase), push = (o) => hab.dfx.push(o);
  if (fx === "petals" && chance(1.2)) {
    const [x, y] = at(rnd(4, 28), rnd(0, 10));
    push({ x, y, vx: gust * .8 + rnd(-4, 4), vy: rnd(4, 9), life: 3, col: pick("#f8b8d0", "#ffe0ec") });
  } else if (fx === "sparkle" && chance(.8)) {
    const [x, y] = d.key === "clover" ? at(16, 26) : at(rnd(10, 22), rnd(8, 22));
    push({ x, y, vx: 0, vy: 0, life: .6, col: "#fff8c0", star: true });
  } else if (fx === "spray" && chance(14)) {
    const [x, y] = at(16, 10);
    push({ x, y, vx: rnd(-12, 12), vy: rnd(-38, -26), g: 90, life: .75, col: phase === "night" ? "#a8c8f0" : "#d8f2ff" });
  } else if (fx === "trickle" && chance(6)) {
    const [x, y] = at(rnd(15, 18), 9);
    push({ x, y, vx: 0, vy: 30, life: .6, col: "#e0f4ff" });
  } else if (fx === "seeds" && day && chance(.7)) {
    const [x, y] = at(rnd(9, 23), 13);
    push({ x, y, vx: rnd(-3, 3), vy: 0, g: 60, life: .55, col: "#d8b070" });
  } else if (fx === "bubbles" && phase !== "night" && chance(1.6)) {
    const [x, y] = at(26, 13);
    push({ x, y, vx: rnd(4, 12) + gust, vy: rnd(-12, -6), life: rnd(2.5, 4.5), col: "#ffffff", bubble: pick(1, 2, 2, 3) });
  } else if (fx === "sprinkler" && day && chance(18)) {
    const [x, y] = at(16, 24), a = Math.sin(d.t * 1.2) * 1.1;
    push({ x, y, vx: Math.sin(a) * 44, vy: -Math.cos(a) * 46, g: 120, life: .8, col: "#d8f2ff" });
  } else if (fx === "bees" && day && chance(3)) {
    const [x, y] = at(16, 22);
    push({ x: x + rnd(-14, 14), y: y + rnd(-14, 2), vx: rnd(-10, 10), vy: rnd(-6, 6), life: .5, col: "#f2c14e" });
  } else if (fx === "rainfill" && habWet() && chance(2)) {
    const [x, y] = at(rnd(8, 24), 30);
    habRipple(x, y);
  } else if (fx === "camera") {
    const s = d.st, [lx, ly] = at(16, 14);
    s.cool = Math.max(0, (s.cool || 0) - dt);
    s.flash = Math.max(0, (s.flash || 0) - dt);
    if (!s.cool) {
      const who = hab.animals.find((a) => !habDecorHidden(a, true) && !HAB_FLIERS.has(a.role) && a.x > lx + 6 && a.x < lx + 34 && Math.abs(a.y - d.y) < 12);
      if (who) { s.cool = 9; s.flash = .25; s.say = 1.8; }
    }
    s.say = Math.max(0, (s.say || 0) - dt);
    s.lens = [lx, ly];
  }
}

// ---- Visits ------------------------------------------------------------------------------
// Returns true while the animal is busy with a decoration (habStep then leaves it be).
function habDecorStep(a, dt, awake) {
  const dv = a.dv;
  if (!hab.decor.length) { a.dv = null; return false; }
  if (dv) {
    if (!awake || !hab.decor.includes(dv.d) || dv.d.gone) {
      if (dv.stage === "leave" || !awake) { a.dv = null; if (a.role === "dive") a.mode = "fly"; }
      else habDecorEnd(a);
      return !!a.dv && awake;
    }
    return habDecorGo(a, dt, dv);
  }
  if (!awake || !habMine() || HAB_SEA.has(a.role) || a.role === "float") return false;
  if (a.mode && !(a.role === "dive" && a.mode === "fly")) return false;
  if ((a.dvIn = (a.dvIn === undefined ? rnd(2, 10) : a.dvIn) - dt) > 0) return false;
  a.dvIn = rnd(8, 22);
  const phase = habPhase(), opts = [];
  for (const d of hab.decor) {
    if (d.gone) continue;
    (d.it.visits || []).forEach((v, i) => {
      if (v.act === "sleep") return;
      if (v.when === "day" && phase === "night" || v.when === "night" && phase !== "night" && phase !== "dusk") return;
      const who = d.busy[i];
      if (who && who !== a && who.dv && who.dv.d === d) return;
      if (habIs(a, v.who)) opts.push([d, i, v]);
    });
  }
  if (!opts.length || Math.random() < .2) return false;
  const [d, i, v] = opts[Math.floor(Math.random() * opts.length)];
  d.busy[i] = a;
  let path = HAB_DECOR_PATHS[v.act];
  // Go through or across from whichever side the animal is on.
  if (path && v.act !== "slide" && a.x > d.x + d.ox) path = path.slice().reverse().map(([x, y]) => [x, y]);
  a.dv = { d, i, v, path, k: 0, stage: "go", left: 0, peck: rnd(.3, 1) };
  if (a.role === "dive") a.mode = null;
  return true;
}

function habDecorGo(a, dt, dv) {
  if (dv.stage === "leave") return habDecorLeave(a, dt);
  const { d, v } = dv, fly = HAB_FLIERS.has(a.role);
  const [gx, gy] = dv.path ? dv.path[dv.k] : [v.x, v.y];
  const [tx, ty] = habDecorAt(d, gx, gy);
  if (dv.stage === "go") {
    const dx = tx - a.x, dy = ty - a.y, dist = Math.hypot(dx, dy);
    const step = (fly ? Math.max(a.speed, 26) : Math.max(a.speed, 9) * (dv.path && dv.k ? 1.4 : 1)) * dt;
    if (dist <= step || dist > 900) {
      a.x = tx; a.y = ty;
      if (dv.path) {
        if (++dv.k >= dv.path.length) habDecorEnd(a);
        return true;
      }
      dv.stage = "stay";
      const [lo, hi] = HAB_STAY[v.act] || [5, 10];
      dv.left = rnd(lo, hi);
      a.rest = v.act === "sit" || v.act === "bask" || v.act === "shelter" ? pick("sit", "idle", "look") : v.act === "watch" ? "look" : "idle";
      if (["eat", "drink", "fish", "watch", "dig", "chase"].includes(v.act)) a.dir = Math.sign(d.x + d.ox - a.x) || a.dir;
      if (v.act === "bump") habDecorKick(d, a);
    } else {
      a.x += dx / dist * step; a.y += dy / dist * step; a.odo += step; a.pause = 0;
      if (Math.abs(dx) > .5) a.dir = Math.sign(dx);
    }
    return true;
  }
  // Staying: follow the spot if it moves, and do the thing.
  a.pause = 1;
  if (v.act === "hover") { a.x = tx + Math.sin(a.phase * 1.3) * 5; a.y = ty + Math.sin(a.phase * 2.1) * 2; }
  else if (v.act === "escort") { a.x = tx - 12 + Math.sin(a.phase) * 4; a.y = ty + Math.sin(a.phase * 1.7) * 3; a.dir = 1; }
  else if (v.act === "chase") { a.x = tx + Math.sin(a.phase * .8) * 14; a.y = ty; a.dir = Math.cos(a.phase * .8) > 0 ? -1 : 1; a.pause = 0; a.odo += dt * 8; }
  else { a.x = tx; a.y = ty; }
  if (["eat", "drink", "fish", "dig"].includes(v.act) && (dv.peck -= dt) <= 0) {
    dv.peck = rnd(.7, 1.8); a.peck = .35;
    if (v.act === "fish" || v.act === "drink") habRipple(a.x + a.dir * 12, a.y - 1);
  }
  if (a.peck > 0) a.peck -= dt;
  if (v.act === "bathe" && Math.random() < dt * 3) {
    for (let i = 0; i < 3; i++) hab.fx.push({ kind: "drop", x: a.x + rnd(-5, 5), y: a.y - 4, vx: rnd(-25, 25), vy: rnd(-50, -25), life: .5 });
  }
  if (HAB_LANDS.has(v.act) && fly && (a.look -= dt) <= 0) { a.look = rnd(1.5, 3.5); a.dir = -a.dir; }
  if ((dv.left -= dt) <= 0) habDecorEnd(a);
  return true;
}

// A walker bumps the beach ball or the soccer ball, which rolls away from it.
function habDecorKick(d, a) {
  const dir = a.dir || (a.x < d.x + d.ox ? 1 : -1);
  if (d.it.fx === "ball") d.st.vx = (a.x < d.x + d.ox ? 1 : -1) * rnd(30, 55);
  else if (d.it.fx === "soccer") d.st.vx = -rnd(20, 36);
  a.dir = dir;
}

function habDecorEnd(a) {
  const dv = a.dv;
  if (dv && dv.d.busy[dv.i] === a) delete dv.d.busy[dv.i];
  a.peck = 0;
  // Hawks and diving birds fly back up to where they were before handing back.
  if (dv && dv.stage !== "leave" && (a.role === "soar" || a.role === "dive")) {
    if (a.role === "soar") [a.cx, a.cy] = habSpot(a);
    else a.cy = habSpot(a)[1];
    a.dv = { d: dv.d, i: -1, v: dv.v, stage: "leave" };
    return;
  }
  a.dv = null;
  a.dvIn = rnd(10, 26);
  if (a.role === "dive") { a.mode = "fly"; a.vx = a.dir || 1; a.diveIn = rnd(3, 8); }
  else if (a.role === "fly" || a.role === "skim") a.vx = a.dir || pick(-1, 1);
  else if (a.role !== "soar") { [a.tx, a.ty] = habSpot(a); a.pause = rnd(0, 1.5); }
}

// Flying back up after a visit: a hawk to its circle, a diving bird to its height.
function habDecorLeave(a, dt) {
  const [tx, ty] = a.role === "soar" ? [a.cx + Math.cos(a.phase * .35) * a.r * 1.6, a.cy + Math.sin(a.phase * .35) * a.r * .5]
    : [a.x + (a.dir || 1) * 40, a.cy];
  const dx = tx - a.x, dy = ty - a.y, dist = Math.hypot(dx, dy), step = Math.max(a.speed, 30) * dt;
  if (dist <= step * 1.5) { [a.x, a.y] = [tx, ty]; habDecorEnd(a); return true; }
  a.x += dx / dist * step; a.y += dy / dist * step;
  if (Math.abs(dx) > .5) a.dir = Math.sign(dx);
  return true;
}

// Sleeping: an animal with a home among the decorations sleeps inside it (hidden), and a
// bed (the leaf pile) gets a sleeper on top. Returns the spot as habRestSpot does.
function habDecorRest(a, awake) {
  if (awake || !habMine() || !hab.decor.length) { a.home = null; return null; }
  let h = a.home;
  if (!h || !hab.decor.includes(h.d) || h.d.gone) {
    h = null;
    for (const d of hab.decor) {
      (d.it.visits || []).forEach((v, i) => {
        if (h || v.act !== "home" && v.act !== "sleep" || !habIs(a, v.who)) return;
        const who = d.homes && d.homes[i];
        if (who && who !== a && who.home && who.home.d === d && hab.animals.includes(who)) return;
        (d.homes = d.homes || {})[i] = a;
        h = { d, v };
      });
    }
    a.home = h || false;
  }
  if (!h) return null;
  const [x, y] = habDecorAt(h.d, h.v.x, h.v.y);
  return [x, y, 1, 1];
}

// Inside a decoration right now: hiding, running through the tunnel, asleep at home.
function habDecorHidden(a, awake) {
  if (!awake) return !!(a.home && a.home.v.act === "home");
  const dv = a.dv;
  if (!dv) return false;
  if (dv.path) return dv.v.act === "through" && dv.k >= 2 && dv.k < dv.path.length;
  if (dv.stage !== "stay") return false;
  if (dv.v.act === "hide") return dv.left > 1.5;      // peeks out before it leaves
  if (dv.v.act === "home") return dv.left < 5;         // stops at the door, then goes in
  return false;
}

// Landed on a decoration (sits still, drawn with it instead of in the sky).
const habDecorLanded = (a) => !!(a.dv && a.dv.stage === "stay" && HAB_LANDS.has(a.dv.v.act) && HAB_FLIERS.has(a.role));

function habDecorPose(a, awake) {
  if (!awake || !a.dv) return null;
  if (habDecorLanded(a)) return [a.x, a.y, .8, .8, 0];
  if (a.dv.stage === "stay" && a.dv.v.act === "ride") return [a.x, a.y, 1, 1, 0];
  return null;
}

function habDecorAnim(a, awake) {
  if (!awake || !a.dv) return null;
  if (habDecorLanded(a)) return ["idle", 0];
  return null;
}

// Depth to sort a visitor by: just in front of the decoration it's on.
function habDecorZ(a, y) {
  const dv = a.dv;
  if (!dv || dv.stage !== "stay" && !dv.path) return y;
  if (dv.path && dv.v.act !== "cross" && dv.v.act !== "slide") return y;
  return dv.d.y + dv.d.oy + .5;
}

// ---- Drawing -------------------------------------------------------------------------------
function habDecorSprite(c, d, phase) {
  if (d.gone) return;
  const img = habDecorImg(d.key);
  if (!img.complete || !img.naturalWidth) return;
  const t = habTinted(img, `decor/${d.key}`, phase), F = img.naturalHeight;
  c.save();
  c.translate(Math.round(d.x + d.ox), Math.round(d.y + d.oy));
  if (d.flip) c.scale(-1, 1);
  c.drawImage(t, Math.min(d.frame, (d.it.frames || 1) - 1) * F, 0, F, F, -F / 2, -F, F, F);
  c.restore();
  if (d.it.fx === "soccer") {  // the ball
    const [bx, by] = habDecorAt(d, 16 + d.st.bx, 31);
    c.fillStyle = "#26222a"; c.fillRect(Math.round(bx) - 2, by - 4, 5, 4);
    c.fillStyle = phase === "night" ? "#9aa0b8" : "#f6f4ee"; c.fillRect(Math.round(bx) - 1, by - 4, 3, 3);
    c.fillStyle = "#26222a"; c.fillRect(Math.round(bx), by - 3, 1, 1);
  }
}

// The ones on the sea, before anything stands on them.
function habDecorDrawArea(c, phase, area) {
  for (const d of hab.decor) if (d.it.area === area) habDecorSprite(c, d, phase);
}

// The meadow, pond and beach decorations as entries to sort in with the animals.
function habDecorDepth() {
  return hab.decor.filter((d) => ["ground", "pond", "sand"].includes(d.it.area)).map((d) => ({ decor: d, z: d.y + d.oy }));
}

// Night lights per effect: [gx, gy, radius, "r,g,b"].
const HAB_GLOWS = {
  lanternglow: [[16, 2, 10, "255,220,120"]], porchlight: [[16, 0, 10, "255,220,120"]], moonglow: [[13, 3, 11, "255,244,190"]],
  lights: [[6, 4, 4, "255,226,122"], [11, 6, 4, "238,126,160"], [16, 7, 4, "158,232,160"], [21, 6, 4, "168,216,255"], [26, 4, 4, "255,226,122"]],
  lanterns: [[8, 5, 7, "255,150,90"], [16, 7, 7, "255,190,90"], [24, 5, 7, "255,150,90"]],
  pathlights: [[5, 20, 7, "255,230,150"], [16, 20, 7, "255,230,150"], [27, 20, 7, "255,230,150"]],
  glowshrooms: [[6, 27, 7, "120,240,255"], [12, 27, 5, "120,240,255"], [19, 26, 8, "120,240,255"], [25, 28, 4, "120,240,255"]],
  tentglow: [[16, 25, 11, "255,190,100"]], windows: [[8, 19, 7, "255,220,120"]], buoy: [[16, 7, 5, "255,90,70"]],
};

// A round pool of light, one pixel row at a time.
function habGlowDisc(c, x, y, r, col) {
  c.fillStyle = col;
  x = Math.round(x); y = Math.round(y);
  for (let dy = -Math.round(r); dy <= Math.round(r); dy++) {
    const w = Math.round(Math.sqrt(Math.max(0, r * r - dy * dy)));
    if (w) c.fillRect(x - w, y + dy, w * 2, 1);
  }
}

function habDecorFx(c, phase) {
  if (!hab.decor.length && !hab.dfx.length) return;
  const dark = phase === "night" ? 1 : phase === "dusk" || phase === "dawn" ? .6 : 0;
  for (const d of hab.decor) {
    if (d.gone) continue;
    const glows = HAB_GLOWS[d.key === "buoy" ? "buoy" : d.it.fx];
    if (glows && dark) {
      if (d.key === "buoy" && Math.sin(d.t * 3) < .4) continue;  // blinks
      glows.forEach(([gx, gy, r, rgb], i) => {
        const [x, y] = habDecorAt(d, gx, gy);
        const tw = d.it.fx === "lights" ? .75 + Math.sin(d.t * 2.2 + i * 1.7) * .25 : 1;
        habGlowDisc(c, x, y, r, `rgba(${rgb},${(.13 * dark * tw).toFixed(3)})`);
        habGlowDisc(c, x, y, r * .55, `rgba(${rgb},${(.2 * dark * tw).toFixed(3)})`);
        c.fillStyle = `rgba(${rgb},${(.9 * tw).toFixed(2)})`;
        c.fillRect(Math.round(x) - 1, Math.round(y) - 1, 2, 2);
      });
    }
    if (d.it.fx === "kite" && d.kite) {
      const [sx, sy] = habDecorAt(d, 16, 24), [kx, ky] = d.kite;
      c.strokeStyle = "rgba(250,250,240,.7)"; c.lineWidth = 1;
      c.beginPath(); c.moveTo(sx + .5, sy + .5); c.quadraticCurveTo(kx - 20, (sy + ky) / 2 + 10, kx + .5, ky + 6.5); c.stroke();
      const px = (x, y, w, h, col) => { c.fillStyle = col; c.fillRect(Math.round(kx + x), Math.round(ky + y), w, h); };
      for (let i = 0; i < 5; i++) px(-i, 1 - i, 1 + i * 2, 1, "#e85a4a");
      for (let i = 0; i < 6; i++) px(-5 + i, -4 + i + 1, 11 - i * 2, 1, "#4f8fdc");
      px(0, -4, 1, 11, "#f6f0e0");
      for (let i = 0; i < 4; i++) px(Math.round(Math.sin(d.t * 3 + i) * 1.5), 7 + i * 3, 2, 2, ["#f2c14e", "#e85a4a"][i % 2]);
    }
    if (d.it.fx === "camera" && d.st.lens) {
      const [lx, ly] = d.st.lens;
      if (d.st.flash) { c.fillStyle = "rgba(255,255,240,.7)"; c.fillRect(lx - 4, ly - 4, 9, 9); c.fillStyle = "rgba(255,255,240,.25)"; c.fillRect(lx - 10, ly - 9, 30, 18); }
      if (d.st.say) {
        const msg = "Caught on camera!";
        c.font = "bold 7px monospace";
        const w = Math.ceil(c.measureText(msg).width) + 6, bx = Math.round(Math.min(Math.max(lx - w / 2, 2), hab.L.w - w - 2)), by = ly - 26;
        c.fillStyle = "rgba(255,255,255,.92)"; c.fillRect(bx, by, w, 11);
        c.fillStyle = "#2f3a2f"; c.fillText(msg, bx + 3, by + 8);
      }
    }
  }
  for (const p of hab.dfx) {
    const a = Math.min(1, p.life * 2);
    c.globalAlpha = a;
    c.fillStyle = p.col;
    const x = Math.round(p.x), y = Math.round(p.y);
    if (p.bubble) {
      const r = p.bubble;
      c.fillStyle = "rgba(255,255,255,.75)";
      c.fillRect(x - r, y - r - 1, r * 2 + 1, 1); c.fillRect(x - r, y + r + 1, r * 2 + 1, 1);
      c.fillRect(x - r - 1, y - r, 1, r * 2 + 1); c.fillRect(x + r + 1, y - r, 1, r * 2 + 1);
      c.fillStyle = "rgba(200,230,255,.35)"; c.fillRect(x - r, y - r, r * 2 + 1, r * 2 + 1);
      c.fillStyle = "#ffffff"; c.fillRect(x - r + 1, y - r + 1, 1, 1);
    } else if (p.star) {
      c.fillRect(x, y - 2, 1, 5); c.fillRect(x - 2, y, 5, 1);
    } else c.fillRect(x, y, p.col === "#f2c14e" ? 2 : 1, 1 + (p.vy > 20 ? 1 : 0));
  }
  c.globalAlpha = 1;
}
