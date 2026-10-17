// The live habitat scene, shared by the website (static/index.html) and the
// Android app (android/app/src/main/assets/habitat.html shows it in a WebView).
// The page defines $, myState, spriteUrl, openDex, caughtNums and dexNumbers,
// has the #habitat, #hab-canvas, #hab-bubble, #hab-note and #hab-peek elements,
// and calls habInit() once they exist. Sprites load from /sprites/.
// Habitat: the animals you've captured, living in one small pixel scene at the top
// of the Field Guide. Each one gets a way of moving from what it is (walkers,
// hoppers, fliers, swimmers, tide pool animals...) and is awake by day, by night
// or both (`activity` from /me/collection). The scene follows the phone's clock,
// and a button peeks at the other half of the day. Tap an animal for its name,
// tap again for its Field Guide page.
const HAB_H = 270;
// While you look at a friend's profile, the scene moves into it and shows their
// animals in their state's scenery (`visit`); closing the profile brings yours back.
const hab = { w: 0, L: null, animals: [], peek: false, picked: null, pickedUntil: 0, last: 0, bg: null, bgKey: "", t: 0,
              fx: [], visit: null };
const habState = () => (hab.visit ? hab.visit.state : myState.code);
const habImgs = {};
// Animation sheets (species/sprites/anim): a row of four frames for each pose, and
// an index of the poses each species really draws. Without them the scene falls
// back to the single sprite, squashed and bobbed.
const habSheets = {};
let habAnimIdx = null;
fetch("/sprites/anim/index.json").then((r) => (r.ok ? r.json() : null)).then((j) => { habAnimIdx = j; }).catch(() => {});
const habStill = matchMedia("(prefers-reduced-motion: reduce)").matches;
const HAB_ROLES = [
  [/pelican|royal_tern|kingfisher|osprey/, "dive"],
  [/black_skimmer/, "skim"],
  [/sea_otter|by_the_wind/, "float"],
  [/jellyfish/, "jelly"],
  [/dolphin|whale|garibaldi|red_drum|sculpin|sea_hare|loggerhead/, "swim"],
  [/seal|sea_lion|crab/, "beach"],
  [/star|anemone|mussel|barnacle|limpet|urchin|turban_snail|hopkins|scotch_bonnet/, "reef"],
  [/mallard|wood_duck|goose|swan|trout|hellbender|beaver|river_otter|alligator/, "paddle"],
  [/pond_slider|pond_turtle|snapping|terrapin|newt|salamander|ensatina/, "shore"],
  [/heron|egret|ibis|oystercatcher/, "wade"],
  [/hawk|eagle|vulture|condor|osprey|kestrel/, "soar"],
  [/hummingbird/, "hover"],
  [/quail|turkey|roadrunner/, "walk"],
  [/firefly|swallowtail|monarch|painted_lady|mourning_cloak|fritillary|luna_moth|flame_skimmer|honey_bee/, "flutter"],
  [/spider|widow/, "dangle"],
  [/frog|toad|peeper|grasshopper/, "hop"],
];
const HAB_DEFAULT_ROLE = { bird: "fly", amphibian: "shore", marine: "swim", fish: "paddle" };
const HAB_FLIERS = new Set(["fly", "soar", "hover", "flutter", "dive", "skim"]);
// Big birds glide between bursts of slow wingbeats.
const HAB_GLIDERS = /pelican|gull|heron|egret|goose|swan|vulture|condor|eagle|osprey|hawk|ibis|(^|_)tern|skimmer/;
// Sea birds rest and sleep on the sea stack (or the lighthouse) instead of the tree.
const HAB_SEABIRDS = /gull|pelican|royal_tern|oystercatcher|black_skimmer|osprey|cormorant/;
// Ground animals that look around while they stand still.
const HAB_LOOKERS = new Set(["walk", "hop", "shore", "wade", "beach"]);
const HAB_SEA = new Set(["swim", "jelly", "reef"]);

function habRole(s) {
  const hit = HAB_ROLES.find(([re]) => re.test(s.slug));
  return hit ? hit[1] : HAB_DEFAULT_ROLE[s.category] || "walk";
}

function habSpeed(a) {
  const slug = a.s.slug;
  if (/roadrunner/.test(slug)) return 45;
  if (/squirrel|chipmunk|lizard|skink|anole/.test(slug)) return 28;
  if (/tortoise|box_turtle|slug|snail/.test(slug)) return 3;
  return { fly: 34, dive: 32, skim: 42, hover: 70, flutter: 16, hop: 22, beach: 10, swim: 12, jelly: 4, float: 4, paddle: 6,
           wade: 5, shore: 5 }[a.role] || { mammal: 16, reptile: 8, invertebrate: 5, bird: 12 }[a.s.category] || 10;
}

// Where the scene's parts sit for a canvas this wide (320 on phones, 480 wider).
function habLayout(w) {
  const L = { w, land: Math.round(w * .64), sea: Math.round(w * .73), water: 168, tree: Math.round(w * .1),
              pond: { x: Math.round(w * .36), y: 229, rx: Math.round(w * .11), ry: 12 }, shore: [], surf: [] };
  // On each row: where the meadow gives way to sand, and the sand to the sea.
  for (let y = 0; y < HAB_H; y++) {
    const k = Math.max(0, y - L.water);
    L.shore[y] = Math.round(L.land + 2 + k * .1 + Math.sin(y * .13) * 3 + Math.sin(y * .41) * 1.2);
    L.surf[y] = Math.round(L.sea + k * .08 + Math.sin(y * .09 + 1) * 3);
  }
  return L;
}

const rnd = (lo, hi) => lo + Math.random() * (hi - lo);
const pick = (...xs) => xs[Math.floor(Math.random() * xs.length)];

// A fresh spot inside the animal's part of the scene: [x, feet y].
function habSpot(a) {
  const L = hab.L, p = L.pond;
  switch (a.role) {
    case "walk": return [rnd(14, L.land - 10), pick(rnd(182, 200), rnd(250, 266))];
    case "hop": case "shore": return [rnd(p.x - p.rx - 34, p.x + p.rx + 34), pick(rnd(204, 212), rnd(248, 258))];
    case "wade": return [rnd(p.x - p.rx + 8, p.x + p.rx - 8), p.y + 3];
    case "paddle": return [rnd(p.x - p.rx + 14, p.x + p.rx - 14), p.y + 7];
    case "beach": return [rnd(L.land + 6, L.sea + 4), rnd(196, 264)];
    case "swim": case "jelly": return [rnd(L.sea + 20, L.w - 18), rnd(L.water + 44, HAB_H - 14)];
    case "float": return [rnd(L.sea + 18, L.w - 16), L.water + 9];
    case "reef": return [rnd(L.sea + 14, L.w - 14), HAB_H - 2 - rnd(0, 8)];
    case "hover": return [rnd(20, L.land - 20), rnd(146, 196)];
    case "flutter": return [rnd(10, L.land), rnd(122, 200)];
    case "dangle": return [L.tree + rnd(14, 26), rnd(146, 170)];
    case "soar": return [rnd(70, L.w - 70), rnd(60, 90)];
    case "dive": return [rnd(-20, L.w + 20), /kingfisher/.test(a.s.slug) ? rnd(96, 116) : rnd(44, 100)];
    case "skim": return [rnd(L.sea, L.w), L.water + 1];
    default: return [rnd(-20, L.w + 20), rnd(42, 128)];  // fly
  }
}

function habSpawn(a) {
  [a.x, a.y] = habSpot(a);
  [a.tx, a.ty] = habSpot(a);
  a.pause = rnd(0, 3);
  a.dir = Math.random() < .5 ? -1 : 1;
  a.odo = 0;
  a.phase = rnd(0, 6.3);
  a.look = rnd(1, 4);
  a.tilt = 0;
  if (a.role === "fly" || a.role === "dive" || a.role === "skim") a.vx = pick(-1, 1) * rnd(.8, 1.2);
  if (a.role === "dive") { a.cy = a.y; a.mode = "fly"; a.diveIn = rnd(2, 6); }
  if (/dolphin|whale/.test(a.s.slug)) a.leapIn = rnd(2, 6);
  if (a.role === "soar") { a.cx = a.x; a.cy = a.y; a.r = rnd(26, 46); }
}

// Called with the captured entries whenever the collection loads. Animals already
// in the scene stay where they are.
function habitatSet(entries) {
  const box = $("habitat");
  const w = box.clientWidth && box.clientWidth < 520 ? 320 : 480;
  const relayout = w !== hab.w;
  if (relayout) { hab.w = w; hab.L = habLayout(w); hab.bgKey = ""; }
  const old = new Map(hab.animals.map((a) => [a.s.slug, a]));
  hab.animals = entries.filter((e) => e.caught && e.species.slug).map((e) => {
    const prev = old.get(e.species.slug);
    if (prev && !relayout) { prev.s = e.species; prev.activity = e.activity || "day"; return prev; }
    const a = { s: e.species, activity: e.activity || "day", role: habRole(e.species), num: e.num };
    a.speed = habSpeed(a);
    habSpawn(a);
    if (!habImgs[a.s.slug]) { habImgs[a.s.slug] = new Image(); habImgs[a.s.slug].src = spriteUrl(a.s.slug, true); }
    if (!habSheets[a.s.slug]) { habSheets[a.s.slug] = new Image(); habSheets[a.s.slug].src = `/sprites/anim/${a.s.slug}.png`; }
    return a;
  });
  habNote();
  if (habStill) setTimeout(habDraw, 300);
}

function habRealPhase() {
  const h = new Date().getHours();
  return h >= 21 || h < 5 ? "night" : h < 7 ? "dawn" : h < 19 ? "day" : "dusk";
}
function habPhase() {
  const real = habRealPhase();
  if (!hab.peek) return real;
  return real === "day" ? "night" : "day";
}
const habAwake = (a, phase) => phase === "dawn" || phase === "dusk" || a.activity === "any"
  || a.activity === (phase === "night" ? "night" : "day");

function habNote() {
  const phase = habPhase(), n = hab.animals.length;
  const asleep = hab.animals.filter((a) => !habAwake(a, phase)).length;
  const who = hab.visit ? `${hab.visit.username}'s habitat` : "here";
  $("hab-note").textContent = !n ? (hab.visit ? `No animals in ${who} yet.` : "Capture animals and they'll move in here.")
    : `${n} animal${n > 1 ? "s" : ""} live${n > 1 ? "" : "s"} ${hab.visit ? "in " + who : "here"}` + (asleep ? `, ${asleep} asleep` : "")
      + ". Tap one to say hi.";
  const night = phase === "night";
  $("hab-peek").textContent = hab.peek ? "Back to now" : night || phase === "dusk" ? "☀️ Peek at daytime" : "🌙 Peek at night";
}

// Birds out on the landmark are far away, so they're drawn smaller.
const HAB_PERCH_SCALE = .72;
// Spots on the state's coastal landmark where sea birds stand: [x, feet y].
// California's sea stack: two on the flat top, one on the ledge, one on the
// small rock beside it. North Carolina's lighthouse: the gallery and the base.
function habPerches(L, state) {
  if (state === "CA") {
    const sx = L.w - Math.round(L.w * .1), top = L.water - 44;
    return [[sx - 7, top], [sx + 6, top], [sx + 17, top + 17], [sx - 27, L.water - 6]];
  }
  if (state === "NC") {
    const lx = L.sea - 12, topY = L.water - 58;
    return [[lx - 4, topY - 1], [lx + 5, topY - 1], [lx - 6, L.water], [lx + 6, L.water]];
  }
  return [];
}

// A free perch for this bird (keeping the one it has), or null.
function habPerchFor(a) {
  const spots = habPerches(hab.L, habState());
  hab.perched = hab.perched || {};
  for (const [i, who] of Object.entries(hab.perched)) if (!hab.animals.includes(who) || who.perch !== +i) delete hab.perched[i];
  if (a.perch !== undefined && hab.perched[a.perch] === a && spots[a.perch]) return a.perch;
  const free = spots.findIndex((_, i) => !hab.perched[i]);
  if (free < 0) return null;
  hab.perched[free] = a;
  return (a.perch = free);
}
function habLeavePerch(a) {
  if (a.perch !== undefined && hab.perched && hab.perched[a.perch] === a) delete hab.perched[a.perch];
  delete a.perch;
}

// Where a sleeping animal rests, or null if it sleeps where it is: sea birds on
// the coastal landmark while there's room, other fliers in the tree.
function habRestSpot(a, awake, counter) {
  if (awake) return null;
  if (HAB_SEABIRDS.test(a.s.slug)) {
    const i = habPerchFor(a);
    if (i !== null) return [...habPerches(hab.L, habState())[i], HAB_PERCH_SCALE, HAB_PERCH_SCALE];
  }
  return HAB_FLIERS.has(a.role) ? habRoost(counter.n++) : null;
}

// Sleeping fliers roost in the tree, then on the grass under it.
function habRoost(i) {
  const t = hab.L.tree;
  const spots = [[t - 16, 116], [t + 4, 106], [t + 20, 118], [t - 4, 128], [t + 12, 132]];
  return spots[i] || [t + 30 + (i - spots.length) * 18 % (hab.L.land - t - 40), 192 + (i % 2) * 8];
}

// Water a diving bird aims for: [left, right, surface y]. Kingfishers fish the pond.
function habPool(a) {
  const L = hab.L, p = L.pond;
  return /kingfisher/.test(a.s.slug) ? [p.x - p.rx + 10, p.x + p.rx - 10, p.y - 3] : [L.sea + 14, L.w - 14, L.water + 2];
}

// Splash: drops flung up plus a ring on the water.
function habSplash(x, y, n, big) {
  for (let i = 0; i < n; i++) {
    hab.fx.push({ kind: "drop", x: x + rnd(-3, 3), y, vx: rnd(-28, 28) * (big ? 1.6 : 1), vy: -rnd(30, 75) * (big ? 1.5 : 1),
                  life: rnd(.4, .8) });
  }
  hab.fx.push({ kind: "ring", x, y, r: 2, life: 1 });
}
const habRipple = (x, y) => hab.fx.push({ kind: "ring", x, y, r: 1, life: .9 });

// Plunge divers cruise across the sky, now and then fold their wings over the
// water, dive in with a splash and climb back out.
function habDive(a, dt) {
  const [lo, hi, surf] = habPool(a);
  a.tilt = 0;
  if (a.mode === "dive") {
    a.vy += 300 * dt; a.y += a.vy * dt; a.x += a.vx * a.speed * .3 * dt;
    a.tilt = Math.min(1.35, Math.atan2(a.vy, 20));
    if (a.y >= surf + 5) { habSplash(a.x, surf, 20, true); a.mode = "under"; a.t = rnd(.5, 1); }
  } else if (a.mode === "under") {
    a.t -= dt;
    if (a.t <= 0) { a.mode = "rise"; a.vy = -55; habSplash(a.x, surf, 6); }
  } else if (a.mode === "rise") {
    a.y += a.vy * dt; a.x += a.vx * a.speed * .5 * dt; a.tilt = -.4;
    if (a.y <= a.cy) { a.mode = "fly"; a.diveIn = rnd(4, 10); }
  } else {
    a.x += a.vx * a.speed * dt;
    a.y += (a.cy - a.y) * Math.min(1, dt * 2);
    // Patrol the coast (or the pond) so there's water below often.
    const L = hab.L, p = L.pond, [min, max] = /kingfisher/.test(a.s.slug)
      ? [p.x - p.rx - 60, p.x + p.rx + 60] : [L.w * .3, L.w + 30];
    if ((a.x < min && a.vx < 0) || (a.x > max && a.vx > 0)) { a.vx = -a.vx; a.cy = habSpot(a)[1]; }
    a.diveIn -= dt;
    if (a.diveIn <= 0 && a.x > lo && a.x < hi) { a.mode = "dive"; a.vy = 15; }
  }
  a.dir = Math.sign(a.vx);
}

// Dolphins leap in an arc; the whale breaches nearly straight up and falls back.
function habLeap(a, dt) {
  const L = hab.L, whale = /whale/.test(a.s.slug), surf = L.water + 4, y0 = a.y;
  a.lt += dt;
  const k = Math.min(1, a.lt / a.dur);
  a.y = a.ly - a.lh * 4 * k * (1 - k);
  a.x += a.lvx * dt;
  a.tilt = whale ? (k < .6 ? -1.2 + k * 1.5 : -.3 + (k - .6) * 3) : (2 * k - 1) * .9;
  if ((y0 > surf) !== (a.y > surf)) habSplash(a.x - a.dir * (whale ? 0 : 6), surf - 1, whale ? 26 : 10, whale);
  if (k >= 1) { a.mode = null; a.tilt = 0; a.leapIn = rnd(5, 12); a.pause = rnd(.5, 2); [a.tx, a.ty] = habSpot(a); }
}

// Awake sea birds: now and then fly to a free perch, rest there looking about,
// then take off again. Returns true while it's handling the bird.
function habPerchStep(a, dt) {
  // Woke up on the perch it slept on: stay a moment before flying off.
  if (a.perch !== undefined && a.mode !== "toPerch" && a.mode !== "perched") {
    const spot = habPerches(hab.L, habState())[a.perch];
    if (spot) { [a.x, a.y] = spot; a.mode = "perched"; a.rest = rnd(2, 6); a.look = rnd(1, 3); }
  }
  if (a.mode === "toPerch" || a.mode === "perched") {
    const spot = a.perch !== undefined && habPerches(hab.L, habState())[a.perch];
    if (!spot) { a.mode = a.role === "dive" ? "fly" : null; habLeavePerch(a); return false; }
    if (a.mode === "toPerch") {
      const dx = spot[0] - a.x, dy = spot[1] - a.y, d = Math.hypot(dx, dy), step = Math.max(a.speed, 26) * dt;
      a.tilt = 0;
      if (d <= step) { [a.x, a.y] = spot; a.mode = "perched"; a.rest = rnd(5, 11); a.look = rnd(1, 3); }
      else { a.x += dx / d * step; a.y += dy / d * step; a.dir = Math.sign(dx) || a.dir; }
      return true;
    }
    a.rest -= dt;
    if ((a.look -= dt) <= 0) { a.look = rnd(1.2, 3.5); a.dir = -a.dir; }
    if (a.rest <= 0) {  // take off
      habLeavePerch(a);
      a.mode = a.role === "dive" ? "fly" : null;
      a.vx = a.dir || pick(-1, 1);
      a.cy = a.role === "dive" ? habSpot(a)[1] : a.cy;
      a.perchIn = rnd(14, 30);
      if (a.role === "dive") a.diveIn = rnd(3, 8);
    }
    return a.mode === "perched";
  }
  if (a.mode === "dive" || a.mode === "under" || a.mode === "rise") return false;
  if (a.perchIn === undefined) a.perchIn = rnd(6, 20);
  if ((a.perchIn -= dt) <= 0) {
    a.perchIn = rnd(8, 16);
    if (habPerchFor(a) !== null) { a.mode = "toPerch"; return true; }
  }
  return false;
}

function habStep(a, dt, awake) {
  a.phase += dt;
  if (awake && HAB_SEABIRDS.test(a.s.slug) && HAB_FLIERS.has(a.role) && habPerchStep(a, dt)) return;
  if (!awake && (a.mode === "toPerch" || a.mode === "perched")) a.mode = a.role === "dive" ? "fly" : null;
  // Awake birds that don't fly to perches (oystercatchers wading) give theirs up.
  if (awake && a.perch !== undefined && !HAB_FLIERS.has(a.role)) habLeavePerch(a);
  if (!awake) {
    // Fell asleep mid-leap: settle back in the water.
    if (a.mode === "leap") { a.y = a.ly; a.mode = null; a.tilt = 0; a.leapIn = rnd(5, 12); }
    return;
  }
  if (a.role === "dive") return habDive(a, dt);
  if (a.role === "skim") {
    // Skimmers fly low over the sea, bill cutting the water.
    a.x += a.vx * a.speed * dt;
    a.dir = Math.sign(a.vx);
    if (a.x < hab.L.land || a.x > hab.L.w + 30) a.vx = -a.vx;
    if (a.x > hab.L.sea && Math.random() < dt * 14) {
      hab.fx.push({ kind: "dot", x: a.x - a.dir * 10, y: hab.L.water + 2, life: .9 });
    }
    return;
  }
  if (a.mode === "leap") return habLeap(a, dt);
  if (a.leapIn !== undefined && (a.leapIn -= dt) <= 0) {
    const whale = /whale/.test(a.s.slug), L = hab.L;
    // Leap toward the open water, away from the near edge.
    a.dir = a.x < (L.sea + L.w) / 2 ? 1 : -1;
    Object.assign(a, { mode: "leap", lt: 0, ly: a.y, dur: whale ? 2.2 : 1.4,
                       lh: a.y - L.water + (whale ? 16 : 26), lvx: a.dir * (whale ? 6 : 34) });
    return;
  }
  if (a.role === "paddle" && a.pause <= 0 && (a.rip = (a.rip || 0) - dt) <= 0) { a.rip = .9; habRipple(a.x, a.y - 8); }
  if (a.role === "float" && (a.rip = (a.rip || 0) - dt) <= 0) { a.rip = rnd(1.5, 3); habRipple(a.x, hab.L.water + 3); }
  if (a.peck > 0) a.peck -= dt;
  if (a.role === "fly") {
    a.x += a.vx * a.speed * dt;
    a.dir = Math.sign(a.vx);
    if (a.x < -30 || a.x > hab.L.w + 30) { a.vx = -a.vx; a.y = rnd(42, 128); }
    return;
  }
  if (a.role === "soar") {
    a.x = a.cx + Math.cos(a.phase * .35) * a.r * 1.6;
    a.y = a.cy + Math.sin(a.phase * .35) * a.r * .5;
    a.dir = Math.sin(a.phase * .35) > 0 ? -1 : 1;
    return;
  }
  if (a.role === "reef") return;
  if (a.pause > 0) {
    a.pause -= dt;
    // Standing still: glance the other way now and then; waders stab at fish.
    if (HAB_LOOKERS.has(a.role) && (a.look -= dt) <= 0) {
      a.look = rnd(1.2, 3.5);
      if (a.role === "wade" && Math.random() < .6) { a.peck = .35; habRipple(a.x + a.dir * 12, a.y - 1); }
      else a.dir = -a.dir;
    }
    return;
  }
  const dx = a.tx - a.x, dy = a.ty - a.y, d = Math.hypot(dx, dy);
  const step = a.speed * dt;
  if (d <= step) {
    a.x = a.tx; a.y = a.ty;
    a.pause = a.role === "hover" ? rnd(.4, 1.4) : rnd(1, 5);
    [a.tx, a.ty] = habSpot(a);
    return;
  }
  a.x += dx / d * step; a.y += dy / d * step; a.odo += step;
  if (Math.abs(dx) > .5 && a.role !== "beach") a.dir = Math.sign(dx);
}

// Wingbeat 0..1 (1 = wings down, sprite squashed). Big birds flap in bursts
// and glide in between; small ones flap all the time.
function habFlap(a, rate) {
  if (HAB_GLIDERS.test(a.s.slug) && Math.sin(a.phase * .7 + a.x * .01) < .1) return 0;
  return (Math.sin(a.phase * rate) + 1) / 2;
}

// Drawn pose: [x, feet y, x scale, y scale, nose-down tilt] with the bounce,
// bob, wingbeat or squash that goes with how it moves.
function habPose(a, awake, roost) {
  if (roost) return roost;
  if (awake && a.mode === "perched") return [a.x, a.y, HAB_PERCH_SCALE, HAB_PERCH_SCALE, 0];
  let { x, y } = a, sx = 1, sy = 1;
  const tilt = a.tilt || 0;
  if (!awake) return [x, y, 1, 1 + Math.sin(a.phase * 1.3) * .03, 0];
  const moving = a.pause <= 0;
  switch (a.role) {
    case "hop": {
      if (!moving) { sy = 1 + Math.sin(a.phase * 2.2) * .03; break; }
      const h = Math.abs(Math.sin(a.odo / 18 * Math.PI));
      y -= h * 9;
      // Stretched in the air, squashed on landing and takeoff.
      if (h < .2) { sy = .86; sx = 1.1; } else { sy = 1 + h * .12; sx = 1 - h * .07; }
      break;
    }
    case "walk": case "shore": case "wade": case "beach":
      if (moving) { y -= Math.floor(a.odo / 3) % 2; sy = 1 - Math.abs(Math.sin(a.odo * Math.PI / 6)) * .06; sx = 2 - sy; }
      else sy = 1 + Math.sin(a.phase * 2.2) * .025;
      if (a.peck > 0) return [x, y, 1, 1, .55];
      break;
    case "fly": y += Math.sin(a.phase * 3) * 2; sy = 1 - habFlap(a, HAB_GLIDERS.test(a.s.slug) ? 7 : 13) * .3; break;
    case "soar": y += Math.sin(a.phase * 3) * 2; sy = Math.sin(a.phase * .45) > .75 ? 1 - habFlap(a, 6) * .3 : 1; break;
    case "dive":
      if (a.mode === "dive") sx = .85;
      else if (a.mode === "rise") sy = 1 - (Math.sin(a.phase * 16) + 1) / 2 * .32;
      else { y += Math.sin(a.phase * 3) * 2; sy = 1 - habFlap(a, 7) * .3; }
      break;
    case "skim": y += Math.sin(a.phase * 2) * .6; sy = 1 - (Math.sin(a.phase * 9) + 1) / 2 * .12; break;
    case "hover": sy = 1 - Math.abs(Math.sin(a.phase * 40)) * .2; y += Math.sin(a.phase * 5) * 1.5; break;
    case "flutter": y += Math.sin(a.phase * 9) * 3; x += Math.sin(a.phase * 2.3) * 2;
      sy = .55 + Math.abs(Math.cos(a.phase * 11)) * .45; break;
    case "swim":
      if (a.mode !== "leap") { y += Math.sin(a.phase * 1.5) * 1.5; sx = 1 + Math.sin(a.phase * 4) * .04; }
      break;
    case "float": case "paddle": y += Math.sin(a.phase * 1.5) * 1.5; break;
    case "jelly": y += Math.sin(a.phase * .8) * 6; sy = 1 + Math.sin(a.phase * .8 + 1.6) * .12; sx = 2 - sy; break;
  }
  return [x, y, sx, sy, tilt];
}

// Which pose of the animation sheet to show, and which of its four frames:
// [pose, frame], or null when the species has no sheet.
function habAnim(a, awake, roost) {
  const acts = habAnimIdx && habAnimIdx.acts[a.s.slug];
  if (!acts) return null;
  const has = (k) => acts.includes(k);
  const cyc = (t) => ((Math.floor(t) % 4) + 4) % 4;
  if (!awake || roost) return ["sleep", cyc(a.phase * 1.2)];
  if (a.mode === "perched") return ["idle", 0];
  if (a.mode === "toPerch") return has("fly") ? ["fly", cyc(a.phase * 9 / (2 * Math.PI) * 4)] : ["idle", 0];
  switch (a.role) {
    case "walk": case "shore": case "wade": case "beach":
      return a.pause > 0 || a.peck > 0 || !has("walk") ? ["idle", 0] : ["walk", cyc(a.odo / 3)];
    case "hop":
      return a.pause > 0 || !has("walk") ? ["idle", 0] : ["walk", cyc((a.odo % 18) / 18 * 4)];
    case "fly": case "soar": case "dive": case "skim": case "hover": case "flutter": {
      if (!has("fly")) return ["idle", 0];
      if (a.role === "dive" && a.mode === "dive") return ["fly", 3];
      const glider = HAB_GLIDERS.test(a.s.slug);
      if (glider && Math.sin(a.phase * .7 + a.x * .01) < .1) return ["fly", 0];  // gliding, wings level
      const rate = { hover: 24, flutter: 10, skim: 5 }[a.role] || (glider ? 6 : 12);
      return ["fly", cyc(a.phase * rate / (2 * Math.PI) * 4)];
    }
    case "swim": case "paddle": case "float": case "jelly":
      return has("swim") ? ["swim", cyc(a.phase * 2.5)] : ["idle", 0];
  }
  return ["idle", 0];
}

function habDraw() {
  const cv = $("hab-canvas");
  if (!hab.L || !cv) return;
  const L = hab.L, phase = habPhase(), key = `${L.w}/${phase}/${habState()}`;
  if (cv.width !== L.w) { cv.width = L.w; cv.height = HAB_H; }
  if (hab.bgKey !== key) { hab.bg = habBackground(L, phase, habState()); hab.bgKey = key; }
  const c = cv.getContext("2d");
  c.imageSmoothingEnabled = false;
  c.drawImage(hab.bg, 0, 0);
  habAmbient(c, L, phase);
  const roosting = { n: 0 };
  const poses = hab.animals.map((a) => {
    const awake = habAwake(a, phase);
    const roost = habRestSpot(a, awake, roosting);
    let [x, y, sx = 1, sy = 1, tilt = 0] = habPose(a, awake, roost);
    const anim = habAnim(a, awake, roost);
    // The frames already beat the wings, step the legs and breathe, so drop the
    // squash that stood in for them (hops and jellies keep theirs).
    if (anim && anim[0] !== "idle" && a.role !== "hop" && a.role !== "jelly" && a.mode !== "rise" && !(roost && roost[2])) sx = sy = 1;
    const perched = awake && a.mode === "perched";
    return { a, awake, phase, anim, roost: !!roost || perched, x: Math.round(x), y: Math.round(y), sx, sy, tilt,
             sky: awake && HAB_FLIERS.has(a.role) && !perched, hidden: awake && a.mode === "under" };
  });
  const sea = poses.filter((p) => HAB_SEA.has(p.a.role) && !p.sky).sort((p, q) => p.y - q.y);
  const land = poses.filter((p) => !HAB_SEA.has(p.a.role) && !p.sky).sort((p, q) => p.y - q.y);
  const sky = poses.filter((p) => p.sky);
  sea.forEach((p) => habSprite(c, p));
  // Seawater over everything in the sea.
  c.fillStyle = { day: "rgba(40,140,210,.31)", dawn: "rgba(80,100,180,.31)", dusk: "rgba(80,80,160,.31)",
                  night: "rgba(20,40,100,.35)" }[phase];
  c.fillRect(L.sea, L.water + 3, L.w - L.sea, HAB_H);
  land.forEach((p) => habSprite(c, p));
  sky.forEach((p) => habSprite(c, p));
  habFx(c, phase);
  for (const p of poses) {
    if (/firefly/.test(p.a.s.slug) && p.awake && phase !== "day") {
      const on = Math.sin(p.a.phase * 4) > -.2;
      if (on) { c.fillStyle = "rgba(255,240,120,.35)"; c.fillRect(p.x - 6, p.y - 14, 12, 10);
                c.fillStyle = "#fff6a0"; c.fillRect(p.x - 2, p.y - 11, 4, 4); }
    }
    if (p.a.s.rarity === "legendary" && Math.sin(p.a.phase * 3) > .3) {
      c.fillStyle = "#ffe27a";
      const sx = p.x + (p.a.phase * 7 % 24) - 12, sy = p.y - 34;
      c.fillRect(sx, sy - 1, 1, 3); c.fillRect(sx - 1, sy, 3, 1);
    }
    if (!p.awake) {
      c.fillStyle = phase === "night" ? "#dfe8ff" : "#33405a";
      c.font = "bold 8px monospace";
      const k = (p.a.phase * .7) % 1;
      c.globalAlpha = 1 - k;
      c.fillText("z", p.x + 8 + k * 4, p.y - 28 - k * 10);
      c.globalAlpha = 1;
    }
  }
  habBubble(poses);
}

// Animals standing on the ground get a soft shadow under their feet.
const HAB_NO_SHADOW = new Set(["swim", "jelly", "reef", "float", "paddle", "wade", "dangle"]);

function habSprite(c, p) {
  const raw = habImgs[p.a.s.slug];
  if (!raw || !raw.complete || !raw.naturalWidth) return;
  const { a, x, y } = p, sheet = habSheets[a.s.slug];
  const framed = p.anim && sheet && sheet.complete && sheet.naturalWidth;
  const img = framed ? habTinted(sheet, `${a.s.slug}@anim`, p.phase) : habTinted(raw, a.s.slug, p.phase);
  // Frame size from the image (40 px: a 32 px drawing with room for wings, tails
  // and antlers), feet on its bottom row.
  const F = framed ? sheet.naturalWidth / habAnimIdx.frames : raw.naturalWidth;
  p.box = [x - F / 2, y - F, x + F / 2, y];
  if (p.hidden) return;
  if (!p.sky && !p.roost && !HAB_NO_SHADOW.has(a.role)) {
    const gy = a.role === "hop" && p.awake ? Math.round(a.y) : y;
    c.fillStyle = "rgba(20,32,10,.25)";
    c.fillRect(x - 7, gy - 1, 14, 1); c.fillRect(x - 9, gy, 18, 1); c.fillRect(x - 6, gy + 1, 12, 1);
  }
  if (a.role === "wade" && p.awake) {
    c.fillStyle = "rgba(225,245,255,.6)";
    c.fillRect(x - 10, y - 1, 5, 1); c.fillRect(x + 5, y - 1, 5, 1);
  }
  c.save();
  if (a.role === "paddle") { c.beginPath(); c.rect(0, 0, hab.L.w, y - 8); c.clip(); }
  // A diving bird disappears into the water as it goes in.
  if (a.role === "dive" && p.awake && a.mode === "dive") { c.beginPath(); c.rect(0, 0, hab.L.w, habPool(a)[2] + 1); c.clip(); }
  if (a.role === "dangle") {
    c.fillStyle = "rgba(255,255,255,.7)";
    c.fillRect(x, 104, 1, y - 104 - 26);
  }
  if (!p.awake && !framed) c.globalAlpha = .85;
  // Fliers and swimmers turn and squash around their middle, the rest around
  // their feet. Sprites face left; mirror the ones heading right.
  const mid = p.sky || a.role === "swim" || a.role === "jelly" ? 16 : 0;
  c.translate(x, y - mid);
  if (a.dir > 0 && a.role !== "reef") c.scale(-1, 1);
  if (p.tilt) c.rotate(-p.tilt);
  if (p.sx !== 1 || p.sy !== 1) c.scale(p.sx, p.sy);
  if (framed) c.drawImage(img, p.anim[1] * F, habAnimIdx.rows.indexOf(p.anim[0]) * F, F, F, -F / 2, mid - F, F, F);
  else c.drawImage(img, -F / 2, mid - F);
  c.restore();
  if (a.role === "paddle") {
    c.fillStyle = "rgba(255,255,255,.55)";
    c.fillRect(x - 12, y - 8, 4, 1); c.fillRect(x + 6, y - 8, 5, 1);
  }
}

// Splash drops, ripple rings and skimmer wakes.
function habFx(c, phase) {
  const light = phase === "night" ? "rgba(200,220,255," : "rgba(240,250,255,";
  for (const f of hab.fx) {
    const a = Math.max(0, Math.min(1, f.life * 1.4));
    if (f.kind === "drop") {
      c.fillStyle = light + a + ")"; c.fillRect(Math.round(f.x), Math.round(f.y), 2, 2);
    } else if (f.kind === "dot") {
      c.fillStyle = light + a * .8 + ")"; c.fillRect(Math.round(f.x) - 1, Math.round(f.y), 3, 1);
    } else {
      c.fillStyle = light + a * .8 + ")";
      const r = Math.round(f.r);
      for (let i = 0; i < 16; i++) {
        const t = i / 16 * Math.PI * 2;
        c.fillRect(Math.round(f.x + Math.cos(t) * r * 1.6), Math.round(f.y + Math.sin(t) * r * .45), 1, 1);
      }
    }
  }
}

function habFxStep(dt) {
  for (const f of hab.fx) {
    f.life -= dt;
    if (f.kind === "drop") { f.vy += 220 * dt; f.x += f.vx * dt; f.y += f.vy * dt; }
    else if (f.kind === "ring") f.r += 9 * dt;
  }
  hab.fx = hab.fx.filter((f) => f.life > 0);
}

function habBubble(poses) {
  const b = $("hab-bubble");
  const p = hab.picked && performance.now() < hab.pickedUntil && poses.find((q) => q.a === hab.picked);
  if (!p) { b.classList.add("hidden"); if (hab.picked && !p) hab.picked = null; return; }
  const scale = $("hab-canvas").clientWidth / hab.L.w;
  b.classList.remove("hidden");
  b.style.left = `${Math.min(Math.max(p.x * scale, 60), $("hab-canvas").clientWidth - 60)}px`;
  b.style.top = `${(p.y - 34) * scale}px`;
}

function habTap(ev) {
  if (!hab.L) return;
  const cv = $("hab-canvas"), r = cv.getBoundingClientRect();
  const x = (ev.clientX - r.left) / r.width * hab.L.w, y = (ev.clientY - r.top) / r.height * HAB_H;
  const phase = habPhase();
  // Front-most first: fliers, then the land and sea animals nearest the bottom.
  const roosting = { n: 0 };
  const hits = hab.animals.map((a) => {
    const awake = habAwake(a, phase);
    const roost = habRestSpot(a, awake, roosting);
    const [px, py] = habPose(a, awake, roost);
    return { a, awake, px, py, z: (awake && HAB_FLIERS.has(a.role) ? 1000 : 0) + py };
  }).filter((h) => Math.abs(x - h.px) <= 18 && y >= h.py - 34 && y <= h.py + 4).sort((p, q) => q.z - p.z);
  if (!hits.length) { hab.picked = null; habDraw(); return; }
  const h = hits[0];
  if (hab.picked === h.a && performance.now() < hab.pickedUntil) {
    if (hab.visit) openDex(h.a.s.number, h.a.num, caughtNums.has(h.a.s.number), hab.visit.state);
    else openDex(h.a.s.number, dexNumbers[h.a.s.number], true);
    return;
  }
  hab.picked = h.a;
  hab.pickedUntil = performance.now() + 4000;
  const b = $("hab-bubble");
  b.textContent = h.a.s.common_name + (h.awake ? "" : " 💤");
  b.title = "Tap again to open its page";
  if (habStill) habDraw();
}

// Show a friend's animals (their Field Guide entries) in their state's scenery,
// inside `slot` on their profile.
function habVisit(username, state, entries, slot) {
  if (!hab.visit) hab.visit = { home: hab.animals.map((a) => ({ caught: true, species: a.s, activity: a.activity })) };
  Object.assign(hab.visit, { username, state });
  slot.append($("habitat"), $("hab-bar"));
  hab.animals = []; hab.w = 0; hab.picked = null; hab.fx = [];
  habitatSet(entries);
}

// Back to your own scene, in its place on the Field Guide tab.
function habLeave() {
  if (!hab.visit) return;
  const home = hab.visit.home;
  hab.visit = null;
  $("grid").before($("habitat"), $("hab-bar"));
  hab.animals = []; hab.w = 0; hab.picked = null; hab.fx = [];
  habitatSet(home);
}

function habLoop(now) {
  requestAnimationFrame(habLoop);
  const box = $("habitat");
  if (document.hidden || !box || box.closest(".off") || box.closest(".hidden")) { hab.last = 0; return; }
  const w = box.clientWidth < 520 ? 320 : 480;
  if (!hab.L || w !== hab.w) habitatSet(hab.animals.map((a) => ({ caught: true, species: a.s, activity: a.activity, num: a.num })));
  const dt = hab.last ? Math.min((now - hab.last) / 1000, .1) : 0;
  hab.last = now;
  const phase = habPhase();
  hab.t += dt;
  hab.animals.forEach((a) => habStep(a, dt, habAwake(a, phase)));
  habFxStep(dt);
  habDraw();
}

// ---- Scenery, painted once per size, time of day and state. ----
// Painted pixel by pixel into a buffer: light comes from the upper left, round
// shapes get shaded like spheres, color steps are blended with ordered
// dithering, and trees, rocks and buildings get a dark outline.
function mulberry(seed) {
  return () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed);
    t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
}
const hexRgb = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16));
const mix = (a, b, k) => `rgb(${hexRgb(a).map((v, i) => Math.round(v + (hexRgb(b)[i] - v) * k)).join(",")})`;

const BAYER = [0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5];
const bayer = (x, y) => (BAYER[(y & 3) * 4 + (x & 3)] + .5) / 16;
function hash2(x, y, s = 0) {
  let h = Math.imul(x | 0, 374761393) + Math.imul(y | 0, 668265263) + Math.imul(s | 0, 1013904223) | 0;
  h = Math.imul(h ^ (h >>> 13), 1274126177);
  return ((h ^ (h >>> 16)) >>> 0) / 4294967296;
}
function vnoise(x, y, s = 0) {
  const xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi;
  const u = xf * xf * (3 - 2 * xf), v = yf * yf * (3 - 2 * yf);
  const a = hash2(xi, yi, s), b = hash2(xi + 1, yi, s), c = hash2(xi, yi + 1, s), d = hash2(xi + 1, yi + 1, s);
  return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v;
}
const fbm = (x, y, s = 0) => vnoise(x, y, s) * .55 + vnoise(x * 2.1, y * 2.1, s + 1) * .3 + vnoise(x * 4.3, y * 4.3, s + 2) * .15;
const clamp01 = (v) => v < 0 ? 0 : v > 1 ? 1 : v;

// A paint buffer of packed 0xRRGGBB colors (-1 = empty).
function pxLayer(w, h) {
  const d = new Int32Array(w * h).fill(-1);
  return {
    w, h, d,
    own: null,  // when set: marks pixels already colored for the time of day (sky, sun, moon)
    set(x, y, col, keep = 0) {
      x |= 0; y |= 0;
      if (x >= 0 && y >= 0 && x < w && y < h) { d[y * w + x] = col; if (this.own) this.own[y * w + x] = keep; }
    },
    get(x, y) { return x >= 0 && y >= 0 && x < w && y < h ? d[y * w + x] : -1; },
    // Copy onto another layer, with a 1px outline around the shapes.
    onto(dst, outline) {
      for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
        const v = d[y * w + x];
        if (v >= 0) dst.set(x, y, v);
        else if (outline !== undefined && (this.get(x - 1, y) >= 0 || this.get(x + 1, y) >= 0
                 || this.get(x, y - 1) >= 0 || this.get(x, y + 1) >= 0)) dst.set(x, y, outline);
      }
    },
  };
}

// Colors for one painting: hex in, packed and tinted for the time of day out.
function pxPalette(phase) {
  const night = phase === "night", dusk = phase === "dawn" || phase === "dusk";
  const cache = {};
  const one = (hex) => {
    if (cache[hex] !== undefined) return cache[hex];
    let [r, g, b] = hexRgb(hex);
    if (night) { r = r + (11 - r) * .55; g = g + (19 - g) * .55; b = b + (48 - b) * .55; }
    else if (dusk) { r = r + (120 - r) * .14; g = g + (70 - g) * .2; b = b + (120 - b) * .14; }
    return (cache[hex] = (Math.round(r) << 16) | (Math.round(g) << 8) | Math.round(b));
  };
  return (...hexes) => hexes.length === 1 ? one(hexes[0]) : hexes.map(one);
}
const pxMix = (a, b, k) => {
  const ch = (s) => Math.round(((a >> s) & 255) + (((b >> s) & 255) - ((a >> s) & 255)) * k);
  return (ch(16) << 16) | (ch(8) << 8) | ch(0);
};
// Pick from a dark-to-light ramp, dithering between neighbors.
const ramp = (pal, v, x, y) => pal[Math.min(pal.length - 1, Math.floor(clamp01(v) * (pal.length - 1) + bayer(x, y)))];

// A round shape shaded like a lump lit from the upper left. rough adds leafy
// or rocky texture; grain sets its size in pixels.
function pxBlob(t, cx, cy, rx, ry, pal, { rough = 0, grain = 2, seed = 0, flat = false, lift = 0 } = {}) {
  for (let dy = -ry; dy <= (flat ? 0 : ry); dy++) for (let dx = -rx; dx <= rx; dx++) {
    const nx = dx / rx, ny = dy / ry, d = nx * nx + ny * ny;
    const edge = rough ? (hash2((cx + dx) / grain | 0, (cy + dy) / grain | 0, seed + 7) - .5) * rough * .5 : 0;
    if (d > 1 + edge) continue;
    const nz = Math.sqrt(Math.max(0, 1 - d));
    let v = .5 + .5 * (-.55 * nx - .65 * ny + .52 * nz) + lift;
    if (rough) v += (hash2((cx + dx) / grain | 0, (cy + dy) / grain | 0, seed) - .5) * rough;
    t.set(cx + dx, cy + dy, ramp(pal, v, cx + dx, cy + dy));
  }
}

const HAB_SKY = { day: ["#3f8fd8", "#7cc1f0", "#cdeefb"], dawn: ["#4b4f9e", "#b884b8", "#ffd1a0"],
                  dusk: ["#272463", "#93487a", "#ff9a5a"], night: ["#040820", "#0c1840", "#25386e"] };
// How each time of day lights the land and the animals: per channel, value * mul + add.
const HAB_GRADE = { dawn: [[.9, 12], [.84, 10], [.88, 22]], dusk: [[.92, 16], [.78, 6], [.78, 18]],
                    night: [[.34, 8], [.42, 14], [.6, 42]] };
// Animals get a little less of it so they stay easy to see.
const HAB_SPRITE_GRADE = Object.fromEntries(Object.entries(HAB_GRADE).map(([k, g]) =>
  [k, g.map(([m, a]) => [m + (1 - m) * .3, a * .7])]));

function gradeData(d, g, skip) {
  for (let i = 0, p = 0; i < d.length; i += 4, p++) {
    if (skip && skip[p]) continue;
    d[i] = d[i] * g[0][0] + g[0][1]; d[i + 1] = d[i + 1] * g[1][0] + g[1][1]; d[i + 2] = d[i + 2] * g[2][0] + g[2][1];
  }
}

const habTints = {};
function habTinted(img, slug, phase) {
  const g = HAB_SPRITE_GRADE[phase];
  if (!g) return img;
  const key = `${slug}/${phase}`;
  if (!habTints[key]) {
    const cv = document.createElement("canvas");
    cv.width = img.naturalWidth; cv.height = img.naturalHeight;
    const c = cv.getContext("2d");
    c.drawImage(img, 0, 0);
    const id = c.getImageData(0, 0, cv.width, cv.height);
    gradeData(id.data, g);
    c.putImageData(id, 0, 0);
    habTints[key] = cv;
  }
  return habTints[key];
}

// Each state gets its own scenery: California has the snowy Sierra behind golden
// hills dotted with oaks, a coast live oak, poppies, a sea stack and kelp; North
// Carolina has the blue ridges of the mountains over forested hills, a longleaf
// pine, dogwood blossoms, dunes with sea oats and a striped lighthouse.
const HAB_SCENES = {
  CA: { far: ["#c99b48", "#dcb35e", "#ecc875", "#f7dc95"], near: ["#7d8a3c", "#97a24a", "#aeb65a", "#c6c977"],
        meadow: ["#5f9a3d", "#77b04a", "#8fc35a", "#a8d36d"], dots: "oak", tree: "oak",
        flowers: [["#ff7a1a", "#ffb347"], ["#ff7a1a", "#ffb347"], ["#ffcf3b", "#fff2a0"], ["#9a7cf0", "#d4c4ff"]] },
  NC: { far: ["#3f7a4a", "#4f8d55", "#62a061", "#79b473"], near: ["#2f6a3c", "#3d7d46", "#4f9150", "#64a55e"],
        meadow: ["#56943c", "#6aaa48", "#80bd57", "#98cf69"], dots: "forest", tree: "pine",
        flowers: [["#ffffff", "#f3e6b0"], ["#ffffff", "#f3e6b0"], ["#f6b8cf", "#ffffff"], ["#ffd84d", "#fff2a0"]] },
  default: { far: ["#6f9e60", "#82b370", "#97c483", "#b0d69a"], near: ["#4f8d43", "#62a250", "#78b55e", "#90c771"],
             meadow: ["#5f9a3d", "#77b04a", "#8fc35a", "#a8d36d"], dots: "round", tree: "round",
             flowers: [["#ffffff", "#ffe9a0"], ["#ffd84d", "#fff2a0"], ["#f27aa8", "#ffc4dc"], ["#b48cff", "#e0d0ff"]] },
};

function habBackground(L, phase, state) {
  // Land is painted in daylight colors, then graded for the time of day at the end.
  const W = L.w, H = HAB_H, sc = HAB_SCENES[state] || HAB_SCENES.default, P = pxPalette("day");
  const night = phase === "night", r = mulberry(7);
  const img = pxLayer(W, H);
  img.own = new Uint8Array(W * H);
  const pack = (a) => (Math.round(a[0]) << 16) | (Math.round(a[1]) << 8) | Math.round(a[2]);
  const unpack = (v) => [v >> 16 & 255, v >> 8 & 255, v & 255];
  const blend = (a, b, k) => [a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k, a[2] + (b[2] - a[2]) * k];
  const dith = (x, y, k) => k * 16 > BAYER[(y & 3) * 4 + (x & 3)] + .5;
  const put = (x, y, c) => img.set(Math.round(x), Math.round(y), pack(c), 1);
  const get = (x, y) => unpack(Math.max(0, img.get(x, y)));
  // Sky: a dithered gradient through three colors down to the horizon.
  const [s0, s1, s2] = HAB_SKY[phase].map(hexRgb), HZ = L.water;
  const skyAt = (k) => k < .55 ? blend(s0, s1, k / .55) : blend(s1, s2, (k - .55) / .45);
  const STEPS = 14, steps = Array.from({ length: STEPS }, (_, i) => skyAt(i / (STEPS - 1)));
  for (let y = 0; y < H; y++) {
    const v = Math.min(y / HZ, 1) * (STEPS - 1), b = Math.floor(v);
    for (let x = 0; x < W; x++) put(x, y, steps[Math.min(b + (dith(x, y, v - b) ? 1 : 0), STEPS - 1)]);
  }
  const skyTop = pack(s0), skyBot = pack(s2);
  // Rings of soft light around the sun or moon, solid inside and dithered at the edge.
  const halo = (cx, cy, r0, r1, col, amt) => {
    for (let y = cy - r1; y <= cy + r1; y++) for (let x = cx - r1; x <= cx + r1; x++) {
      const dd = Math.hypot(x - cx, y - cy);
      if (dd <= r0 || dd > r1 || y < 0 || y >= HZ) continue;
      const k = 1 - (dd - r0) / (r1 - r0);
      const ring = k > .66 ? .3 : k > .33 ? .17 : dith(x, y, k * 3) ? .17 : 0;
      if (ring) put(x, y, blend(get(x, y), col, ring * amt));
    }
  };
  const disc = (cx, cy, rr, fn) => {
    for (let y = -rr; y <= rr; y++) for (let x = -rr; x <= rr; x++)
      if (x * x + y * y <= rr * rr + rr * .8) fn(cx + x, cy + y, x / rr, y / rr);
  };
  const stars = [];
  if (night) {
    // A faint band of the Milky Way, then stars, a few of them bright.
    for (let y = 0; y < HZ - 20; y++) for (let x = 0; x < W; x++) {
      const band = 1 - Math.abs(x * .5 - y - W * .1) / 24;
      if (band > 0 && dith(x, y, band * vnoise(x / 7, y / 7, 5) * .6)) put(x, y, blend(get(x, y), hexRgb("#7584c4"), .28));
    }
    const sr = mulberry(11);
    for (let i = 0; i < 120; i++) {
      const x = Math.floor(sr() * W), y = Math.floor(sr() * (HZ - 26)), b = sr();
      put(x, y, blend(get(x, y), [255, 255, 255], .3 + b * .7));
      if (b > .9) {
        stars.push([x, y]);
        for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) put(x + dx, y + dy, blend(get(x + dx, y + dy), hexRgb("#cfe0ff"), .4));
      }
    }
    const mx = W - 72, my = 38;
    hab.glowX = mx;
    halo(mx, my, 10, 32, hexRgb("#8fa2e0"), .6);
    disc(mx, my, 10, (x, y, u, v) => {
      const l = u * .5 - v * .6;
      put(x, y, hexRgb(l > .4 ? "#fffbe6" : l > -.3 ? "#f1ebc8" : "#d8cfa6"));
    });
    for (const [dx, dy, rr] of [[-3, -2, 2], [3, 3, 1], [2, -5, 1], [-5, 4, 1]]) disc(mx + dx, my + dy, rr, (x, y) => put(x, y, hexRgb("#cfc499")));
  } else {
    const low = phase !== "day";
    const sx = low ? Math.round(W * .52) : W - 78, sy = low ? HZ - 30 : 36, sr = low ? 15 : 11;
    hab.glowX = sx;
    halo(sx, sy, sr, sr + (low ? 40 : 26), hexRgb(low ? "#ffd08a" : "#fff6cc"), .75);
    disc(sx, sy, sr, (x, y, u, v) => put(x, y, hexRgb(Math.hypot(u - .3, v + .3) < .5 ? "#fffbe8" : low ? "#ffc867" : "#ffe98a")));
  }
  hab.stars = stars;
  // Far mountains, sloping down to the coast.
  const coastEnd = L.sea + 10;
  // Mountains and hills sink toward the coast instead of stopping in a wall.
  const env = (x, len) => { const k = clamp01((coastEnd - 14 - x) / len); return k * k * (3 - 2 * k); };
  // Mountains reach down to the sea's horizon so none of them float over the coast.
  const foot = L.water + 1;
  const fade = (x, h) => Math.round(foot - (foot - h) * env(x, 90));
  const atmo = (col, k) => pxMix(col, 0xcdeefb, k);
  if (state === "CA") {
    // The Sierra Nevada: sharp shaded peaks with snow on top.
    const rock = P("#6c6a8c", "#8583a6", "#9e9cbc", "#b8b6d2"), snow = P("#aeb9dc", "#d2dbf2", "#f2f5ff", "#ffffff");
    const hm = [];
    for (let x = -1; x <= coastEnd + 1; x++) {
      const ridge = 1 - Math.abs(vnoise(x / 34, 0, 3) * 2 - 1);
      const det = 1 - Math.abs(vnoise(x / 9, 0, 4) * 2 - 1);
      hm[x + 1] = fade(x, Math.round(124 - ridge * 38 - det * 9));
    }
    for (let x = 0; x < coastEnd; x++) {
      const h = hm[x + 1], s = hm[x + 2] - hm[x];
      for (let y = h; y < foot; y++) {
        const v = .5 - s * .3 + (vnoise(x / 7, y / 4, 9) - .5) * .22 - (y - h) * .006;
        const isSnow = y < 98 + vnoise(x / 4, y / 3, 5) * 8 - (y - h) * .2;
        img.set(x, y, atmo(ramp(isSnow ? snow : rock, v, x, y), .28));
      }
    }
  } else if (state === "NC") {
    // The Blue Ridge: ridges fading into the haze.
    [[96, "#9fb6dc", "#b4c8e8"], [108, "#8199c8", "#98aedb"], [121, "#6683b8", "#7c97c9"]].forEach(([base, a, b], i) => {
      const pal = P(a, b);
      for (let x = 0; x < coastEnd; x++) {
        const h = fade(x, Math.round(base - fbm(x / 40, i * 3, 11 + i) * 18 + Math.sin(x / 23 + i) * 2));
        for (let y = h; y < foot; y++) img.set(x, y, y === h ? pal[1] : ramp(pal, .7 - (y - h) / 30, x, y));
      }
    });
  }
  // Hills, far then near, each with a lit top edge.
  const hills = [[132, 12, .021, sc.far, 20], [150, 9, .034, sc.near, 21]];
  hills.forEach(([base, amp, k, hex, seed], li) => {
    const pal = P(...hex);
    for (let x = 0; x < L.sea - 10; x++) {
      const raw = base + Math.sin(x * k + base) * amp + Math.sin(x * k * 2.7) * 3;
      const h = Math.round(L.water + 10 - (L.water + 10 - raw) * env(x + 10, 60));
      const slope = Math.cos(x * k + base) * amp * k + Math.cos(x * k * 2.7) * 3 * k * 2.7;
      for (let y = h; y < L.water + 10; y++) {
        const v = .62 - slope * 1.2 - (y - h) / 40 + (fbm(x / 12, y / 6, seed) - .5) * .4;
        img.set(x, y, y === h ? pal[3] : ramp(pal, v, x, y));
      }
    }
    // Trees on the hills: little oaks, a dense forest, or round trees.
    const dots = sc.dots, tl = pxLayer(W, H), tr = mulberry(31 + li);
    const n = dots === "forest" ? (li ? 70 : 90) : dots === "oak" ? (li ? 14 : 9) : (li ? 10 : 6);
    const leaf = dots === "oak" ? P("#3f5a26", "#526f30", "#67853b", "#7f9c4a")
      : dots === "forest" ? P("#1f4f2c", "#2b6236", "#387542", "#4a8a4f") : P("#2f6a34", "#3f7f41", "#55964f", "#6dad60");
    for (let i = 0; i < n; i++) {
      const x = Math.floor(tr() * (L.sea - 30)) + 4;
      const raw = base + Math.sin(x * k + base) * amp + Math.sin(x * k * 2.7) * 3;
      const h = Math.round(L.water + 10 - (L.water + 10 - raw) * env(x + 10, 60));
      const y = h + Math.floor(tr() * (dots === "forest" ? 14 : 8)) + (li ? 2 : 1);
      if (y > L.water + 2) continue;
      const s = li ? 1 : .7;
      if (dots === "oak") pxBlob(tl, x, y - 2, Math.round(5 * s + tr() * 2), Math.round(3 * s + 1), leaf, { rough: .5, seed: i });
      else if (dots === "forest") {
        if (tr() < .5) pxBlob(tl, x, y, Math.round(3 * s + 1), Math.round(4 * s + 1), leaf, { rough: .45, seed: i });
        else for (let j = 0; j < 7 * s + 2; j++) {
          const w = Math.round(j * .45);
          for (let dx = -w; dx <= w; dx++) tl.set(x + dx, y - 8 * s + j, ramp(leaf, .75 - (dx + w) / (2 * w + 1) * .7, x + dx, y + j));
        }
      } else pxBlob(tl, x, y - 2, Math.round(4 * s + 1), Math.round(4 * s + 1), leaf, { rough: .4, seed: i });
    }
    tl.onto(img, li ? P("#22401f") : undefined);
  });
  // Sea: lighter at the horizon, deep blue below, with wave texture.
  const sea = P("#1b4f8c", "#22629f", "#2c78b6", "#3a8fca", "#58a9dc", "#83c6ec");
  for (let y = L.water; y < H; y++) for (let x = L.sea - 30; x < W; x++) {
    let v = 1 - (y - L.water) / (H - L.water) * 1.05;
    const wv = vnoise(x / 9, y / 1.6, 13);
    if (wv > .74) v += .18; else if (wv < .22) v -= .12;
    img.set(x, y, ramp(sea, v, x, y));
  }
  for (let x = L.sea - 30; x < W; x++) img.set(x, L.water, P("#cdeefc"));
  // Meadow with patchy grass color.
  const mead = P(...sc.meadow);
  for (let y = L.water + 4; y < H; y++) for (let x = 0; x < L.shore[y] + 3; x++) {
    img.set(x, y, ramp(mead, .35 + (fbm(x / 16, y / 7, 17) - .5) * 1.1 + (y < L.water + 8 ? .2 : 0), x, y));
  }
  // Sandy shore curving down to the sea, wet near the water.
  const sand = P("#cdb27a", "#dcc38b", "#e9d49f", "#f4e3b6"), wet = P("#b39a68", "#c4aa76");
  for (let y = L.water + 2; y < H; y++) {
    const x0 = L.shore[y], x1 = L.surf[y];
    for (let x = x0; x < x1; x++) {
      const speck = hash2(x, y, 4);
      if (x >= x1 - 4) img.set(x, y, ramp(wet, (x1 - x) / 4, x, y));
      else img.set(x, y, speck > .93 ? sand[0] : speck < .05 ? sand[3] : ramp(sand, .45 + (vnoise(x / 6, y / 3, 5) - .5) * .7, x, y));
    }
    // Grass creeping onto the sand.
    const reach = Math.floor(vnoise(0, y / 3, 6) * 5);
    for (let i = 0; i < reach; i++) img.set(x0 + i, y, ramp(mead, .5 - i * .1, x0 + i, y));
  }
  // Grass tufts and clusters of flowers.
  const blade = P(sc.meadow[0], sc.meadow[3]);
  for (let i = 0; i < 260; i++) {
    const x = Math.floor(r() * (L.land - 6)), y = L.water + 7 + Math.floor(r() * (H - L.water - 8));
    img.set(x, y, blade[0]); img.set(x, y - 1, blade[0]); img.set(x + 1, y - 2, blade[1]); img.set(x - 1, y - 1, blade[1]);
  }
  const flowerSets = sc.flowers.map((f) => P(...f));
  for (let i = 0; i < 26; i++) {
    const cx = Math.floor(r() * (L.land - 16)) + 6, cy = L.water + 12 + Math.floor(r() * (H - L.water - 16));
    const [petal, mid] = flowerSets[Math.floor(r() * flowerSets.length)];
    for (let j = 0; j < 3 + r() * 3; j++) {
      const x = cx + Math.round((r() - .5) * 12), y = cy + Math.round((r() - .5) * 6);
      img.set(x, y + 1, blade[0]); img.set(x, y + 2, blade[0]);
      img.set(x - 1, y, petal); img.set(x + 1, y, petal); img.set(x, y - 1, petal); img.set(x, y + 1, petal); img.set(x, y, mid);
    }
  }
  // Sea floor rocks, some with moss.
  const rocks = pxLayer(W, H), stone = P("#3f434f", "#555a68", "#6e7383", "#8a8f9e");
  for (let i = 0; i < 7; i++) {
    const x = Math.round(L.sea + 8 + i * (W - L.sea) / 6.5 + (r() - .5) * 8);
    pxBlob(rocks, x, H - 1, 8 + i % 3 * 3, 6 + i % 2 * 2, stone, { rough: .35, seed: i, grain: 2 });
    if (i % 2) pxBlob(rocks, x - 2, H - 6 - i % 3, 4, 2, P("#4d7a3a", "#6a9a48"), { rough: .5, seed: i });
  }
  rocks.onto(img, P("#262a35"));
  // Pond: a ring of stones, deep water, sky reflection, lily pads and cattails.
  const p = L.pond, pond = pxLayer(W, H), pw = P("#1f5f97", "#2b76b0", "#3b8fc8", "#5eaee0");
  for (let dy = -p.ry; dy <= p.ry; dy++) for (let dx = -p.rx; dx <= p.rx; dx++) {
    const d = (dx / p.rx) ** 2 + (dy / p.ry) ** 2;
    if (d > 1) continue;
    pond.set(p.x + dx, p.y + dy, ramp(pw, .2 + (dy + p.ry) / (2 * p.ry) * .7 - (d > .75 && dy < 0 ? .2 : 0), p.x + dx, p.y + dy));
  }
  const pebble = P("#6d6a62", "#8c887d", "#a9a597", "#c4c0b1");
  for (let a = 0; a < Math.PI * 2; a += .26) {
    const x = Math.round(p.x + Math.cos(a) * (p.rx + 2)), y = Math.round(p.y + Math.sin(a) * (p.ry + 1.5));
    pxBlob(pond, x, y, 2 + (hash2(a * 100, 1) > .5 ? 1 : 0), 2, pebble);
  }
  pond.onto(img, P("#3c5a2c"));
  const refl = P("#8fd0f5"), pad = P("#3e7d34", "#5a9c42", "#76b653");
  for (const [dx, dy, w] of [[-18, -5, 9], [6, -3, 12], [-6, 4, 6]]) for (let i = 0; i < w; i++) img.set(p.x + dx + i, p.y + dy, refl);
  for (const [dx, dy] of [[-p.rx + 12, 2], [p.rx - 16, -3], [8, 6]]) {
    pxBlob(img, p.x + dx, p.y + dy, 4, 2, pad);
    img.set(p.x + dx + 1, p.y + dy - 1, pw[2]); img.set(p.x + dx + 2, p.y + dy, pw[2]);
  }
  img.set(p.x + p.rx - 16, p.y - 4, P("#ffd1e6")); img.set(p.x + p.rx - 15, p.y - 4, P("#ff9cc6")); img.set(p.x + p.rx - 16, p.y - 5, P("#ffd1e6"));
  const reed = P("#2f6a2c", "#4c8f3c"), cat = P("#6b4227", "#8a5833");
  for (const dx of [-p.rx - 3, -p.rx + 1, -p.rx + 4, p.rx - 2, p.rx + 2, p.rx + 5]) {
    const hgt = 12 + Math.floor(hash2(dx, 2) * 6);
    for (let i = 0; i < hgt; i++) { img.set(p.x + dx, p.y - 1 - i, reed[i % 3 ? 0 : 1]); }
    img.set(p.x + dx - 1, p.y - 4, reed[1]); img.set(p.x + dx + 1, p.y - 7, reed[1]);
    for (let i = 0; i < 4; i++) { img.set(p.x + dx, p.y - hgt - i, cat[i % 2]); img.set(p.x + dx + 1, p.y - hgt - i, cat[0]); }
    img.set(p.x + dx, p.y - hgt - 4, reed[0]);
  }
  // State extras on the shore and in the sea.
  if (state === "CA") {
    // A sea stack off the coast, like the ones along Big Sur: layered sandstone
    // stepping out in ledges, an arch worn through its foot, a flat top streaked
    // white where the sea birds stand, a smaller rock beside it and surf at the base.
    const st = pxLayer(W, H), sx = W - Math.round(W * .1), top = L.water - 44, base = L.water + 3;
    const rk = P("#3e3630", "#56493f", "#6f6052", "#8a7a68", "#a6957f");
    const wet = P("#22201f", "#2f2c29", "#3d3934"), guano = P("#cfcabd", "#ece8dc", "#fbfaf4");
    const halfW = (y) => {
      const band = Math.floor((y - top) / 8), k = (y - top) / (base - top);
      const left = 11 + band * 1.6 + k * 3 + Math.sin(y * .45) * .8;
      // the right side juts out into a ledge partway down
      const right = 10 + band * 1.2 + k * 2 + (y >= top + 17 ? 6 : 0) + Math.sin(y * .6 + 1) * .7;
      return [Math.round(left), Math.round(right)];
    };
    const inArch = (x, y) => ((x - (sx - 3)) / 5) ** 2 + ((y - base) / 12) ** 2 < 1;
    for (let y = top; y <= base; y++) {
      const [hl, hr] = halfW(y), ledge = (y - top) % 8 === 0 || y === top + 17, under = (y - top) % 8 === 7 || y === top + 18;
      for (let dx = -hl; dx <= hr; dx++) {
        const x = sx + dx;
        // round off the top corners
        if (y - top < 2 && (dx < -hl + 2 - (y - top) || dx > hr - 2 + (y - top))) continue;
        if (inArch(x, y)) continue;
        const across = (dx + hl) / (hl + hr + 1);
        let v = .85 - across * .75 + (ledge ? .2 : 0) - (under ? .25 : 0) + (fbm(x / 3, y / 2, 11) - .5) * .35;
        // cracks running down the rock
        if (hash2(Math.round(x / 2), y >> 3, 12) > .86 && hash2(x, 3, 13) > .5) v -= .3;
        st.set(x, y, y >= L.water - 1 ? ramp(wet, v, x, y) : ramp(rk, v, x, y));
      }
    }
    // White streaks where the birds stand: the top, the ledge, dribbling down.
    const [htl, htr] = halfW(top);
    for (let dx = -htl + 1; dx <= htr - 1; dx++) {
      st.set(sx + dx, top, ramp(guano, .9, sx + dx, top));
      if (hash2(dx, 4, 14) > .45) st.set(sx + dx, top + 1, ramp(guano, .5, sx + dx, top + 1));
      if (hash2(dx, 5, 15) > .72) for (let k = 2, n = 2 + Math.floor(hash2(dx, 6, 16) * 6); k < n; k++) st.set(sx + dx, top + k, guano[k % 2]);
    }
    const [, hrL] = halfW(top + 17);
    for (let dx = hrL - 6; dx <= hrL; dx++) {
      st.set(sx + dx, top + 17, guano[2]);
      if (hash2(dx, 7, 17) > .55) for (let k = 1; k < 2 + Math.floor(hash2(dx, 8, 18) * 4); k++) st.set(sx + dx, top + 17 + k, guano[0]);
    }
    // A tuft of ice plant clinging to the top corner.
    for (const [dx, dy] of [[-htl + 1, -1], [-htl + 2, -1], [-htl + 2, -2], [-htl + 3, -1], [-htl, 0]]) st.set(sx + dx, top + dy, P("#5e8a3a"));
    st.set(sx - htl + 2, top - 2, P("#e86aa8"));
    // The smaller rock beside it.
    pxBlob(st, sx - 27, L.water + 2, 7, 8, rk, { flat: true, rough: .45, grain: 2, seed: 21 });
    for (let dx = -31; dx <= -23; dx++) if (hash2(dx, 9, 19) > .35) st.set(sx + dx, L.water - 6 + (Math.abs(dx + 27) > 3 ? 1 : 0), guano[1]);
    st.onto(img, P("#1e1a17"));
    // Surf breaking white around the base and through the arch.
    const foam = P("#e9f6ff"), foam2 = P("#bfe2f5");
    for (let dx = -38; dx <= 30; dx++) {
      const [hl, hr] = halfW(base);
      const out = dx < -hl - 1 || dx > hr + 1;
      if (out && Math.abs(dx + 27) > 8 && hash2(dx, 9) > .25) img.set(sx + dx, L.water + 3, foam);
      if (out && hash2(dx, 10) > .55) img.set(sx + dx, L.water + 4, foam2);
      if (hash2(dx, 11) > .6 && Math.abs(dx) < 34) img.set(sx + dx + 2, L.water + 6, foam2);
    }
    for (let dx = -7; dx <= -1; dx++) if (hash2(dx, 12) > .3) img.set(sx + dx, L.water + 2, foam);
  } else if (state === "NC") {
    // Dunes with sea oats on the beach.
    const dune = pxLayer(W, H), ds = P("#d9c28c", "#e9d6a4", "#f5e7c0");
    for (const [dx, rx] of [[-6, 15], [13, 12]]) pxBlob(dune, L.land + dx, L.water + 8, rx, 7, ds, { flat: true });
    dune.onto(img);
    const oat = P("#8a8a3e", "#b5ad5a", "#d8c97a");
    for (let i = 0; i < 16; i++) {
      const x = L.land - 18 + Math.floor(hash2(i, 5) * 40), base = L.water + 4 + Math.floor(hash2(i, 6) * 3), hgt = 6 + Math.floor(hash2(i, 7) * 6);
      for (let j = 0; j < hgt; j++) img.set(x + (j > hgt * .6 ? 1 : 0), base - j, oat[j > hgt - 3 ? 2 : 0]);
      img.set(x + 2, base - hgt + 1, oat[1]); img.set(x - 1, base - 3, oat[1]);
    }
    // A black-and-white spiral-striped lighthouse with a red lantern roof.
    const lh = pxLayer(W, H), lx = L.sea - 12, topY = L.water - 58;
    const white = P("#b9b5aa", "#dcd8cc", "#f6f3ea", "#ffffff"), black = P("#15171c", "#22252c", "#33373f", "#474c56");
    for (let y = topY; y < L.water + 2; y++) {
      const hw = Math.round(3 + (y - topY) * .06);
      for (let dx = -hw; dx <= hw; dx++) {
        const v = .5 + .5 * -Math.sin(dx / (hw + .5) * Math.PI / 2) * .9 + .1;
        const band = Math.floor((y + dx * .9) / 7) % 2;
        lh.set(lx + dx, y, ramp(band ? black : white, v, lx + dx, y));
      }
    }
    for (let dx = -5; dx <= 5; dx++) { lh.set(lx + dx, topY - 1, black[1]); lh.set(lx + dx, topY, black[2]); }
    for (let y = topY - 6; y < topY - 1; y++) for (let dx = -3; dx <= 3; dx++) lh.set(lx + dx, y, Math.abs(dx) === 3 || y === topY - 4 && dx === 0 ? black[1] : P("#ffe9a0"));
    for (let y = topY - 10; y < topY - 6; y++) for (let dx = -(y - topY + 11); dx <= y - topY + 11; dx++) lh.set(lx + dx, y, ramp(P("#7a2318", "#a8352a", "#cf5143"), .8 - (dx + 4) / 9, lx + dx, y));
    lh.set(lx, topY - 11, black[1]);
    for (let y = L.water; y < L.water + 4; y++) for (let dx = -8; dx <= 8; dx++) lh.set(lx + dx, y, ramp(P("#7a3a2a", "#9a4c36", "#b8634a"), .8 - (dx + 8) / 17, lx + dx, y));
    lh.onto(img, P("#14161b"));
  }
  // The tree for roosting birds and a spider's thread: a big leafy oak, or in
  // North Carolina a longleaf pine.
  const tree = pxLayer(W, H), tx = L.tree, kind = sc.tree, ground = 194;
  for (let y = ground - 5; y <= ground + 6; y++) for (let x = tx - 30; x <= tx + 40; x++)
    if (((x - tx - 6) / 34) ** 2 + ((y - ground) / 6) ** 2 <= 1 && dith(x, y, .5)) img.set(x, y, pxMix(img.get(x, y), 0x1e3a14, .45));
  const bark = P("#4a3020", "#6e4a2e", "#8f6840", "#a98050");
  if (kind === "pine") {
    for (let y = 76; y < 196; y++) {
      const hw = 2 + (y > 186 ? 2 : 0);
      for (let dx = -hw; dx <= hw; dx++) {
        const v = .85 - (dx + hw) / (2 * hw + 1) * .8 + (hash2(tx + dx, y >> 2, 6) - .5) * .3;
        tree.set(tx + dx, y, ramp(bark, v, tx + dx, y));
      }
    }
    const leaf = P("#1c4426", "#265732", "#316b3d", "#3f8049", "#55985a");
    const crowns = [[-12, 110, 9, 4], [14, 100, 10, 4], [-4, 82, 12, 6], [6, 92, 9, 4], [-9, 96, 8, 4], [2, 74, 7, 4]];
    for (const [dx, dy] of crowns) for (let i = 0; i < Math.abs(dx); i++) tree.set(tx + Math.sign(dx) * i, dy + 2 + Math.floor(i / 4), bark[1]);
    crowns.forEach(([dx, dy, rx, ry], i) => pxBlob(tree, tx + dx, dy, rx, ry, leaf, { rough: .8, grain: 1, seed: i }));
    tree.onto(img, P("#13281a"));
  } else {
    const limb = (x0, y0, x1, y1, w0, w1) => {
      const n = Math.max(Math.abs(x1 - x0), Math.abs(y1 - y0));
      for (let k = 0; k <= n; k++) {
        const f = k / n, x = Math.round(x0 + (x1 - x0) * f), y = Math.round(y0 + (y1 - y0) * f), w = Math.round(w0 + (w1 - w0) * f);
        for (let j = 0; j < w; j++) img.set(x, y + j, bark[j === 0 ? 2 : j === w - 1 ? 0 : 1]);
      }
    };
    for (let y = 92; y <= ground; y++) {
      const hw = 4 + (y > ground - 8 ? Math.round((y - ground + 8) * .9) : 0);
      for (let x = tx - hw; x < tx + hw; x++) {
        const u = (x - tx + .5) / hw;
        let col = u < -.45 ? bark[2] : u < .35 ? bark[1] : bark[0];
        if (hash2(x, Math.floor(y / 3), 13) > .78) col = bark[0];
        else if (u < -.45 && hash2(x, y, 14) > .85) col = bark[3];
        img.set(x, y, col);
      }
    }
    limb(tx + 2, 104, tx + 28, 100, 3, 2);
    limb(tx - 2, 110, tx - 22, 101, 3, 2);
    limb(tx + 2, 133, tx + 18, 130, 2, 1);
    // California's coast live oak is a darker, olive green.
    const leaf = kind === "oak" ? P("#24391c", "#344f25", "#486b2f", "#62893c", "#86ab55")
      : P("#22492a", "#2f6633", "#41863d", "#5aa548", "#84c55c");
    const crown = [[-20, 88, 12], [22, 86, 13], [-8, 74, 14], [12, 70, 13], [2, 58, 11], [0, 92, 18],
                   [-18, 104, 13], [17, 101, 14], [-4, 112, 9], [27, 106, 8]];
    for (const [dx, cy, rr] of crown) {
      const cx = tx + dx;
      for (let y = cy - rr - 2; y <= cy + rr + 2; y++) for (let x = cx - rr - 2; x <= cx + rr + 2; x++) {
        const a = Math.atan2(y - cy, x - cx), dd = Math.hypot(x - cx, y - cy);
        const edge = rr * (.88 + vnoise(a * 2.4 + 10, dx, 17) * .24);
        if (dd > edge) continue;
        // Lit from the upper left, like the rest of the scene.
        const l = -(x - cx) / rr * .45 - (y - cy) / rr * .75 + (hash2(x, y, 18) - .5) * .5;
        let i = dd > edge - 1.2 && l < .25 ? 0 : l > .62 ? 4 : l > .2 ? 3 : l > -.3 ? 2 : 1;
        if (hash2(x >> 1, y, 19) > .86) i = Math.max(0, Math.min(4, i + (l > 0 ? 1 : -1)));
        img.set(x, y, leaf[i]);
      }
    }
  }

  const cv = document.createElement("canvas");
  cv.width = W; cv.height = H;
  const c = cv.getContext("2d"), data = c.createImageData(W, H);
  for (let i = 0; i < W * H; i++) {
    const v = img.d[i] < 0 ? skyTop : img.d[i];
    data.data[i * 4] = v >> 16 & 255; data.data[i * 4 + 1] = v >> 8 & 255; data.data[i * 4 + 2] = v & 255; data.data[i * 4 + 3] = 255;
  }
  if (HAB_GRADE[phase]) gradeData(data.data, HAB_GRADE[phase], img.own);
  c.putImageData(data, 0, 0);
  return cv;
}

// Fluffy clouds, shaded underneath, painted once per time of day.
const habClouds = {};
function habCloud(phase, i) {
  const key = `${phase}/${i}`;
  if (habClouds[key]) return habClouds[key];
  const P = pxPalette(phase === "night" ? "day" : phase), w = [56, 72, 44, 36][i], h = 22;
  const pal = phase === "day" ? P("#b9d3ea", "#d8e8f5", "#f3f8fd", "#ffffff")
    : P("#b98aa6", "#e0a8b0", "#f6c9c0", "#ffe6d6");
  const l = pxLayer(w + 4, h + 4), rr = mulberry(50 + i);
  const puffs = [[w * .3, 14, w * .2, 7], [w * .55, 11, w * .22, 9], [w * .78, 15, w * .16, 6], [w * .18, 16, w * .13, 5]];
  for (const [x, y, rx, ry] of puffs) pxBlob(l, Math.round(x + 2), Math.round(y + 2), Math.round(rx), Math.round(ry + rr()), pal, { lift: .15 });
  // Flat bottom.
  for (let x = 0; x < w + 4; x++) for (let y = 20; y < h + 4; y++) l.d[y * (w + 4) + x] = -1;
  const cv = document.createElement("canvas");
  cv.width = w + 4; cv.height = h + 4;
  const c = cv.getContext("2d"), data = c.createImageData(w + 4, h + 4);
  for (let k = 0; k < l.d.length; k++) {
    const v = l.d[k];
    if (v < 0) continue;
    data.data[k * 4] = v >> 16 & 255; data.data[k * 4 + 1] = v >> 8 & 255; data.data[k * 4 + 2] = v & 255;
    data.data[k * 4 + 3] = phase === "day" ? 240 : 215;
  }
  c.putImageData(data, 0, 0);
  return (habClouds[key] = cv);
}

// Things that move without being animals: clouds, surf, kelp, light on the sea.
function habAmbient(c, L, phase) {
  const t = hab.t;
  if (phase !== "night") {
    [[30, 22, 2.2], [L.w * .45, 8, 1.4], [L.w * .72, 44, 3], [L.w * .2, 58, 2.6]].forEach(([x0, y, v], i) => {
      const img = habCloud(phase, i), x = Math.round(((x0 + t * v) % (L.w + img.width * 2)) - img.width);
      c.drawImage(img, x, y);
    });
  }
  if (habState() === "CA") {
    // Kelp swaying on the sea floor, with leaf blades.
    const dark = phase === "night" ? "#24402a" : "#3f6a26", light = phase === "night" ? "#355a2f" : "#6d9a35";
    for (let i = 0; i < 4; i++) {
      const kx = L.sea + 24 + i * (L.w - L.sea - 40) / 4, len = 50 + (i * 17) % 30;
      for (let j = 0; j < len; j++) {
        const x = Math.round(kx + Math.sin(t * 1.1 + i + j * .08) * j * .1), y = HAB_H - 4 - j;
        c.fillStyle = dark; c.fillRect(x, y, 2, 1);
        c.fillStyle = light; c.fillRect(x, y, 1, 1);
        if (j % 9 === 4) { c.fillStyle = light; c.fillRect(x + (j % 18 ? 2 : -3), y, 3, 1); c.fillStyle = dark; c.fillRect(x + (j % 18 ? 2 : -3), y + 1, 3, 1); }
      }
    }
  } else if (habState() === "NC" && phase !== "day") {
    // The lighthouse lamp flashes after sundown.
    const on = Math.sin(t * 2.4) > .2, lx = L.sea - 12, ly = L.water - 62;
    if (on) {
      c.fillStyle = "rgba(255,240,160,.3)"; c.fillRect(lx - 11, ly - 4, 22, 8);
      c.fillStyle = "rgba(255,240,160,.25)"; c.fillRect(lx - 20, ly - 1, 40, 3);
      c.fillStyle = "#fff6c0"; c.fillRect(lx - 2, ly - 2, 5, 4);
    }
  }
  // Surf washing up the shore.
  c.fillStyle = phase === "night" ? "rgba(190,210,250,.55)" : "rgba(255,255,255,.85)";
  const roll = (t * .3) % 1, night = phase === "night";
  for (let y = L.water + 1; y < HAB_H; y++) {
    const e = L.surf[y], sway = Math.round(Math.sin(t * 1.4 + y * .21) * 1.5);
    c.fillStyle = night ? "rgba(200,215,255,.55)" : "rgba(255,255,255,.85)";
    c.fillRect(e - 1 + sway, y, 2, 1);
    // A wave rolling in toward the beach.
    c.fillStyle = night ? `rgba(200,215,255,${.5 * roll})` : `rgba(255,255,255,${.7 * roll})`;
    if ((y + Math.floor(t * 6)) % 3) c.fillRect(e + 2 + Math.round((1 - roll) * 16) + sway, y, 1, 1);
  }
  // Sun or moon glitter on the sea.
  if (hab.glowX > L.surf[L.water] + 8) {
    c.fillStyle = night ? "rgba(225,232,255,.5)" : phase === "day" ? "rgba(255,250,215,.7)" : "rgba(255,210,150,.6)";
    for (let y = L.water + 2; y < L.water + 44; y += 2) {
      const k = (y - L.water) / 44, w = Math.round((3 + k * 12) * (.6 + .4 * Math.sin(t * 2.1 + y * 1.7)));
      if (Math.sin(t * 3 + y * 2.3) > -.3) c.fillRect(hab.glowX - (w >> 1) + Math.round(Math.sin(t + y) * 2), y, w, 1);
    }
  }
  // Light drifting across the pond.
  const p = L.pond;
  c.fillStyle = night ? "rgba(200,215,255,.45)" : "rgba(225,245,255,.65)";
  for (let i = 0; i < 3; i++) {
    const k = (t * .06 + i / 3) % 1;
    c.fillRect(Math.round(p.x - p.rx * .7 + k * p.rx * 1.4), p.y - 4 + i * 4, 4 - i, 1);
  }
  // Bright stars twinkle.
  if (night) (hab.stars || []).forEach(([x, y], i) => {
    const s = Math.sin(t * 2.3 + i * 1.9);
    if (s <= .4) return;
    c.fillStyle = `rgba(255,255,255,${((s - .4) * 1.5).toFixed(2)})`;
    c.fillRect(x - 1, y, 3, 1); c.fillRect(x, y - 1, 1, 3);
  });
  // Glints that slide along the waves and fade in and out.
  for (let i = 0; i < 16; i++) {
    const a = Math.sin(t * 1.3 + i * 2.1);
    if (a < .2) continue;
    const span = L.w - L.sea, x = L.sea + ((i * 37 + t * (4 + i % 3 * 2)) % span), y = L.water + 4 + (i * 23) % 92;
    c.fillStyle = phase === "night" ? `rgba(160,190,255,${a * .5})` : `rgba(230,248,255,${a * .85})`;
    c.fillRect(Math.round(x), y, 3 + i % 3, 1);
    c.fillRect(Math.round(x) + 1, y - 1, 1 + i % 2, 1);
  }
}

function habInit() {
  $("hab-canvas").addEventListener("click", habTap);
  $("hab-peek").onclick = () => { hab.peek = !hab.peek; habNote(); if (habStill) habDraw(); };
  if (!habStill) requestAnimationFrame(habLoop);
}
