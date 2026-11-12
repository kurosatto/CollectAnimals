// The live habitat scene, shared by the website (static/index.html) and the
// Android app (android/app/src/main/assets/habitat.html shows it in a WebView).
// The page defines $, myState, spriteUrl, openDex, caughtNums and dexNumbers,
// has the #habitat, #hab-canvas, #hab-bubble, #hab-note and #hab-peek elements,
// and calls habInit() once they exist. Sprites load from /sprites/. It may also
// define animalFacts(species) -> list (or promise of a list) of fun facts that a
// tapped animal tells you.
// Habitat: the animals you've captured, living in one small pixel scene at the top
// of the Field Guide. Each one gets a way of moving from what it is (walkers,
// hoppers, fliers, swimmers, tide pool animals...) and is awake by day, by night
// or both (`activity` from /me/collection). The scene follows the real sun and
// moon, and a button peeks at the other half of the day. Tap an animal and it tells
// you its name and a fun fact; tap it again for another fact, or the bubble's
// link for its Field Guide page. The sky follows the real weather outside
// (rain, snow, fog, wind, storms) and the animals react to it.
const HAB_H = 270;
// While you look at a friend's profile, the scene moves into it and shows their
// animals in their state's scenery (`visit`); closing the profile brings yours back.
const hab = { w: 0, L: null, animals: [], peek: false, picked: null, pickedUntil: 0, factIdx: 0, last: 0, bg: null, bgKey: "", t: 0,
              fx: [], visit: null };
const habRealState = () => (hab.visit ? hab.visit.state : myState.code);
// The state whose scenery the habitat is drawn with (HAB_TWIN for countries).
const habState = () => { const st = habRealState(); return HAB_TWIN[st] || st; };
const habImgs = {};
// Animation sheets (species/sprites/anim): a row of frames for each pose (8 now, 4 in
// older sheets), and an index of the poses each species really draws. Without them
// the scene falls back to the single sprite, squashed and bobbed.
const habSheets = {};
let habAnimIdx = null;
fetch("/sprites/anim/index.json").then((r) => (r.ok ? r.json() : null)).then((j) => { habAnimIdx = j; }).catch(() => {});
// Every animal is a 40-unit drawing (40 px images; a 2x sheet of 80 px would draw at the
// same size). HAB_RES 2 would draw the canvas at 2x for such sheets; at 1 animals stand
// on whole pixels, matching the scenery (kuro prefers that look).
const HAB_UNIT = 40, HAB_RES = 1;
const habSnap = (v) => Math.round(v * HAB_RES) / HAB_RES;
const habNF = () => (habAnimIdx && habAnimIdx.frames) || 4;
// The frame at time t, counted in quarter loops (t = 4 is one whole loop), so a pose
// keeps its pace whatever number of frames the sheet has.
function habCyc(t) {
  const n = habNF();
  return ((Math.floor(t * n / 4) % n) + n) % n;
}
// Standing still: a slow breath in and out, with a blink (the index's "blink" frame)
// only every other breath, at a different moment for each animal.
function habIdleFrame(t, seed = 0) {
  const n = habNF(), u = Math.floor(t * n / 4), blink = habAnimIdx && habAnimIdx.blink;
  let f = ((u % n) + n) % n;
  if (blink != null && f === blink && (Math.floor(u / n) + seed) % 2) f = blink - 1;
  return f;
}
// How big each animal is drawn, next to a 1.0 crow: from 0.4 for a bee to 1.5 for a
// whale (tools/make_game_stats.py), so a seal is bigger than a banana slug.
let habScaleIdx = {};
fetch("/sprites/game_stats.json").then((r) => (r.ok ? r.json() : null)).then((j) => { habScaleIdx = (j && j.scale) || {}; })
  .catch(() => {});
const habScale = (slug) => habScaleIdx[slug] || 1;
const habStill = matchMedia("(prefers-reduced-motion: reduce)").matches;
const HAB_ROLES = [
  [/millipede|centipede|woodlouse/, "walk"],
  [/pelican|royal_tern|kingfisher|osprey|cormorant|anhinga/, "dive"],
  [/black_skimmer/, "skim"],
  [/sea_otter|by_the_wind/, "float"],
  [/jellyfish|man_o_war/, "jelly"],
  [/dolphin|whale|orca|porpoise|manatee|garibaldi|red_drum|snapper|sculpin|sea_hare|loggerhead|sea_turtle|octopus/, "swim"],
  [/seal|sea_lion|crab/, "beach"],
  [/star|anemone|mussel|barnacle|limpet|urchin|turban_snail|hopkins|scotch_bonnet/, "reef"],
  [/mallard|wood_duck|whistling_duck|shoveler|coot|gallinule|goose|swan|trout|bluegill|sunfish|bass|cichlid|gar$|mosquitofish|hellbender|beaver|coypu|muskrat|river_otter|alligator/, "paddle"],
  [/pond_slider|pond_turtle|painted_turtle|snapping|terrapin|cooter|softshell|crayfish|newt|salamander|ensatina/, "shore"],
  [/heron|egret|ibis|crane|stork|spoonbill|limpkin|oystercatcher/, "wade"],
  [/sanderling|willet|turnstone|killdeer/, "beach"],
  [/hawk|eagle|vulture|condor|osprey|kestrel/, "soar"],
  [/hummingbird/, "hover"],
  [/quail|turkey|roadrunner/, "walk"],
  [/firefly|swallowtail|monarch|painted_lady|mourning_cloak|fritillary|luna_moth|flame_skimmer|honey_bee|bumble_bee|queen|buckeye|hairstreak|white_peacock|longwing|salt_marsh_moth|pondhawk|dasher|pennant|_bat$|carpenter_bee|lanternfly|spongy_moth|small_white|skipper|whitetail|crescent|tailed_blue/, "flutter"],
  [/spider|widow|orbweaver/, "dangle"],
  [/frog|toad|peeper|grasshopper/, "hop"],
];
const HAB_DEFAULT_ROLE = { bird: "fly", amphibian: "shore", marine: "swim", fish: "paddle" };
const HAB_FLIERS = new Set(["fly", "soar", "hover", "flutter", "dive", "skim"]);
// Big birds glide between bursts of slow wingbeats.
const HAB_GLIDERS = /pelican|gull|heron|egret|crane|stork|spoonbill|goose|swan|vulture|condor|eagle|osprey|hawk|ibis|(^|_)tern|skimmer/;
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
  a.rest = habRestPose();
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

// A big collection doesn't all fit in the scene at once (85 animals were a heap at
// night), so the animals take turns: up to HAB_ROOM are out at a time, and a new
// mix comes out every HAB_TURN_MIN minutes. Everyone gets their turn; nothing to save.
const HAB_ROOM = { 320: 32, 480: 44 }, HAB_TURN_MIN = 20;
const habTurn = () => Math.floor(habNow() / (HAB_TURN_MIN * 60000));
function habOutNow(caught) {
  const room = HAB_ROOM[hab.w] || 32;
  hab.turn = habTurn();
  if (caught.length <= room) return caught;
  const mix = (slug) => { let h = hab.turn * 2654435761 >>> 0; for (const ch of slug) h = Math.imul(h ^ ch.charCodeAt(0), 16777619) >>> 0; return h; };
  return [...caught].sort((x, y) => mix(x.species.slug) - mix(y.species.slug)).slice(0, room);
}

// Called with the captured entries whenever the collection loads. Animals already
// in the scene stay where they are.
function habitatSet(entries) {
  const box = $("habitat");
  const w = box.clientWidth && box.clientWidth < 520 ? 320 : 480;
  const relayout = w !== hab.w;
  if (relayout) { hab.w = w; hab.L = habLayout(w); hab.bgKey = ""; }
  const old = new Map(hab.animals.map((a) => [a.s.slug, a]));
  const caught = entries.filter((e) => e.caught && e.species.slug);
  hab.entries = entries; hab.total = caught.length;
  hab.animals = habOutNow(caught).map((e) => {
    const prev = old.get(e.species.slug);
    if (prev && !relayout) { prev.s = e.species; prev.activity = e.activity || "day"; return prev; }
    const a = { s: e.species, activity: e.activity || "day", role: habRole(e.species), num: e.num };
    a.speed = habSpeed(a);
    habSpawn(a);
    if (!habImgs[a.s.slug]) { habImgs[a.s.slug] = new Image(); habImgs[a.s.slug].src = spriteUrl(a.s.slug, true); }
    if (!habSheets[a.s.slug]) { habSheets[a.s.slug] = new Image(); habSheets[a.s.slug].src = `/sprites/anim/${a.s.slug}.png`; }
    return a;
  });
  habWeather();
  habNote();
  if (habStill) setTimeout(habDraw, 300);
}

// ---- The real sky: where the sun and moon are right now, worked out on the phone
// from the date and the place (no downloads). Day, dawn, dusk and night follow the
// real sunrise and sunset, the sun and moon cross the sky, and the moon shows its
// real phase. Your own scene uses your rough position when the weather already
// uses it, otherwise the state's big city (the same cities as backend/app/weather.py).
// Preview another time with ?at=2026-10-23T03:00:00Z.
const HAB_CITY = {
  AL: [33.52, -86.81], AK: [61.22, -149.90], AZ: [33.45, -112.07], AR: [34.75, -92.29],
  CA: [34.05, -118.24], CO: [39.74, -104.99], CT: [41.76, -72.68], DE: [39.74, -75.55],
  FL: [28.54, -81.38], GA: [33.75, -84.39], HI: [21.31, -157.86], ID: [43.62, -116.20],
  IL: [41.88, -87.63], IN: [39.77, -86.16], IA: [41.59, -93.62], KS: [37.69, -97.34],
  KY: [38.25, -85.76], LA: [29.95, -90.07], ME: [43.66, -70.26], MD: [39.29, -76.61],
  MA: [42.36, -71.06], MI: [42.33, -83.05], MN: [44.98, -93.27], MS: [32.30, -90.18],
  MO: [39.10, -94.58], MT: [45.78, -108.50], NE: [41.26, -95.93], NV: [36.17, -115.14],
  NH: [42.99, -71.46], NJ: [40.74, -74.17], NM: [35.08, -106.65], NY: [40.71, -74.01],
  NC: [35.23, -80.84], ND: [46.88, -96.79], OH: [39.96, -83.00], OK: [35.47, -97.52],
  OR: [45.52, -122.68], PA: [39.95, -75.17], RI: [41.82, -71.41], SC: [34.00, -81.03],
  SD: [43.54, -96.73], TN: [36.16, -86.78], TX: [29.76, -95.37], UT: [40.76, -111.89],
  VT: [44.48, -73.21], VA: [37.54, -77.44], WA: [47.61, -122.33], WV: [38.35, -81.63],
  WI: [43.04, -87.91], WY: [41.14, -104.82],
  // European countries (ISO alpha-3 codes): their capitals.
  ALB: [41.33, 19.82], AUT: [48.20, 16.36], BLR: [53.90, 27.56], BEL: [50.84, 4.33],
  BIH: [43.85, 18.38], BGR: [42.69, 23.31], HRV: [45.80, 16.00], CYP: [35.17, 33.37],
  CZE: [50.09, 14.46], DNK: [55.68, 12.56], EST: [59.43, 24.73], FIN: [60.18, 24.93],
  FRA: [48.87, 2.33], DEU: [52.52, 13.40], GRC: [37.99, 23.73], HUN: [47.50, 19.08],
  ISL: [64.15, -21.95], IRL: [53.34, -6.25], ITA: [41.90, 12.48], XKX: [42.67, 21.17],
  LVA: [56.95, 24.10], LTU: [54.68, 25.32], LUX: [49.61, 6.13], MLT: [35.90, 14.51],
  MDA: [47.01, 28.86], MNE: [42.47, 19.27], NLD: [52.35, 4.91], MKD: [42.00, 21.43],
  NOR: [59.92, 10.75], POL: [52.25, 21.00], PRT: [38.72, -9.15], ROU: [44.44, 26.10],
  RUS: [55.75, 37.61], SRB: [44.82, 20.47], SVK: [48.15, 17.12], SVN: [46.06, 14.51],
  ESP: [40.40, -3.69], SWE: [59.35, 18.10], CHE: [46.92, 7.47], TUR: [39.93, 32.86],
  UKR: [50.44, 30.51], GBR: [51.50, -0.12],
};
// A European country's habitat borrows the scenery of a US state with a similar
// landscape and no US landmark: the Mediterranean coast is California's golden
// hills and sea, the Alps are Colorado's peaks, the Balkan and Carpathian hills
// the Smokies, the Baltic and Nordic woods Minnesota's and Maine's, Iceland and
// Norway Alaska's, Ukraine Kansas's wheat. The sun, moon and weather still use the
// country's own capital (habRealState).
const HAB_TWIN = {
  ALB: "CA", AUT: "CO", BLR: "MN", BEL: "DE", BIH: "TN", BGR: "TN", HRV: "CA", CYP: "CA",
  CZE: "KY", DNK: "RI", EST: "ME", FIN: "MN", FRA: "MD", DEU: "KY", GRC: "CA", HUN: "IA",
  ISL: "AK", IRL: "RI", ITA: "CA", XKX: "TN", LVA: "ME", LTU: "MN", LUX: "KY", MLT: "CA",
  MDA: "IA", MNE: "CA", NLD: "DE", MKD: "TN", NOR: "AK", POL: "WI", PRT: "CA", ROU: "TN",
  RUS: "MN", SRB: "KY", SVK: "TN", SVN: "CO", ESP: "CA", SWE: "MN", CHE: "CO", TUR: "CA",
  UKR: "KS", GBR: "RI",
};
// The water on the right of the scene is the Pacific in these states, so the sun
// sets over it there; everywhere else it rises on the water side.
const HAB_WEST_SEA = new Set(["CA", "OR", "WA", "AK", "HI"]);
const habAtTest = (() => { try { return Date.parse(new URLSearchParams(location.search).get("at")) || null; } catch { return null; } })();
const habNow = () => habAtTest || Date.now();
// Sun is in the sky above this many degrees, below minus HAB_TWILIGHT it's night.
const HAB_DAYLIGHT = 6, HAB_TWILIGHT = 8;

// Altitude and azimuth (degrees, azimuth from north through east) of a body at
// ecliptic longitude/latitude lam/beta, seen from lat/lon d days after J2000.
function habAltAz(lam, beta, d, lat, lon) {
  const r = Math.PI / 180, e = 23.4397 * r;
  const l = lam * r, b = beta * r;
  const ra = Math.atan2(Math.sin(l) * Math.cos(e) - Math.tan(b) * Math.sin(e), Math.cos(l));
  const dec = Math.asin(Math.sin(b) * Math.cos(e) + Math.cos(b) * Math.sin(e) * Math.sin(l));
  const H = (280.16 + 360.9856235 * d + lon) * r - ra, p = lat * r;
  const alt = Math.asin(Math.sin(p) * Math.sin(dec) + Math.cos(p) * Math.cos(dec) * Math.cos(H));
  const az = Math.atan2(Math.sin(H), Math.cos(H) * Math.sin(p) - Math.tan(dec) * Math.cos(p));
  return { alt: alt / r, az: (az / r + 540) % 360 };
}
// The sun and moon (simple formulas, good to about a degree) for a time and place.
function habSkyAt(ms, lat, lon) {
  const r = Math.PI / 180, d = ms / 864e5 - 10957.5;
  const M = (357.5291 + .98560028 * d) * r;
  const sunLam = M / r + 1.9148 * Math.sin(M) + .02 * Math.sin(2 * M) + .0003 * Math.sin(3 * M) + 282.9372;
  const Lm = 218.316 + 13.176396 * d, Mm = (134.963 + 13.064993 * d) * r, F = (93.272 + 13.22935 * d) * r;
  const moonLam = Lm + 6.289 * Math.sin(Mm), moonBeta = 5.128 * Math.sin(F);
  // How far the moon is round from the sun: 0 new, 180 full.
  const gap = ((moonLam - sunLam) % 360 + 360) % 360;
  const elong = Math.acos(Math.cos(moonBeta * r) * Math.cos(gap * r)) / r;
  return { sun: habAltAz(sunLam, 0, d, lat, lon), moon: { ...habAltAz(moonLam, moonBeta, d, lat, lon),
           elong, waxing: gap < 180, lit: (1 - Math.cos(elong * r)) / 2 } };
}
function habSkyNow() {
  const state = habRealState(), here = !hab.visit && hab.here && hab.here.state === state && hab.here;
  const [lat, lon] = here ? [here.lat, here.lon] : HAB_CITY[state] || HAB_CITY.CA;
  const at = Math.floor(habNow() / 15e3), key = `${state}/${lat}/${lon}/${at}`;
  if (hab.skyKey !== key) { hab.sky = habSkyAt(at * 15e3, lat, lon); hab.skyKey = key; }
  return hab.sky;
}
function habRealPhase() {
  const { alt, az } = habSkyNow().sun;
  return alt >= HAB_DAYLIGHT ? "day" : alt <= -HAB_TWILIGHT ? "night" : az < 180 ? "dawn" : "dusk";
}
const HAB_MOON_NAMES = [["🌑", "New moon"], ["🌒", "Waxing crescent moon"], ["🌓", "First quarter moon"],
  ["🌔", "Waxing gibbous moon"], ["🌕", "Full moon"], ["🌖", "Waning gibbous moon"], ["🌗", "Last quarter moon"],
  ["🌘", "Waning crescent moon"]];
function habMoonName() {
  const m = habSkyNow().moon, age = m.waxing ? m.elong : 360 - m.elong;
  return HAB_MOON_NAMES[Math.round(age / 45) % 8];
}
// Where the sun or moon sits in the scene: east to west across it (mirrored where
// the sea is to the west), and higher the higher it is in the real sky.
function habSkyXY(body, L) {
  const west = HAB_WEST_SEA.has(habState()) ? 1 : -1;
  const k = Math.max(-1, Math.min(1, (((body.az - 180) % 360 + 540) % 360 - 180) / 120));
  const x = Math.round(L.w / 2 + west * k * L.w * .42);
  // It climbs fast at first so a sun or moon a little way up clears the far hills.
  const a = body.alt, y = Math.round(L.water - 30 - (a > 0 ? (L.water - 66) * Math.sqrt(Math.min(1, a / 50)) : Math.max(a, -10) * 2.5));
  return [x, y];
}
// The sun and moon to draw for this phase: real ones now, or set ones while peeking.
function habLights(L, phase) {
  const sky = habSkyNow(), west = HAB_WEST_SEA.has(habState()) ? 1 : -1;
  const moon = { lit: sky.moon.lit, elong: sky.moon.elong, side: sky.moon.waxing ? west : -west };
  if (hab.peek) {
    return phase === "night" ? { moon: { ...moon, xy: [L.w - 72, 38] } } : { sun: { xy: [L.w - 78, 36] } };
  }
  const out = {};
  if (phase !== "night") out.sun = { xy: habSkyXY(sky.sun, L), low: phase !== "day" };
  // A moon that's up and not too thin; in daylight only a fat one shows, pale.
  if (sky.moon.alt > -1 && moon.lit > .03 && (phase !== "day" || (moon.lit > .25 && sky.moon.alt > 5))) {
    out.moon = { ...moon, xy: habSkyXY(sky.moon, L), pale: phase === "day" };
  }
  return out;
}
function habPhase() {
  const real = habRealPhase();
  if (!hab.peek) return real;
  return real === "day" ? "night" : "day";
}
const habAwake = (a, phase) => !habTuckedIn(a) && (phase === "dawn" || phase === "dusk" || a.activity === "any"
  || a.activity === (phase === "night" ? "night" : "day"));

function habNote() {
  if (hab.visit?.showcase) return;
  const phase = habPhase(), n = Math.max(hab.total || 0, hab.animals.length);
  const asleep = hab.animals.filter((a) => !habAwake(a, phase)).length;
  const out = hab.animals.length < n ? `, ${hab.animals.length} out now` : "";
  const who = hab.visit ? `${hab.visit.username}'s habitat` : "here";
  $("hab-note").textContent = !n ? (hab.visit ? `No animals in ${who} yet.` : "Capture animals and they'll move in here.")
    : `${n} animal${n > 1 ? "s" : ""} live${n > 1 ? "" : "s"} ${hab.visit ? "in " + who : "here"}` + out + (asleep ? `, ${asleep} asleep` : "")
      + (hab.wx ? ". " + habWxLine() : ". Tap one to say hi.")
      // Whole sentences: "It's fall." and at night "It's fall, under a full moon."
      + ` It's ${habSeason()}${phase === "night" ? ", under a " + habMoonName()[1].toLowerCase() : ""}.`;
  const night = phase === "night";
  const here = document.getElementById("hab-wx-here");
  if (here) here.hidden = !(hab.wxAsk && hab.wx && !hab.visit);
  // Pixel sun and moon icons (tools/make_ui_icons.py), not emojis.
  const toDay = night || phase === "dusk", peek = $("hab-peek");
  if (hab.peek) peek.textContent = "Back to now";
  else {
    const ic = document.createElement("img");
    ic.className = "pi"; ic.alt = ""; ic.src = `/sprites/ui_ic_${toDay ? "sun" : "moon"}.png`;
    peek.replaceChildren(ic, toDay ? "Peek at daytime" : "Peek at night");
  }
}

// Birds out on the landmark are far away, so they're drawn smaller.
const HAB_PERCH_SCALE = .72;
// Spots on the state's coastal landmark where sea birds stand: [x, feet y].
// California's sea stack: two on the flat top, one on the ledge, one on the
// small rock beside it. North Carolina's lighthouse: the gallery and the base.
// Texas's windmill: its platform, the tail vane and the stock tank below.
// Florida's mangrove island: the top of its canopy.
// Scenery for the states drawn from shared pieces: the distant landscape (far:
// snowy peaks, Blue Ridge-style ridges, mesas, cypress swamp, farmland, or a
// volcano), the landmark on the water (sea: a lighthouse island, a sea stack,
// a steamboat, icebergs, the Gateway Arch or the Space Needle), the palette
// (look), and the state flower's colors.
const HAB_STATE_LAND = {
  AL: { far: "cypress", sea: "lighthouse", look: "swamp", flower: ["#d8283a", "#ff9aa0"] },
  AK: { far: "peaks", sea: "iceberg", look: "north", flower: ["#5a7ae0", "#c4d0ff"] },
  AZ: { far: "mesas", look: "desert", flower: ["#ffffff", "#f8e8a0"], saguaro: true },
  AR: { far: "ridges", look: "forest", flower: ["#ffffff", "#f8d0e0"] },
  CO: { far: "peaks", look: "north", flower: ["#7a8ae0", "#ffffff"] },
  CT: { far: "ridges", sea: "lighthouse", look: "coast", flower: ["#f8c8d8", "#ffffff"] },
  DE: { sea: "lighthouse", look: "coast", flower: ["#f8a8c8", "#ffe0ec"] },
  HI: { far: "shield", look: "tropical", flower: ["#ffd23a", "#c8641e"] },
  ID: { far: "peaks", look: "north", flower: ["#ffffff", "#f3e6b0"] },
  IN: { far: "farm", look: "plains", flower: ["#9a5ad8", "#e8c0ff"] },
  IA: { far: "farm", look: "plains", flower: ["#f6b8cf", "#ffffff"] },
  KS: { far: "farm", look: "plains", flower: ["#ffd23a", "#6a3a1a"] },
  KY: { far: "ridges", look: "forest", flower: ["#ffd23a", "#fff2a0"] },
  LA: { far: "cypress", sea: "steamboat", look: "swamp", flower: ["#ffffff", "#f3e6b0"] },
  ME: { far: "ridges", sea: "lighthouse", look: "north", flower: ["#ffffff", "#e8dcc0"], lh: "white" },
  MD: { far: "ridges", sea: "lighthouse", look: "coast", flower: ["#ffc81e", "#5a2a14"] },
  MA: { sea: "lighthouse", look: "coast", flower: ["#f8c8d8", "#ffffff"], lh: "white" },
  MN: { far: "ridges", sea: "lighthouse", look: "north", flower: ["#f6b8cf", "#ffffff"], lh: "white" },
  MS: { far: "cypress", sea: "steamboat", look: "swamp", flower: ["#ffffff", "#f3e6b0"] },
  MO: { far: "farm", sea: "arch", look: "plains", flower: ["#ffffff", "#f8d0e0"] },
  MT: { far: "peaks", look: "north", flower: ["#f6b8cf", "#ffffff"] },
  NE: { far: "farm", look: "plains", flower: ["#ffd23a", "#fff2a0"] },
  NV: { far: "mesas", look: "desert", flower: ["#c8b8e0", "#ffffff"] },
  NH: { far: "ridges", look: "maple", flower: ["#9a6ad8", "#e8d0ff"] },
  NM: { far: "mesas", look: "desert", flower: ["#ffffff", "#f8e8a0"] },
  ND: { far: "mesas", look: "plains", flower: ["#f27aa8", "#ffc4dc"] },
  OK: { far: "farm", look: "plains", flower: ["#d8283a", "#ff9aa0"] },
  OR: { far: "volcano", sea: "stack", look: "north", flower: ["#ffd23a", "#fff2a0"] },
  RI: { sea: "lighthouse", look: "coast", flower: ["#9a6ad8", "#e8d0ff"], lh: "white" },
  SC: { far: "cypress", sea: "lighthouse", look: "swamp", flower: ["#ffd23a", "#fff2a0"] },
  SD: { far: "mesas", look: "plains", flower: ["#b48cff", "#f0e8ff"] },
  TN: { far: "ridges", look: "forest", flower: ["#9a6ad8", "#e8d0ff"] },
  UT: { far: "mesas", look: "desert", flower: ["#ffffff", "#f8e0a0"] },
  VT: { far: "ridges", look: "maple", flower: ["#d8283a", "#ffffff"] },
  WA: { far: "volcano", sea: "needle", look: "north", flower: ["#f27aa8", "#ffc4dc"] },
  WV: { far: "ridges", look: "forest", flower: ["#f6b8cf", "#ffffff"] },
  WI: { far: "farm", sea: "lighthouse", look: "plains", flower: ["#9a6ad8", "#e8d0ff"], lh: "white" },
  WY: { far: "peaks", look: "north", flower: ["#d8402a", "#ff9a7a"] },
};
const habLand = (state) => HAB_STATE_LAND[state] || {};
// The Gateway Arch on the far bank: its feet and how tall it stands.
function habArch(L) {
  const ax = L.sea + Math.round((L.w - L.sea) * .5), ground = L.water - 1;
  return { ax, ground, half: 20, h: 50 };
}
// The Space Needle on its point: the saucer's height and the spire's tip.
function habNeedle(L) {
  const nx = L.sea + Math.round((L.w - L.sea) * .5), ground = L.water - 1, deck = ground - 44;
  return { nx, ground, deck, tip: [nx, deck - 14] };
}
// A paddlewheel steamboat on the river: its middle, waterline and stacks.
function habSteamboat(L) {
  const bx = L.sea + Math.round((L.w - L.sea) * .5), wl = L.water + 2;
  return { bx, wl, stacks: [[bx - 6, wl - 26], [bx - 1, wl - 26]] };
}
function habPerches(L, state) {
  const land = habLand(state);
  if (land.sea === "lighthouse") {
    const { ix, ground, lx, ltop } = habAssateague(L);
    return [[lx - 4, ltop - 1], [lx + 5, ltop - 1], [ix - 20, ground + 1], [ix + 22, ground + 1]];
  }
  if (land.sea === "stack") state = "CA";
  if (land.sea === "arch") {
    const { ax, ground, half, h } = habArch(L);
    return [[ax, ground - h - 1], [ax - half - 4, ground], [ax + half + 4, ground], [ax - 6, ground - h + 2]];
  }
  if (land.sea === "needle") {
    const { nx, ground, deck } = habNeedle(L);
    return [[nx - 7, deck - 1], [nx + 7, deck - 1], [nx - 16, ground], [nx + 16, ground]];
  }
  if (land.sea === "steamboat") {
    const { bx, wl, stacks } = habSteamboat(L);
    return [stacks[0], stacks[1], [bx + 12, wl - 15], [bx - 16, wl - 8]];
  }
  if (state === "CA") {
    const sx = L.w - Math.round(L.w * .1), top = L.water - 44;
    return [[sx - 7, top], [sx + 6, top], [sx + 17, top + 17], [sx - 27, L.water - 6]];
  }
  if (state === "NC") {
    const lx = L.sea - 12, topY = L.water - 58;
    return [[lx - 4, topY - 1], [lx + 5, topY - 1], [lx - 6, L.water], [lx + 6, L.water]];
  }
  if (state === "TX") {
    // The ranch windmill: the platform under the wheel and the tail vane.
    const wx = L.land - 34, top = L.water - 52;
    return [[wx - 4, top + 14], [wx + 4, top + 14], [wx + 15, top], [wx - 7, L.water + 8]];
  }
  if (state === "FL") {
    // The mangrove island just offshore: along the top of its canopy.
    const mx = L.sea + Math.round((L.w - L.sea) * .45), top = L.water - 14;
    return [[mx - 12, top + 3], [mx - 3, top], [mx + 7, top + 1], [mx + 15, top + 4]];
  }
  if (state === "NY") {
    // The Statue of Liberty: the pedestal's top corners and the star fort's.
    const { sx, ftop, ptop } = habLiberty(L);
    return [[sx - 5, ptop], [sx + 5, ptop], [sx - 12, ftop], [sx + 12, ftop]];
  }
  if (state === "VA") {
    // Assateague: the lighthouse gallery and the island's sandy ends.
    const { ix, ground, lx, ltop } = habAssateague(L);
    return [[lx - 4, ltop - 1], [lx + 5, ltop - 1], [ix - 20, ground + 1], [ix + 22, ground + 1]];
  }
  if (state === "NJ") {
    // The Ferris wheel's top and the pier's railing on either side of it.
    const { x0, x1, deck, hx, hy, r } = habPier(L);
    return [[hx, hy - r - 2], [x0 + 6, deck - 3], [x1 - 6, deck - 3], [hx - r - 6, deck - 3]];
  }
  if (state === "MI") {
    // The tops of the bridge's two towers and the deck between them.
    const { deck, t1, t2, ttop } = habMackinac(L);
    return [[t1, ttop - 1], [t2, ttop - 1], [Math.round((t1 + t2) / 2) - 6, deck - 1], [Math.round((t1 + t2) / 2) + 6, deck - 1]];
  }
  if (state === "GA") {
    // The shrimp boat's mast top, both boom tips and the cabin roof.
    const { bx, wl, mast, booms } = habShrimper(L);
    return [[bx, mast], booms[0], booms[1], [bx + 9, wl - 11]];
  }
  if (state === "OH") {
    // The roller coaster's lift-hill crest and loop top, and the peninsula's ends.
    const { cx, g, top, loop } = habCoaster(L);
    return [[top[0], top[1]], [loop[0], loop[1]], [cx - 36, g + 1], [cx + 34, g + 1]];
  }
  if (state === "IL") {
    // The Willis Tower's roof on either side of its antennas, and its shoulders.
    const { wx, wtop } = habChicago(L);
    return [[wx - 3, wtop], [wx + 3, wtop], [wx - 6, wtop + 8], [wx + 6, wtop + 12]];
  }
  if (state === "PA") {
    // The covered bridge: both ends of its roof ridge and the two banks.
    const { bx, half, ridge, bank } = habBridge(L);
    return [[bx - half + 3, ridge], [bx + half - 3, ridge], [bx - half - 8, bank], [bx + half + 8, bank]];
  }
  return [];
}
// A Jersey Shore pier: the boardwalk deck, and the Ferris wheel standing on it
// (its hub, radius and the gondolas' positions as it turns).
function habPier(L) {
  const x0 = L.sea + 6, x1 = L.sea + Math.round((L.w - L.sea) * .9), deck = L.water - 6;
  const r = 21, hx = L.sea + Math.round((L.w - L.sea) * .55), hy = deck - r - 4;
  const cars = (a) => Array.from({ length: 8 }, (_, i) => [hx + Math.cos(a + i * Math.PI / 4) * r, hy + Math.sin(a + i * Math.PI / 4) * r]);
  return { x0, x1, deck, hx, hy, r, cars };
}
// The Mackinac Bridge across the Straits: deck height, the two towers and the
// main cable's curve between and beyond them.
function habMackinac(L) {
  const x0 = L.sea + 4, x1 = L.w + 4, deck = L.water - 8, t1 = L.sea + Math.round((L.w - L.sea) * .3);
  const t2 = L.sea + Math.round((L.w - L.sea) * .8), ttop = deck - 34;
  const sag = deck - 4 - ttop, side = (d, len) => ttop + Math.pow(d / len, 1.3) * sag;
  const cable = (x) => x < t1 ? side(t1 - x, t1 - x0) : x > t2 ? side(x - t2, x1 - t2)
    : ttop + sag * 4 * (x - t1) * (t2 - x) / ((t2 - t1) * (t2 - t1));
  return { x0, x1, deck, t1, t2, ttop, cable };
}
// A Georgia shrimp boat out on the water: its middle, waterline, mast top and the
// tips of the two net booms.
function habShrimper(L) {
  const bx = L.sea + Math.round((L.w - L.sea) * .5), wl = L.water + 2, mast = wl - 30;
  return { bx, wl, mast, booms: [[bx - 20, wl - 20], [bx + 20, wl - 20]] };
}
// A Cedar Point roller coaster on its peninsula in Lake Erie: the track as a list
// of points (lift hill, drop, loop, run-out) and the ground it stands on.
function habCoaster(L) {
  const cx = L.sea + Math.round((L.w - L.sea) * .5), g = L.water - 1, pts = [];
  const seg = (a, b, n) => { for (let i = 0; i < n; i++) pts.push([a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n]); };
  seg([cx - 32, g - 3], [cx - 20, g - 40], 40);
  for (let i = 0; i <= 20; i++) { const u = i / 20; pts.push([cx - 20 + u * 8, g - 40 - Math.sin(u * Math.PI) * 2 + u * u * 36]); }
  for (let i = 0; i < 20; i++) { const u = i / 20; pts.push([cx - 12 + u * 14, g - 4 + Math.sin(u * Math.PI) * 2]); }
  const lx = cx + 10, ly = g - 13, r = 9;
  for (let i = 0; i <= 48; i++) { const a = Math.PI / 2 + i / 48 * Math.PI * 2; pts.push([lx + Math.cos(a) * r * .8 + i / 48 * 4, ly + Math.sin(a) * r]); }
  seg([lx + 4, g - 4], [cx + 30, g - 3], 16);
  return { cx, g, pts, top: [cx - 20, g - 41], loop: [lx + 2, ly - r - 1] };
}
// Chicago across Lake Michigan: the skyline's left and right ends, its base on the
// horizon, and the Willis Tower (where it stands, its roof and the antenna tops).
function habChicago(L) {
  const x0 = L.sea + 14, x1 = L.w - 6, base = L.water, wx = x0 + Math.round((x1 - x0) * .62), wtop = base - 30;
  return { x0, x1, base, wx, wtop, tips: [[wx - 2, wtop - 7], [wx + 2, wtop - 7]] };
}
// The red covered bridge out on the water: its middle, half-length, deck, roof
// ridge, the banks it joins and the lanterns hung at each end.
function habBridge(L) {
  const bx = L.sea + Math.round((L.w - L.sea) * .5), half = 21, deck = L.water - 4, ridge = deck - 19, bank = L.water - 1;
  return { bx, half, deck, ridge, bank, lamps: [[bx - half, deck - 7], [bx + half, deck - 7]] };
}
// Assateague Island out in the bay: where it sits, its lighthouse and the lamp.
function habAssateague(L) {
  const ix = L.sea + Math.round((L.w - L.sea) * .5), ground = L.water - 2, lx = ix + 12, ltop = ground - 46;
  return { ix, ground, lx, ltop, lamp: [lx, ltop - 4] };
}
// Where the Statue of Liberty stands on its island in the harbor.
function habLiberty(L) {
  const sx = L.sea + Math.round((L.w - L.sea) * .55), ftop = L.water - 4, ptop = ftop - 15;
  return { sx, ftop, ptop, torch: [sx - 7, ptop - 31] };
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

// Where a sleeping (or sheltering) animal rests, or null if it sleeps where it is:
// sea birds on the coastal landmark while there's room, other fliers in the tree.
function habRestSpot(a, awake, counter) {
  const home = habDecorRest(a, awake);  // a birdhouse, bat box, tent... of your own
  if (home) return home;
  // Small fliers wait out the rain in the tree.
  if (awake) return habSheltering(a) ? habRoost(counter.n++) : null;
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
    // Most dives come up with a fish, held for a few seconds.
    if (a.t <= 0) { a.mode = "rise"; a.vy = -55; habSplash(a.x, surf, 6); a.fish = Math.random() < .8 ? rnd(4, 7) : 0; }
  } else if (a.mode === "rise") {
    a.y += a.vy * dt; a.x += a.vx * a.speed * .5 * dt; a.tilt = -.4;
    if (a.y <= a.cy) { a.mode = "fly"; a.diveIn = rnd(4, 10); }
  } else {
    a.x += a.vx * a.speed * dt;
    a.y += (a.cy - a.y) * Math.min(1, dt * 2);
    if (a.fish > 0) a.fish -= dt;
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
  habWxReact(a, dt, awake);
  habTimers(a, dt, awake);
  if (habDecorStep(a, dt, awake)) return;
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
    // A gull tags along after a diver carrying a fish, hoping it drops it.
    const f = a.chase;
    if (f && f.fish > 0 && f.mode === "fly") {
      const goal = f.x - Math.sign(f.vx) * 16;
      a.vx = Math.max(-1.4, Math.min(1.4, (goal - a.x) / 20)) || a.vx;
      a.y += (f.y + 6 - a.y) * Math.min(1, dt * 1.5);
    } else a.chase = null;
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
    // Drinking at the pond: little rings where the nose touches the water.
    if (a.drinking && (a.rip = (a.rip || 0) - dt) <= 0) { a.rip = rnd(.8, 1.4); habRipple(a.x + a.dir * 13, hab.L.pond.y - 1); }
    // Standing still: glance the other way now and then; waders stab at fish,
    // birds on the ground peck at seeds and now and then sing.
    if (HAB_LOOKERS.has(a.role) && (a.look -= dt) <= 0) {
      const bird = a.s.category === "bird";
      a.look = bird && a.role !== "wade" ? rnd(.5, 1.3) : rnd(1.2, 3.5);
      if (a.role === "wade" && Math.random() < .6) { a.peck = .6; habRipple(a.x + a.dir * 12, a.y - 1); }
      else if (bird && (a.drinking || Math.random() < .7)) {
        a.peck = .6;
        if (a.drinking) habRipple(a.x + a.dir * 10, hab.L.pond.y - 1);
      } else if (bird && HAB_SINGERS.test(a.s.slug) && Math.random() < .3) a.react = { kind: "note", life: 1.6 };
      else if (!a.drinking && a.rest !== "eat") a.dir = -a.dir;
    }
    return;
  }
  if (a.drinking) a.drinking = false;
  // Chasing a playmate: run to where it is now.
  if (a.chase && a.chaseT > 0) {
    const o = a.chase;
    if (Math.hypot(o.x - a.x, o.y - a.y) < 8) {
      // Caught up: both stop and face each other for a moment.
      a.chaseT = 0; a.chase = null; o.flee = 0;
      for (const [m, n] of [[a, o], [o, a]]) { m.pause = rnd(1.2, 2); m.rest = "idle"; m.dir = Math.sign(n.x - m.x) || 1; }
      return;
    }
    a.tx = o.x + Math.sign(a.x - o.x) * 4; a.ty = o.y;
  }
  const dx = a.tx - a.x, dy = a.ty - a.y, d = Math.hypot(dx, dy);
  // Startled animals dash, chasers run.
  const step = a.speed * dt * (a.flee > 0 ? 3 : a.chaseT > 0 ? 2.6 : 1);
  if (d <= step) {
    a.x = a.tx; a.y = a.ty;
    a.pause = a.role === "hover" ? rnd(.4, 1.4) : rnd(1, 5);
    a.rest = habRestPose();
    if (a.toDrink) {
      // At the water's edge: face the pond and drink (a grazer's head-down pose).
      a.toDrink = false; a.drinking = true;
      a.dir = a.x < hab.L.pond.x ? 1 : -1;
      a.pause = rnd(4, 7); a.rest = "eat"; a.rip = .4;
    }
    if (HAB_DRINKERS.has(a.role) && /mammal|bird/.test(a.s.category) && !a.drinking && Math.random() < .14) {
      const p = hab.L.pond, side = Math.random() < .5 ? -1 : 1;
      a.tx = p.x + side * (p.rx + 9); a.ty = p.y + 1; a.toDrink = true;
    } else [a.tx, a.ty] = habSpot(a);
    return;
  }
  a.x += dx / d * step; a.y += dy / d * step; a.odo += step;
  if (Math.abs(dx) > .5 && a.role !== "beach") a.dir = Math.sign(dx);
}

// ---- Interactions: what the animals do when you tap them, and with each other.
// Small songbirds (not crows, gulls, waders or fowl) sing now and then.
const HAB_SINGERS = /sparrow|finch|warbler|robin|wren|thrush|bluebird|cardinal|chickadee|titmouse|oriole|tanager|bunting|grosbeak|meadowlark|mockingbird|thrasher|catbird|junco|towhee|lark|goldfinch|siskin|canary|bulbul|shama|white_eye|leiothrix|amakihi|apapane|i_iwi|phoebe|flycatcher|kingbird|blackbird|bobolink|dickcissel|vireo|kinglet|waxwing|swallow|nuthatch|verdin|bushtit/;
// Ground animals that bolt when startled (the rest stop and look at you).
const HAB_SKITTISH = /squirrel|chipmunk|rabbit|cottontail|hare|jackrabbit|mouse|vole|rat$|kangaroo_rat|pika|lizard|skink|anole|whiptail|fence|spiny|racerunner|quail|grouse|ptarmigan|francolin|pheasant|roadrunner|killdeer|sanderling|turnstone|plover|sandpiper|dunlin|willet|tattler|chicken|turkey/;
// Shy ones that pull in instead.
const HAB_SHY = /turtle|tortoise|terrapin|cooter|slider|snapping|softshell|snail|slug|crab|armadillo|hedgehog|porcupine|opossum/;
// Young-at-heart mammals that play chase with each other.
const HAB_PLAYFUL = /squirrel|chipmunk|otter|fox|coyote|raccoon|rabbit|cottontail|hare|marmot|prairie_dog|dog$|cat$|ferret|mink|weasel|skunk|pika/;
// Hunters overhead that make small animals freeze.
const HAB_RAPTORS = /hawk|eagle|kestrel|falcon|harrier|kite|osprey|owl/;
// Who walks down to the pond for a drink.
const HAB_DRINKERS = new Set(["walk"]);

// Count down the little actions.
function habTimers(a, dt, awake) {
  for (const k of ["flee", "swoop", "shy", "chaseT"]) if (a[k] > 0) a[k] -= dt;
  if (a.chaseT <= 0) a.chase = null;
  if (!awake) a.toDrink = a.drinking = false;
}

// A few spots the animal could run to, the one farthest from x.
function habAwayFrom(a, x) {
  let best = habSpot(a);
  for (let i = 0; i < 5; i++) {
    const t = habSpot(a);
    if (Math.abs(t[0] - x) > Math.abs(best[0] - x)) best = t;
  }
  return best;
}

function habBolt(a, fromX) {
  if (a.dv || a.mode) return;
  [a.tx, a.ty] = habAwayFrom(a, fromX);
  a.flee = 1.6; a.pause = 0; a.toDrink = a.drinking = false; a.chase = null; a.chaseT = 0;
  a.jump = .35; a.react = { kind: "!", life: 1.2 };
}

// Tapped: each kind of animal answers in its own way.
function habReact(a) {
  if (hab.t < (a.tapCd || 0)) return;
  a.tapCd = hab.t + 1.5;
  const awake = habAwake(a, habPhase()), slug = a.s.slug, bird = a.s.category === "bird";
  const acts = (habAnimIdx && habAnimIdx.acts[slug]) || [];
  if (!awake) { a.shake = .25; return; }  // stirs in its sleep and dozes on
  if (a.dv || a.mode === "perched" || a.mode === "toPerch") {
    if (bird) a.react = { kind: HAB_SINGERS.test(slug) ? "note" : "?", life: 1.6 };
    return;
  }
  switch (a.role) {
    case "swim":
      if (a.leapIn !== undefined && a.mode !== "leap") { a.leapIn = 0; return; }  // dolphins and whales leap
      if (a.mode) return;
      a.flee = 1.5; a.pause = 0; [a.tx, a.ty] = habAwayFrom(a, a.x); return;
    case "paddle": case "float":
      a.jump = .35; habSplash(a.x, a.y - (a.role === "float" ? 6 : 4), 6);
      if (a.role === "paddle") { a.flee = 1.5; a.pause = 0; [a.tx, a.ty] = habAwayFrom(a, a.x); }
      return;
    case "reef": case "jelly": case "dangle": a.shy = 1.6; return;
    case "fly": case "soar": case "dive": case "skim":
      if (a.mode === "dive" || a.mode === "under" || a.mode === "rise") return;
      a.swoop = 1.2;
      if (HAB_SINGERS.test(slug)) a.react = { kind: "note", life: 1.6 };
      return;
    case "hover": case "flutter":
      a.flee = 1.2; a.pause = 0; [a.tx, a.ty] = habAwayFrom(a, a.x); return;
  }
  if (HAB_SHY.test(slug)) { a.shy = 1.6; a.pause = Math.max(a.pause, 2.5); a.rest = "idle"; return; }
  if (HAB_SKITTISH.test(slug) || a.role === "hop" || (bird && a.role !== "wade")) {
    habBolt(a, a.x - a.dir * 10);
    // It startles its skittish neighbours too.
    for (const o of hab.animals) {
      if (o !== a && HAB_LAND.has(o.role) && Math.abs(o.x - a.x) < 40 && Math.abs(o.y - a.y) < 24 && habAwake(o, habPhase())
          && (HAB_SKITTISH.test(o.s.slug) || o.s.category === "bird")) habBolt(o, a.x);
    }
    return;
  }
  // The rest stop and turn to look at you.
  a.pause = Math.max(a.pause, 3); a.toDrink = a.drinking = false;
  a.rest = acts.includes("look") ? "look" : "idle";
  a.react = { kind: "?", life: 1.6 };
}

// Every half second: the animals notice each other.
function habSocial(dt, phase) {
  if ((hab.socialIn = (hab.socialIn || 0) - dt) > 0) return;
  hab.socialIn = .5;
  const t = hab.t, up = hab.animals.filter((a) => habAwake(a, phase) && !a.dv);
  const ready = (a) => t >= (a.socialCd || 0);
  const free = (a) => HAB_LAND.has(a.role) && !a.mode && !(a.flee > 0) && !(a.chaseT > 0) && !a.drinking;
  // A hawk or eagle passing low overhead: small animals below freeze for a moment.
  for (const r of up) {
    if (!HAB_RAPTORS.test(r.s.slug) || !HAB_FLIERS.has(r.role) || r.mode === "perched") continue;
    for (const a of up) {
      if (a === r || !free(a) || !ready(a) || HAB_RAPTORS.test(a.s.slug) || habScale(a.s.slug) > .8) continue;
      if (Math.abs(a.x - r.x) > 26) continue;
      a.socialCd = t + 12;
      a.pause = Math.max(a.pause, 1.8); a.rest = "idle";
      a.react = { kind: "!", life: 1.2 };
    }
  }
  // A gull spots a diver with a fish and follows it.
  for (const d of up) {
    if (!(d.fish > 0) || d.role !== "dive" || d.mode !== "fly") continue;
    const g = up.find((o) => /gull/.test(o.s.slug) && o.role === "fly" && !o.mode && !o.chase && Math.abs(o.x - d.x) < 160);
    if (g) g.chase = d;
  }
  // Two playful animals that meet play chase; two others meeting stop to sniff.
  const land = up.filter((a) => free(a) && ready(a));
  for (let i = 0; i < land.length; i++) {
    for (let j = i + 1; j < land.length; j++) {
      const a = land[i], b = land[j];
      if (!ready(a) || !ready(b) || Math.abs(a.x - b.x) > 30 || Math.abs(a.y - b.y) > 14) continue;
      a.socialCd = b.socialCd = t + rnd(15, 25);
      if (Math.random() > .5) continue;
      if (HAB_PLAYFUL.test(a.s.slug) && HAB_PLAYFUL.test(b.s.slug) && a.s.category === "mammal" && b.s.category === "mammal") {
        const [c, r] = Math.random() < .5 ? [a, b] : [b, a];
        [r.tx, r.ty] = habAwayFrom(r, c.x); r.flee = 2.5; r.pause = 0;
        c.chase = r; c.chaseT = 3; c.pause = 0;
      } else if (a.s.category === "mammal" || b.s.category === "mammal") {
        for (const [m, n] of [[a, b], [b, a]]) { m.pause = Math.max(m.pause, rnd(1.5, 2.5)); m.rest = "idle"; m.dir = Math.sign(n.x - m.x) || 1; }
      }
    }
  }
}

// Drawn pose: [x, feet y, x scale, y scale, tilt] (the scales and tilt stay 1, 1, 0
// except for a bird perched far off, drawn smaller), with the arc of a hop or a bob.
function habPose(a, awake, roost) {
  // Only where the animal is: every bit of motion (wingbeats, hops, breathing, dives,
  // leaps) is a drawn frame of its sheet, never the picture stretched or turned.
  // (A bird perched up on the sea stack is drawn smaller, all over, as it's farther away.)
  if (roost) return roost;
  const visiting = habDecorPose(a, awake);
  if (visiting) return visiting;
  if (awake && a.mode === "perched") return [a.x, a.y, HAB_PERCH_SCALE, HAB_PERCH_SCALE, 0];
  let { x, y } = a;
  if (!awake) return [x, y, 1, 1, 0];
  const moving = a.pause <= 0;
  switch (a.role) {
    case "hop":
      if (moving) y -= Math.abs(Math.sin(a.odo / 18 * Math.PI)) * 9;  // the arc of each hop
      break;
    case "walk": case "shore": case "wade": case "beach":
      if (moving && !a.hasWalk) y -= Math.floor(a.odo / 3) % 2;  // no walk frames: a little bob
      break;
    case "fly": case "soar": y += Math.sin(a.phase * 3) * 2; break;
    case "dive": if (a.mode !== "dive" && a.mode !== "rise") y += Math.sin(a.phase * 3) * 2; break;
    case "skim": y += Math.sin(a.phase * 2) * .6; break;
    case "hover": y += Math.sin(a.phase * 5) * 1.5; break;
    case "flutter": y += Math.sin(a.phase * 9) * 3; x += Math.sin(a.phase * 2.3) * 2; break;
    case "swim": if (a.mode !== "leap") y += Math.sin(a.phase * 1.5) * 1.5; break;
    case "float": case "paddle": y += Math.sin(a.phase * 1.5) * 1.5; break;
    case "jelly": y += Math.sin(a.phase * .8) * 6; break;
  }
  // Shaking off the rain or shivering, and jumping at thunder (or a tap).
  if (a.shake > 0) x += Math.floor(a.shake * 28) % 2 ? 1 : -1;
  if (a.jump > 0) y -= Math.sin(a.jump / .35 * Math.PI) * 7;
  // Tapped: a flier swoops up in an arc.
  if (a.swoop > 0) y -= Math.sin((1 - a.swoop / 1.2) * Math.PI) * 14;
  return [x, y, 1, 1, 0];
}

// The "dive" row is drawn pitched from 55 degrees nose up (frame 0) to 75 nose down
// (the last frame), as tools/make_sprites.py DIVE_DEG; the frame for a tilt in radians
// (positive = nose down).
function habPitchFrame(tilt) {
  const n = habNF(), deg = tilt * 180 / Math.PI;
  return Math.max(0, Math.min(n - 1, Math.round((deg + 55) / 130 * (n - 1))));
}

// What a ground animal does while it stands still: just stand, sit up on its
// haunches (a bird settles down), turn its head to look at you, glance back over
// its shoulder, put its head down to graze, or groom (a dog scratches, a cat or
// squirrel washes, a bird or duck preens, a lizard does push-ups, a frog calls) --
// only the animals whose sheets draw that pose.
function habRestPose() {
  return ["idle", "idle", "sit", "look", "back", "eat", "eat", "groom", "groom"][Math.floor(Math.random() * 9)];
}

// Which pose of the animation sheet to show, and which of its frames:
// [pose, frame], or null when the species has no sheet.
function habAnim(a, awake, roost) {
  const acts = habAnimIdx && habAnimIdx.acts[a.s.slug];
  if (!acts) return null;
  const has = (k) => acts.includes(k);
  const cyc = habCyc;
  // Still, it breathes (one breath every ~3 s) and now and then blinks.
  const still = ["idle", habIdleFrame(a.phase * 4 / 3 + (a.x % 7) * .3, Math.round(a.x) & 1)];
  if (!awake) return ["sleep", cyc(a.phase * 1.2)];
  // Tapped: a reef animal or jelly pulls in and opens up again; a turtle or snail
  // tucks into its shell for a moment.
  if (a.shy > 0) {
    if (has("hide")) return ["hide", Math.min(habNF() - 1, Math.floor((1 - a.shy / 1.6) * habNF()))];
    if (HAB_SHY.test(a.s.slug)) return ["sleep", 0];
  }
  if (roost || habDecorAnim(a, awake)) return still;  // sheltering from the rain, or perched on a decoration
  if (a.mode === "perched") return still;
  if (a.mode === "toPerch") return has("fly") ? ["fly", cyc(a.phase * 9 / (2 * Math.PI) * 4)] : still;
  switch (a.role) {
    case "walk": case "shore": case "wade": case "beach": case "hop": {
      if (a.peck > 0 || (a.drinking && a.s.category === "bird")) return has("eat") ? ["eat", cyc(a.phase * 2.5)] : still;
      if (a.pause > 0 || !has("walk")) {
        const r = a.rest && has(a.rest) ? a.rest : "idle";
        // sitting up, it nibbles; standing, looking about, it breathes
        return r === "idle" ? still : [r, r === "sit" || r === "eat" || r === "groom" ? cyc(a.phase * 2.5) : habIdleFrame(a.phase * 4 / 3, 1)];
      }
      // bolting from you, or chasing: the gallop (or the bounding run)
      if ((a.flee > 0 || a.chaseT > 0) && has("run")) return ["run", cyc(a.odo / 6)];
      return ["walk", a.role === "hop" ? cyc((a.odo % 18) / 18 * 4) : cyc(a.odo / 3)];
    }
    case "fly": case "soar": case "dive": case "skim": case "hover": case "flutter": {
      if (!has("fly")) return still;
      // Plunging: drawn steeper and steeper, wings swept back. Climbing out: flapping hard.
      if (a.role === "dive" && a.mode === "dive") return has("dive") ? ["dive", habPitchFrame(a.tilt)] : ["fly", cyc(3)];
      if (a.role === "dive" && a.mode === "rise") return ["fly", cyc(a.phase * 16 / (2 * Math.PI) * 4)];
      const glider = HAB_GLIDERS.test(a.s.slug);
      if (glider && Math.sin(a.phase * .7 + a.x * .01) < .1) return ["fly", 0];  // gliding, wings level
      const rate = { hover: 24, flutter: 10, skim: 5 }[a.role] || (glider ? 6 : 12);
      return ["fly", cyc(a.phase * rate / (2 * Math.PI) * 4)];
    }
    case "swim": case "paddle": case "float": case "jelly":
      // A dolphin or whale leaping: drawn nose up as it leaves the water, nose down coming back.
      if (a.mode === "leap" && has("dive")) return ["dive", habPitchFrame(a.tilt)];
      return has("swim") ? ["swim", cyc(a.phase * (a.role === "jelly" ? 1 : 2.5))] : still;
  }
  return still;
}

function habDraw() {
  const cv = $("hab-canvas");
  if (!hab.L || !cv) return;
  const L = hab.L, phase = habPhase(), lights = habLights(L, phase);
  habDecorPlace();
  // The sun and moon creep across the sky, so the scenery is redrawn every few pixels they move.
  const spot = (b) => (b ? b.xy.map((v) => v >> 2).join(",") + (b.lit ? "/" + Math.round(b.lit * 40) : "") : "-");
  const key = `${L.w}/${phase}/${habState()}/${habSeason()}/${spot(lights.sun)}/${spot(lights.moon)}`;
  if (cv.width !== L.w * HAB_RES) { cv.width = L.w * HAB_RES; cv.height = HAB_H * HAB_RES; }
  if (hab.bgKey !== key) { hab.bg = habBackground(L, phase, habState(), lights); hab.bgKey = key; }
  const c = cv.getContext("2d");
  c.setTransform(HAB_RES, 0, 0, HAB_RES, 0, 0);
  c.imageSmoothingEnabled = false;
  c.drawImage(hab.bg, 0, 0);
  habWxShade(c, L, phase);
  habAmbient(c, L, phase);
  const roosting = { n: 0 };
  const poses = hab.animals.map((a) => {
    const awake = habAwake(a, phase);
    const roost = habRestSpot(a, awake, roosting);
    let [x, y, sx = 1, sy = 1, tilt = 0] = habPose(a, awake, roost);
    const anim = habAnim(a, awake, roost);
    a.hasWalk = !!anim && (habAnimIdx.acts[a.s.slug] || []).includes("walk");
    const perched = awake && a.mode === "perched";
    // Landed on a decoration: drawn with it, not in the sky (unless it's the balloon).
    const landed = habDecorLanded(a) && a.dv.d.it.area !== "sky";
    return { a, awake, phase, anim, roost: !!roost || perched, x: habSnap(x), y: habSnap(y), sx, sy, tilt,
             sky: awake && HAB_FLIERS.has(a.role) && !perched && !roost && !landed,
             hidden: awake && a.mode === "under" || habDecorHidden(a, awake), z: habDecorZ(a, Math.round(y)) };
  });
  const sea = poses.filter((p) => HAB_SEA.has(p.a.role) && !p.sky).sort((p, q) => p.y - q.y);
  // The meadow's animals and decorations, back to front.
  const land = [...poses.filter((p) => !HAB_SEA.has(p.a.role) && !p.sky), ...habDecorDepth()].sort((p, q) => p.z - q.z);
  const sky = poses.filter((p) => p.sky);
  sea.forEach((p) => habSprite(c, p));
  // Seawater over everything in the sea.
  c.fillStyle = { day: "rgba(40,140,210,.31)", dawn: "rgba(80,100,180,.31)", dusk: "rgba(80,80,160,.31)",
                  night: "rgba(20,40,100,.35)" }[phase];
  c.fillRect(L.sea, L.water + 3, L.w - L.sea, HAB_H);
  habDecorDrawArea(c, phase, "sea");
  land.forEach((p) => (p.decor ? habDecorSprite(c, p.decor, phase) : habSprite(c, p)));
  habDecorDrawArea(c, phase, "sky");
  sky.forEach((p) => habSprite(c, p));
  habFx(c, phase);
  habDecorFx(c, phase);
  habWxDraw(c, L, phase, poses);
  habReactDraw(c, poses);
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

// One frame of an animation sheet on its own little canvas. Tilting or squashing a
// frame cut straight out of the sheet picks up stray pixels from the frame next
// to it (dark specks around the animal).
const habFrameCache = new WeakMap();
// Skins and decorations bought with minigame coins (app/games.py). Skins only show in
// the minigames (kuro: animals keep their real colours everywhere else); decorations go
// in your own habitat, not a friend's (decor.js). minigames.js and habitat.html call habLookSet().
let habLook = { skins: {}, decor: [] };
function habLookSet(look) {
  habLook = { skins: (look && look.skins) || {}, decor: (look && look.decor) || [] };
  hab.decorKey = "";  // decor.js places them again
}
const habMine = () => !hab.visit;
// Each skin recolours the animal by brightness, keeping the darkest outline pixels.
const HAB_SKINS = {
  frosty: (l) => [l * .7 + 60, l * .85 + 65, l * .9 + 90],
  rose: (l) => [l * .9 + 80, l * .55 + 40, l * .65 + 65],
  midnight: (l) => [l * .45 + 30, l * .4 + 30, l * .8 + 70],
  golden: (l) => [l * 1.05 + 70, l * .85 + 45, l * .3 + 10],
};
const habSkinCache = new Map();
function habSkin(img, skin) {
  const fn = HAB_SKINS[skin];
  if (!fn || !img || !img.complete || !img.naturalWidth) return img;
  const key = `${img.src}~${skin}`;
  if (!habSkinCache.has(key)) {
    const cv = document.createElement("canvas");
    cv.width = img.naturalWidth; cv.height = img.naturalHeight;
    const c = cv.getContext("2d");
    c.drawImage(img, 0, 0);
    const id = c.getImageData(0, 0, cv.width, cv.height), d = id.data;
    for (let i = 0; i < d.length; i += 4) {
      if (!d[i + 3]) continue;
      const l = d[i] * .3 + d[i + 1] * .59 + d[i + 2] * .11;
      if (l < 36) continue;
      const [r, g, b] = fn(l);
      d[i] = Math.min(255, r); d[i + 1] = Math.min(255, g); d[i + 2] = Math.min(255, b);
    }
    c.putImageData(id, 0, 0);
    cv.naturalWidth = cv.width; cv.naturalHeight = cv.height; cv.complete = true; cv.src = key;
    habSkinCache.set(key, cv);
  }
  return habSkinCache.get(key);
}

function habFrame(sheet, row, frame, F) {
  let frames = habFrameCache.get(sheet);
  if (!frames) habFrameCache.set(sheet, frames = {});
  const key = `${row}/${frame}`;
  if (!frames[key]) {
    const cv = document.createElement("canvas");
    cv.width = F; cv.height = F;
    cv.getContext("2d").drawImage(sheet, frame * F, row * F, F, F, 0, 0, F, F);
    frames[key] = cv;
  }
  return frames[key];
}

// Where a fish goes on a flying frame: the bill tip (the frontmost drawn
// pixel), or the talons (the lowest one) for an osprey. Cached per frame.
function habCatchSpot(fr, talons) {
  const k = talons ? "_talon" : "_tip";
  if (fr[k] === undefined) {
    fr[k] = null;
    try {
      const w = fr.width, h = fr.height, d = fr.getContext("2d").getImageData(0, 0, w, h).data;
      if (talons) {
        for (let y = h - 1; y >= 0 && !fr[k]; y--) for (let x = 0; x < w; x++) if (d[(y * w + x) * 4 + 3] > 128) { fr[k] = [x, y]; break; }
      } else {
        for (let x = 0; x < w && !fr[k]; x++) for (let y = 0; y < h; y++) if (d[(y * w + x) * 4 + 3] > 128) { fr[k] = [x, y]; break; }
      }
    } catch (e) { /* unreadable canvas: no fish drawn */ }
  }
  return fr[k];
}

// A small silver fish held in the bill (or an osprey's talons). Drawn in the
// sprite's own (left-facing) space so it turns and tilts with the bird.
function habFish(c, fr, F, FP, mid, talons) {
  const at = habCatchSpot(fr, talons);
  if (!at) return;
  const u = F / FP, x = Math.round(-F / 2 + at[0] * u) + (talons ? 0 : 1), y = Math.round(mid - F + at[1] * u);
  // Hangs head-up from the bill tip (or talons), tail flapping below.
  const flap = Math.sin(performance.now() / 90) > 0 ? 1 : -1;
  c.fillStyle = "#3d4a52"; c.fillRect(x - 1, y, 4, 7); c.fillRect(x - 1 + flap, y + 7, 4, 2);
  c.fillStyle = "#8fa3ae"; c.fillRect(x, y + 1, 1, 5);
  c.fillStyle = "#d9e4ea"; c.fillRect(x + 1, y + 1, 1, 5);
  c.fillStyle = "#1b2226"; c.fillRect(x + 1, y + 1, 1, 1);
}

function habSprite(c, p) {
  const raw = habImgs[p.a.s.slug];
  if (!raw || !raw.complete || !raw.naturalWidth) return;
  const { a, x, y } = p, sheet = habSheets[a.s.slug];
  const framed = p.anim && sheet && sheet.complete && sheet.naturalWidth;
  const img = framed ? habTinted(sheet, `${a.s.slug}@anim`, p.phase) : habTinted(raw, a.s.slug, p.phase);
  // Drawn 40 units square (a 32-unit drawing with room for wings, tails and antlers)
  // whatever the image's resolution, feet on its bottom row; FP is the frame in pixels.
  const F = HAB_UNIT, FP = framed ? sheet.naturalWidth / habAnimIdx.frames : raw.naturalWidth;
  // Fliers and swimmers turn and squash around their middle, the rest around
  // their feet.
  const mid = p.sky || a.role === "swim" || a.role === "jelly" ? 16 : 0;
  // Small animals still get a fingertip-sized box to tap.
  const k = habScale(a.s.slug), side = Math.max(F * k, 16), top = y - mid + (mid - F) * k;
  p.box = [x - side / 2, top, x + side / 2, top + side];
  if (p.hidden) return;
  if (!p.sky && !p.roost && !HAB_NO_SHADOW.has(a.role)) {
    const gy = a.role === "hop" && p.awake ? Math.round(a.y) : y;
    const sw = (n) => Math.max(2, Math.round(n * k));
    c.fillStyle = "rgba(20,32,10,.25)";
    c.fillRect(x - sw(7), gy - 1, sw(7) * 2, 1); c.fillRect(x - sw(9), gy, sw(9) * 2, 1); c.fillRect(x - sw(6), gy + 1, sw(6) * 2, 1);
  }
  if (a.role === "wade" && p.awake) {
    c.fillStyle = "rgba(225,245,255,.6)";
    c.fillRect(x - 10, y - 1, 5, 1); c.fillRect(x + 5, y - 1, 5, 1);
  }
  c.save();
  if (a.role === "paddle") { c.beginPath(); c.rect(0, 0, hab.L.w, y - Math.round(8 * k)); c.clip(); }
  // A diving bird disappears into the water as it goes in.
  if (a.role === "dive" && p.awake && a.mode === "dive") { c.beginPath(); c.rect(0, 0, hab.L.w, habPool(a)[2] + 1); c.clip(); }
  if (a.role === "dangle" && !a.dv) {
    c.fillStyle = "rgba(255,255,255,.7)";
    c.fillRect(x, 104, 1, y - 104 - Math.round(26 * k));
  }
  if (!p.awake && !framed) c.globalAlpha = .85;
  // Sprites face left; mirror the ones heading right.
  c.translate(x, y - mid);
  if (k !== 1) c.scale(k, k);
  if (a.dir > 0 && a.role !== "reef") c.scale(-1, 1);
  if (p.sx !== 1 || p.sy !== 1) c.scale(p.sx, p.sy);
  if (framed) c.drawImage(habFrame(img, habAnimIdx.rows.indexOf(p.anim[0]), p.anim[1], FP), -F / 2, mid - F, F, F);
  else c.drawImage(img, -F / 2, mid - F, F, F);
  if (framed && p.awake && a.role === "dive" && a.fish > 0 && (a.mode === "fly" || a.mode === "rise"))
    habFish(c, habFrame(img, habAnimIdx.rows.indexOf(p.anim[0]), p.anim[1], FP), F, FP, mid, /osprey/.test(a.s.slug));
  c.restore();
  if (a.role === "paddle") {
    c.fillStyle = "rgba(255,255,255,.55)";
    c.fillRect(x - 12, y - 8, 4, 1); c.fillRect(x + 6, y - 8, 5, 1);
  }
}

// Splash drops, ripple rings, skimmer wakes and frosty breath.
function habFx(c, phase) {
  const light = phase === "night" ? "rgba(200,220,255," : "rgba(240,250,255,";
  for (const f of hab.fx) {
    const a = Math.max(0, Math.min(1, f.life * 1.4));
    if (f.kind === "drop") {
      c.fillStyle = light + a + ")"; c.fillRect(Math.round(f.x), Math.round(f.y), 2, 2);
    } else if (f.kind === "dot") {
      c.fillStyle = light + a * .8 + ")"; c.fillRect(Math.round(f.x) - 1, Math.round(f.y), 3, 1);
    } else if (f.kind === "puff") {
      // A frosty breath.
      const n = Math.round(2 + (1.2 - f.life) * 3);
      c.fillStyle = light + (a * .6).toFixed(2) + ")"; c.fillRect(Math.round(f.x) - (n >> 1), Math.round(f.y) - (n >> 1), n, n);
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
    else if (f.kind === "puff") { f.x += f.vx * dt; f.y -= 5 * dt; }
  }
  hab.fx = hab.fx.filter((f) => f.life > 0);
}

function habBubble(poses) {
  const b = $("hab-bubble");
  const p = hab.picked && performance.now() < hab.pickedUntil && poses.find((q) => q.a === hab.picked);
  if (!p) { b.classList.add("hidden"); if (hab.picked && !p) hab.picked = null; return; }
  const cw = $("hab-canvas").clientWidth, scale = cw / hab.L.w;
  b.classList.remove("hidden");
  const half = Math.min(b.offsetWidth / 2, cw / 2);
  b.style.left = `${Math.min(Math.max(p.x * scale, half), cw - half)}px`;
  // Above the animal, or below it when there's no room (a bird high in the sky).
  const above = (p.y - 34) * scale >= b.offsetHeight;
  b.classList.toggle("below", !above);
  b.style.top = `${(above ? p.y - 34 : p.y + 4) * scale}px`;
}

// Fun facts per species number, fetched once from the page's animalFacts().
const habFactCache = {};
function habFacts(a) {
  const n = a.s.number;
  if (habFactCache[n] === undefined) {
    habFactCache[n] = [];
    if (typeof animalFacts === "function") {
      Promise.resolve(animalFacts(a.s)).then((list) => {
        habFactCache[n] = (list || []).filter(Boolean);
        if (hab.picked === a) habSay(a);
      }).catch(() => {});
    }
  }
  return habFactCache[n];
}

// The tapped animal's speech bubble: its name (and mood), then a fun fact.
function habSay(a) {
  const b = $("hab-bubble");
  const awake = habAwake(a, habPhase());
  const mood = habWxMood(a, awake);
  const facts = habFacts(a);
  b.innerHTML = "";
  const name = document.createElement("div");
  name.className = "hab-name";
  name.textContent = a.s.common_name + (mood ? ` · ${mood}` : awake ? "" : " · asleep");
  b.append(name);
  if (facts.length) {
    const fact = document.createElement("div");
    fact.className = "hab-fact";
    fact.textContent = facts[hab.factIdx % facts.length];
    b.append(fact);
  }
  if (!hab.visit?.showcase) {
    const more = document.createElement("div");
    more.className = "hab-more";
    if (facts.length > 1) more.append(document.createTextNode("Tap again for another fact · "));
    const link = document.createElement("a");
    link.href = "#";
    link.textContent = "Field Guide ›";
    link.onclick = (ev) => { ev.preventDefault(); ev.stopPropagation(); habOpen(a); };
    more.append(link);
    b.append(more);
  }
  b.classList.toggle("wide", facts.length > 0);
  // Long enough to read the fact.
  hab.pickedUntil = performance.now() + (facts.length ? 9000 : 4000);
  if (habStill) habDraw();
}

function habOpen(a) {
  hab.picked = null;
  if (hab.visit) openDex(a.s.number, a.num, caughtNums.has(a.s.number), hab.visit.state);
  else openDex(a.s.number, dexNumbers[a.s.number], true);
  habDraw();
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
    // Again: the next fact, or (with no facts to tell) its Field Guide page.
    if (habFacts(h.a).length > 1) { hab.factIdx++; habSay(h.a); }
    else if (!habFacts(h.a).length && !hab.visit?.showcase) habOpen(h.a);
    return;
  }
  hab.picked = h.a;
  habReact(h.a);
  // A different fact first each time you come back to it.
  hab.factIdx = Math.floor(Math.random() * 3);
  habSay(h.a);
}

// Show a friend's animals (their Field Guide entries) in their state's scenery,
// inside `slot` on their profile.
function habVisit(username, state, entries, slot) {
  if (!hab.visit) hab.visit = { home: hab.entries || hab.animals.map((a) => ({ caught: true, species: a.s, activity: a.activity })) };
  Object.assign(hab.visit, { username, state });
  slot.append($("habitat"), $("hab-bar"));
  hab.animals = []; hab.w = 0; hab.picked = null; hab.fx = [];
  habitatSet(entries);
}

// Back to your own scene, in its place on the Capture tab.
function habLeave() {
  if (!hab.visit) return;
  const home = hab.visit.home;
  hab.visit = null;
  $("hab-home").append($("habitat"), $("hab-bar"));
  hab.animals = []; hab.w = 0; hab.picked = null; hab.fx = [];
  habitatSet(home);
}

// Before you log in: your state's scenery with one featured animal, as a taste of
// the game (the login page and the app's account screen). Harmless animals only.
const HAB_SHOWCASE = {
  CA: { slug: "annas_hummingbird", common_name: "Anna's Hummingbird", category: "bird", rarity: "common" },
  NC: { slug: "northern_cardinal", common_name: "Northern Cardinal", category: "bird", rarity: "common" },
  TX: { slug: "northern_mockingbird", common_name: "Northern Mockingbird", category: "bird", rarity: "common" },
  FL: { slug: "roseate_spoonbill", common_name: "Roseate Spoonbill", category: "bird", rarity: "uncommon" },
  NY: { slug: "black_capped_chickadee", common_name: "Black-capped Chickadee", category: "bird", rarity: "common" },
  VA: { slug: "northern_cardinal", common_name: "Northern Cardinal", category: "bird", rarity: "common" },
  NJ: { slug: "american_goldfinch", common_name: "American Goldfinch", category: "bird", rarity: "common" },
  MI: { slug: "american_robin", common_name: "American Robin", category: "bird", rarity: "common" },
  GA: { slug: "brown_thrasher", common_name: "Brown Thrasher", category: "bird", rarity: "common" },
  OH: { slug: "northern_cardinal", common_name: "Northern Cardinal", category: "bird", rarity: "common" },
  IL: { slug: "northern_cardinal", common_name: "Northern Cardinal", category: "bird", rarity: "common" },
  PA: { slug: "eastern_bluebird", common_name: "Eastern Bluebird", category: "bird", rarity: "common" },
  // States without their own pick yet: a robin, found in every state.
  default: { slug: "american_robin", common_name: "American Robin", category: "bird", rarity: "common" },
};
function habShowcase(state, slot) {
  const s = HAB_SHOWCASE[state] || HAB_SHOWCASE.default;
  if (slot && $("habitat").parentElement !== slot) slot.append($("habitat"));
  if (!hab.visit || !hab.visit.showcase || hab.visit.state !== state) {
    hab.visit = { showcase: true, state, home: [] };
    hab.animals = []; hab.w = 0; hab.picked = null; hab.fx = [];
  }
  const fresh = !hab.animals.length;
  habitatSet([{ caught: true, activity: "any", species: { number: 0, ...s } }]);
  // Start it in plain view instead of flying in from off the edge.
  if (fresh && hab.animals[0]) hab.animals[0].x = rnd(hab.L.w * .3, hab.L.w * .6);
}

function habLoop(now) {
  requestAnimationFrame(habLoop);
  const box = $("habitat");
  if (document.hidden || !box || box.closest(".off") || box.closest(".hidden")) { hab.last = 0; return; }
  const w = box.clientWidth < 520 ? 320 : 480;
  // A new size, or the next turn of animals coming out (see habOutNow).
  if (!hab.L || w !== hab.w || (hab.total > hab.animals.length && habTurn() !== hab.turn))
    habitatSet(hab.entries || hab.animals.map((a) => ({ caught: true, species: a.s, activity: a.activity, num: a.num })));
  const dt = hab.last ? Math.min((now - hab.last) / 1000, .1) : 0;
  hab.last = now;
  const phase = habPhase();
  hab.t += dt;
  habWeather();
  habDecorTick(dt);
  hab.animals.forEach((a) => habStep(a, dt, habAwake(a, phase)));
  habSocial(dt, phase);
  habFxStep(dt);
  habWxStep(dt);
  habDraw();
}

// ---- Weather: the real sky outside right now (GET /weather/{state}, from the
// National Weather Service, or MET Norway in Europe) as clouds, rain, snow, fog,
// wind and thunderstorms.
// The animals react: small fliers wait out the rain in the tree, ducks and frogs
// love it, the others shake it off or shiver, reptiles, amphibians and bugs stay
// tucked in when it's cold, and everyone jumps at thunder. Add ?weather=rain,windy
// (or storm, snow, fog, cloudy, clear; breezy; cold) to the page's URL to preview.
const HAB_GREY = new Set(["cloudy", "rain", "storm", "snow"]);
const HAB_LAND = new Set(["walk", "hop", "shore", "wade", "beach"]);
const HAB_WX_ICON = { clear: "☀️", partly: "⛅", cloudy: "☁️", fog: "🌫️", rain: "🌧️", storm: "⛈️", snow: "🌨️" };
const HAB_WX_WORDS = { clear: "Clear skies", partly: "Some clouds", cloudy: "Cloudy", fog: "Foggy", rain: "Raining",
                       storm: "Thunderstorms", snow: "Snowing" };
const habWxTest = (() => { try { return new URLSearchParams(location.search).get("weather"); } catch { return null; } })();
Object.assign(hab, { wx: null, wxKey: "", wxAt: 0, drops: [], gusts: [], flash: 0, bolt: null, boltIn: 5 });

// Fetches the weather for the scene's state, again every 15 minutes.
function habWeather() {
  if (habWxTest) {
    if (!hab.wx) {
      const w = habWxTest.split(",");
      hab.wx = { sky: w.find((k) => k in HAB_WX_ICON) || "clear", wind: w.find((k) => k === "breezy" || k === "windy") || "calm",
                 wind_from: 270, temp_f: w.includes("cold") ? 30 : 60, text: "Preview", place: null };
      habNote();
    }
    return;
  }
  const state = habRealState(), now = Date.now();
  if (state === hab.wxKey && now - hab.wxAt < 15 * 60e3) return;
  if (state !== hab.wxKey) { hab.wx = null; hab.drops = []; }
  hab.wxKey = state; hab.wxAt = now;
  // Your own scene uses roughly where you are (to about 10 km) when you've let
  // the page know; a friend's uses their state's big city. In the Android app
  // the app adds your rough position itself (here=1).
  const own = !hab.visit;
  habWxSpot(own).then((pos) => {
    const q = pos ? `?lat=${pos.lat.toFixed(1)}&lon=${pos.lon.toFixed(1)}` : own ? "?here=1" : "";
    return fetch(`/weather/${state}${q}`).then((r) => (r.ok ? r.json() : null)).then((w) => [w, pos]);
  }).catch(() => [null, null]).then(([w, pos]) => {
    if (hab.wxKey !== state) return;
    hab.wx = w && w.sky ? w : null;
    // The sun and moon use your spot too, once the weather says it's in this state.
    hab.here = w && w.near && pos ? { state, lat: +pos.lat.toFixed(1), lon: +pos.lon.toFixed(1) } : null;
    hab.drops = [];
    habNote();
    if (habStill) habDraw();
  });
}

// Your position for the weather: known already, or the browser has said yes before.
// Otherwise null, and the scene offers a "📍 My weather" button instead of asking
// out of the blue.
async function habWxSpot(own) {
  hab.wxAsk = false;
  if (!own || typeof myPosition === "undefined" || !navigator.geolocation) return null;
  if (typeof feedPos !== "undefined" && feedPos) return feedPos;
  let st = "prompt";
  try { st = (await navigator.permissions.query({ name: "geolocation" })).state; } catch {}
  if (st === "granted") return myPosition();
  hab.wxAsk = st !== "denied";
  return null;
}
function habWxHere() {
  myPosition().then((pos) => { if (pos) { hab.wxKey = null; habWeather(); } });
}

// The wind across the scene in px/s, + to the right (a west wind).
function habGust() {
  const w = hab.wx;
  if (!w || w.wind === "calm") return 0;
  const k = w.wind === "windy" ? 14 : 7;
  return w.wind_from == null || -Math.sin(w.wind_from * Math.PI / 180) >= 0 ? k : -k;
}
const habCold = () => !!hab.wx && (hab.wx.sky === "snow" || (hab.wx.temp_f != null && hab.wx.temp_f < 45));
const habWet = () => !!hab.wx && (hab.wx.sky === "rain" || hab.wx.sky === "storm");
const habColdBlooded = (a) => /reptile|amphibian|invertebrate|insect/.test(a.s.category) && !HAB_SEA.has(a.role);
const habTuckedIn = (a) => habColdBlooded(a) && (habCold() || habHibernating());
const habSheltering = (a) => habWet() && ["fly", "flutter", "hover", "soar"].includes(a.role) && !HAB_SEABIRDS.test(a.s.slug);
const habLovesRain = (a) => a.s.category === "amphibian" || a.role === "paddle" || /duck|goose|swan|mallard|gallinule|coot/.test(a.s.slug);

// ---- Seasons: the scene follows the real time of year by itself. Spring brings
// more flowers, fall turns the leaves and drops them on the meadow, and winter
// browns the grass, bares the leafy trees and (in states with real winters)
// lays snow, while the reptiles, amphibians and insects hibernate.
// Preview with ?season=fall.
const HAB_SEASONS = ["winter", "winter", "spring", "spring", "spring", "summer", "summer", "summer", "fall", "fall", "fall", "winter"];
const HAB_SEASON_ICON = { spring: "🌸", summer: "☀️", fall: "🍂", winter: "❄️" };
// States where winter is mild: no snow on the ground, and the animals stay up.
const HAB_MILD_WINTER = new Set(["CA", "FL", "HI", "TX", "AZ", "LA", "MS", "AL", "GA", "SC", "NC"]);
const habSeasonTest = (() => { try { return new URLSearchParams(location.search).get("season"); } catch { return null; } })();
function habSeason() {
  return HAB_SEASONS.includes(habSeasonTest) ? habSeasonTest : HAB_SEASONS[new Date().getMonth()];
}
const habSnowy = (state = habState()) => habSeason() === "winter" && !HAB_MILD_WINTER.has(state);
const habHibernating = () => habSnowy();
const hexMix = (a, b, k) => "#" + hexRgb(a).map((v, i) => Math.round(v + (hexRgb(b)[i] - v) * k).toString(16).padStart(2, "0")).join("");

// A state's scene for the season: colors, how many flowers, what the leafy
// trees are doing (green, fall or bare) and whether there's snow.
function habSeasonScene(sc, season, state) {
  const mild = HAB_MILD_WINTER.has(state), tint = (cols, to, k) => cols.map((c) => hexMix(c, to, k));
  const out = { ...sc, leaves: "green", flowerCount: 26, snow: false };
  if (season === "spring") {
    out.flowerCount = 44;
    out.flowers = [...sc.flowers, ["#f6b8cf", "#ffffff"]];
  } else if (season === "fall") {
    const k = mild ? .12 : .28;
    out.leaves = "fall";
    out.meadow = tint(sc.meadow, "#c8a040", k);
    out.far = tint(sc.far, "#c87a30", k * .8);
    out.near = tint(sc.near, "#c87a30", k);
    out.flowerCount = 14;
    out.flowers = [["#9a6ad8", "#ffd84d"], ["#ffd23a", "#c8641e"]];  // asters and goldenrod
  } else if (season === "winter") {
    out.leaves = mild ? "green" : "bare";
    out.meadow = tint(sc.meadow, "#b8a070", mild ? .22 : .5);
    out.far = tint(sc.far, "#8a8070", mild ? .1 : .35);
    out.near = tint(sc.near, "#8a8070", mild ? .12 : .4);
    out.flowerCount = mild ? 8 : 0;
    out.snow = !mild;
  }
  return out;
}

// "🌧️ Raining in Houston, 61°F." for the line under the scene.
function habWxLine() {
  const w = hab.wx;
  let line = HAB_WX_WORDS[w.sky];
  if (w.wind === "windy") line += " and windy";
  if (w.place) line += ` ${w.near ? "near" : "in"} ${w.place}`;
  // Europe's (MET Norway, which asks to be credited) is in °C.
  if (w.temp_c != null) return line + `, ${w.temp_c}°C. Weather: MET Norway.`;
  if (w.temp_f != null) line += `, ${w.temp_f}°F`;
  return line + ".";
}

// What a tapped animal is up to in this weather, or null.
function habWxMood(a, awake) {
  if (!hab.wx) return null;
  if (habTuckedIn(a)) return habCold() ? "tucked in from the cold" : "hibernating till spring";
  if (!awake) return null;
  if (habSheltering(a)) return "staying dry";
  if (habWet() && habLovesRain(a)) return "loves the rain";
  if (hab.wx.sky === "snow") return "out in the snow";
  if (hab.wx.wind === "windy" && HAB_FLIERS.has(a.role)) return "riding the wind";
  return null;
}

// Every few seconds an animal reacts to the weather.
function habWxReact(a, dt, awake) {
  if (a.react && (a.react.life -= dt) <= 0) a.react = null;
  if (a.shake > 0) a.shake -= dt;
  if (a.jump > 0) a.jump -= dt;
  if (!hab.wx || !awake || habSheltering(a)) return;
  const gust = habGust();
  if (gust && (a.role === "fly" || a.role === "flutter")) a.x += gust * (a.role === "flutter" ? .5 : 1) * dt;
  if ((a.wxIn = (a.wxIn ?? rnd(2, 8)) - dt) > 0) return;
  a.wxIn = rnd(6, 14);
  if (habWet() && habLovesRain(a)) { a.react = { kind: "note", life: 1.6 }; return; }
  if (!HAB_LAND.has(a.role) || a.pause <= 0) return;
  const nose = a.x + (a.dir > 0 ? 12 : -12);
  if (habWet()) {
    a.shake = .5;
    for (let i = 0; i < 6; i++) {
      hab.fx.push({ kind: "drop", x: a.x + rnd(-6, 6), y: a.y - rnd(8, 18), vx: rnd(-45, 45), vy: rnd(-80, -30), life: .6 });
    }
  } else if (habCold()) {
    a.shake = .8;
    hab.fx.push({ kind: "puff", x: nose, y: a.y - 16, vx: (a.dir > 0 ? 1 : -1) * 5, life: 1.2 });
  }
}

function habDrop(d, anywhere) {
  d.x = rnd(-20, hab.L.w + 20);
  d.floor = rnd(140, HAB_H);
  d.y = anywhere ? rnd(-10, d.floor) : rnd(-30, -4);
  d.v = d.snow ? rnd(14, 30) : rnd(230, 300);
  d.len = Math.floor(rnd(4, 8));
  d.ph = rnd(0, 6.3);
  d.big = Math.random() < .3;
  return d;
}
function habGustLine(gust, anywhere) {
  const L = hab.L;
  return { x: anywhere ? rnd(0, L.w) : gust < 0 ? L.w + 30 : -30, y: rnd(20, 240), len: Math.floor(rnd(14, 30)),
           v: rnd(150, 230), leaf: Math.random() < .4, col: pick("#7aa040", "#c8862a", "#a8b848") };
}
// Enough raindrops, snowflakes and gusts for the weather and the canvas width.
function habWxFill() {
  const w = hab.wx, L = hab.L, snow = !!w && w.sky === "snow";
  const n = w ? Math.round(({ rain: 70, storm: 120, snow: 90 }[w.sky] || 0) * L.w / 480) : 0;
  if (hab.drops.length && hab.drops[0].snow !== snow) hab.drops = [];
  while (hab.drops.length < n) hab.drops.push(habDrop({ snow }, true));
  hab.drops.length = Math.min(hab.drops.length, n);
  const g = !w || w.wind === "calm" ? 0 : w.wind === "windy" ? 8 : 3;
  while (hab.gusts.length < g) hab.gusts.push(habGustLine(habGust(), true));
  hab.gusts.length = Math.min(hab.gusts.length, g);
}

// Raindrops hitting water make rings; on land, a tiny splash.
function habSplashAt(x, y) {
  if (Math.random() > .25) return;
  const L = hab.L, p = L.pond, row = Math.min(HAB_H - 1, Math.round(y));
  const wet = (y > L.water + 2 && x > L.surf[row]) || ((x - p.x) / p.rx) ** 2 + ((y - p.y) / p.ry) ** 2 < 1;
  hab.fx.push(wet ? { kind: "ring", x, y, r: 1, life: .5 } : { kind: "dot", x, y, life: .25 });
}

function habWxStep(dt) {
  const w = hab.wx, L = hab.L;
  if (!L) return;
  habWxFill();
  if (!w) return;
  const gust = habGust();
  for (const d of hab.drops) {
    d.y += d.v * dt;
    d.x += (d.snow ? Math.sin(hab.t * 1.3 + d.ph) * 8 + gust * 1.5 : gust * 4) * dt;
    if (d.y >= d.floor) { if (!d.snow) habSplashAt(d.x, d.floor); habDrop(d, false); }
    if (d.x < -20) d.x += L.w + 40; else if (d.x > L.w + 20) d.x -= L.w + 40;
  }
  for (const g of hab.gusts) {
    g.x += (gust < 0 ? -1 : 1) * g.v * dt;
    if (g.x > L.w + 30 || g.x < -30) Object.assign(g, habGustLine(gust, false));
  }
  hab.flash = Math.max(0, hab.flash - dt * 2.2);
  // A gentle flash every so often in a thunderstorm (not with reduced motion).
  if (w.sky === "storm" && !habStill && (hab.boltIn -= dt) <= 0) {
    hab.boltIn = rnd(8, 18);
    hab.flash = .45;
    const pts = [];
    for (let x = rnd(L.w * .2, L.w * .85), y = 0, end = rnd(70, 110); y < end; y += rnd(5, 10), x += rnd(-6, 6)) pts.push([x, y]);
    hab.bolt = pts;
    const phase = habPhase();
    for (const a of hab.animals) {
      if (HAB_LAND.has(a.role) && habAwake(a, phase)) { a.jump = .35; a.react = { kind: "!", life: 1.2 }; }
    }
  }
}

// Under a heavy sky: the sky goes grey (hiding the sun), the land a little
// darker, and snow whitens the ground. Drawn before the clouds and animals.
function habWxShade(c, L, phase) {
  const w = hab.wx, sky = w && { cloudy: .5, rain: .65, storm: .75, snow: .55, fog: .45 }[w.sky];
  if (!sky) return;
  const pale = w.sky === "snow" || w.sky === "fog", night = phase === "night";
  const rgb = night ? (pale ? "70,78,100" : "26,30,44") : pale ? "200,206,214" : w.sky === "storm" ? "92,100,114" : "128,138,152";
  for (let y = 0; y < 160; y += 2) {
    c.fillStyle = `rgba(${rgb},${(sky * (1 - (y / 160) ** 2)).toFixed(3)})`;
    c.fillRect(0, y, L.w, 2);
  }
  const land = { cloudy: .08, rain: .16, storm: .24, snow: .2, fog: .14 }[w.sky];
  c.fillStyle = pale ? `rgba(235,240,248,${land})` : `rgba(50,60,80,${land})`;
  c.fillRect(0, 0, L.w, HAB_H);
}

const HAB_GLYPHS = { note: ["..###", "..#.#", "..#..", "###..", "###.."], "!": ["##", "##", "##", "..", "##"],
                     "?": [".##.", "#..#", "..#.", "....", "..#."] };
function habGlyph(c, kind, x, y) {
  const rows = HAB_GLYPHS[kind];
  const dots = (dx, dy) => rows.forEach((r, j) => [...r].forEach((ch, i) => ch === "#" && c.fillRect(x + i + dx, y + j + dy, 1, 1)));
  c.fillStyle = "#1c2a1c";
  [[-1, 0], [1, 0], [0, -1], [0, 1]].forEach(([dx, dy]) => dots(dx, dy));
  c.fillStyle = kind === "!" ? "#ff6a4a" : kind === "?" ? "#ffe27a" : "#ffffff";
  dots(0, 0);
}

// Fog, rain, snow, gusts and lightning in front of everything, and the animals'
// little reactions over their heads.
function habWxDraw(c, L, phase, poses) {
  const w = hab.wx;
  if (!w) return;
  if (!hab.drops.length) habWxFill();
  const night = phase === "night", t = hab.t, gust = habGust();
  if (w.sky === "fog") {
    for (let b = 0; b < 4; b++) {
      const y0 = 60 + b * 50, x0 = ((t * (3 + b) * (b % 2 ? 1 : -1)) % 64 + 64) % 64;
      for (let r = 0; r < 22; r++) {
        c.fillStyle = (night ? "rgba(150,160,185," : "rgba(235,240,245,") + (Math.sin(r / 22 * Math.PI) * .38).toFixed(3) + ")";
        for (let x = x0 - 64; x < L.w; x += 64) c.fillRect(Math.round(x + Math.sin(r * .7 + b) * 6), y0 + r, 48 + (r % 3) * 4, 1);
      }
    }
  }
  const rain = night ? "rgba(170,190,235,.5)" : "rgba(215,230,250,.65)";
  const snow = night ? "rgba(225,232,255,.85)" : "rgba(255,255,255,.95)";
  for (const d of hab.drops) {
    if (d.snow) { c.fillStyle = snow; const n = d.big ? 2 : 1;
      c.fillRect(Math.round(d.x), Math.round(d.y), n + 1, n); c.fillRect(Math.round(d.x) + (n > 1 ? 1 : 0), Math.round(d.y) - 1, 1, n + 2); continue; }
    c.fillStyle = rain;
    const sx = gust * 4 / d.v;
    for (let k = 0; k < d.len; k++) c.fillRect(Math.round(d.x - sx * k), Math.round(d.y) - k, 1, 1);
  }
  for (const g of hab.gusts) {
    const x = Math.round(g.x), y = Math.round(g.y + Math.sin(g.x * .05) * 3);
    if (g.leaf) {
      c.fillStyle = g.col;
      const flip = Math.floor(g.x / 6) % 2;
      c.fillRect(x, y, flip ? 2 : 3, flip ? 2 : 1);
    } else {
      c.fillStyle = night ? "rgba(200,215,255,.45)" : "rgba(255,255,255,.75)";
      c.fillRect(x, y, g.len, 1);
      c.fillRect(gust < 0 ? x - 3 : x + g.len, y - 1, 3, 1);
    }
  }
  if (hab.flash > 0) {
    if (hab.bolt && hab.flash > .25) {
      c.fillStyle = "#fffbe0";
      hab.bolt.forEach(([x, y], i) => {
        const [nx, ny] = hab.bolt[i + 1] || [x, y + 6];
        for (let k = 0; k <= 6; k++) c.fillRect(Math.round(x + (nx - x) * k / 6), Math.round(y + (ny - y) * k / 6), 2, 2);
      });
    }
    c.fillStyle = `rgba(255,255,255,${(hab.flash * .8).toFixed(2)})`;
    c.fillRect(0, 0, L.w, HAB_H);
  }
}

// The animals' little reactions over their heads: ! startled, ? curious, a note singing.
function habReactDraw(c, poses) {
  for (const p of poses) {
    const r = p.a.react;
    if (!r || p.hidden) continue;
    const k = 1 - r.life / (r.kind === "!" ? 1.2 : 1.6);
    c.globalAlpha = Math.min(1, r.life * 2);
    habGlyph(c, r.kind, p.x + 6, Math.round(p.y - 36 * habScale(p.a.s.slug) - k * 6));
    c.globalAlpha = 1;
  }
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
// pine, dogwood blossoms, dunes with sea oats and a striped lighthouse; Texas has
// flat-topped mesas over Hill Country, a live oak, bluebonnets and Indian
// paintbrush, prickly pear and a ranch windmill by the Gulf; Florida is flat
// sawgrass with cypress domes and cabbage palms, coreopsis, a palm for the
// roosting tree, a mangrove island offshore and a rocket on its launch pad; New
// York is fall color, with the Manhattan skyline beyond the hills, a sugar maple
// and the Statue of Liberty out in the harbor; Virginia has the Blue Ridge over
// Shenandoah's forests, flowering dogwood and Virginia bluebells, and Assateague
// Island offshore with its red-and-white lighthouse and wild ponies.
const HAB_SCENES = {
  CA: { far: ["#c99b48", "#dcb35e", "#ecc875", "#f7dc95"], near: ["#7d8a3c", "#97a24a", "#aeb65a", "#c6c977"],
        meadow: ["#5f9a3d", "#77b04a", "#8fc35a", "#a8d36d"], dots: "oak", tree: "oak",
        flowers: [["#ff7a1a", "#ffb347"], ["#ff7a1a", "#ffb347"], ["#ffcf3b", "#fff2a0"], ["#9a7cf0", "#d4c4ff"]] },
  NC: { far: ["#3f7a4a", "#4f8d55", "#62a061", "#79b473"], near: ["#2f6a3c", "#3d7d46", "#4f9150", "#64a55e"],
        meadow: ["#56943c", "#6aaa48", "#80bd57", "#98cf69"], dots: "forest", tree: "pine",
        flowers: [["#ffffff", "#f3e6b0"], ["#ffffff", "#f3e6b0"], ["#f6b8cf", "#ffffff"], ["#ffd84d", "#fff2a0"]] },
  TX: { far: ["#8f9550", "#a3a75b", "#b8b969", "#cccb7c"], near: ["#647f36", "#789341", "#8ca64d", "#a2b85e"],
        meadow: ["#678f38", "#7da344", "#92b652", "#a8c765"], dots: "oak", tree: "oak",
        flowers: [["#3a58d0", "#ffffff"], ["#3a58d0", "#ffffff"], ["#e4502c", "#ffa860"], ["#ffd84d", "#fff2a0"]] },
  FL: { far: ["#6f8f5a", "#7f9f63", "#90ae6e", "#a3bf7c"], near: ["#7a9a48", "#8eac52", "#a2bd5e", "#b8cd70"],
        meadow: ["#5f9a3d", "#76ae48", "#8cc156", "#a3d26a"], dots: "palm", tree: "palm", flat: true,
        flowers: [["#ffd23a", "#c8641e"], ["#ffd23a", "#c8641e"], ["#f27aa8", "#ffe0ec"], ["#b48cff", "#f0e8ff"]] },
  NY: { far: ["#9a7a52", "#b08a5a", "#c49c66", "#d6b078"], near: ["#7a7a3a", "#8e8a42", "#a49a4c", "#b8ac5a"],
        meadow: ["#5f9a3d", "#77b04a", "#8fc35a", "#a8d36d"], dots: "maple", tree: "maple",
        flowers: [["#9a6ad8", "#ffd84d"], ["#9a6ad8", "#ffd84d"], ["#ffd23a", "#c8641e"], ["#ffffff", "#ffe9a0"]] },
  VA: { far: ["#4a7f52", "#5a925c", "#6ca567", "#82b878"], near: ["#3a7442", "#4a874c", "#5c9a56", "#72ad66"],
        meadow: ["#5f9a3d", "#77b04a", "#8fc35a", "#a8d36d"], dots: "forest", tree: "round",
        flowers: [["#ffffff", "#f3e6b0"], ["#f6b8cf", "#ffffff"], ["#5a7ae0", "#f6b8cf"], ["#5a7ae0", "#c4d0ff"]] },
  NJ: { far: ["#5f8f56", "#70a160", "#84b46c", "#9cc67e"], near: ["#4c8442", "#5e984e", "#72aa5a", "#88bc6a"],
        meadow: ["#5f9a3d", "#77b04a", "#8fc35a", "#a8d36d"], dots: "round", tree: "oak",
        flowers: [["#7a5ad8", "#c4b4ff"], ["#7a5ad8", "#c4b4ff"], ["#ffffff", "#ffe9a0"], ["#ffd84d", "#fff2a0"]] },
  MI: { far: ["#3f7a4a", "#4f8d55", "#62a061", "#79b473"], near: ["#2f6a3c", "#3d7d46", "#4f9150", "#64a55e"],
        meadow: ["#5f9a3d", "#77b04a", "#8fc35a", "#a8d36d"], dots: "forest", tree: "pine",
        flowers: [["#f8b8c8", "#ffffff"], ["#ffffff", "#ffe9a0"], ["#ffd84d", "#fff2a0"], ["#9a6ad8", "#ffd84d"]] },
  GA: { far: ["#5a8a4e", "#6a9c58", "#7cae64", "#92c076"], near: ["#4a7e3c", "#5a9046", "#6ca252", "#82b462"],
        meadow: ["#5f9a3d", "#77b04a", "#8fc35a", "#a8d36d"], dots: "forest", tree: "oak",
        flowers: [["#ffffff", "#f3e6b0"], ["#f27aa8", "#ffc4dc"], ["#f27aa8", "#ffc4dc"], ["#ffb08a", "#ffe0d0"]] },
  OH: { far: ["#5f8f56", "#70a160", "#84b46c", "#9cc67e"], near: ["#4c8442", "#5e984e", "#72aa5a", "#88bc6a"],
        meadow: ["#5f9a3d", "#77b04a", "#8fc35a", "#a8d36d"], dots: "round", tree: "round",
        flowers: [["#d8283a", "#ff8a8a"], ["#d8283a", "#ff8a8a"], ["#ffffff", "#ffe9a0"], ["#ffd84d", "#fff2a0"]] },
  IL: { far: ["#7f9a52", "#91aa5c", "#a3ba68", "#b8cc7a"], near: ["#6a8e3c", "#7ea248", "#92b454", "#a8c664"],
        meadow: ["#6a9a3a", "#80ae46", "#96c054", "#acd068"], dots: "oak", tree: "oak", flat: true,
        flowers: [["#b45ab4", "#e8a0d8"], ["#b45ab4", "#e8a0d8"], ["#ffd23a", "#c8641e"], ["#ffffff", "#ffe9a0"]] },
  PA: { far: ["#4f7f5a", "#5f9262", "#71a56c", "#88b87e"], near: ["#3c7040", "#4c834a", "#5e9654", "#74aa66"],
        meadow: ["#5f9a3d", "#77b04a", "#8fc35a", "#a8d36d"], dots: "forest", tree: "oak",
        flowers: [["#f6c4d8", "#ffffff"], ["#f6c4d8", "#ffffff"], ["#ffffff", "#f8e0ea"], ["#ffd84d", "#fff2a0"]] },
  default: { far: ["#6f9e60", "#82b370", "#97c483", "#b0d69a"], near: ["#4f8d43", "#62a250", "#78b55e", "#90c771"],
             meadow: ["#5f9a3d", "#77b04a", "#8fc35a", "#a8d36d"], dots: "round", tree: "round",
             flowers: [["#ffffff", "#ffe9a0"], ["#ffd84d", "#fff2a0"], ["#f27aa8", "#ffc4dc"], ["#b48cff", "#e0d0ff"]] },
};
// The palettes the HAB_STATE_LAND states are drawn in.
const HAB_LOOKS = {
  forest: HAB_SCENES.NC, north: HAB_SCENES.MI, plains: HAB_SCENES.IL, coast: HAB_SCENES.NJ, maple: HAB_SCENES.NY,
  swamp: { ...HAB_SCENES.GA, dots: "forest", tree: "oak" },
  tropical: { ...HAB_SCENES.FL, flat: false },
  desert: { far: ["#b8946a", "#c8a476", "#d8b688", "#e6c89a"], near: ["#9a8a5a", "#ae9c66", "#c0ae74", "#d0c084"],
            meadow: ["#8a9a52", "#9eac5e", "#b2be6c", "#c4ce80"], dots: "round", tree: "oak",
            flowers: [["#ff7a1a", "#ffb347"], ["#ffd84d", "#fff2a0"], ["#e85a8a", "#ffc4dc"], ["#ffffff", "#ffe9a0"]] },
};
for (const [st, d] of Object.entries(HAB_STATE_LAND)) {
  const base = HAB_LOOKS[d.look];
  HAB_SCENES[st] = { ...base, saguaro: !!d.saguaro, flowers: [d.flower, d.flower, ...base.flowers.slice(2)] };
}
// Each state's own ground cover, hillside plants and big tree (2026-11-07): dry
// desert scrub, short-grass prairie, aspens, junipers...
const HAB_DRY = ["#9a9652", "#aeaa60", "#c2bc70", "#d4cc84"], HAB_PRAIRIE = ["#86963c", "#9aaa46", "#aebc54", "#c2cc66"];
const HAB_SAND = ["#b89a6a", "#c8aa78", "#d8bc8a", "#e6cc9c"], HAB_REDSAND = ["#a8603e", "#bc744c", "#d08a5e", "#e0a272"];
const HAB_SAGE = ["#8a8a6a", "#9c9c78", "#b0ae88", "#c2c09a"], HAB_GRASS = ["#9a9a4a", "#aeac56", "#c2bc66", "#d4cc7a"];
const HAB_SCENE_OVERRIDE = {
  AZ: { meadow: HAB_DRY, far: HAB_SAND, near: ["#a8925e", "#baa46c", "#ccb67e", "#dcc890"], dots: "sage", tree: "juniper", flat: true, saguaro: true },
  UT: { meadow: HAB_DRY, far: HAB_REDSAND, near: ["#9a5a3a", "#ae6c48", "#c28058", "#d4966a"], dots: "juniper", tree: "juniper", flat: true },
  NM: { meadow: HAB_DRY, far: HAB_SAND, near: ["#a08a5e", "#b49c6c", "#c6ae7c", "#d6c08e"], dots: "juniper", tree: "juniper", flat: true },
  NV: { meadow: HAB_DRY, far: HAB_SAGE, near: ["#7e7e62", "#909070", "#a4a280", "#b6b490"], dots: "sage", tree: "juniper", flat: true },
  WY: { meadow: HAB_PRAIRIE, far: HAB_SAGE, near: ["#7e8262", "#909470", "#a2a67e", "#b4b68e"], dots: "sage", tree: "cottonwood", flat: true },
  ND: { meadow: HAB_PRAIRIE, far: HAB_GRASS, near: ["#8a8c44", "#9c9e50", "#b0b05e", "#c2c070"], dots: "grass", tree: "cottonwood", flat: true },
  SD: { meadow: HAB_PRAIRIE, far: HAB_GRASS, near: ["#8a8c44", "#9c9e50", "#b0b05e", "#c2c070"], dots: "grass", tree: "cottonwood", flat: true },
  NE: { meadow: HAB_PRAIRIE, far: HAB_GRASS, near: ["#8a8c44", "#9c9e50", "#b0b05e", "#c2c070"], dots: "grass", tree: "cottonwood", flat: true },
  KS: { meadow: HAB_PRAIRIE, far: HAB_GRASS, near: ["#8a8c44", "#9c9e50", "#b0b05e", "#c2c070"], dots: "grass", tree: "cottonwood", flat: true },
  OK: { meadow: HAB_PRAIRIE, far: ["#a8704a", "#ba8258", "#cc966a", "#dcaa7e"], near: ["#8a7a44", "#9c8c50", "#b09e5e", "#c2b070"], dots: "grass", tree: "cottonwood", flat: true },
  CO: { dots: "forest", tree: "aspen" },
  MT: { dots: "forest", tree: "pine" },
  ID: { dots: "forest", tree: "pine" },
  VT: { dots: "forest", near: ["#3e6a2a", "#4e8034", "#629840", "#78ae4e"] },
};
for (const [st, o] of Object.entries(HAB_SCENE_OVERRIDE)) HAB_SCENES[st] = { ...(HAB_SCENES[st] || HAB_SCENES.default), ...o };


function habBackground(L, phase, state, lights = {}) {
  // Land is painted in daylight colors, then graded for the time of day at the end.
  const W = L.w, H = HAB_H, season = habSeason(), snowy = habSnowy(state);
  const sc = habSeasonScene(HAB_SCENES[state] || HAB_SCENES.default, season, state), P = pxPalette("day");
  const night = phase === "night", r = mulberry(7), land = habLand(state);
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
  }
  hab.glowX = -1;
  const { sun, moon } = lights;
  if (sun) {
    const [sx, sy] = sun.xy, low = sun.low, sr = low ? 15 : 11;
    hab.glowX = sx;
    halo(sx, sy, sr, sr + (low ? 40 : 26), hexRgb(low ? "#ffd08a" : "#fff6cc"), .75);
    disc(sx, sy, sr, (x, y, u, v) => put(x, y, hexRgb(Math.hypot(u - .3, v + .3) < .5 ? "#fffbe8" : low ? "#ffc867" : "#ffe98a")));
  }
  if (moon) {
    // The lit part ends at the terminator: an ellipse across the disc that sweeps
    // from the sunny edge (new moon) over to the far edge (full moon).
    const [mx, my] = moon.xy, c = Math.cos(moon.elong * Math.PI / 180);
    if (!moon.pale) {
      if (!sun) hab.glowX = mx;
      halo(mx, my, 10, 32, hexRgb("#8fa2e0"), .6 * Math.min(1, .25 + moon.lit));
    }
    const craters = [[-3, -2, 2], [3, 3, 1], [2, -5, 1], [-5, 4, 1]];
    disc(mx, my, 10, (x, y, u, v) => {
      const lit = u * moon.side > c * Math.sqrt(Math.max(0, 1 - v * v));
      const pit = craters.some(([dx, dy, rr]) => (x - mx - dx) ** 2 + (y - my - dy) ** 2 <= rr * rr + rr * .8);
      if (moon.pale) { if (lit) put(x, y, blend(get(x, y), [255, 255, 255], pit ? .4 : .6)); return; }
      const l = u * .5 - v * .6;
      // The dark part keeps a faint earthshine so the round shape still shows.
      put(x, y, lit ? hexRgb(pit ? "#cfc499" : l > .4 ? "#fffbe6" : l > -.3 ? "#f1ebc8" : "#d8cfa6") : blend(get(x, y), hexRgb("#4a5688"), .35));
    });
  }
  hab.stars = stars;
  // Far mountains, sloping down to the coast.
  // Inland states look across a lake or river instead of the sea, so their far
  // scenery runs the whole width (habWaterKind).
  const wk = habWaterKind(state), inland = wk !== "sea" && wk !== "great";
  const coastEnd = inland ? W + 110 : L.sea + 10;
  // Mountains and hills sink toward the coast instead of stopping in a wall.
  const env = (x, len) => { const k = clamp01((coastEnd - 14 - x) / len); return k * k * (3 - 2 * k); };
  // Mountains reach down to the sea's horizon so none of them float over the coast.
  const foot = L.water + 1;
  const fade = (x, h) => Math.round(foot - (foot - h) * env(x, 90));
  const atmo = (col, k) => pxMix(col, 0xcdeefb, k);
  const fc = { img, P, W, H, L, foot, coastEnd, fade, atmo, night, season, snowy, sc, state, land, wk, inland };
  if (habFarScene(fc)) {
    // A state's own far scenery (habFarScene).
  } else if (state === "CA" || land.far === "peaks") {
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
  } else if (state === "GA") {
    // Stone Mountain: one huge bare granite dome rising out of the forest.
    const rock = P("#7a7a80", "#94949a", "#aeaeb2", "#c8c8ca"), mx = Math.round(coastEnd * .4), mw = 64, mtop = 108;
    for (let x = mx - mw; x <= mx + mw; x++) {
      // A long, low whaleback, steeper on its left face.
      const u = (x - mx) / mw, e = u < 0 ? Math.pow(-u, 1.6) : Math.pow(u, 2.4);
      const h = fade(x, Math.round(mtop + e * 36 + (fbm(x / 9, 0, 52) - .5) * 4));
      for (let y = h; y < foot; y++) {
        // Bare granite streaked dark where rain runs down, with lichen patches.
        const streak = habRidged(x / 2.2, y / 14, 53) - .5;
        let v = .62 - u * .35 + streak * .45 + (vnoise(x / 8, y / 5, 51) - .5) * .15 - (y - h) * .004 + (y - h < 1.5 ? .15 : 0);
        img.set(x, y, atmo(ramp(rock, v, x, y), .22));
      }
    }
  } else if (state === "IL" || land.far === "farm") {
    // Prairie farmland to the horizon: a red barn and a silo.
    const barn = P("#6a1e16", "#8e2a1e", "#a8382a"), silo = P("#8a8e94", "#a8acb0", "#c4c8cc"), roofP = P("#4a4440", "#5e5852");
    const bx = Math.round(coastEnd * .3), gy = 147;
    for (let y = gy - 7; y < gy; y++) for (let dx = -6; dx <= 6; dx++) img.set(bx + dx, y, atmo(barn[dx < -3 ? 0 : dx > 3 ? 2 : 1], .2));
    for (let y = gy - 11; y < gy - 7; y++) for (let dx = -(y - gy + 12) * 2; dx <= (y - gy + 12) * 2; dx++) img.set(bx + dx, y, atmo(roofP[1], .2));
    for (let dx = -1; dx <= 1; dx++) for (let y = gy - 4; y < gy; y++) img.set(bx + dx, y, atmo(P("#e8e2d4")[0], .2));
    for (let y = gy - 16; y < gy; y++) for (let dx = 0; dx < 4; dx++) img.set(bx + 8 + dx, y, atmo(silo[dx === 0 ? 2 : dx === 3 ? 0 : 1], .2));
    for (let dx = 0; dx < 4; dx++) img.set(bx + 8 + dx, gy - 17, atmo(silo[2], .2));
  } else if (state === "PA" || state === "NC" || state === "VA" || land.far === "ridges") {
    // The Blue Ridge, or Pennsylvania's long even Ridge-and-Valley crests: ridges
    // one behind another, going blue in the haze, the nearest wooded.
    const pa = state === "PA";
    habPaintRidges(fc, pa ? [[8, 26, 160], [18, 52, 200], [30, 74, 260], [42, 90, 300]] : [[6, 28, 50], [14, 50, 70], [24, 76, 90], [36, 96, 120], [46, 108, 150]],
      { vs: 1.25, blue: "#7a96c8", mist: !pa, pines: .2, crownMax: 16, seed: pa ? 548 : 549 });
  } else if (state === "FL" || land.far === "cypress") {
    // Cypress domes and cabbage palms on the far edge of the sawgrass: one ragged
    // tree line down to the ground, swelling into domes where the cypress stand.
    const dome = P("#3d5a44", "#4b6b4f", "#5b7d5a", "#6d8f66");
    const domes = [...Array(9)].map((_, i) => [Math.round((i + .3 + hash2(i, 41) * .5) * coastEnd / 9), 10 + hash2(i, 42) * 12, 5 + hash2(i, 43) * 7]);
    for (let x = 0; x < coastEnd; x++) {
      let h = 3 + vnoise(x / 6, 0, 45) * 3;
      for (const [dx, rx, rh] of domes) { const u = (x - dx) / rx; if (Math.abs(u) < 1) h = Math.max(h, rh * Math.sqrt(1 - u * u)); }
      h += (vnoise(x / 2.2, 0, 46) - .5) * 3;
      const top = Math.round(152 - h);
      for (let y = top; y < foot; y++) {
        // Crowns lit on top, darker lower down, with clumpy texture.
        const v = .5 + (y - top < 2 ? .2 : 0) - (y - top) * .025 + (vnoise(x / 3, y / 2, 47) - .5) * .35;
        img.set(x, y, atmo(ramp(dome, v, x, y), .2));
      }
    }
    // Cabbage palms: thin trunks with a shaggy head of drooping fronds.
    const pf = P("#4f7a4a", "#6a9658"), trunk = P("#7a6a52");
    for (let i = 0; i < 12; i++) {
      const x = Math.round(hash2(i, 44) * (coastEnd - 10)) + 4, h = 12 + Math.round(hash2(i, 45) * 6), y0 = 150;
      const lean = (hash2(i, 48) - .5) * .25;
      for (let j = 0; j < h; j++) img.set(Math.round(x + lean * j), y0 - j, atmo(trunk[0], .2));
      const hx = Math.round(x + lean * h), hy = y0 - h;
      for (let f = 0; f < 7; f++) {
        const a = -Math.PI * (.1 + .8 * f / 6) + (hash2(i, f, 49) - .5) * .3, len = 3 + hash2(f, i, 50) * 2;
        for (let t = 1; t <= len; t++) img.set(Math.round(hx + Math.cos(a) * t), Math.round(hy + Math.sin(a) * t * .7 + t * t * .12), atmo(pf[t < 2 ? 1 : 0], .2));
      }
    }
  } else if (state === "NY") {
    // The Manhattan skyline, hazy in the distance, with the Empire State Building
    // in the middle; its windows light up at night.
    const bld = P("#6a7894", "#7e8ca6", "#95a2ba", "#aab5ca"), lit = P("#ffe9a0", "#ffd36a");
    const x0 = Math.round(coastEnd * .18), x1 = Math.round(coastEnd * .78), es = Math.round((x0 + x1) / 2);
    for (let x = x0, i = 0; x < x1; i++) {
      const w = 4 + Math.floor(hash2(i, 61) * 6), h = 12 + Math.floor(hash2(i, 62) * 22 * (1 - Math.abs(x - es) / (x1 - x0)));
      for (let dx = 0; dx < w && x + dx < x1; dx++) for (let y = 138 - h; y < 140; y++) {
        const edge = dx === 0 ? 2 : dx === w - 1 ? 0 : 1;
        const win = dx % 2 === 1 && dx < w - 1 && (y - 138 + h) % 3 === 1 && y > 138 - h + 1;
        if (win && night && hash2(x + dx, y, 63) > .55) img.set(x + dx, y, lit[hash2(x, y, 64) > .5 ? 0 : 1], 1);
        else img.set(x + dx, y, atmo(win ? bld[3] : bld[edge], .3));
      }
      x += w + (hash2(i, 65) > .7 ? 1 : 0);
    }
    // The Empire State Building: setbacks and a spire.
    for (const [hw, y0, y1] of [[4, 100, 140], [3, 92, 100], [2, 86, 92], [1, 80, 86], [0, 70, 80]])
      for (let y = y0; y < y1; y++) for (let dx = -hw; dx <= hw; dx++) {
        const win = hw > 1 && dx % 2 === 0 && dx !== -hw && y % 3 === 0;
        if (win && night && hash2(dx, y, 66) > .5) img.set(es + dx, y, lit[0], 1);
        else img.set(es + dx, y, atmo(bld[dx < 0 ? 2 : dx > 0 ? 0 : 1], .25));
      }
  } else if (state === "TX" || land.far === "mesas") {
    // Mesas and buttes on the far plains: eroded caprock tables over banded red
    // cliffs, painted with the same rough walls and talus as the Southwest scenes.
    habPaintMesas(fc, [[.0, .16, 30, "#b46c4c", .3], [.27, .31, 22, "#b46c4c", .32], [.38, .56, 34, "#b0664a", .26]]);
  } else if (land.far === "volcano" || land.far === "shield") {
    // A lone volcano: a tall snow-capped cone (Mount Rainier, Mount Hood), or in
    // Hawaii a broad green shield volcano.
    const shield = land.far === "shield", mx = Math.round(coastEnd * .42), half = shield ? 120 : 64, peak = shield ? 104 : 74;
    const rock = shield ? P("#3f6a4a", "#4f7e54", "#64945e", "#7caa70") : P("#5e6a8a", "#76829e", "#8e9ab4", "#a8b2ca");
    const snow = P("#c4cfe6", "#e0e8f6", "#f6f9ff", "#ffffff");
    for (let x = Math.max(0, mx - half); x <= Math.min(coastEnd, mx + half); x++) {
      const u = Math.abs(x - mx) / half, h = fade(x, Math.round(peak + Math.pow(u, shield ? 1.8 : .95) * (150 - peak) + (vnoise(x / 7, 0, 61) - .5) * 3));
      for (let y = h; y < foot; y++) {
        const v = .62 - (x - mx) / half * .35 + (vnoise(x / 5, y / 3, 62) - .5) * .25 - (y - h) * .004;
        const cap = !shield && y < peak + 14 + vnoise(x / 4, y / 3, 63) * 9 - (y - h) * .1;
        img.set(x, y, atmo(ramp(cap ? snow : rock, v, x, y), .3));
      }
    }
  }
  const snowPal = P("#b8c4d8", "#d4dcea", "#eef2f8", "#ffffff");
  // Hills, far then near, each with a lit top edge (low and gentle in flat states).
  // The hills always slope down to the shore, even when the far scenery runs on.
  const envH = (x, len) => { const k = clamp01((L.sea - 4 - x) / len); return k * k * (3 - 2 * k); };
  const bio = HAB_BIOME[state];
  if (bio) habFoothills(fc, bio);
  const hills = bio ? [] : sc.flat ? [[150, 3, .021, sc.far, 20], [158, 2, .034, sc.near, 21]]
    : [[132, 12, .021, sc.far, 20], [150, 9, .034, sc.near, 21]];
  hills.forEach(([base, amp, k, hex, seed], li) => {
    const pal = P(...hex);
    for (let x = 0; x < L.sea - 10; x++) {
      const raw = base + Math.sin(x * k + base) * amp + Math.sin(x * k * 2.7) * 3;
      const h = Math.round(L.water + 10 - (L.water + 10 - raw) * envH(x + 10, 60));
      const slope = Math.cos(x * k + base) * amp * k + Math.cos(x * k * 2.7) * 3 * k * 2.7;
      for (let y = h; y < L.water + 10; y++) {
        const v = .62 - slope * 1.2 - (y - h) / 40 + (fbm(x / 12, y / 6, seed) - .5) * .4;
        if (sc.snow && y - h < 2 + fbm(x / 6, y / 4, seed + 5) * 9) img.set(x, y, ramp(snowPal, v + .2, x, y));
        else img.set(x, y, y === h ? pal[3] : ramp(pal, v, x, y));
      }
    }
    // Trees on the hills: little oaks, a dense forest, or round trees.
    const dots = sc.dots, tl = pxLayer(W, H), tr = mulberry(31 + li);
    const n = dots === "forest" ? (li ? 70 : 90) : dots === "oak" ? (li ? 14 : 9) : dots === "palm" ? (li ? 12 : 8)
      : dots === "maple" ? (li ? 34 : 46) : dots === "sage" ? (li ? 60 : 70) : dots === "juniper" ? (li ? 34 : 40)
      : dots === "grass" ? (li ? 140 : 120) : (li ? 10 : 6);
    // Fall color: red, orange and gold maples among a few green ones.
    const fall = [P("#7a2216", "#9a2e1a", "#bc4222", "#d85a2a"), P("#9a4a14", "#bc5e18", "#d8781e", "#ec9a30"),
                  P("#9a7a14", "#bc9a1e", "#d8b82a", "#ecd048"), P("#2f6a34", "#3f7f41", "#55964f", "#6dad60")];
    const leaf = dots === "oak" ? P("#3f5a26", "#526f30", "#67853b", "#7f9c4a")
      : dots === "forest" ? P("#1f4f2c", "#2b6236", "#387542", "#4a8a4f") : P("#2f6a34", "#3f7f41", "#55964f", "#6dad60");
    // Leafy trees (not oaks, pines or palms) follow the season.
    const twig = P("#5a4a3e", "#6e5c4c", "#857060", "#9a8472");
    const leafy = (j) => sc.leaves === "fall" ? fall[j % 3] : sc.leaves === "bare" ? twig : dots === "maple" ? fall[3] : leaf;
    for (let i = 0; i < n; i++) {
      const x = Math.floor(tr() * (L.sea - 30)) + 4;
      const raw = base + Math.sin(x * k + base) * amp + Math.sin(x * k * 2.7) * 3;
      const h = Math.round(L.water + 10 - (L.water + 10 - raw) * envH(x + 10, 60));
      const y = h + Math.floor(tr() * (dots === "forest" ? 14 : 8)) + (li ? 2 : 1);
      if (y > L.water + 2) continue;
      const s = li ? 1 : .7;
      if (sc.saguaro && i % 2) {
        // A saguaro with raised arms.
        const cac = P("#3d6a3a", "#4f8046", "#64965a"), hh = Math.round(10 * s + tr() * 6), arm = Math.round(hh * .5);
        for (let j = 0; j < hh; j++) for (let dx = -1; dx <= 1; dx++) tl.set(x + dx, y - j, cac[dx + 1]);
        for (const side of tr() < .5 ? [-1, 1] : [1]) {
          tl.set(x + side * 2, y - arm, cac[1]); tl.set(x + side * 3, y - arm, cac[1]);
          for (let j = arm; j < arm + 4; j++) tl.set(x + side * 3, y - j, cac[side > 0 ? 2 : 0]);
        }
        continue;
      }
      if (dots === "sage") pxBlob(tl, x, y - 1, Math.round(2 * s + tr() * 1.5), Math.round(1 * s + 1), P("#5e6a52", "#76826a", "#909c82", "#aab49a"), { rough: .6, grain: 1, seed: i });
      else if (dots === "juniper") pxBlob(tl, x, y - 2, Math.round(2 * s + tr() * 2), Math.round(2 * s + 1), P("#22301e", "#2e4028", "#3c5234", "#4e6644"), { rough: .7, grain: 1, seed: i });
      else if (dots === "grass") {
        // Tufts of bunchgrass, gold in the fall.
        const g = sc.leaves === "fall" ? P("#9a7a2a", "#c4a03e", "#e0c264") : P(...sc.near.slice(0, 2), sc.near[3]);
        for (let j = -1; j <= 1; j++) for (let k2 = 0; k2 < 2 + (j === 0 ? 1 : 0) + (li ? 1 : 0); k2++) tl.set(x + j, y - k2, g[k2 === 0 ? 0 : j < 0 ? 2 : 1]);
      }
      else if (dots === "oak") pxBlob(tl, x, y - 2, Math.round(5 * s + tr() * 2), Math.round(3 * s + 1), leaf, { rough: .5, seed: i });
      else if (dots === "forest") {
        if (tr() < .5) pxBlob(tl, x, y, Math.round(3 * s + 1), Math.round(4 * s + 1), sc.leaves === "green" ? leaf : leafy(i), { rough: .45, seed: i });
        else for (let j = 0; j < 7 * s + 2; j++) {
          const w = Math.round(j * .45);
          for (let dx = -w; dx <= w; dx++) tl.set(x + dx, y - 8 * s + j, ramp(leaf, .75 - (dx + w) / (2 * w + 1) * .7, x + dx, y + j));
        }
      } else if (dots === "palm") {
        // A cabbage palm: a thin trunk and a burst of fronds.
        const h = Math.round(9 * s + tr() * 4);
        for (let j = 0; j < h; j++) tl.set(x, y - j, P("#7a6a52"));
        for (const [dx, dy] of [[-4, 1], [-3, 0], [-2, -1], [-1, -1], [1, -1], [2, -1], [3, 0], [4, 1], [0, -2], [-1, -3], [1, -3], [-5, 2], [5, 2]])
          tl.set(x + dx, y - h + dy, leaf[dy < -1 ? 3 : dy < 0 ? 2 : 1]);
      } else if (dots === "maple") {
        pxBlob(tl, x, y - 1, Math.round(3 * s + 1), Math.round(3 * s + 1), leafy(Math.floor(tr() * 4)), { rough: .5, seed: i });
      } else pxBlob(tl, x, y - 2, Math.round(4 * s + 1), Math.round(4 * s + 1), leafy(i), { rough: .4, seed: i });
    }
    tl.onto(img, li && dots !== "grass" && dots !== "sage" ? P("#22401f") : undefined);
  });
  // Sea: lighter at the horizon, deep blue below, with wave texture.
  const sea = P(...HAB_WATER[wk].water);
  for (let y = L.water; y < H; y++) for (let x = L.sea - 30; x < W; x++) {
    let v = 1 - (y - L.water) / (H - L.water) * 1.05;
    const wv = vnoise(x / 9, y / 1.6, 13);
    if (wv > .74) v += .18; else if (wv < .22) v -= .12;
    img.set(x, y, ramp(sea, v, x, y));
  }
  if (inland) habFarBank(fc); else for (let x = L.sea - 30; x < W; x++) img.set(x, L.water, P(HAB_WATER[wk].line));
  // Meadow, painted: lighter and hazier far off, rich and dark close up, with
  // the shadows of clouds drifting over it in big soft shapes.
  // The ground's colors run from cool shadow to warm sunlight around its palette.
  const meadHex = bio === "desert" ? HAB_GROUND[state] || HAB_GROUND.desert : sc.meadow;
  const mead = P(hexMix(meadHex[0], "#1e3048", .5), hexMix(meadHex[0], "#1e3048", .25), ...meadHex, hexMix(meadHex[3], "#fff2c8", .3));
  const meadV = (x, y) => {
    const d = (y - L.water) / (H - L.water);
    return .74 - d * .42 + (fbm(x / 40, y / 14, 17) - .5) * .2 - (fbm(x / 70 + 3, y / 22, 71) > .54 ? .17 : 0);
  };
  for (let y = L.water + 4; y < H; y++) for (let x = 0; x < L.shore[y] + 3; x++) {
    const v = meadV(x, y);
    if (sc.snow && fbm(x / 22, y / 9, 27) > .4) img.set(x, y, ramp(snowPal, v + .1, x, y));
    else img.set(x, y, ramp(mead, v, x, y));
  }
  // Grass strokes: short upright blades in a lighter or darker tone than the
  // ground under them, longer toward the viewer.
  for (let i = 0; i < 2400; i++) {
    const x = Math.floor(hash2(i, 1, 860) * (L.land - 2)), y = L.water + 5 + Math.floor(Math.pow(hash2(i, 2, 860), .8) * (H - L.water - 6));
    if (x >= L.shore[y] - 2) continue;
    const d = (y - L.water) / (H - L.water), len = 1 + Math.round(d * 4 * hash2(i, 3, 860)), lean = hash2(i, 4, 860) > .5 ? 1 : 0;
    const onSnow = sc.snow && fbm(x / 22, y / 9, 27) > .4, pal = onSnow ? snowPal : mead;
    const c = ramp(pal, meadV(x, y) + (hash2(i, 5, 860) > .45 ? .2 : -.22), x, y);
    for (let j = 0; j < len; j++) img.set(x + (j > len / 2 ? lean : 0), y - j, c);
  }
  // Sandy shore curving down to the sea, wet near the water.
  const sand = P(...HAB_WATER[wk].sand), wet = P(...HAB_WATER[wk].wet);
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
  if (bio === "north" || bio === "alpine") {
    // Weathered granite boulders scattered along a cold shore, in clusters of
    // different sizes, each with a wet dark base.
    const gr = P("#3e3e46", "#56565e", "#6e6e76", "#8a8a92", "#a6a6ac");
    for (let i = 0; i < 14; i++) {
      const y = 182 + Math.floor(hash2(i, 1, 840) * 84), x = Math.round(L.shore[y] + (L.surf[y] - L.shore[y]) * (.25 + hash2(i, 2, 840) * .6));
      const rx = 1 + Math.floor(hash2(i, 3, 840) ** 2 * 6), ry = Math.max(1, Math.round(rx * (.5 + hash2(i, 4, 840) * .3)));
      for (let dx = -rx - 1; dx <= rx + 1; dx++) img.set(x + dx, y + ry, P("#2e2e30"));
      pxBlob(img, x, y, rx, ry, gr, { rough: .6, grain: 1, seed: i + 5, flat: false });
    }
  } else if (bio === "marsh") {
    // Marsh grass where the meadow meets the water.
    const mg = P("#4a5a2a", "#647438", "#8a9a50");
    for (let y = L.water + 4; y < H; y += 2) for (let b = 0; b < 3; b++) {
      const x = L.shore[y] + Math.floor(hash2(y, b, 841) * 10), h = 4 + Math.floor(hash2(b, y, 842) * 5);
      for (let k = 0; k < h; k++) img.set(x + Math.round(k * (b - 1) * .25), y - k, mg[k > h - 3 ? 2 : b % 2]);
    }
  }
  // Grass tufts and clusters of flowers.
  const blade = P(sc.meadow[0], sc.meadow[3]);
  if (bio) habGround(fc, bio, mulberry(77));
  else for (let i = 0; i < 260; i++) {
    const x = Math.floor(r() * (L.land - 6)), y = L.water + 7 + Math.floor(r() * (H - L.water - 8));
    img.set(x, y, blade[0]); img.set(x, y - 1, blade[0]); img.set(x + 1, y - 2, blade[1]); img.set(x - 1, y - 1, blade[1]);
  }
  const flowerSets = sc.flowers.map((f) => P(...f));
  for (let i = 0; i < (bio ? 0 : sc.flowerCount); i++) {
    const cx = Math.floor(r() * (L.land - 16)) + 6, cy = L.water + 12 + Math.floor(r() * (H - L.water - 16));
    const [petal, mid] = flowerSets[Math.floor(r() * flowerSets.length)];
    for (let j = 0; j < 3 + r() * 3; j++) {
      const x = cx + Math.round((r() - .5) * 12), y = cy + Math.round((r() - .5) * 6);
      img.set(x, y + 1, blade[0]); img.set(x, y + 2, blade[0]);
      img.set(x - 1, y, petal); img.set(x + 1, y, petal); img.set(x, y - 1, petal); img.set(x, y + 1, petal); img.set(x, y, mid);
    }
  }
  if (sc.leaves === "fall" && !bio) {
    // Fallen leaves scattered on the meadow (plenty under New York's maples).
    const lv = [P("#c8441c"), P("#e8782a"), P("#e8b82a"), P("#9a2a16")];
    for (let i = 0; i < (sc.dots === "maple" ? 90 : 45); i++) {
      const x = Math.floor(hash2(i, 71) * (L.land - 6)) + 2, y = L.water + 10 + Math.floor(hash2(i, 72) * (HAB_H - L.water - 12));
      if (((x - L.pond.x) / (L.pond.rx + 4)) ** 2 + ((y - L.pond.y) / (L.pond.ry + 4)) ** 2 < 1) continue;
      img.set(x, y, lv[i % 4]); if (hash2(i, 73) > .5) img.set(x + 1, y, lv[(i + 1) % 4]);
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
  const ps = bio && habPondStyle(bio, state);
  const p = L.pond, pond = pxLayer(W, H), pw = P(...(ps?.water || ["#1f5f97", "#2b76b0", "#3b8fc8", "#5eaee0"]));
  // An uneven, natural outline rather than a perfect oval.
  const pR = (a) => .84 + .16 * vnoise(Math.cos(a) * 1.6 + 4, Math.sin(a) * 1.6 + 4, 880);
  const pD = (dx, dy) => ((dx / p.rx) ** 2 + (dy / p.ry) ** 2) / pR(Math.atan2(dy / p.ry, dx / p.rx)) ** 2;
  for (let dy = -p.ry; dy <= p.ry; dy++) for (let dx = -p.rx; dx <= p.rx; dx++) {
    const d = pD(dx, dy);
    if (d > 1) continue;
    // The far bank's shadow along the top, then the sky reflected, brighter toward the viewer.
    pond.set(p.x + dx, p.y + dy, ramp(pw, dy < -p.ry + 3 + (d > .8 ? 1 : 0) ? .05 : .45 + (dy + p.ry) / (2 * p.ry) * .55, p.x + dx, p.y + dy));
  }
  const pebble = P(...(ps?.rim || ["#6d6a62", "#8c887d", "#a9a597", "#c4c0b1"]));
  if (ps && !ps.rim) {
    // A muddy bank instead of stones.
    const mud = P("#3a2e22", "#4e3e2e", "#64503c");
    for (let a = 0; a < Math.PI * 2; a += .02) {
      const w = 1 + Math.floor(vnoise(a * 3, 0, 832) * 3);
      for (let k = 0; k < w; k++) {
        const x = Math.round(p.x + Math.cos(a) * (p.rx * pR(a) + k)), y = Math.round(p.y + Math.sin(a) * (p.ry * pR(a) + k * .6));
        if (pond.get(x, y) < 0) pond.set(x, y, mud[Math.min(2, k + (Math.sin(a) < 0 ? 0 : 1))]);
      }
    }
  } else {
    // A dark wet margin, then stones of every size in loose groups along the bank,
    // flat and half sunk, with stretches where the grass runs right to the water.
    for (let a = 0; a < Math.PI * 2; a += .015) {
      const x = Math.round(p.x + Math.cos(a) * (p.rx * pR(a) + 1)), y = Math.round(p.y + Math.sin(a) * (p.ry * pR(a) + .6));
      if (pond.get(x, y) < 0) pond.set(x, y, P("#3a3a2c"));
    }
    for (let a = 0; a < Math.PI * 2; a += .12 + hash2(Math.round(a * 90), 3, 881) * .22) {
      if (vnoise(a * 1.4, 7, 882) > .68) continue;
      const big = hash2(Math.round(a * 90), 2, 881) > (ps?.big ? .55 : .78), sz = 1 + Math.floor(hash2(Math.round(a * 90), 1, 881) * 2.6) + (big ? 2 : 0);
      const x = Math.round(p.x + Math.cos(a) * (p.rx * pR(a) + 1.5)), y = Math.round(p.y + Math.sin(a) * (p.ry * pR(a) + 1));
      pxBlob(pond, x, y, sz + 1, Math.max(1, Math.round(sz * .6)), pebble, { rough: .55, grain: 1, seed: Math.round(a * 50) });
    }
  }
  pond.onto(img);
  const refl = P("#8fd0f5"), pad = P("#3e7d34", "#5a9c42", "#76b653");
  for (const [dx, dy, w] of [[-18, -5, 9], [6, -3, 12], [-6, 4, 6]]) for (let i = 0; i < w; i++) img.set(p.x + dx + i, p.y + dy, refl);
  if (ps?.duckweed) for (let i = 0; i < 90; i++) {
    const a = hash2(i, 1, 830) * Math.PI * 2, d = .55 + hash2(i, 2, 830) * .4;
    img.set(Math.round(p.x + Math.cos(a) * p.rx * d), Math.round(p.y + Math.sin(a) * p.ry * d), pad[1 + (i % 2)]);
  }
  if (ps?.knees) for (const dx of [-p.rx - 6, -p.rx + 6, p.rx - 4, p.rx + 7, -4]) {
    // Cypress knees poking up around the bayou.
    const ky = dx === -4 ? p.y - p.ry - 3 : p.y + (dx < 0 ? 3 : -2), kh = 3 + Math.floor(hash2(dx, 3, 831) * 3);
    for (let k = 0; k < kh; k++) for (let w = -Math.floor((kh - k) / 2); w <= Math.floor((kh - k) / 2); w++) img.set(p.x + dx + w, ky - k, P(w < 0 ? "#6a5440" : "#4e3c2c"));
  }
  if (!ps || ps.lilies) for (const [dx, dy] of [[-p.rx + 12, 2], [p.rx - 16, -3], [8, 6]]) {
    pxBlob(img, p.x + dx, p.y + dy, 4, 2, pad);
    img.set(p.x + dx + 1, p.y + dy - 1, pw[2]); img.set(p.x + dx + 2, p.y + dy, pw[2]);
  }
  if (!ps || ps.lilies) { img.set(p.x + p.rx - 16, p.y - 4, P("#ffd1e6")); img.set(p.x + p.rx - 15, p.y - 4, P("#ff9cc6")); img.set(p.x + p.rx - 16, p.y - 5, P("#ffd1e6")); }
  const reed = P("#2f6a2c", "#4c8f3c"), cat = P("#6b4227", "#8a5833");
  if (ps?.sedge) for (const dx of [-p.rx - 2, -p.rx + 3, p.rx - 3, p.rx + 3, p.rx + 6]) {
    // Sedge tufts instead of cattails at a cold mountain pool.
    for (let b = -2; b <= 2; b++) for (let k = 0; k < 6 - Math.abs(b); k++) img.set(p.x + dx + b + Math.round(b * k * .2), p.y - 1 - k, reed[k > 2 ? 1 : 0]);
  }
  for (const dx of [-p.rx - 3, -p.rx + 1, -p.rx + 4, p.rx - 2, p.rx + 2, p.rx + 5].slice(0, ps && !ps.sedge ? ps.reeds : ps?.sedge ? 0 : 6)) {
    const hgt = 12 + Math.floor(hash2(dx, 2) * 6);
    for (let i = 0; i < hgt; i++) { img.set(p.x + dx, p.y - 1 - i, reed[i % 3 ? 0 : 1]); }
    img.set(p.x + dx - 1, p.y - 4, reed[1]); img.set(p.x + dx + 1, p.y - 7, reed[1]);
    for (let i = 0; i < 4; i++) { img.set(p.x + dx, p.y - hgt - i, cat[i % 2]); img.set(p.x + dx + 1, p.y - hgt - i, cat[0]); }
    img.set(p.x + dx, p.y - hgt - 4, reed[0]);
  }
  // Dark blades along the bottom edge frame the scene from up close.
  for (let x = 0; x < L.shore[H - 1] - 2; x++) {
    const h = Math.round(3 + vnoise(x / 5, 0, 870) * 10);
    for (let j = 0; j < h; j++) if ((x * 7 + j * 3) % 5 !== 0 || j < 2)
      img.set(x + Math.round(j * (vnoise(x / 3, 1, 871) - .5)), H - 1 - j, ramp(sc.snow ? snowPal : mead, j / h * .2, x, H - 1 - j));
  }
  // State extras on the shore and in the sea.
  if (state === "CA" || land.sea === "stack") {
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
  } else if (state === "FL") {
    // A mangrove island just offshore: a dense canopy over arching prop roots.
    const mg = pxLayer(W, H), mx = L.sea + Math.round((W - L.sea) * .45), top = L.water - 14;
    const root = P("#4a3a2c", "#6a5440", "#8a7058"), leaf = P("#1f4a2a", "#2b5f34", "#3b7640", "#4f8f4c", "#6aa85a");
    for (let k = -18; k <= 18; k += 4) {
      // each root arches out from the trunks and down into the water
      for (let t = 0; t <= 1; t += .06) {
        const x = Math.round(mx + k * .4 + (k * .6) * t), y = Math.round(top + 10 + t * (L.water + 4 - top - 10) - Math.sin(t * Math.PI) * 3);
        mg.set(x, y, root[t < .5 ? 2 : 1]);
      }
    }
    for (const [dx, dy, rx, ry] of [[-10, 6, 9, 6], [8, 6, 10, 6], [-2, 2, 11, 7], [14, 9, 6, 4], [-16, 9, 5, 4]])
      pxBlob(mg, mx + dx, top + dy, rx, ry, leaf, { rough: .9, grain: 1, seed: dx + 40 });
    mg.onto(img, P("#132a18"));
    const foam = P("#e9f6ff");
    for (let dx = -22; dx <= 22; dx++) if (hash2(dx, 47) > .45) img.set(mx + dx, L.water + 4 + (hash2(dx, 48) > .7 ? 1 : 0), foam);
    // Cape Canaveral: a white rocket on its launch pad beside a red gantry tower.
    const rk = pxLayer(W, H), rx = L.land - 30, pad = L.water + 10, rtop = L.water - 62;
    const white = P("#a8acb4", "#cfd3da", "#eceef2", "#ffffff"), red = P("#8a2a22", "#b83a2e", "#d8574a");
    const steel = P("#3a3a40", "#55565e");
    for (let y = rtop + 6; y < pad; y++) {
      const hw = y < rtop + 14 ? Math.round((y - rtop - 6) * .45) : 4;
      for (let dx = -hw; dx <= hw; dx++) rk.set(rx + dx, y, ramp(white, .85 - (dx + hw) / (2 * hw + 1) * .7, rx + dx, y));
      if ((y - rtop) % 16 === 0) for (let dx = -hw; dx <= hw; dx++) rk.set(rx + dx, y, steel[1]);
    }
    for (let y = rtop; y < rtop + 6; y++) rk.set(rx, y, red[1]);
    for (let y = rtop + 6; y < rtop + 12; y++) for (let dx = -2; dx <= 2; dx++) if (Math.abs(dx) <= (y - rtop - 6) * .45) rk.set(rx + dx, y, ramp(red, .8 - (dx + 2) / 5, rx + dx, y));
    for (let y = rtop + 30; y < rtop + 36; y++) for (let dx = -4; dx <= 4; dx++) rk.set(rx + dx, y, ramp(P("#2a4aa0", "#3a64c8"), .8 - (dx + 4) / 9, rx + dx, y));
    // fins at the bottom
    for (let k = 0; k < 6; k++) { rk.set(rx - 5 - (k >> 1), pad - 6 + k, white[1]); rk.set(rx + 5 + (k >> 1), pad - 6 + k, white[1]); }
    // the gantry: a lattice tower with arms reaching to the rocket
    const gx = rx + 12;
    for (let y = rtop + 4; y <= pad; y++) {
      rk.set(gx - 3, y, red[0]); rk.set(gx + 3, y, red[1]);
      if ((y - rtop) % 6 === 0) for (let dx = -3; dx <= 3; dx++) rk.set(gx + dx, y, red[2]);
      if ((y - rtop) % 6 === 3) { rk.set(gx - 1, y, red[0]); rk.set(gx + 1, y, red[0]); }
    }
    for (const ay of [rtop + 16, rtop + 34]) for (let x = rx + 5; x < gx - 3; x++) rk.set(x, ay, steel[0]);
    for (let dx = -10; dx <= 18; dx++) for (let y = pad; y < pad + 3; y++) rk.set(rx + dx, y, ramp(P("#7a7a80", "#9a9aa0", "#b8b8bc"), .8 - (y - pad) * .3, rx + dx, y));
    rk.onto(img, P("#1e1e24"));
  } else if (state === "VA" || land.sea === "lighthouse") {
    // Assateague Island: a sandy barrier island with marsh grass, the striped
    // lighthouse, and the wild ponies grazing.
    const as = pxLayer(W, H), { ix, ground, lx, ltop } = habAssateague(L);
    const sand = P("#c8b07a", "#dcc690", "#ecdcac"), marsh = P("#6a8a3a", "#7f9e44", "#98b456", "#b0c66a");
    pxBlob(as, ix, ground + 5, 34, 6, sand, { flat: true, rough: .3, seed: 11 });
    pxBlob(as, ix - 4, ground + 2, 24, 4, marsh, { flat: true, rough: .8, grain: 1, seed: 12 });
    for (let i = 0; i < 18; i++) {
      const x = ix - 26 + Math.floor(hash2(i, 81) * 50), y = ground + 1 + Math.floor(hash2(i, 82) * 3);
      as.set(x, y - 1, marsh[3]); as.set(x, y - 2, marsh[2]);
    }
    // the lighthouse: red and white bands, a black lantern and a white base house
    const red = P("#7a2018", "#a8302a", "#c84a3a", "#de6a56"), white = P("#b9b5aa", "#dcd8cc", "#f6f3ea", "#ffffff");
    const black = P("#15171c", "#2a2d34");
    for (let y = ltop; y < ground + 1; y++) {
      const hw = Math.round(2 + (y - ltop) * .07);
      for (let dx = -hw; dx <= hw; dx++)
        as.set(lx + dx, y, ramp(Math.floor((y - ltop) / 8) % 2 || land.lh === "white" ? white : red, .9 - (dx + hw) / (2 * hw + 1) * .75, lx + dx, y));
    }
    for (let dx = -4; dx <= 4; dx++) as.set(lx + dx, ltop - 1, black[0]);
    for (let y = ltop - 6; y < ltop - 1; y++) for (let dx = -2; dx <= 2; dx++)
      as.set(lx + dx, y, Math.abs(dx) === 2 ? black[1] : P("#ffe9a0"), night ? 1 : 0);
    for (let y = ltop - 9; y < ltop - 6; y++) for (let dx = -(y - ltop + 10); dx <= y - ltop + 10; dx++) as.set(lx + dx, y, black[1]);
    as.set(lx, ltop - 10, black[0]);
    for (let y = ground - 4; y < ground + 1; y++) for (let dx = 4; dx <= 10; dx++)
      as.set(lx + dx, y, y === ground - 4 ? red[0] : ramp(white, .8 - (dx - 4) / 7 * .5, lx + dx, y));
    // the wild ponies: a chestnut pinto and a bay, heads down in the grass, and a foal
    const pony = (px, py, coat, patch, mane, s, grazing) => {
      const c = P(...coat);
      for (let y = 0; y < 4 * s; y++) for (let x = 0; x < 8 * s; x++) {
        const pinto = patch && hash2(Math.floor(x / 3), Math.floor(y / 2), px) > .55;
        as.set(px + x, py - 3 * s - y, pinto ? P(patch) : ramp(c, .85 - y / (4 * s) * .5, px + x, py - y));
      }
      for (const lx2 of [0, 2 * s, 5 * s, 7 * s]) for (let y = 0; y < 3 * s; y++) as.set(px + lx2, py - y, c[0]);
      // neck and head: down to the grass, or up and looking
      const hx = px - 1, nk = grazing ? [[0, -6], [-1, -5], [-1, -4], [-2, -3], [-2, -2], [-3, -1]] : [[0, -6], [0, -7], [-1, -8], [-1, -9], [-2, -9], [-3, -9], [-3, -8]];
      for (const [dx, dy] of nk) for (let k = 0; k < s; k++) as.set(hx + dx * s + k, py + dy * s + (s > 1 ? 1 : 0), c[1]);
      for (const [dx, dy] of grazing ? [[0, -7], [1, -7]] : [[0, -10], [1, -9]]) as.set(hx + dx * s, py + dy * s, P(mane));
      as.set(px + 8 * s, py - 6 * s, P(mane)); as.set(px + 8 * s, py - 5 * s, P(mane));  // tail
    };
    if (state === "VA") pony(ix - 28, ground + 2, ["#7a3a1c", "#9a4e26", "#b86a38"], "#f2ece0", "#f2ece0", 1, true);
    if (state === "VA") pony(ix - 14, ground + 3, ["#4a2a1a", "#6a3c24", "#86522e"], null, "#1e1612", 1, false);
    if (state === "VA") pony(ix - 1, ground + 4, ["#9a5e34", "#b8784a", "#d09060"], "#f6f0e4", "#5a3a22", 1, true);
    as.onto(img, P("#2a2014"));
    const foam = P("#e9f6ff");
    for (let dx = -36; dx <= 36; dx++) if (hash2(dx, 83) > .45) img.set(ix + dx, ground + 9 + (hash2(dx, 84) > .7 ? 1 : 0), foam);
  } else if (state === "NJ") {
    // A Jersey Shore pier on wooden pilings, with a Ferris wheel at the end
    // (its gondolas turn and the rim lights up after dark).
    const pr = pxLayer(W, H), { x0, x1, deck, hx, hy, r } = habPier(L);
    const wood = P("#6a5038", "#8a6a4a", "#a8885e"), steel = P("#c8ccd4", "#e8eaee"), red = P("#c8302a");
    for (let x = x0; x <= x1; x++) {
      pr.set(x, deck, wood[2]); pr.set(x, deck + 1, wood[1]);
      if (x % 5 === 0) for (let y = deck + 2; y < L.water + 3; y++) pr.set(x, y, wood[0]);
      if (x % 3 === 0) pr.set(x, deck - 2, wood[1]);
      pr.set(x, deck - 3, wood[2]);
    }
    for (let a = 0; a < 96; a++) { const u = a / 96 * Math.PI * 2; pr.set(Math.round(hx + Math.cos(u) * r), Math.round(hy + Math.sin(u) * r), steel[1]); }
    for (let i = 0; i < 8; i++) { const u = i * Math.PI / 4; for (let k = 1; k < r; k++) pr.set(Math.round(hx + Math.cos(u) * k), Math.round(hy + Math.sin(u) * k), steel[0]); }
    for (let k = 0; k < r + 4; k++) { pr.set(Math.round(hx - k * .45), hy + k, steel[0]); pr.set(Math.round(hx + k * .45), hy + k, steel[0]); }
    pr.set(hx, hy, red[0]);
    // a little striped ticket booth by the wheel
    for (let y = deck - 7; y < deck; y++) for (let dx = 0; dx < 5; dx++) pr.set(x1 - 9 + dx, y, y === deck - 7 ? red[0] : (dx % 2 ? P("#f4f0e8")[0] : red[0]));
    pr.onto(img);
  } else if (state === "MI") {
    // The Mackinac Bridge: two tall towers, the main cables sweeping between them
    // with hangers down to the deck; the cables are strung with lights at night.
    const mb = pxLayer(W, H), { x0, x1, deck, t1, t2, ttop, cable } = habMackinac(L);
    const tw = P("#4a6a5a", "#5e8270", "#76988a"), cb = P("#e8e2c8"), dk = P("#5a5e64", "#7a7e84"), lamp = P("#fff0b0");
    for (let x = x0; x < Math.min(x1, W); x++) {
      mb.set(x, deck, dk[1]); mb.set(x, deck + 1, dk[0]);
      if (x % 6 === 0) for (let y = deck + 2; y < L.water + 2; y++) mb.set(x, y, dk[0]);  // the piers under the deck
      const cy = Math.round(cable(x));
      mb.set(x, cy, cb[0], night && x % 3 === 0 ? 1 : 0);
      if (x % 4 === 0) for (let y = cy + 1; y < deck; y++) mb.set(x, y, cb[0]);
    }
    for (const tx of [t1, t2]) for (let y = ttop; y < L.water + 2; y++) for (let dx = -2; dx <= 2; dx++) {
      if (Math.abs(dx) === 0 && (y - ttop) % 9 > 2 && y < deck) continue;  // daylight between the tower legs
      mb.set(tx + dx, y, ramp(tw, .85 - (dx + 2) / 5 * .6, tx + dx, y));
    }
    mb.onto(img);
  } else if (state === "GA") {
    // A shrimp boat off the Georgia coast: white hull, a little wheelhouse, the
    // tall mast and two outrigger booms with their green nets hanging down.
    const sb = pxLayer(W, H), { bx, wl, mast, booms } = habShrimper(L);
    const hull = P("#b8bcc4", "#dcdfe4", "#f4f6f8"), trim = P("#2a5a9a"), wood = P("#5a4a3a", "#7a6a56"), net = P("#3a6a4a", "#4e8a5e");
    for (let y = wl - 6; y < wl + 1; y++) {
      const k = y - (wl - 6), l = bx - 16 + Math.round(k * .6), r = bx + 18 - Math.round(k * 1.2);
      for (let x = l; x <= r; x++) sb.set(x, y, y === wl - 5 ? trim[0] : ramp(hull, .85 - k * .08, x, y));
    }
    for (let x = bx - 18; x <= bx - 14; x++) sb.set(x, wl - 7 + Math.round((bx - 14 - x) * -.4), hull[2]);  // the raised bow
    for (let y = wl - 12; y < wl - 6; y++) for (let x = bx + 5; x <= bx + 13; x++) {
      const win = y === wl - 10 && (x === bx + 7 || x === bx + 9 || x === bx + 11);
      sb.set(x, y, win ? P("#2a3a4a")[0] : ramp(hull, .9 - (x - bx - 5) * .05, x, y));
    }
    for (let x = bx + 4; x <= bx + 14; x++) sb.set(x, wl - 12, trim[0]);
    for (let y = mast; y < wl - 6; y++) sb.set(bx, y, wood[1]);
    for (const [ex, ey] of booms) {
      const n = Math.abs(ex - bx);
      for (let i = 0; i <= n; i++) sb.set(bx + Math.sign(ex - bx) * i, Math.round(mast + 4 + (ey - mast - 4) * i / n), wood[0]);
      for (let y = ey + 1; y < ey + 9; y++) for (let dx = -1; dx <= 1; dx++) if ((y + dx) % 2 === 0 || dx === 0) sb.set(ex + dx, y, net[(y + dx) & 1]);
    }
    sb.onto(img, P("#1e2430"));
    const foam = P("#e9f6ff");
    for (let dx = -20; dx <= 20; dx++) if (hash2(dx, 47) > .45) img.set(bx + dx, wl + 1 + (hash2(dx, 48) > .7 ? 1 : 0), foam);
  } else if (state === "OH") {
    // Cedar Point on Lake Erie: a sandy peninsula with a red roller coaster on
    // white supports, its lift hill, a big drop and a loop; lights run along it at night.
    const cp = pxLayer(W, H), { cx, g, pts } = habCoaster(L);
    const sand = P("#c8b07a", "#dcc690", "#ecdcac"), grass = P("#4f7e3e", "#64944c", "#7aa85c");
    const red = P("#8a1a1a", "#b82626", "#d84040"), wht = P("#c8ccd4", "#e8eaee", "#ffffff");
    pxBlob(cp, cx, g + 4, 38, 5, sand, { flat: true, rough: .3, seed: 41 });
    pxBlob(cp, cx - 4, g + 2, 28, 3, grass, { flat: true, rough: .7, grain: 1, seed: 42 });
    const posts = new Set();
    pts.forEach(([x, y]) => {
      const px = Math.round(x);
      if (px % 3 || posts.has(px) || y > g - 4) return;
      posts.add(px);
      for (let yy = Math.round(y) + 2; yy < g + 1; yy++) cp.set(px, yy, wht[1]);
    });
    pts.forEach(([x, y]) => { cp.set(Math.round(x), Math.round(y), red[1]); cp.set(Math.round(x), Math.round(y) + 1, red[0]); });
    // a train of cars climbing the lift hill
    for (let k = 0; k < 4; k++) { const [x, y] = pts[14 + k * 3]; cp.set(Math.round(x), Math.round(y) - 1, P(["#2a5ad8", "#f0c020", "#2a5ad8", "#f0c020"][k])); }
    cp.onto(img, P("#2a1414"));
    const foam = P("#e9f6ff");
    for (let dx = -40; dx <= 40; dx++) if (hash2(dx, 43) > .45) img.set(cx + dx, g + 9 + (hash2(dx, 44) > .7 ? 1 : 0), foam);
  } else if (state === "IL") {
    // The Chicago skyline far across Lake Michigan, the black Willis Tower with its
    // twin antennas standing tallest; windows light up at night.
    const { x0, x1, base, wx, wtop, tips } = habChicago(L);
    const bld = P("#7e8aa2", "#93a0b6", "#a8b4c8", "#bcc6d6"), lit = P("#ffe9a0", "#ffd36a"), wil = P("#2a2c34", "#3a3c46", "#4c4e5a");
    for (let x = x0, i = 0; x < x1; i++) {
      const w = 3 + Math.floor(hash2(i, 94) * 4), h = 5 + Math.floor(hash2(i, 95) * 14 * (1 - Math.abs(x - wx) / (x1 - x0) * .8));
      for (let dx = 0; dx < w && x + dx < x1; dx++) for (let y = base - h; y < base; y++) {
        const win = dx % 2 === 1 && dx < w - 1 && (y - base + h) % 3 === 1;
        if (win && night && hash2(x + dx, y, 96) > .55) img.set(x + dx, y, lit[hash2(x, y, 97) > .5 ? 0 : 1], 1);
        else img.set(x + dx, y, win ? bld[3] : bld[dx === 0 ? 2 : dx === w - 1 ? 0 : 1]);
      }
      x += w + (hash2(i, 98) > .7 ? 1 : 0);
    }
    // The Willis Tower: stacked black tubes stepping back as they rise.
    for (const [l, r, y0] of [[-6, 6, wtop + 14], [-4, 6, wtop + 8], [-4, 3, wtop + 3], [-3, 3, wtop]])
      for (let y = y0; y < base; y++) for (let dx = l; dx <= r; dx++) {
        const win = dx % 2 === 0 && y % 2 === 0 && dx > l && dx < r;
        if (win && night && hash2(dx, y, 99) > .6) img.set(wx + dx, y, lit[1], 1);
        else img.set(wx + dx, y, wil[dx < -1 ? 2 : dx > 2 ? 0 : 1]);
      }
    for (const [tx, ty] of tips) for (let y = ty; y < wtop; y++) img.set(tx, y, wil[2]);
    const foam = P("#e9f6ff");
    for (let x = x0 - 4; x < x1 + 2; x++) if (hash2(x, 89) > .55) img.set(x, base + 2, foam);
  } else if (state === "PA") {
    // A red covered bridge on stone piers, joining two wooded banks; lanterns
    // hang at both ends after dark.
    const br = pxLayer(W, H), { bx, half, deck, ridge, bank, lamps } = habBridge(L);
    const grass = P("#3f6a34", "#4f7e3e", "#64944c", "#7aa85c"), stone = P("#6a6660", "#8a857c", "#a8a296", "#c4beb0");
    const red = P("#5a1a14", "#7e241a", "#9e3224", "#bc4632"), roof = P("#3a3634", "#4e4a46", "#66605a");
    const dark = P("#1e1410"), lamp = P("#ffe9a0");
    for (const side of [-1, 1]) {
      pxBlob(br, bx + side * (half + 9), bank + 3, 12, 5, grass, { flat: true, rough: .6, grain: 1, seed: 20 + side });
      for (let y = deck; y < L.water + 3; y++) for (let dx = -3; dx <= 3; dx++)
        br.set(bx + side * (half - 2) + dx, y, ramp(stone, .85 - (dx + 3) / 7 * .6 + ((y + dx) % 3 === 0 ? -.2 : 0), bx + dx, y));
    }
    // the walls: red boards with a row of small windows, open portals at the ends
    for (let y = ridge + 6; y <= deck; y++) for (let dx = -half; dx <= half; dx++) {
      const portal = Math.abs(dx) > half - 4 && y > ridge + 8, win = (y === deck - 7 || y === deck - 6) && Math.abs(dx) < half - 6 && (dx + 64) % 6 < 2;
      const trim = Math.abs(dx) === half - 4 && y > ridge + 7 || Math.abs(dx) > half - 4 && y === ridge + 8;
      br.set(bx + dx, y, trim ? P("#e8e2d4") : portal || win ? dark[0] : ramp(red, .8 - (y - ridge - 6) * .04 + (dx % 3 === 0 ? -.15 : 0), bx + dx, y));
    }
    for (let dx = -half; dx <= half; dx++) br.set(bx + dx, deck + 1, stone[0]);
    // the gable roof, overhanging both ends
    for (let y = ridge; y < ridge + 6; y++) for (let dx = -half - 2 + (ridge + 5 - y) % 1; dx <= half + 2; dx++)
      br.set(bx + dx, y, ramp(roof, .85 - (y - ridge) * .14, bx + dx, y));
    for (let dx = -half - 2; dx <= half + 2; dx++) br.set(bx + dx, ridge, roof[2]);
    for (const [lx2, ly] of lamps) { br.set(lx2, ly, lamp[0], night ? 1 : 0); br.set(lx2, ly - 1, roof[0]); }
    br.onto(img, P("#1a1410"));
    const foam = P("#e9f6ff");
    for (let dx = -half - 20; dx <= half + 20; dx++) if (hash2(dx, 91) > .5) img.set(bx + dx, L.water + 7 + (hash2(dx, 92) > .7 ? 1 : 0), foam);
  } else if (state === "NY") {
    // The Statue of Liberty on its island: a star fort, the stone pedestal, and
    // the copper-green statue holding up her torch.
    const lib = pxLayer(W, H), { sx, ftop, ptop, torch } = habLiberty(L);
    const isle = P("#4a6a3a", "#5a7e44", "#6e9450"), stone = P("#8a7e6a", "#a89a82", "#c4b69c", "#dccfb4");
    const fort = P("#7a7466", "#948e7e", "#aea896"), cu = P("#2f6a58", "#3f7f6a", "#5a9e86", "#7dbca2", "#a6d6c0");
    pxBlob(lib, sx, L.water + 3, 22, 5, isle, { flat: true, rough: .4, seed: 7 });
    for (let y = ftop; y < L.water + 1; y++) for (let dx = -13 - (y - ftop); dx <= 13 + (y - ftop); dx++)
      lib.set(sx + dx, y, ramp(fort, .8 - (dx + 16) / 32 * .6 - (y === ftop ? -.2 : 0), sx + dx, y));
    for (let y = ptop; y < ftop; y++) {
      const hw = y < ptop + 3 ? 6 : 5 + (y > ftop - 4 ? 1 : 0);
      for (let dx = -hw; dx <= hw; dx++) lib.set(sx + dx, y, ramp(stone, .85 - (dx + hw) / (2 * hw + 1) * .7 + (y === ptop + 2 ? -.3 : 0), sx + dx, y));
    }
    // her robe, widening to the feet
    const top = ptop - 22;
    for (let y = top + 6; y < ptop; y++) {
      const hw = Math.round(1.5 + (y - top - 6) * .14);
      for (let dx = -hw; dx <= hw; dx++) lib.set(sx + dx, y, ramp(cu, .85 - (dx + hw) / (2 * hw + 1) * .75 + ((y + dx) % 4 === 0 ? -.2 : 0), sx + dx, y));
    }
    pxBlob(lib, sx, top + 3, 2, 2, cu, { seed: 3 });  // head
    for (const [dx, dy] of [[-3, -1], [-2, -2], [0, -3], [2, -2], [3, -1]]) lib.set(sx + dx, top + 2 + dy, cu[3]);  // crown spikes
    // the raised arm and the torch with its gold flame
    for (let k = 0; k <= 9; k++) lib.set(sx - 2 - Math.round(k * .5), top + 6 - k, cu[k > 6 ? 3 : 2]);
    lib.set(torch[0] + 1, torch[1] + 2, cu[1]); lib.set(torch[0], torch[1] + 1, cu[2]); lib.set(torch[0] + 1, torch[1] + 1, cu[2]);
    for (const [dx, dy, c] of [[0, 0, "#ffd84a"], [1, 0, "#ffb02a"], [0, -1, "#ffe98a"], [1, -1, "#ffd84a"], [0, -2, "#fff4c0"]])
      lib.set(torch[0] + dx, torch[1] + dy, P(c), night ? 1 : 0);
    // the tablet in her other arm
    for (let y = top + 8; y < top + 12; y++) for (let dx = 2; dx <= 3; dx++) lib.set(sx + dx, y, cu[dx === 2 ? 3 : 1]);
    lib.onto(img, P("#1a2a24"));
    const foam = P("#e9f6ff");
    for (let dx = -26; dx <= 26; dx++) if (hash2(dx, 74) > .45) img.set(sx + dx, L.water + 6 + (hash2(dx, 75) > .7 ? 1 : 0), foam);
  } else if (land.sea === "iceberg") {
    // Icebergs drifting in the bay, white above and glassy blue below the water.
    const ice = pxLayer(W, H), ib = P("#9ac8e0", "#c4e2f0", "#e8f6fc", "#ffffff");
    for (const [fx, rx, ry, seed] of [[.3, 14, 10, 71], [.62, 9, 6, 72], [.82, 6, 4, 73]]) {
      const cx = L.sea + Math.round((W - L.sea) * fx);
      pxBlob(ice, cx, L.water + 1, rx, ry, ib, { flat: true, rough: .6, seed });
      for (let dx = -rx + 2; dx <= rx - 2; dx++) if (hash2(dx, seed) > .4) ice.set(cx + dx, L.water + 2, P("#6aa8d0")[0]);
    }
    ice.onto(img, P("#3a6a8a"));
  } else if (land.sea === "arch") {
    // The Gateway Arch: a tall stainless-steel curve on the far bank of the river.
    const ga = pxLayer(W, H), { ax, ground, half, h } = habArch(L), steel = P("#8a96a6", "#b4bec8", "#dce2e8", "#ffffff");
    pxBlob(ga, ax, ground + 3, half + 10, 3, P("#4f7e3e", "#64944c", "#7aa85c"), { flat: true, rough: .5, seed: 74 });
    for (let k = -half * 4; k <= half * 4; k++) {
      const u = k / (half * 4), y = Math.round(ground - h * (1 - u * u)), x = ax + Math.round(u * half), w = 1 + Math.round((1 - Math.abs(u)) * 0) + (Math.abs(u) > .8 ? 1 : 0);
      for (let d = 0; d <= w; d++) ga.set(x + (u < 0 ? -d : d), y, steel[u < 0 ? 3 - d : 1 + d]);
    }
    ga.onto(img, P("#3a4250"));
  } else if (land.sea === "needle") {
    // The Space Needle on a green point: three slender legs, the flying-saucer
    // top and its spire.
    const sn = pxLayer(W, H), { nx, ground, deck, tip } = habNeedle(L);
    const wht = P("#b8bcc4", "#dcdfe4", "#f4f6f8"), orange = P("#d8782a");
    pxBlob(sn, nx, ground + 3, 22, 4, P("#3f6a34", "#4f7e3e", "#64944c"), { flat: true, rough: .5, seed: 75 });
    for (let y = deck + 2; y < ground + 1; y++) {
      const k = (y - deck) / (ground - deck), spread = Math.round(2 + Math.abs(k - .45) * 7);
      sn.set(nx - spread, y, wht[0]); sn.set(nx + spread, y, wht[2]); sn.set(nx, y, wht[1]);
    }
    for (let y = deck - 3; y <= deck + 1; y++) {
      const hw = y === deck - 3 ? 5 : y === deck + 1 ? 6 : 9;
      for (let dx = -hw; dx <= hw; dx++) sn.set(nx + dx, y, y === deck - 1 ? orange[0] : wht[dx < 0 ? 2 : 1]);
    }
    for (let y = tip[1]; y < deck - 3; y++) sn.set(nx, y, wht[1]);
    sn.onto(img, P("#3a404a"));
  } else if (land.sea === "steamboat") {
    // A Mississippi paddlewheel steamboat: white decks with railings, two tall
    // black smokestacks and a red paddlewheel at the stern.
    const sb = pxLayer(W, H), { bx, wl, stacks } = habSteamboat(L);
    const wht = P("#c8ccd4", "#e8eaee", "#ffffff"), red = P("#8a1a1a", "#c8302a"), blk = P("#1e1e24", "#3a3a42");
    for (const [y0, y1, l, r] of [[wl - 4, wl + 1, -18, 16], [wl - 10, wl - 4, -15, 12], [wl - 15, wl - 10, -11, 8]])
      for (let y = y0; y < y1; y++) for (let dx = l; dx <= r; dx++) {
        const rail = y === y0 && dx % 2 === 0, win = y === y0 + 2 && dx % 3 === 0 && y1 - y0 > 4;
        sb.set(bx + dx, y, win ? blk[1] : rail ? wht[0] : wht[dx < 0 ? 2 : 1]);
      }
    for (const [sx, sy] of stacks) for (let y = sy; y < wl - 15; y++) { sb.set(sx, y, blk[0]); sb.set(sx + 1, y, blk[1]); }
    for (const [sx, sy] of stacks) { sb.set(sx - 1, sy, blk[0]); sb.set(sx + 2, sy, blk[0]); }
    for (let y = wl - 9; y <= wl + 1; y++) for (let dx = 17; dx <= 22; dx++) sb.set(bx + dx, y, (y + dx) % 3 === 0 ? red[0] : red[1]);
    sb.onto(img, P("#2a2a30"));
    const foam = P("#e9f6ff");
    for (let dx = -20; dx <= 24; dx++) if (hash2(dx, 76) > .45) img.set(bx + dx, wl + 2 + (hash2(dx, 77) > .7 ? 1 : 0), foam);
  } else if (state === "TX") {
    // Prickly pear: clumps of flat pads with yellow flowers and red fruit.
    const pad = P("#3d6a32", "#4f8240", "#669a4c", "#82b45e"), cac = pxLayer(W, H);
    for (const [fx, fy, n] of [[.26, 262, 4], [.52, 196, 3], [.58, 254, 4], [.07, 252, 3]]) {
      const cx = Math.round(L.w * fx);
      if (Math.abs(cx - L.pond.x) < L.pond.rx + 12 && Math.abs(fy - L.pond.y) < 22) continue;
      const pads = [[0, 0], [-5, -5], [5, -6], [1, -11], [-8, 1], [8, 0]].slice(0, n + 1);
      // Pads of different sizes, set at odd angles off each other, worn and uneven.
      pads.forEach(([dx, dy], i) => pxBlob(cac, cx + dx + Math.round((hash2(i, fx * 9, 811) - .5) * 2), fy + dy - 5,
        2 + Math.round(hash2(i, fx * 9, 812) * 2), 3 + Math.round(hash2(i, fx * 9, 813) * 2) + (i === 0 ? 1 : 0), pad, { rough: .5, grain: 1, seed: i + fx * 10 }));
      pads.forEach(([dx, dy], i) => {
        if (i % 2) { cac.set(cx + dx, fy + dy - 10, P("#ffd94a")); cac.set(cx + dx + 1, fy + dy - 10, P("#ffe98a")); }
        else if (i) cac.set(cx + dx + 2, fy + dy - 9, P("#c8304a"));
        for (const [sx, sy] of [[-1, -6], [1, -4], [-2, -3], [2, -7]]) if (hash2(dx + sx, dy + sy, i) > .4) cac.set(cx + dx + sx, fy + dy + sy, P("#e8e4b8"));
      });
    }
    cac.onto(img, P("#34552c"));
    // Bluebonnets: spikes of blue with a white tip, in drifts across the meadow.
    const bb = P("#2c3e9e", "#3a58d0", "#6f8cf0"), tip = P("#ffffff");
    for (let i = 0; i < 70; i++) {
      const x = Math.floor(hash2(i, 31) * (L.land - 10)) + 4, y = L.water + 14 + Math.floor(hash2(i, 32) * (HAB_H - L.water - 20));
      if (((x - L.pond.x) / (L.pond.rx + 6)) ** 2 + ((y - L.pond.y) / (L.pond.ry + 6)) ** 2 < 1) continue;
      img.set(x, y + 1, blade[0]); img.set(x, y + 2, blade[0]);
      img.set(x, y, bb[0]); img.set(x - 1, y - 1, bb[1]); img.set(x + 1, y - 1, bb[1]); img.set(x, y - 2, bb[2]); img.set(x, y - 3, tip);
    }
    // A ranch windmill and its stock tank by the coast.
    const wm = pxLayer(W, H), wx = L.land - 34, top = L.water - 52, gnd = L.water + 12;
    const steel = P("#3a3a40", "#55565e", "#74767e", "#9a9ca4");
    for (let y = top + 14; y <= gnd; y++) {
      const spread = Math.round((y - top - 14) * .16);
      wm.set(wx - 2 - spread, y, steel[1]); wm.set(wx + 2 + spread, y, steel[2]);
      if ((y - top) % 9 === 0) for (let dx = -1 - spread; dx <= 1 + spread; dx++) wm.set(wx + dx, y, steel[1]);
      if ((y - top) % 9 === 4) { wm.set(wx - spread, y, steel[0]); wm.set(wx + spread, y, steel[0]); }
    }
    for (let dx = -6; dx <= 6; dx++) { wm.set(wx + dx, top + 14, steel[2]); wm.set(wx + dx, top + 15, steel[0]); }
    // The wheel: blades around a hub.
    const hubX = wx - 1, hubY = top + 4;
    for (let a = 0; a < Math.PI * 2; a += Math.PI / 9) for (let rr = 3; rr <= 10; rr++) {
      const x = Math.round(hubX + Math.cos(a) * rr), y = Math.round(hubY + Math.sin(a) * rr);
      wm.set(x, y, rr === 10 ? steel[0] : steel[2 + (Math.cos(a - 2.3) > 0 ? 1 : 0)]);
    }
    for (let a = 0; a < Math.PI * 2; a += .1) wm.set(Math.round(hubX + Math.cos(a) * 10.5), Math.round(hubY + Math.sin(a) * 10.5), steel[0]);
    pxBlob(wm, hubX, hubY, 2, 2, steel);
    // The tail vane sticking out behind, with a red stripe.
    for (let dx = 2; dx <= 12; dx++) wm.set(wx + dx, hubY, steel[1]);
    for (let y = hubY - 4; y <= hubY + 2; y++) for (let dx = 12; dx <= 18; dx++) wm.set(wx + dx, y, y === hubY - 1 ? P("#c8302a") : ramp(steel, .8 - (dx - 12) / 10, wx + dx, y));
    // Stock tank: a round galvanised tank with water in it.
    for (let dx = -12; dx <= -2; dx++) for (let y = gnd - 4; y <= gnd + 1; y++) wm.set(wx + dx, y, y === gnd - 4 ? P("#7fc0e8") : ramp(steel, .9 - (dx + 12) / 12, wx + dx, y));
    wm.onto(img, P("#1e1e24"));
  }
  habLandmark(fc);
  // The tree for roosting birds and a spider's thread: a big leafy oak, or in
  // North Carolina a longleaf pine.
  const tree = pxLayer(W, H), tx = L.tree, kind = sc.tree, ground = 194;
  for (let y = ground - 5; y <= ground + 6; y++) for (let x = tx - 30; x <= tx + 40; x++)
    if (((x - tx - 6) / 34) ** 2 + ((y - ground) / 6) ** 2 <= 1 && dith(x, y, .5)) img.set(x, y, pxMix(img.get(x, y), 0x1e3a14, .45));
  const bark = P(...({ juniper: ["#3e342c", "#5a4c40", "#766656", "#92806e"], paloverde: ["#3e5a2a", "#527036", "#688844", "#80a056"],
    cottonwood: ["#3e3a34", "#5a544c", "#767066", "#928c82"], aspen: ["#4a4842", "#b8b6a8", "#dcdacc", "#f2f0e4"] }[kind]
    || ["#4a3020", "#6e4a2e", "#8f6840", "#a98050"]));
  if (kind === "palm") {
    // A cabbage palm: a tall, slightly curving trunk with crossed leaf bases,
    // and a round burst of fan fronds drooping at the tips.
    const top = 106, cx = (y) => tx + Math.round(Math.sin((ground - y) / 60) * 5);
    for (let y = top; y < 196; y++) {
      const hw = 2 + (y > 186 ? 1 : 0), x0 = cx(y);
      for (let dx = -hw; dx <= hw; dx++) {
        const v = .8 - (dx + hw) / (2 * hw + 1) * .7 + ((y + (dx > 0 ? 2 : 0)) % 4 === 0 ? -.25 : 0);
        tree.set(x0 + dx, y, ramp(bark, v, x0 + dx, y));
      }
    }
    const frond = P("#1e4a2c", "#2a6036", "#377642", "#4a8e4e", "#62a85e"), hx = cx(top), hy = top;
    for (let a = -Math.PI; a <= Math.PI; a += Math.PI / 11) {
      const len = 22 + hash2(Math.round(a * 10), 5, 46) * 8;
      for (let t = 2; t < len; t += .5) {
        const droop = Math.max(0, t - len * .45) ** 1.6 * .05;
        const x = Math.round(hx + Math.cos(a) * t), y = Math.round(hy + Math.sin(a) * t * .55 + droop + (Math.cos(a) ** 2) * t * .1);
        const wdt = t < len * .3 ? 1 : t < len * .8 ? 2 : 1;
        for (let k = 0; k < wdt; k++) tree.set(x, y + k, frond[Math.sin(a) < -.2 ? 4 - k : Math.sin(a) < .3 ? 3 - k : 2 - k]);
      }
    }
    pxBlob(tree, hx, hy + 2, 4, 3, P("#5a4a32", "#7a6444"), { rough: .5 });
    tree.onto(img, P("#13281a"));
  } else if (kind === "pine") {
    for (let y = 76; y < 196; y++) {
      const hw = 2 + (y > 186 ? 2 : 0);
      for (let dx = -hw; dx <= hw; dx++) {
        const v = .85 - (dx + hw) / (2 * hw + 1) * .8 + (hash2(tx + dx, y >> 2, 6) - .5) * .3;
        tree.set(tx + dx, y, ramp(bark, v, tx + dx, y));
      }
    }
    const leaf = P("#1c4426", "#265732", "#316b3d", "#3f8049", "#55985a");
    // Branches angling out from the trunk, each carrying a ragged pad of needle tufts.
    const pads = [[-14, 112, 11, 5], [15, 102, 12, 5], [-5, 84, 13, 7], [7, 93, 10, 5], [-10, 97, 9, 4], [2, 74, 8, 5], [12, 117, 7, 3]];
    for (const [dx, dy] of pads) for (let i = 0; i < Math.abs(dx) - 2; i++) tree.set(tx + Math.sign(dx) * i, dy + 2 + Math.floor(i / 4), bark[1]);
    tree.onto(img);
    pads.forEach(([dx, dy, rx, ry], i) => habNeedlePad(img, tx + dx, dy, rx, ry, leaf, 70 + i));
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
        if (kind === "aspen" && hash2(x >> 1, Math.floor(y / 5), 15) > .86) col = P("#2a2824");
        else if (u < -.45 && hash2(x, y, 14) > .85) col = bark[3];
        img.set(x, y, col);
      }
    }
    limb(tx + 2, 104, tx + 28, 100, 3, 2);
    limb(tx - 2, 110, tx - 22, 101, 3, 2);
    limb(tx + 2, 133, tx + 18, 130, 2, 1);
    // California's coast live oak is a darker, olive green.
    // Oaks stay green all year; other leafy trees turn in fall and are bare in a
    // snowy winter (New York's sugar maple is the reddest).
    // Junipers and palo verdes are evergreen; aspens and cottonwoods turn gold.
    const ever = kind === "oak" || kind === "juniper" || kind === "paloverde";
    const turn = !ever && sc.leaves === "fall";
    const leaf = kind === "juniper" ? P("#1e2c24", "#2c3e32", "#3e5444", "#526a56", "#6c846c")
      : kind === "paloverde" ? P("#3e5424", "#52702e", "#6a8c3a", "#86a84a", "#a6c262")
      : turn && (kind === "aspen" || kind === "cottonwood") ? P("#7a5a0e", "#a87e12", "#d0a420", "#e8c43a", "#f8e070")
      : kind === "oak" ? P("#24391c", "#344f25", "#486b2f", "#62893c", "#86ab55")
      : turn && kind === "maple" ? P("#6a1a12", "#9a2a16", "#c8441c", "#e8702a", "#f6b040")
      : turn ? P("#7a3a14", "#a8561a", "#d07a24", "#e8a032", "#f6c850")
      : P("#22492a", "#2f6633", "#41863d", "#5aa548", "#84c55c");
    if (ever || sc.leaves !== "bare") habLeafCrown(img, tx + 3, 90, 34, 40, leaf, 91);
    else {
      // Bare winter branches: a fan of twigs reaching up from the limbs.
      const twig = P("#3a2e26", "#54443a");
      for (let b = 0; b < 26; b++) {
        let x = tx + (hash2(b, 1, 92) - .5) * 30, y = 100 + hash2(b, 2, 92) * 20, a = -Math.PI / 2 + (hash2(b, 3, 92) - .5) * 2.2;
        for (let k = 0; k < 18 + hash2(b, 4, 92) * 16; k++) { img.set(x, y, twig[k < 6 ? 0 : 1]); a += (hash2(b, k, 93) - .5) * .5; x += Math.cos(a); y += Math.sin(a) * .9; }
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

// A leafy crown painted as dozens of irregular leaf clusters rather than a few
// round balls: an uneven outline, the clusters at the back darker, each lit on
// its upper left, ragged leafy edges, and sky showing through a few gaps.
function habLeafCrown(img, cx, cy, rx, ry, pal, seed) {
  const r = mulberry(seed), clumps = [];
  for (let i = 0; i < 170; i++) {
    const a = r() * Math.PI * 2, d = Math.sqrt(r());
    const env = .78 + .32 * vnoise(Math.cos(a) * 2 + 5, Math.sin(a) * 2 + 5, seed);   // a lumpy outline
    if (d > env) continue;
    const x = cx + Math.cos(a) * d * rx, y = cy + Math.sin(a) * d * ry * (Math.sin(a) > 0 ? .8 : 1);
    clumps.push({ x, y, r: 4 + r() * 5, back: r() < .4, s: i });
  }
  clumps.sort((a, b) => (b.back - a.back) || (a.y - b.y));
  for (const k of clumps) {
    const R = Math.ceil(k.r) + 1, gl = -(k.x - cx) / rx * .35 - (k.y - cy) / ry * .55;
    for (let dy = -R; dy <= R; dy++) for (let dx = -R; dx <= R; dx++) {
      const x = Math.round(k.x + dx), y = Math.round(k.y + dy);
      const ang = Math.atan2(dy, dx), edge = k.r * (.82 + .3 * hash2(Math.round(ang * 4), k.s, seed + 1));
      const dd = Math.hypot(dx, dy * 1.15);
      if (dd > edge) continue;
      if (dd > edge - 1.3 && hash2(x, y, seed + 2) > .7) continue;                 // ragged leaf tips
      let v = .5 + gl + (-dx / k.r * .3 - dy / k.r * .45) - (k.back ? .3 : 0) + (hash2(x, y, seed + 3) - .5) * .18;
      if (dd > edge - 1.4 && dy > 0) v -= .2;                                       // shade under each cluster
      img.set(x, y, pal[Math.max(0, Math.min(pal.length - 1, Math.floor(v * pal.length)))]);
    }
  }
}
// A pine's pad of needles: overlapping flat tufts lit from above, with needle
// strokes hanging from the underside.
function habNeedlePad(img, cx, cy, rx, ry, pal, seed) {
  const r = mulberry(seed);
  for (let i = 0; i < 16; i++) {
    const tx = cx + (r() - .5) * rx * 1.7, ty = cy + (r() - .5) * ry * 1.1, w = 2.5 + r() * 3, h = 1.5 + r() * 1.5;
    if (((tx - cx) / rx) ** 2 + ((ty - cy) / ry) ** 2 > 1) continue;
    for (let dy = -Math.ceil(h); dy <= Math.ceil(h) + 1; dy++) for (let dx = -Math.ceil(w); dx <= Math.ceil(w); dx++) {
      const x = Math.round(tx + dx), y = Math.round(ty + dy);
      if ((dx / w) ** 2 + (dy / h) ** 2 > 1 + hash2(x, y, seed) * .5) continue;
      const v = .55 - dy / h * .35 - (tx - cx) / rx * .15 - (ty - cy) / ry * .25 + (hash2(x, y, seed + 1) - .5) * .2;
      img.set(x, y, pal[Math.max(0, Math.min(pal.length - 1, Math.floor(v * pal.length)))]);
    }
    for (let n = 0; n < 4; n++) {
      const x = Math.round(tx + (r() - .5) * w * 1.6), y = Math.round(ty + h);
      for (let k = 0; k < 2 + (n % 2); k++) img.set(x + (n % 2 ? k >> 1 : -(k >> 1)), y + k, pal[1]);
    }
  }
}
// Fluffy clouds, shaded underneath, painted once per time of day.
const habClouds = {};
// ---- Each state's own scenery (2026-11-07) ----------------------------------
// Inland states look out over a lake or a river instead of the sea; the Great
// Lakes states over a freshwater sea with no far shore.
const HAB_WATER = {
  sea: { water: ["#1b4f8c", "#22629f", "#2c78b6", "#3a8fca", "#58a9dc", "#83c6ec"], line: "#cdeefc",
         sand: ["#cdb27a", "#dcc38b", "#e9d49f", "#f4e3b6"], wet: ["#b39a68", "#c4aa76"] },
  great: { water: ["#1a5070", "#226684", "#2c7c98", "#3c93aa", "#5cadbe", "#8acad4"], line: "#d4f0f2",
           sand: ["#c8b08a", "#d8c29c", "#e6d4b0", "#f2e4c6"], wet: ["#a89878", "#bcaa88"] },
  lake: { water: ["#173e4e", "#1d5262", "#246874", "#2f7e86", "#46989a", "#6cb4b0"], line: "#9ccfc8",
          sand: ["#6e6a62", "#8a857a", "#a6a092", "#c2bcac"], wet: ["#5a564e", "#6e6a60"] },
  river: { water: ["#3a4a34", "#46593c", "#546a46", "#647c52", "#7a9262", "#96aa7a"], line: "#b8c8a0",
           sand: ["#8a7656", "#a08a66", "#b6a07a", "#cab690"], wet: ["#6e5e44", "#806e50"] },
  muddy: { water: ["#5a4632", "#6c5640", "#80674e", "#94795c", "#a88e6e", "#c0a886"], line: "#d6c4a4",
           sand: ["#9a7a58", "#ae8e68", "#c2a27a", "#d4b890"], wet: ["#7a5e42", "#8c6e50"] },
  red: { water: ["#6a3a28", "#7e4832", "#92583e", "#a66a4c", "#ba7e5e", "#cc9878"], line: "#e0bca0",
         sand: ["#a8583a", "#bc6a48", "#cc7e58", "#da946c"], wet: ["#8a4430", "#9c5038"] },
};
// Which water each state looks out on. Everything else is the sea.
const HAB_WATER_KIND = {
  AZ: "river", AR: "river", CO: "lake", ID: "lake", IA: "muddy", KS: "muddy", KY: "river", MO: "muddy",
  MT: "lake", NE: "muddy", NV: "lake", NM: "muddy", ND: "muddy", OK: "red", SD: "lake", TN: "lake", UT: "lake",
  VT: "lake", WV: "river", WY: "lake", NH: "lake", IN: "great", WI: "great", MN: "great", MS: "muddy",
};
// The kind ("sea", "great", or an inland water) for drawing, and whether it has a far shore.
const habWaterKind = (state) => HAB_WATER_KIND[state] || "sea";

// Across a lake or river: a dark tree line on the far bank, and in still water
// the mountains reflected, broken by ripples.
function habFarBank(c) {
  const { img, P, W, L, wk, state } = c, x0 = L.sea - 30, o = HAB_FAR_BANK[state] || {};
  const bank = P(...(o.bank || ["#1e3424", "#284430", "#34543a", "#426446"])), lineC = P(HAB_WATER[wk].line);
  const still = wk === "lake";
  for (let x = x0; x < W; x++) {
    const th = Math.round((o.h ?? 4) + vnoise(x / 9, 0, 120) * (o.h ?? 4) + (x % 3 === 1 && o.spiky !== false ? 2 : 0));
    for (let y = L.water - th; y <= L.water; y++) {
      const v = .7 - (y - L.water + th) / (th + 1) * .6 + (hash2(x, y, 121) - .5) * .4;
      img.set(x, y, ramp(bank, v, x, y));
    }
    img.set(x, L.water + 1, lineC);
  }
  if (!still) {
    // Current: long pale streaks drifting downstream.
    for (let y = L.water + 3; y < c.H; y += 2) for (let x = x0; x < W; x++)
      if (vnoise(x / 16, y / 1.2, 124) > .74) img.set(x, y, pxMix(img.get(x, y), lineC, .3));
    return;
  }
  // Reflections: the far scenery mirrored in the lake, fading into the water color.
  const water = P(...HAB_WATER[wk].water);
  for (let y = L.water + 2; y < L.water + 60; y++) {
    const k = (y - L.water) / 60, sy = 2 * L.water - y + 1;
    const wob = Math.round(Math.sin(y * 1.7) * (k * 2.2));
    for (let x = x0; x < W; x++) {
      const src = img.get(x + wob, sy);
      if (src < 0 || hash2(x >> 2, y, 122) < k * .5) continue;
      const base = ramp(water, .6 - k * .4, x, y);
      img.set(x, y, pxMix(pxMix(src, 0x10263a, .22), base, .18 + k * .75));
    }
    // light ripple lines on the water
    for (let x = x0; x < W; x++) if (vnoise(x / 7, y / 1.3, 123) > .8) img.set(x, y, pxMix(img.get(x, y), lineC, .45));
  }
}
const HAB_FAR_BANK = {
  AZ: { bank: ["#6a2e1e", "#843c28", "#9e4e34", "#b46444"], h: 3, spiky: false },
  NM: { bank: ["#4a5a2a", "#5e7034", "#74883e", "#8aa04c"], h: 3 },
  NE: { bank: ["#3e5426", "#4e6830", "#62803a", "#789646"], h: 4 },
  KS: { bank: ["#3e5426", "#4e6830", "#62803a", "#789646"], h: 4 },
  ND: { bank: ["#5e6a3a", "#727e46", "#889454", "#9eaa66"], h: 2, spiky: false },
  OK: { bank: ["#3e5426", "#4e6830", "#62803a", "#789646"], h: 3 },
  UT: { bank: ["#7a3a22", "#94482c", "#ae5a38", "#c47048"], h: 3, spiky: false },
  NV: { bank: ["#6a6452", "#807a64", "#989078", "#aea68c"], h: 2, spiky: false },
};

// A mountain range in layers, back to front. Each layer: the ground line `base`,
// its peaks [x as a fraction of the width, top y, half-width, sharpness], how
// jagged the ridgeline is, the snowline and treeline (y), and how hazy it is.
function habRange(c, o) {
  const { img, P, foot, atmo, W } = c, span = Math.min(c.coastEnd, W + 2);
  const snowPal = P("#8e9fc0", "#b8c6e2", "#dfe7f6", "#ffffff");
  o.layers.forEach((ly, li) => {
    const rock = P(...ly.rock), forest = ly.forest ? P(...ly.forest) : null, seed = 300 + li * 17 + (o.seed || 0);
    const hm = new Float32Array(span + 4);
    for (let x = -1; x <= span + 2; x++) {
      let h = ly.base;
      for (const [px, top, hw, sharp = 1] of ly.peaks) {
        const d = Math.abs(x - px * W) / hw;
        h = Math.min(h, top + Math.pow(d, sharp) * (ly.base - top));
      }
      const jag = (1 - Math.abs(vnoise(x / (ly.jagW || 6), li, seed) * 2 - 1)) * (ly.jag ?? 5)
        + (vnoise(x / 2.2, li, seed + 1) - .5) * (ly.fine ?? 2);
      hm[x + 1] = c.fade(x, Math.round(h - jag + (ly.jag ?? 5) * .5));
    }
    for (let x = 0; x < span; x++) {
      const h = hm[x + 1], s = (hm[x + 2] - hm[x]) / 2;
      const snowY = (ly.snow ?? -99) + (vnoise(x / 8, 0, seed + 2) - .5) * 14;
      const treeY = (ly.tree ?? 999) + (vnoise(x / 5, 0, seed + 3) - .5) * 10;
      for (let y = h; y < foot; y++) {
        const dep = y - h;
        // Gullies and couloirs streaking down the faces, slanting with the slope.
        const g = 1 - Math.abs(vnoise(x / 2.4 - dep * s * .25, dep / 9, seed + 4) * 2 - 1);
        const strata = ly.bands ? Math.sin((y + vnoise(x / 30, 0, seed + 5) * 6) * ly.bands) * .12 : 0;
        let v = .52 - Math.max(-1.6, Math.min(1.6, s)) * .2 + (g - .5) * .45 + strata + (vnoise(x / 4, y / 3, seed + 6) - .5) * .16;
        if (dep === 0) v += .15;
        let col;
        if (forest && y > treeY - (x % 3 === 1 ? 2 : x % 3 === 0 ? 1 : 0)) {
          // Dark conifers below the treeline, in tiny pointed crowns.
          const crown = (hash2(x >> 1, (y + (x >> 1) * 3) >> 2, seed + 7) - .5) * .6;
          col = ramp(forest, .55 - s * .12 + crown - (y - treeY) * .004, x, y);
          if (ly.aspen && c.season === "fall" && hash2(x >> 2, y >> 2, seed + 8) > .72) col = ramp(P("#a8720e", "#d0961a", "#ecc040"), .5 + crown, x, y);
        } else if (y < snowY + (g > .55 ? 9 : 0) - (s > .8 ? 6 : 0) || (c.snowy && y < treeY - 2 && g > .4)) {
          col = ramp(snowPal, v + .3 - (g < .3 ? .25 : 0), x, y);
        } else col = ramp(rock, v, x, y);
        img.set(x, y, atmo(col, ly.haze ?? .2));
      }
    }
  });
}

const HAB_ROCK = {
  maroon: ["#3e2026", "#5a2e32", "#7a403e", "#965650", "#b07066"],
  granite: ["#40434f", "#585c6a", "#727786", "#8e93a2", "#acb0bc"],
  pale: ["#56545a", "#72707a", "#8e8c96", "#acaab2", "#cac8ce"],
  argillite: ["#46302e", "#5e4038", "#765644", "#8a6e54", "#a08a6a"],
  blue: ["#5a6a8c", "#6e7ea0", "#8292b4", "#98a6c6", "#b0bcd8"],
};
const HAB_CONIFER = ["#122418", "#1a3020", "#22402a", "#2c5034"];

// Ridged noise: sharp crests where plain noise crosses its middle.
const habRidged = (x, z, s) => {
  let t = 0, a = .6, f = 1;
  for (let o = 0; o < 3; o++, a *= .45, f *= 2.1) { const n = 1 - Math.abs(vnoise(x * f, z * f, s + o) * 2 - 1); t += a * n * (.5 + .5 * n); }
  return t / .93;
};
// A landscape seen from the side, drawn like a relief model: the land is a height
// map h(x, z) sliced front to back (z = 0 nearest), each slice smaller with
// distance and hidden behind nearer ones. Shading comes from the slope, so
// ridges, gullies and spurs catch the light from the upper left.
// o: h(x, z) in pixels, n slices, shrink per slice, color(x, z, ht, slopeX, slopeZ, y) -> packed color.
function habTerrain(c, o) {
  const { img, foot, W } = c, span = Math.min(c.coastEnd, W + 2), n = o.n || 48, k = o.shrink ?? .022;
  const lift = o.lift || 0, vs = o.vs || 1;
  for (let x = 0; x < span; x++) {
    let ymin = foot + 1;
    for (let i = 0; i < n && ymin > 0; i++) {
      const f = 1 / (1 + i * k), ht = o.h(x, i);
      if (ht <= 0) continue;
      const y = Math.round(foot - ht * f * vs - lift * (1 - f));
      if (y >= ymin) continue;
      const sx = (o.h(x + 1, i) - o.h(x - 1, i)) / 2, sz = (o.h(x, i + 1) - o.h(x, i - 1)) / 2;
      for (let yy = y; yy < ymin; yy++) {
        const col = o.color(x, i, ht - (yy - y) / f / vs, sx, sz, yy, yy - y);
        img.set(x, yy, c.atmo(col, Math.min(.85, (o.haze ?? .1) + i * (o.hazeK ?? .012))));
      }
      ymin = y;
    }
  }
}
// Massifs for habTerrain: [x as a fraction of the width, z (slice), height, half-width
// in x, half-depth in z, power]; the ridged noise breaks each into peaks and spurs.
function habMassifs(c, ms, { rough = .55, scale = 26, seed = 500, floor = 0 } = {}) {
  const W = c.W;
  return (x, z) => {
    let h = floor;
    for (const [mx, mz, mh, wx, wz, p = 1.3] of ms) {
      const d = Math.hypot((x - mx * W) / wx, (z - mz) / wz);
      if (d >= 1) continue;
      const e = Math.pow(1 - d, p);
      // Ridged noise breaks the cone into peaks and spurs; a finer octave carves
      // gullies and buttresses into the faces so they never read as flat triangles.
      const fine = habRidged(x / (scale * .28), z / (scale * .2), seed + 3) - .55;
      h = Math.max(h, mh * e * (1 - rough + rough * 1.3 * habRidged(x / scale, z / (scale * .5), seed) + .22 * fine * Math.min(1, e * 2)));
    }
    return h;
  };
}
// Rock, snow and forest by height and slope, the usual mountain coloring.
function habMountainColor(c, o) {
  const P = c.P, rock = P(...o.rock), snow = P("#8e9fc0", "#b8c6e2", "#dfe7f6", "#ffffff");
  const forest = P(...(o.forest || HAB_CONIFER)), fall = o.fall && c.season === "fall" ? o.fall.map((f) => P(...f)) : null;
  return (x, z, ht, sx, sz, y, dep) => {
    const steep = Math.abs(sx) + Math.max(0, -sz) * .5;
    const light = clamp01(.55 - Math.max(-.4, Math.min(.4, sx * .2)) + sz * .05 + (vnoise(x / 9, y / 6, 610 + z) - .5) * .12 - dep * .005 + (dep < 1 ? .15 : 0));
    const bands = o.bands ? Math.sin((ht + vnoise(x / 25, z, 611) * 6) * o.bands) * .14 : 0;
    // Vertical gullies and ribs running down the faces: they break up the flat
    // planes, and snow lingers longer in the gullies.
    const rib = habRidged(x / 2.4, y / 8 + z * .7, 617) - .5;
    const sn = (o.snow ?? 9999) + (vnoise(x / 7, z / 2, 612) - .5) * 14 + rib * 16;
    const tr = (o.tree ?? -1) + (vnoise(x / 5, z / 3, 613) - .5) * 10;
    if (ht > sn && steep < 2.6 || c.snowy && ht > tr && steep < 1.4) return ramp(snow, light + .25 + rib * .3, x, y);
    if (ht < tr && steep < 2.4) {
      // Little tree crowns: a lit pixel up-left of each, darker between them.
      const cx = x % 3, cy = (y + (x / 3 | 0) * 2) % 4, crown = cx === 0 && cy === 0 ? .26 : cx === 2 || cy === 3 ? -.18 : 0;
      if (fall) {
        // Groves of fall color, in patches rather than speckles.
        const g = vnoise(x / 9, y / 5, 615);
        if (g < o.fallShare) return ramp(fall[Math.floor(vnoise(x / 14, y / 9, 616) * fall.length * .999)], light + crown + .1, x, y);
      }
      return ramp(forest, light * .9 + crown + rib * .2, x, y);
    }
    return ramp(rock, light + bands + rib * .4, x, y);
  };
}

// Benches and cliffs: heights snap to flat ledges with steep steps between.
const habTerrace = (h, step, cliff = .72) => {
  const f = h / step, i = Math.floor(f), t = f - i;
  return (i + (t < cliff ? t * .12 : .0864 + (t - cliff) / (1 - cliff) * .9136)) * step;
};
// Layered rock colored by height (bands: [[from height, ramp], ...] low to high),
// lit by slope, with sparse dark shrubs on the flats when `shrubs` is set.
function habStrataColor(c, o) {
  const P = c.P, bands = o.bands.map(([h, pal]) => [h, P(...pal)]), shrub = o.shrubs ? P(...o.shrubs) : null;
  const snow = P("#8e9fc0", "#b8c6e2", "#dfe7f6", "#ffffff");
  return (x, z, ht, sx, sz, y, dep) => {
    const light = clamp01(.58 - Math.max(-.4, Math.min(.4, sx * .22)) + (vnoise(x / 8, y / 5, 640 + z) - .5) * .1 - Math.min(dep, 20) * .01 + (dep === 0 ? .18 : 0));
    if (o.snow && ht > o.snow + (vnoise(x / 6, z, 641) - .5) * 10 && Math.abs(sx) < 2) return ramp(snow, light + .2, x, y);
    const hh = ht + (vnoise(x / 18, z / 2, 642) - .5) * (o.wobble ?? 4);
    let pal = bands[0][1];
    for (const [h, p] of bands) if (hh >= h) pal = p;
    if (shrub && dep < 3 && Math.abs(sx) < .6 && hash2(x, y + z * 13, 643) > .82) return ramp(shrub, light, x, y);
    return ramp(pal, light + Math.sin(hh * (o.fine ?? 1.7)) * .1, x, y);
  };
}
// A lone feature for habTerrain: adds a spire or butte of height h at x (fraction),
// slice z, half-width w, steepness p.
const habSpire = (c, x0, z0, h, w, p = 3, wz = 3) => (x, z) => {
  const d = Math.hypot((x - x0 * c.W) / w, (z - z0) / wz);
  return d < 1 ? h * Math.pow(1 - d, 1 / p) : 0;
};

// Long wooded ridges one behind another (the Appalachians, the Ozarks): ls is
// [slice, height, wavelength in px] front to back. Haze turns them blue with distance.
function habRidgeLine(c, ls, seed) {
  return (x, z) => {
    let h = 0;
    for (const [lz, lh, wl] of ls) {
      const d = Math.abs(z - lz);
      if (d > 2.5) continue;
      const crest = lh * (.62 + .5 * fbm(x / wl, lz, seed) + .12 * habRidged(x / (wl * .4), lz, seed + 9));
      h = Math.max(h, crest * (1 - d / 3));
    }
    return h;
  };
}
// Forest colors for hills: conifers and hardwoods that follow the season, with
// misty blue haze (`blue`) deep in the distance.
function habForestColor(c, o = {}) {
  const P = c.P, conifer = P(...HAB_CONIFER), hard = P(...(o.hard || ["#1e3a22", "#2a4e2c", "#386438", "#4a7a44"]));
  const fall = [P("#6a1e14", "#922c18", "#b84420", "#d8642a"), P("#8a4612", "#b05e16", "#d07e22", "#e8a034"), P("#8a6e12", "#b0901c", "#d0b02a", "#e8cc48")];
  const bare = P("#4a4038", "#5e5248", "#74685c", "#8a7e70"), snow = P("#a8b4c8", "#c8d2e2", "#e4eaf2", "#ffffff");
  const blue = o.blue ? hexRgb(o.blue) : null;
  return (x, z, ht, sx, sz, y, dep) => {
    const light = clamp01(.55 - sx * .22 + (dep === 0 ? .12 : 0) - Math.min(dep, 24) * .008);
    const cx = x % 3, cy = (y + (x / 3 | 0) * 2) % 4, crown = cx === 0 && cy === 0 ? .28 : cx === 2 || cy === 3 ? -.22 : 0;
    const pine = vnoise(x / 7, y / 5 + z, 650) < (o.pines ?? .35);
    let col;
    if (c.snowy) col = pine ? ramp(conifer, light + crown - .1, x, y) : ramp(bare, light + crown, x, y);
    else if (pine) col = ramp(conifer, light + crown, x, y);
    else if (c.sc.leaves === "fall") col = ramp(fall[Math.floor(vnoise(x / 6, y / 4 + z * 3, 651) * 2.999)], light + crown + .05, x, y);
    else if (c.sc.leaves === "bare") col = ramp(bare, light + crown, x, y);
    else col = ramp(hard, light + crown, x, y);
    // Snow dusting the woods: on open ground between crowns and on branch tops.
    if (c.snowy && vnoise(x / 1.5, y, 653) > (pine ? .66 : .5)) col = pxMix(col, 0xe8eef6, .6);
    if (blue && z > (o.blueFrom ?? 10)) col = pxMix(col, (blue[0] << 16) | (blue[1] << 8) | blue[2], Math.min(.75, (z - (o.blueFrom ?? 10)) * .03));
    // Mist lying in the valleys between ridges.
    if (o.mist && dep > 6 && vnoise(x / 30, z, 652) > .45) col = pxMix(col, 0xe8f0f4, Math.min(.6, (dep - 6) * .05));
    return col;
  };
}
// Farm fields to the horizon: crop rows that converge with distance.
function habFieldsColor(c, o) {
  const P = c.P, fields = o.fields.map((f) => P(...f)), snow = P("#c8d2e2", "#e4eaf2", "#ffffff");
  return (x, z, ht, sx, sz, y, dep) => {
    if (c.snowy) return ramp(snow, .6 - sx * .1 + (hash2(x, y, 660) - .5) * .3, x, y);
    const plot = Math.floor(vnoise(x / 40, z / 6, 661) * fields.length * .999), pal = fields[plot];
    const row = (x + z * 7) % (z < 8 ? 3 : 2) === 0 ? -.18 : 0;
    return ramp(pal, .55 - sx * .2 + row + (hash2(x, y, 662) - .5) * .2, x, y);
  };
}

// Sabal palmettos standing over the low woods.
function habPalmettos(c) {
  const { img, P, foot } = c, trunk = P("#6a5a44", "#7e6c52"), frond = P("#2a4a26", "#3a5e30", "#4e763c");
  for (let i = 0; i < 14; i++) {
    const x = Math.round(hash2(i, 1, 570) * (c.coastEnd - 20)) + 8, h = 16 + Math.round(hash2(i, 2, 570) * 12), y0 = foot - 6 - Math.round(hash2(i, 3, 570) * 6);
    for (let j = 0; j < h; j++) img.set(x + (j > h * .6 ? 1 : 0), y0 - j, c.atmo(trunk[j % 3 ? 0 : 1], .15));
    const top = y0 - h;
    for (let a = 0; a < 9; a++) {
      const ang = -Math.PI + a * Math.PI / 8, len = 5 + (a % 2);
      for (let t = 1; t <= len; t++) img.set(x + 1 + Math.round(Math.cos(ang) * t), top + Math.round(Math.sin(ang) * t * .6 + (t > 3 ? (t - 3) * .6 : 0)), c.atmo(frond[a % 3], .15));
    }
  }
}
// Farm buildings on the far fields: a red barn and silos, a white farmhouse, a
// concrete grain elevator in Kansas, an oil pumpjack in Oklahoma.
function habFarm(c, st) {
  const { img, P, W, foot } = c, fl = pxLayer(W, c.H), sh = (col, k) => c.atmo(col, k ?? .12);
  const barnAt = (bx, gy, s, round) => {
    const red = P("#6a1a14", "#8e2a1e", "#b03c2a"), roof = P("#3a3430", "#56504a"), white = P("#d8d4c8", "#f2eee4");
    const w = 7 * s, h = 6 * s;
    for (let y = gy - h; y < gy; y++) for (let dx = -w; dx <= w; dx++) fl.set(bx + dx, y, sh(red[dx < -w / 2 ? 2 : dx > w / 2 ? 0 : 1]));
    for (let k = 0; k <= 5 * s; k++) for (let dx = -(w + 1) + (round ? Math.round(k * k / (5 * s) * .9) : k); dx <= w + 1 - (round ? Math.round(k * k / (5 * s) * .9) : k); dx++)
      fl.set(bx + dx, gy - h - k, sh(roof[dx < 0 ? 1 : 0]));
    for (let y = gy - 3 * s; y < gy; y++) for (let dx = -s; dx <= s; dx++) fl.set(bx + dx, y, sh(white[0]));
    for (let dx = -s - 1; dx <= s + 1; dx++) fl.set(bx + dx, gy - 3 * s - 1, sh(white[1]));
  };
  const silo = (sx, gy, h, w, dome) => {
    const pal = dome ? P("#3a4a5e", "#4e6078", "#64768e") : P("#8a8a8e", "#a8a8ac", "#c8c8cc");
    for (let y = gy - h; y < gy; y++) for (let dx = 0; dx < w; dx++) fl.set(sx + dx, y, sh(pal[dx === 0 ? 2 : dx === w - 1 ? 0 : 1]));
    for (let dx = 1; dx < w - 1; dx++) fl.set(sx + dx, gy - h - 1, sh(pal[2]));
    fl.set(sx + (w >> 1), gy - h - 2, sh(pal[2]));
  };
  const house = (hx, gy) => {
    const wall = P("#c8c4b8", "#e8e4d8", "#faf8f0"), roof = P("#4a4440", "#625c56");
    for (let y = gy - 6; y < gy; y++) for (let dx = 0; dx < 9; dx++) fl.set(hx + dx, y, sh(wall[dx < 2 ? 2 : 1]));
    for (let k = 0; k < 4; k++) for (let dx = k - 1; dx <= 9 - k; dx++) fl.set(hx + dx, gy - 7 - k, sh(roof[1]));
    for (const wx of [2, 6]) fl.set(hx + wx, gy - 4, sh(P("#3a4a5e")));
  };
  const gy = foot - 8;
  if (st === "KS") {
    // A prairie grain elevator: a row of tall concrete bins with a head house on top.
    const ex = Math.round(W * .62), con = P("#9a968c", "#b8b4aa", "#d4d0c6", "#ecE8de".toLowerCase());
    for (let b = 0; b < 4; b++) for (let y = gy - 40; y < gy; y++) for (let dx = 0; dx < 6; dx++)
      fl.set(ex + b * 6 + dx, y, sh(con[dx === 0 ? 3 : dx === 5 ? 0 : dx < 3 ? 2 : 1], .2));
    for (let y = gy - 52; y < gy - 40; y++) for (let dx = 6; dx < 16; dx++) fl.set(ex + dx, y, sh(con[dx < 9 ? 2 : 1], .2));
    for (let dx = 7; dx < 15; dx++) fl.set(ex + dx, gy - 53, sh(con[0], .2));
    for (let y = gy - 14; y < gy; y++) for (let dx = -10; dx < 0; dx++) fl.set(ex + dx, y, sh(P("#8a8a90")));
    barnAt(Math.round(W * .86), gy + 3, 2);
  } else if (st === "OK") {
    // An oil pumpjack nodding in a red-dirt field.
    const px = Math.round(W * .66), steel = P("#2a2a30", "#3e3e46", "#56565e"), y0 = gy;
    for (let y = y0 - 16; y < y0; y++) { fl.set(px - 1 - ((y0 - y) >> 3), y, sh(steel[1])); fl.set(px + 1 + ((y0 - y) >> 3), y, sh(steel[0])); }
    for (let dx = -14; dx <= 10; dx++) fl.set(px + dx, y0 - 17 + Math.round(dx * .12), sh(steel[2]));
    for (let k = 0; k < 6; k++) for (let dx = -16; dx <= -13; dx++) fl.set(px + dx, y0 - 22 + k, sh(steel[1]));
    for (let y = y0 - 15; y < y0; y++) fl.set(px - 15, y, sh(steel[0]));
    for (let dx = -6; dx <= 6; dx++) fl.set(px + dx, y0, sh(steel[0]));
    barnAt(Math.round(W * .86), gy + 3, 2);
  } else if (st === "IA") {
    barnAt(Math.round(W * .3), gy, 3); silo(Math.round(W * .3) + 25, gy, 40, 7); silo(Math.round(W * .3) + 33, gy, 34, 6, true);
    house(Math.round(W * .58), gy + 2);
  } else if (st === "WI") {
    // A dairy barn with a rounded gambrel roof and blue silos.
    barnAt(Math.round(W * .4), gy, 3, true); silo(Math.round(W * .4) + 25, gy, 44, 7, true); silo(Math.round(W * .4) + 33, gy, 38, 7, true);
    house(Math.round(W * .18), gy + 2);
  } else if (st === "IN") {
    barnAt(Math.round(W * .3), gy - 4, 2); silo(Math.round(W * .3) + 16, gy - 4, 30, 5);
  }
  fl.onto(c.img, P("#2a2a2a"));
}

// Biomes for the near scenery: the foothills, the meadow floor, the pond and the
// shore change with them. States without one keep the classic look.
const HAB_BIOME = {};
for (const [bio, sts] of Object.entries({
  desert: "AZ NM NV UT", prairie: "ND SD NE KS OK TX CA", alpine: "CO WY MT ID",
  forest: "TN WV KY AR VT NH PA NY OH IN IL IA MO WI MI MA CT RI NJ DE MD VA NC GA AL",
  north: "ME MN AK WA OR", marsh: "LA MS FL SC", tropical: "HI",
})) for (const st of sts.split(" ")) HAB_BIOME[st] = bio;
const HAB_FARM_STATES = new Set(["KS", "IA", "OK", "IN", "WI"]);
const HAB_GROUND = {
  desert: ["#a88c5c", "#b89c6a", "#c8ac7a", "#d6bc8c"], UT: ["#a8704a", "#b8805a", "#c8926a", "#d6a47c"],
  NM: ["#a8845a", "#b89468", "#c8a678", "#d6b88a"],
};
// Leafy canopy seen from the side: lumpy crowns lit from the upper left, darker
// in the gaps between trees.
function habCanopy(c, pals, o = {}) {
  const s = o.size || 4;
  return (x, z, ht, sx, sz, y, dep) => {
    const n = vnoise(x / s, y / (s * .8), 720 + z), m = vnoise((x + 1) / s, (y + 1) / (s * .8), 720 + z);
    let light = .52 + (n - m) * 3.2 + (n - .5) * .5 - Math.min(dep, 30) * .012 - sx * .08;
    if (n < .28) light -= .3;
    const pal = pals.length > 1 ? pals[Math.floor(vnoise(x / 11, y / 7 + z * 2, 721) * pals.length * .999)] : pals[0];
    return ramp(pal, light, x, y);
  };
}
// Crowns along a skyline: round bumps for leafy trees, spires for conifers.
function habCrowns(x, z, kind, s) {
  const p = kind === "conifer" ? 5 : 7, cell = Math.floor((x + z * 3) / p), j = hash2(cell, z, 722);
  const u = ((x + z * 3) % p) / p, hh = s * (.6 + j * .6);
  if (kind === "conifer") return hh * 1.6 * Math.max(0, 1 - Math.abs(u * 2 - 1) * 1.15);
  return hh * Math.sqrt(Math.max(0, 1 - (u * 2 - 1) ** 2));
}
function habLeafPals(c, kind) {
  const P = c.P, sc = c.sc;
  const green = { forest: ["#1e3a1e", "#2a4e26", "#386432", "#4a7a3e", "#5e9048"], marsh: ["#26382a", "#344a34", "#425c3e", "#58704c"],
    tropical: ["#1a4a20", "#26622a", "#347a34", "#4a9440", "#66ae54"], conifer: HAB_CONIFER }[kind] || ["#1e3a1e", "#2a4e26", "#386432", "#4a7a3e"];
  if (kind === "conifer" || kind === "tropical" || kind === "marsh") return [P(...green)];
  if (sc.leaves === "fall") return [P("#6a1e14", "#922c18", "#b84420", "#d8642a"), P("#8a4612", "#b05e16", "#d07e22", "#e8a034"),
    P("#8a6e12", "#b0901c", "#d0b02a", "#e8cc48"), P(...green.slice(0, 4))];
  if (sc.leaves === "bare") return [P("#3a3430", "#4e4640", "#62584e", "#786c60")];
  return [P(...green)];
}
// Foothills between the far scenery and the meadow, drawn with the terrain
// renderer so they get real shading and a skyline of tree crowns.
function habFoothills(c, bio) {
  const { L, P, sc } = c, envH = (x) => { const k = clamp01((L.sea - 14 - x) / 60); return k * k * (3 - 2 * k); };
  const low = bio === "prairie" || bio === "marsh" || HAB_FARM_STATES.has(c.state), back = low ? 22 : bio === "desert" ? 14 : 52, front = low ? 12 : bio === "desert" ? 8 : back * .5;
  const kind = bio === "north" || bio === "alpine" ? "conifer" : bio === "desert" || bio === "prairie" ? "none" : "leafy";
  const hf = (x, z) => {
    let h = 0;
    if (z >= 6 && z <= 13) h = back * (.6 + .5 * fbm(x / 60, 1, 701)) * (1 - Math.abs(z - 9.5) / 4.5);
    if (z <= 4) h = Math.max(h, front * (.55 + .55 * fbm(x / 45, 2, 702)) * (1 - Math.abs(z - 2) / 3));
    if (h <= 0) return 0;
    if (kind !== "none") h += habCrowns(x, z, kind, z > 5 ? 4 : 6);
    else if (bio === "prairie" && fbm(x / 30, z, 703) > .66) h += habCrowns(x, z, "leafy", 3);  // trees along creeks
    return h * envH(x + 10);
  };
  const leafy = habCanopy(c, habLeafPals(c, bio === "marsh" ? "marsh" : bio === "tropical" ? "tropical" : "forest"), { size: 4 });
  const conifer = habCanopy(c, habLeafPals(c, "conifer"), { size: 3 });
  const snow = P("#a8b4c8", "#c8d2e2", "#e4eaf2", "#ffffff");
  const ground = P(...(bio === "desert" ? (HAB_GROUND[c.state] || HAB_GROUND.desert) : sc.near));
  const rock = P("#6a5a4a", "#847260", "#9e8a74", "#b8a48a"), shrub = P("#3e4a2e", "#4e5c38", "#627044");
  const moss = P("#7a8a6a", "#94a280");
  const color = (x, z, ht, sx, sz, y, dep) => {
    let col;
    if (bio === "desert") {
      const band = Math.sin(ht * .5 + vnoise(x / 20, z, 704) * 3) * .12;
      col = Math.abs(sx) > 1.4 ? ramp(rock, .5 - sx * .25 + band, x, y) : ramp(ground, .55 - sx * .3 + band + (hash2(x, y, 705) - .5) * .2, x, y);
      if (hash2(x >> 1, y >> 1, 706) > .93 && dep > 1) col = ramp(shrub, .5 - sx * .2, x, y);
    } else if (bio === "prairie" && !(fbm(x / 30, z, 703) > .66 && dep < 9)) {
      const wind = Math.sin(x * .25 + y * 1.3 + vnoise(x / 9, y, 707) * 4) * .1;
      col = ramp(ground, .55 - sx * .25 + wind - dep * .01 + (hash2(x, y, 708) - .5) * .18, x, y);
    } else if (kind === "conifer") {
      col = conifer(x, z, ht, sx, sz, y, dep);
      if (bio === "north" && hash2(x >> 2, y >> 2, 710) > .9 && dep > 6) col = ramp(rock, .5 - sx * .2, x, y);
    } else {
      col = leafy(x, z, ht, sx, sz, y, dep);
      // Spanish moss hanging from the live oaks and cypress.
      if (bio === "marsh" && x % 4 === 0 && dep > 1 && dep < 4 + hash2(x, z, 712) * 6) col = ramp(moss, .5, x, y);
    }
    if (c.snowy && (bio !== "desert" || ht > 14) && vnoise(x / 1.5, y, 713) > (kind === "conifer" ? .62 : .45)) col = pxMix(col, 0xe8eef6, .65);
    return col;
  };
  if (kind !== "none") {
    // Wooded foothills: two painted ridges of tree crowns sloping down to the shore.
    const pals = habLeafPals(c, bio === "marsh" ? "marsh" : bio === "tropical" ? "tropical" : "forest");
    habPaintRidges({ ...c, foot: L.water + 5, coastEnd: L.sea - 4 }, [[9, back, 60], [2, front, 45]],
      { shrink: .03, haze: .02, hazeK: .01, env: (x) => envH(x + 10), pals, pines: kind === "conifer" ? .9 : bio === "forest" ? .2 : .05, crownMax: 12, seed: 560 });
  } else habTerrain({ ...c, foot: L.water + 5, coastEnd: L.sea - 4 }, { n: 14, shrink: .03, haze: .03, hazeK: .012, h: hf, color });
  if (sc.saguaro) {
    // Saguaros with raised arms standing on the slopes.
    const cac = P("#2e5a30", "#3d6a3a", "#4f8046", "#64965a");
    for (let i = 0; i < 12; i++) {
      const x = 6 + Math.floor(hash2(i, 1, 850) * (L.sea - 40)), y = L.water + 3 + Math.floor(hash2(i, 2, 850) * 6);
      const hh = 9 + Math.floor(hash2(i, 3, 850) * 10), arm = Math.round(hh * .45), s = c.atmo;
      for (let j = 0; j < hh; j++) for (let dx = -1; dx <= 1; dx++) c.img.set(x + dx, y - j, s(cac[dx + 2], .08));
      c.img.set(x, y - hh, s(cac[2], .08));
      for (const side of hash2(i, 4, 850) < .5 ? [-1, 1] : [1]) {
        c.img.set(x + side * 2, y - arm, s(cac[1], .08)); c.img.set(x + side * 3, y - arm, s(cac[1], .08));
        for (let j = arm; j < arm + 4 + (i % 3); j++) c.img.set(x + side * 3, y - j, s(cac[side > 0 ? 3 : 0], .08));
      }
    }
  }
}
// Low plants, stones and litter on the meadow, by biome. `free` keeps them off the pond.
function habGround(c, bio, r) {
  const { img, P, L, H, sc, season } = c, p = L.pond;
  const free = (x, y, m = 6) => ((x - p.x) / (p.rx + m)) ** 2 + ((y - p.y) / (p.ry + m * .6)) ** 2 > 1 && x < L.shore[Math.min(H - 1, Math.max(0, y))] - 3;
  const spot = (top = 6) => [Math.floor(r() * (L.land - 8)) + 2, L.water + top + Math.floor(r() * (H - L.water - top - 2))];
  const bloom = season === "spring" ? 1.4 : season === "summer" ? 1 : season === "fall" ? .4 : sc.snow ? 0 : .2;
  const mead = sc.meadow, blade = P(mead[0], mead[1], mead[3]);
  const stone = (x, y, s, pal, lichen) => {
    // a soft cast shadow on the ground, down and to the right
    for (let dy = 0; dy <= Math.max(1, s * .5); dy++) for (let dx = -s; dx <= s + 2; dx++)
      if (((dx - 1) / (s + 1.5)) ** 2 + (dy / Math.max(1, s * .6)) ** 2 <= 1) img.set(x + dx, y + 1 + dy, pxMix(img.get(x + dx, y + 1 + dy), 0x1a2418, .35));
    pxBlob(img, x, y, s, Math.max(1, s * .7), pal, { rough: .35, grain: 1, seed: x + y });
    if (lichen) for (let i = 0; i < s; i++) img.set(x - s + 1 + Math.floor(hash2(x, i, 801) * s * 2 - 1), y - Math.floor(hash2(i, y, 802) * s * .6), lichen);
  };
  const tufts = (n, hmax, pal) => {
    for (let i = 0; i < n; i++) {
      const [x, y] = spot(4); if (!free(x, y, 3)) continue;
      const h = 2 + Math.floor(r() * hmax) + (y > 230 ? 1 : 0);
      for (let k = 0; k < h; k++) { img.set(x, y - k, pal[k ? 1 : 0]); if (k > 1) img.set(x + (i % 2 ? 1 : -1), y - k - 1, pal[2]); }
      if (r() < .5) for (let k = 0; k < h - 1; k++) img.set(x + 2, y - k, pal[k ? 1 : 0]);
    }
  };
  const flowers = (n, sets) => {
    for (let i = 0; i < n * bloom; i++) {
      const [x, y] = spot(8); if (!free(x, y)) continue;
      const [pet, mid] = sets[i % sets.length].map((h) => P(h));
      img.set(x, y + 1, blade[0]); img.set(x, y + 2, blade[0]);
      img.set(x - 1, y, pet); img.set(x + 1, y, pet); img.set(x, y - 1, pet); img.set(x, y + 1, pet); img.set(x, y, mid);
    }
  };
  if (bio === "desert") {
    // Gravel, flat stones, creosote bushes, prickly pear and a little dry grass.
    const grav = P("#7a6a52", "#968266", "#e0d0b0");
    for (let i = 0; i < 120; i++) { const [x, y] = spot(4); if (free(x, y, 0)) img.set(x, y, grav[i % 3]); }
    const sand = c.state === "UT" ? P("#7a3e26", "#9a5236", "#b8684a", "#d08a66") : P("#7a6650", "#968068", "#b29a80", "#ccb69a");
    for (let i = 0; i < 9; i++) { const [x, y] = spot(10); if (free(x, y, 8)) stone(x, y, 2 + Math.floor(r() * 3), sand); }
    const creo = P("#2e3a22", "#3e4c2c", "#566238", "#6e7a46"), stem = P("#4a3e30");
    for (let i = 0; i < 7; i++) {
      const [x, y] = spot(14); if (!free(x, y, 12)) continue;
      for (let k = 0; k < 4; k++) { img.set(x - 2 + k, y - Math.abs(k - 1.5) | 0, stem); }
      pxBlob(img, x, y - 4, 5 + Math.floor(r() * 2), 3, creo, { rough: .7, grain: 1, seed: i + 40 });
      if (season === "spring") for (let k = 0; k < 4; k++) img.set(x - 3 + Math.floor(hash2(i, k, 803) * 7), y - 5 - Math.floor(hash2(k, i, 804) * 3), P("#f0d040"));
    }
    const pear = P("#3e6a3a", "#4e8048", "#66985a", "#82b070");
    for (let i = 0; i < 4; i++) {
      const [x, y] = spot(16); if (!free(x, y, 12)) continue;
      for (const [dx, dy, w, h] of [[0, -3, 3, 4], [-4, -7, 2, 3], [3, -8, 2, 3], [0, -10, 2, 3]]) {
        pxBlob(img, x + dx, y + dy, w, h, pear, { rough: .2, seed: i + dx });
        img.set(x + dx - 1, y + dy - 1, pear[3]);
      }
      if (season !== "winter") for (const [dx, dy] of [[-4, -11], [3, -12]]) img.set(x + dx, y + dy, P(season === "spring" ? "#f0c030" : "#a02850"));
      for (let k = 0; k < 6; k++) img.set(x - 4 + Math.floor(hash2(i, k, 805) * 9), y - 2 - Math.floor(hash2(k, i, 806) * 10), P("#e8e0b8"));  // spines
    }
    tufts(40, 3, P("#8a7a3e", "#a8964e", "#c8b46a"));
    flowers(10, [["#f0d040", "#c88a20"], ["#e87a3a", "#f0d040"]]);  // desert marigold, globe mallow
    return;
  }
  if (bio === "prairie") {
    // Tall grass and the prairie flowers: coneflowers and black-eyed susans.
    const g = season === "fall" || sc.snow ? P("#8a6a2e", "#b08a3e", "#d0ae5e") : P(mead[0], mead[2], mead[3]);
    tufts(420, 5, g);
    const seed = P(season === "fall" ? "#e0c070" : "#c8b870");
    for (let i = 0; i < 80; i++) { const [x, y] = spot(4); if (free(x, y, 2)) { img.set(x, y - 6, seed); img.set(x, y - 7, seed); img.set(x, y - 5, blade[0]); img.set(x, y - 4, blade[0]); } }
    flowers(26, [["#c86ab0", "#6a3a20"], ["#f0c020", "#3a2010"], ["#ffffff", "#f0d040"]]);
    return;
  }
  if (bio === "alpine") {
    // A mountain meadow: lupine and paintbrush, lichened granite boulders.
    tufts(160, 3, blade);
    const gran = P("#5a5a62", "#74747c", "#90909a", "#acacb4");
    for (let i = 0; i < 5; i++) { const [x, y] = spot(10); if (free(x, y, 10)) stone(x, y, 3 + Math.floor(r() * 4), gran, P("#c8c070")); }
    for (let i = 0; i < 34 * bloom; i++) {
      const [x, y] = spot(8); if (!free(x, y)) continue;
      const lup = i % 3 !== 2, col = lup ? P("#5a4ab0", "#7a6ad0", "#a49af0") : P("#a82a20", "#d84a30", "#f07a50");
      for (let k = 0; k < 3; k++) img.set(x, y - k, blade[0]);
      for (let k = 0; k < (lup ? 5 : 3); k++) { img.set(x, y - 3 - k, col[k % 3]); if (k % 2 === 0) img.set(x + (lup ? 1 : -1), y - 3 - k, col[1]); }
    }
    flowers(10, [["#ffffff", "#f0d040"], ["#f0d040", "#c88a20"]]);
    return;
  }
  if (bio === "forest" || bio === "north" || bio === "tropical") {
    // Woodland edge: ferns, a mossy log, mushrooms, stones; granite and blueberry
    // in the north; lava rock and ginger in Hawaii.
    tufts(bio === "tropical" ? 150 : 120, 3, blade);
    const fern = bio === "tropical" ? P("#1e5a22", "#2e7a30", "#46984a") : season === "fall" ? P("#7a5a20", "#a07a2a", "#c09a40") : P("#2a5a26", "#3a7432", "#56903e");
    if (!sc.snow) for (let i = 0; i < (bio === "tropical" ? 14 : 9); i++) {
      const [x, y] = spot(10); if (!free(x, y, 10)) continue;
      // A clump of arching fronds of different lengths, each with little leaflets
      // along its stem that shrink toward the drooping tip.
      const nF = 5 + (i % 3);
      for (let f = 0; f < nF; f++) {
        const ang = -Math.PI / 2 + (f / (nF - 1) - .5) * 2.4 + (hash2(i, f, 890) - .5) * .3, len = 6 + hash2(f, i, 891) * 6;
        let fx = x, fy = y, a = ang;
        for (let t = 0; t < len; t++) {
          a += Math.sign(Math.cos(ang)) * .12 + (Math.cos(ang) === 0 ? 0 : 0);    // arch outward and droop
          fx += Math.cos(a) * .9; fy += Math.sin(a) * .9 + t * .025;
          const lit = Math.cos(a) < 0 ? 2 : 1;
          img.set(Math.round(fx), Math.round(fy), fern[t < 2 ? 0 : lit]);
          if (t > 1 && t < len - 1 && t % 2 === 0) {
            const lf = Math.max(1, Math.round((len - t) / 4));
            for (let q = 1; q <= lf; q++) {
              img.set(Math.round(fx - Math.sin(a) * q), Math.round(fy + Math.cos(a) * q * .6 + q * .3), fern[lit]);
              img.set(Math.round(fx + Math.sin(a) * q), Math.round(fy - Math.cos(a) * q * .6 + q * .3), fern[t % 4 ? 1 : 0]);
            }
          }
        }
      }
    }
    const rockPal = bio === "tropical" ? P("#1e1c1e", "#2e2a2c", "#403a3a", "#58504c") : P("#5a5a5a", "#747472", "#8e8e8a", "#a8a8a2");
    for (let i = 0; i < (bio === "north" ? 6 : 3); i++) { const [x, y] = spot(12); if (free(x, y, 10)) stone(x, y, 2 + Math.floor(r() * (bio === "north" ? 5 : 3)), rockPal, bio === "tropical" ? null : P("#7a9a4a")); }
    if (bio !== "tropical") {
      // A fallen log with moss along the top.
      const lx = Math.round(L.land * .64), ly = 196, bark = P("#3a2a1e", "#54402c", "#6e563c"), mo = P("#4a7a2a", "#6a9a3a");
      if (free(lx, ly, 14) && free(lx + 18, ly, 14)) {
        for (let k = 0; k < 20; k++) for (let t = 0; t < 4; t++) img.set(lx + k, ly - t, bark[t === 3 ? 2 : t === 0 ? 0 : 1]);
        for (let k = 0; k < 20; k++) if (hash2(k, 1, 807) > .35) img.set(lx + k, ly - 4, sc.snow ? P("#eef2f8") : mo[k % 2]);
        for (let t = 0; t < 4; t++) img.set(lx + 20, ly - t, P("#a08060")), img.set(lx + 21, ly - t, P("#c8a07a"));
      }
      const cap = bio === "north" ? P("#c83020", "#f0f0e8") : P("#8a5a34", "#c8a07a");
      if (season !== "winter") for (let i = 0; i < 4; i++) {
        const [x, y] = spot(14); if (!free(x, y, 8)) continue;
        img.set(x, y, P("#e8e0d0")); img.set(x, y - 1, P("#e8e0d0"));
        for (let d = -1; d <= 1; d++) img.set(x + d, y - 2, cap[0]); img.set(x, y - 3, cap[0]); img.set(x - 1, y - 3, cap[1]);
      }
    }
    if (bio === "north" && !sc.snow) {
      const berry = P("#2a4a2a", "#3a5e34", "#4e7444"), fruit = P("#3a4a8a");
      for (let i = 0; i < 8; i++) { const [x, y] = spot(10); if (!free(x, y, 8)) continue; pxBlob(img, x, y - 2, 3, 2, berry, { rough: .6, seed: i }); if (season === "summer") img.set(x + 1, y - 2, fruit), img.set(x - 1, y - 3, fruit); }
    }
    const fl = bio === "tropical" ? [["#e02a30", "#ffd040"], ["#ffffff", "#ffd040"], ["#e86a20", "#ffd040"]]
      : bio === "north" ? [["#ffffff", "#c8c040"], ["#c86ab0", "#ffffff"]] : sc.flowers.map(([a, b]) => [a, b]);
    flowers(bio === "tropical" ? 26 : 18, fl);
    if (sc.leaves === "fall") {
      const lv = [P("#c8441c"), P("#e8782a"), P("#e8b82a"), P("#9a2a16")];
      for (let i = 0; i < 120; i++) { const [x, y] = spot(6); if (free(x, y, 2)) { img.set(x, y, lv[i % 4]); if (hash2(i, 74) > .5) img.set(x + 1, y, lv[(i + 1) % 4]); } }
    }
    return;
  }
  if (bio === "marsh") {
    // Wet ground: puddles, sawgrass clumps and pickerelweed.
    tufts(200, 4, blade);
    const pud = P("#3a5a6a", "#5a8aa0", "#9ad0e8");
    for (let i = 0; i < 6; i++) {
      const [x, y] = spot(12); if (!free(x, y, 14)) continue;
      pxBlob(img, x, y, 6 + Math.floor(r() * 5), 2, pud, { rough: .3, seed: i });
      for (let k = -3; k < 3; k++) img.set(x + k, y - 1, pud[2]);
    }
    const saw = P("#4a5a2a", "#647438", "#7e8e48");
    for (let i = 0; i < 14; i++) {
      const [x, y] = spot(8); if (!free(x, y, 6)) continue;
      for (let b = -3; b <= 3; b++) for (let k = 0; k < 7 - Math.abs(b); k++) img.set(x + b + Math.round(b * k * .15), y - k, saw[k > 4 ? 2 : b < 0 ? 0 : 1]);
    }
    flowers(18, [["#6a5ad0", "#ffffff"], ["#ffffff", "#f0d040"]]);
  }
}
// The pond's look by biome: rim stones, water color, lilies, reeds.
function habPondStyle(bio, state) {
  if (bio === "desert") return { rim: state === "UT" ? ["#7a3e26", "#9a5236", "#b8684a", "#d08a66"] : ["#7a6650", "#968068", "#b29a80", "#ccb69a"], big: 1,
    water: ["#1e5a6a", "#28707e", "#3a8a92", "#5aa8a8"], lilies: false, reeds: 2 };
  if (bio === "alpine" || bio === "north") return { rim: ["#4e4e56", "#686870", "#84848c", "#a0a0a8"], big: 1,
    water: ["#183e66", "#20507e", "#2e6894", "#4a88b0"], lilies: bio === "north", reeds: 3, sedge: true };
  if (bio === "tropical") return { rim: ["#1e1c1e", "#2e2a2c", "#403a3a", "#58504c"], big: 1, lilies: true, reeds: 0 };
  if (bio === "marsh") return { rim: null, water: ["#1e3a32", "#2a4a3e", "#3a5e4a", "#5a7a5e"], lilies: true, reeds: 6, duckweed: true, knees: true };
  return null;
}

// Painted ridges, far to near: each ridge a clean silhouette whose color fades into
// the haze with distance, lit on the slopes facing the sun (from the left) with a
// bright rim along the crest, and wooded ridges covered in individually shaded
// tree crowns. ridges: [[slice, height, wavelength]], o: { pal (hex ramp, dark to
// light) or pals (one per crown kind), shrink, vs, haze, hazeK, blue, pines, mist, seed }.
function habPaintRidges(c, ridges, o = {}) {
  const { img, P, W, foot } = c, k = o.shrink ?? .028, vs = o.vs ?? 1, seed = o.seed ?? 540, span = Math.min(c.coastEnd, W + 2);
  const leafy = o.pals || habLeafPals(c, "forest"), conifer = habLeafPals(c, "conifer")[0];
  const blue = o.blue ? hexRgb(o.blue) : null, blueC = blue ? (blue[0] << 16) | (blue[1] << 8) | blue[2] : 0;
  const snowy = c.snowy, mist = o.mist ? 0xdde6ea : 0;
  const sorted = [...ridges].sort((a, b) => b[0] - a[0]);
  sorted.forEach(([lz, lh, wl], ri) => {
    const f = 1 / (1 + lz * k), haze = Math.min(.85, (o.haze ?? .05) + lz * (o.hazeK ?? .016));
    const tint = (col) => { let v = c.atmo(col, haze); if (blue) v = pxMix(v, blueC, Math.min(.6, lz * .022)); return v; };
    // The crest is uneven at every scale and slopes down to the shore at the
    // right end instead of stopping in a straight cut.
    const end = (x) => Math.pow(clamp01((span - x) / (24 + wl * .15)), .6);
    const crest = (x) => lh * (.62 + .5 * fbm(x / wl, lz, seed) + .12 * habRidged(x / (wl * .4), lz, seed + 9) + .05 * (vnoise(x / 3.5, lz, seed + 11) - .5)) * (o.env ? o.env(x) : 1) * end(x);
    const top = (x) => foot - crest(x) * f * vs;
    const base = leafy[0].map(tint), con = conifer.map(tint);
    const near = 1 - Math.min(1, lz / 40);
    for (let x = 0; x < span; x++) {
      const t = Math.round(top(x)), slope = top(x + 2) - top(x - 2);
      for (let y = t; y < foot; y++) {
        let v = .42 + Math.max(-.25, Math.min(.25, slope * .1)) - (y - t) * .004 + (y - t < 1.5 ? .25 : 0);
        let col = ramp(base, v, x, y);
        if (mist && ri < sorted.length - 1) { const m = clamp01((y - t) / 24); col = pxMix(col, c.atmo(mist, .1), Math.round(m * m * .55 * 5 + bayer(x, y) - .5) / 5); }
        img.set(x, y, col);
      }
    }
    if (lz > (o.crownMax ?? 22) || o.crowns === false) return;
    // Crowns packed over the slope, rounder for broadleaf trees and pointed for
    // conifers, lit from the upper left; nearer ridges get bigger crowns.
    const cr = 1.4 + near * 2.6, sp = cr * 1.45, pines = o.pines ?? .3;
    let row = 0;
    for (let gy = 0; gy < 70 * f; gy += sp * .72, row++) for (let gx = -4; gx < span + 4; gx += sp) {
      const jx = hash2(gx | 0, row, seed + lz) - .5, cx = gx + jx * sp + (row % 2) * sp * .5;
      const ty = top(cx), cy = ty + gy + (hash2(gx | 0, row, seed + lz + 1) - .5) * 2 - cr * .3;
      if (cy > foot + 1 || crest(cx) < 1) continue;
      const slope = top(cx + 2) - top(cx - 2), pine = hash2(gx | 0, row, seed + lz + 2) < pines;
      const pal = pine ? con : leafy[Math.floor(vnoise(cx / 14, cy / 8 + lz, seed + 3) * leafy.length * .999)].map(tint);
      const rad = cr * (.8 + hash2(gx | 0, row, seed + lz + 3) * .45), R = Math.ceil(rad * (pine ? 1.6 : 1));
      for (let dy = -R; dy <= Math.ceil(rad); dy++) for (let dx = -Math.ceil(rad); dx <= Math.ceil(rad); dx++) {
        if (pine) { if (dy < -R || Math.abs(dx) > (dy + R) / (R + rad) * rad * 1.1) continue; }
        else if (Math.hypot(dx, dy * 1.1) > rad) continue;
        const px = Math.round(cx + dx), py = Math.round(cy + dy);
        if (py >= foot) continue;
        let v = .44 - dx / rad * .32 - dy / rad * .36 + Math.max(-.15, Math.min(.15, -slope * .06)) - gy * .004;
        if (!pine && Math.hypot(dx, dy) > rad * .82) v -= .12;
        let col = ramp(pal, v, px, py);
        if (snowy && dy < -rad * .25 && v > .45 && bayer(px, py) < .55) col = c.atmo(0xe4ebf4, haze);  // snow on the tops of the crowns
        img.set(px, py, col);
      }
    }
  });
}
// Mesas and buttes, painted: flat caprock tops, sheer cliffs in horizontal rock
// bands, the sunlit face to the left and a cool shadowed face to the right, and a
// skirt of talus spreading below. ms: [x0, x1 (fractions of the width), top
// (height above the foot), color, haze], drawn in order (far ones first).
function habPaintMesas(c, ms) {
  const { img, W, foot } = c, P = c.P;
  ms.forEach(([f0, f1, h, hc, haze], mi) => {
    const x0 = f0 * W, x1 = f1 * W, top = foot - h, cliffH = h * .62, skirt = 18 + h * .25, sd = 900 + mi * 7;
    const pal = P(hexMix(hc, "#3a2848", .45), hexMix(hc, "#3a2848", .2), hc, hexMix(hc, "#fff0c8", .22), hexMix(hc, "#fff0c8", .45));
    const tint = pal.map((col) => c.atmo(col, haze));
    // The walls are eroded: they step out at harder rock ledges, wander in and out
    // where blocks have fallen, and the caprock edge is notched and uneven.
    const wall = (y, side) => {
      const k = (y - top) / cliffH, ledge = Math.floor(k * 4 + vnoise(y / 9, side, sd) * .8) * 1.6;
      return ledge + (fbm(y / 4, side * 3, sd + 1) - .5) * 5 + k * 3;
    };
    const capTop = (x) => top + (fbm(x / 7, 0, sd + 2) - .5) * 3 + (hash2(x >> 2, 0, sd + 3) > .85 ? 2 : 0);
    const span = Math.min(c.coastEnd, W + 2);
    for (let x = Math.floor(x0 - skirt - 4); x < x1 + skirt + 4; x++) {
      if (x < 0 || x >= span) continue;
      for (let y = Math.round(top - 3); y < foot; y++) {
        const cliffBase = top + cliffH + (fbm(x / 10, 5, sd + 4) - .5) * 4;
        let inside = false, face = 0, talus = false;
        if (y < cliffBase) {
          const l = x0 - wall(y, 1), r = x1 + wall(y, 2);
          inside = x >= l && x <= r && y >= capTop(x);
          face = x - l < 4 ? .22 : r - x < 6 ? -.3 : 0;
        } else {
          // Talus: a rough apron of fallen rock spreading from the cliff foot.
          const out = Math.max(0, Math.max(x0 - x, x - x1)), t = cliffBase + out * (h - cliffH) / skirt + out ** 1.5 * .18 + (fbm(x / 5, 9, sd + 5) - .5) * 4;
          inside = y >= t || (x >= x0 - wall(cliffBase, 1) && x <= x1 + wall(cliffBase, 2)); talus = true; face = x < x0 ? .12 : x > x1 ? -.16 : 0;
        }
        if (!inside) continue;
        let v = .5 + face + (y - capTop(x) < 1.5 && !talus ? .25 : 0);
        const band = Math.floor((y - top + fbm(x / 20, 1, 32) * 3) / 5) % 3;
        v += talus ? -.06 + (hash2(x >> 1, y >> 1, 33) > .86 ? -.22 : hash2(x >> 1, y >> 1, 36) > .9 ? .15 : 0) : band === 0 ? .1 : band === 2 ? -.1 : 0;
        if (!talus) v += (habRidged(x / 2.5, y / 9, sd + 6) - .5) * .3;   // vertical joints and varnish streaks
        img.set(x, y, ramp(tint, v, x, y));
      }
    }
  });
}
// Far scenery for states with their own: true when it drew something.
function habFarScene(c) {
  const R = HAB_ROCK, st = c.state;
  if (st === "CA") {
    // The Sierra Nevada: pale granite crest with snow in the gullies, above
    // golden foothills dotted with oaks.
    habTerrain(c, { n: 56, vs: 1.1, h: habMassifs(c, [[.3, 30, 92, 120, 18, 1.2], [.62, 34, 104, 110, 18, 1.15], [.95, 30, 80, 90, 16],
      [.12, 10, 40, 70, 8], [.5, 12, 44, 90, 8]], { seed: 507, scale: 30, rough: .5 }),
      color: habMountainColor(c, { rock: R.granite, snow: 78, tree: 50 }) });
    return true;
  }
  if (st === "CO") {
    // The Maroon Bells: two banded maroon pyramids over aspen woods, mirrored in Maroon Lake.
    habTerrain(c, { n: 56, h: habMassifs(c, [[.46, 4, 104, 70, 14, 1.05], [.63, 8, 96, 62, 14, 1.05],
      [.15, 26, 70, 90, 20], [.9, 22, 80, 80, 20], [.5, 40, 60, 160, 20]], { seed: 501, scale: 34 }),
      color: habMountainColor(c, { rock: R.maroon, bands: .45, snow: 70, tree: 30, fall: [["#8a5e0c", "#b8840e", "#e0ae1e", "#f4d050"]], fallShare: .45 }) });
    return true;
  }
  if (st === "WY") {
    // The Teton Range: jagged granite spires rising straight out of the flat valley.
    habTerrain(c, { n: 50, h: habMassifs(c, [[.5, 6, 116, 36, 10, .85], [.4, 8, 96, 30, 10, .9], [.6, 9, 92, 30, 10, .9],
      [.3, 10, 76, 34, 12], [.74, 12, 74, 46, 12], [.12, 16, 60, 50, 14], [.9, 16, 62, 50, 14]], { seed: 502, rough: .6, scale: 22 }),
      color: habMountainColor(c, { rock: R.granite, snow: 64, tree: 22 }) });
    return true;
  }
  if (st === "MT") {
    // Glacier National Park: broad horn peaks of red and green layered rock with snowfields.
    habTerrain(c, { n: 56, h: habMassifs(c, [[.24, 6, 92, 60, 12, 1.15], [.57, 8, 106, 66, 14, 1.15], [.88, 6, 86, 56, 12],
      [.4, 26, 80, 120, 18], [.8, 30, 78, 100, 18]], { seed: 503, rough: .5, scale: 34 }),
      color: habMountainColor(c, { rock: R.argillite, bands: .3, snow: 74, tree: 34 }) });
    return true;
  }
  if (st === "ID") {
    // The Sawtooths: a long row of pale granite teeth above Redfish Lake.
    habTerrain(c, { n: 50, h: habMassifs(c, [[.5, 8, 90, 170, 10, .9], [.3, 24, 70, 140, 16], [.8, 24, 72, 120, 16]],
      { seed: 504, rough: .7, scale: 16 }),
      color: habMountainColor(c, { rock: R.pale, snow: 66, tree: 30 }) });
    return true;
  }
  if (st === "AK") {
    // Denali: a huge white massif far away, above dark glaciated ridges.
    habTerrain(c, { n: 64, h: habMassifs(c, [[.55, 40, 260, 150, 26, 1.25], [.32, 38, 190, 90, 20], [.2, 6, 46, 50, 8],
      [.48, 8, 40, 60, 8], [.75, 6, 48, 50, 8]], { seed: 505, rough: .45, scale: 36 }),
      color: habMountainColor(c, { rock: R.granite, snow: 46, tree: 26 }) });
    return true;
  }
  if (st === "AZ") {
    // Monument Valley: red sandstone mesas and buttes standing out of the desert
    // floor, the farther ones softened by the haze.
    const far = c.P("#b8846c");
    for (let x = 0; x < Math.min(c.coastEnd, c.W + 2); x++) {
      const t = Math.round(c.foot - 8 - (fbm(x / 60, 2, 524) - .5) * 6);
      for (let y = t; y < c.foot; y++) c.img.set(x, y, c.atmo(far, .35));
    }
    habPaintMesas(c, [[-.06, .2, 58, "#b0664a", .2], [.46, .62, 76, "#b0664a", .2], [.64, .72, 48, "#b0664a", .2], [.82, 1.08, 64, "#b0664a", .2],
      [.12, .36, 34, "#a8562e", .06], [.7, .9, 30, "#a8562e", .06], [.31, .4, 52, "#a8562e", .06]]);
    return true;
  }
  if (st === "UT") {
    // Canyonlands slickrock: rounded red sandstone fins and benches, the snowy La Sal
    // Mountains far off. Delicate Arch stands on the far shore (habLandmark).
    const fins = habMassifs(c, [[.15, 8, 46, 60, 8, 1.2], [.42, 10, 40, 70, 8], [.75, 8, 50, 70, 8, 1.2],
      [.3, 20, 52, 90, 10], [.85, 22, 48, 80, 10]], { seed: 522, rough: .5, scale: 16 });
    const lasal = habMassifs(c, [[.62, 46, 96, 140, 14, 1.3], [.3, 44, 74, 90, 12]], { seed: 523, rough: .4, scale: 30 });
    const rock = habStrataColor(c, { bands: [[0, ["#7a3820", "#9a4a2a", "#b85e36", "#d07a4a"]], [22, ["#a04a2a", "#c0603a", "#d8784a", "#eca070"]],
      [40, ["#c49c78", "#d8b490", "#e8caa8", "#f6e0c4"]]], shrubs: ["#3a4a2a", "#4e6038"], wobble: 3 });
    const mtn = habMountainColor(c, { rock: HAB_ROCK.blue, snow: 82, tree: 60, forest: ["#3a4a5a", "#4a5a6a", "#5a6a7a", "#6a7a8a"] });
    habTerrain(c, { vs: 1.7, n: 56, h: (x, z) => Math.max(z > 40 ? lasal(x, z) : 0, habTerrace(fins(x, z), 9, .62)),
      color: (x, z, ht, sx, sz, y, dep) => z > 40 ? mtn(x, z, ht, sx, sz, y, dep) : rock(x, z, ht, sx, sz, y, dep) });
    return true;
  }
  if (st === "NM") {
    // Shiprock: a dark volcanic spire with its long rock walls, alone on the desert,
    // and flat-topped mesas on the horizon.
    const mesas = habMassifs(c, [[.12, 34, 34, 70, 10, .6], [.85, 36, 30, 80, 10, .6], [.5, 44, 22, 120, 10, .6]], { seed: 524, rough: .2, scale: 30 });
    // Shiprock: a broad, ragged mass of blunt towers and buttresses. Its outline
    // steps up and down between towers instead of rising to one point.
    const mass = (x, z) => { const d = Math.hypot((x - .45 * c.W) / 36, (z - 14) / 5); return d < 1 ? 92 * Math.sqrt(1 - d ** 2.2) : 0; }, wing = habSpire(c, .54, 14, 46, 24, 1.1, 4);
    const ship = (x, z) => {
      const m = mass(x, z); if (!m) return 0;
      const tower = .3 + .7 * Math.floor((.2 + .8 * fbm(x / 6, 0, 530)) * 6 + vnoise(x / 2, 0, 531) * .6) / 6;
      return m * Math.min(1, tower + .07 * habRidged(x / 3, z / 2, 532));
    };
    const dike = (x, z) => z === 10 && x > c.W * .55 && x < c.W * .95 ? 9 + vnoise(x / 3, 0, 525) * 5 : 0;
    const rock = habStrataColor(c, { bands: [[0, ["#2a2428", "#3a3236", "#4c4246", "#5e5458"]]], wobble: 0, fine: 3 });
    const mesa = habStrataColor(c, { bands: [[0, ["#9a6a4a", "#b07e5a", "#c4946e", "#d8ac86"]], [24, ["#b89a7a", "#ccb08e", "#dcc4a4", "#ecd8bc"]]] });
    habTerrain(c, { vs: 1.35, n: 56, h: (x, z) => {
      const s = Math.max(ship(x, z) * (.75 + .35 * habRidged(x / 7, z / 3, 526)), wing(x, z) * (.7 + .4 * habRidged(x / 6, z / 3, 527)), dike(x, z));
      return Math.max(s, habTerrace(mesas(x, z), 12, .5), 3 + vnoise(x / 12, z, 528) * 3);
    }, color: (x, z, ht, sx, sz, y, dep) => (z >= 9 && z <= 20 && ht > 9) ? rock(x, z, ht, sx, sz, y, dep) : mesa(x, z, ht, sx, sz, y, dep) });
    return true;
  }
  if (st === "NV") {
    // Basin and range: long bare mountain ranges one behind another, snow on the
    // highest. Pyramid Lake's tufa pyramid rises out of the water (habLandmark).
    const ranges = habMassifs(c, [[.25, 8, 58, 130, 5, 1.1], [.7, 10, 50, 140, 5, 1.1], [.45, 22, 84, 170, 6, 1.2],
      [.15, 36, 110, 150, 8, 1.2], [.8, 38, 120, 160, 8, 1.2]], { seed: 529, rough: .5, scale: 22 });
    habTerrain(c, { vs: 1.15, n: 56, h: ranges, color: habMountainColor(c, { rock: ["#5e5048", "#786658", "#927e6c", "#ac9882", "#c4b29a"], bands: .25, snow: 92 }) });
    return true;
  }
  if (st === "ND" || st === "SD") {
    // Badlands: eroded buttes and spires striped in grey, tan and rose (with dark
    // coal seams in North Dakota). South Dakota's dark Black Hills behind.
    const nd = st === "ND";
    const bad = habMassifs(c, [[.2, 6, 44, 70, 8, 1], [.48, 8, 52, 80, 8, 1], [.8, 6, 46, 70, 8, 1], [.35, 18, 40, 120, 10], [.7, 20, 44, 120, 10]],
      { seed: nd ? 530 : 531, rough: .55, scale: 12 });
    const hills = habMassifs(c, [[.5, 44, 90, 220, 12, 1.6]], { seed: 532, rough: .3, scale: 40 });
    const stripes = habStrataColor(c, { bands: nd
      ? [[0, ["#6e6660", "#8a8078", "#a49a90", "#bcb4aa"]], [10, ["#2a2624", "#3a3430", "#4a4440"]], [13, ["#9a8a76", "#b4a28c", "#ccbca4", "#e0d2bc"]],
         [24, ["#8a4a34", "#a85e44", "#c47a5c"]], [29, ["#a89a86", "#c2b49e", "#d8ccb8", "#ece2d0"]], [40, ["#5e7a3a", "#74904a", "#8aa45c"]]]
      : [[0, ["#8a7a78", "#a8968e", "#c2b2a8", "#dccec6"]], [12, ["#b07a64", "#c8907a", "#dcaa94", "#ecc4b0"]], [20, ["#a8a090", "#c2baa8", "#d8d2c2", "#ece8dc"]],
         [30, ["#c4a070", "#d8b888", "#e8cca0"]], [38, ["#a89a8a", "#c4b6a4", "#dcd0c0", "#f0e8dc"]]], wobble: 2, fine: 2.4 });
    const pines = habMountainColor(c, { rock: HAB_ROCK.granite, tree: 200, forest: ["#18241c", "#203026", "#2a3c30", "#34483a"] });
    habTerrain(c, { vs: 1.5, n: 56, h: (x, z) => Math.max(!nd && z > 40 ? hills(x, z) : 0, habTerrace(bad(x, z), 5, .55), 2),
      color: (x, z, ht, sx, sz, y, dep) => !nd && z > 40 ? pines(x, z, ht, sx, sz, y, dep) : stripes(x, z, ht, sx, sz, y, dep) });
    return true;
  }
  if (st === "NE") {
    // Chimney Rock: a slender sandstone spire on a cone of clay, alone on the
    // plains along the Oregon Trail; low bluffs beyond.
    const cone = habSpire(c, .5, 12, 34, 40, .7, 6), spire = habSpire(c, .5, 12, 60, 6, 3, 2);
    const bluffs = habMassifs(c, [[.15, 30, 30, 90, 10, .8], [.85, 32, 26, 100, 10, .8], [.6, 40, 20, 140, 10, .8]], { seed: 533, rough: .3, scale: 24 });
    habTerrain(c, { vs: 1.4, n: 56, h: (x, z) => Math.max(cone(x, z), spire(x, z), habTerrace(bluffs(x, z), 8, .55), 1.5),
      color: habStrataColor(c, { bands: [[0, ["#8a8a52", "#a2a060", "#b8b470", "#ccc684"]], [6, ["#a89478", "#c0ac8e", "#d4c2a6", "#e6d8be"]],
        [44, ["#b4a088", "#cab69c", "#ddcab2", "#eee0cc"]]], shrubs: ["#4a5a2a", "#5e7036"] }) });
    return true;
  }
  if (st === "TN") {
    // The Great Smoky Mountains: ridge after ridge going blue in the haze, mist in the hollows.
    habPaintRidges(c, [[4, 44, 50], [10, 62, 70], [17, 76, 90], [25, 90, 110], [34, 100, 140], [42, 104, 170]],
      { vs: 1.2, blue: "#7a96c8", mist: true, pines: .25 });
    return true;
  }
  if (st === "WV" || st === "KY" || st === "AR" || st === "VT") {
    // Wooded Appalachian and Ozark hills: steep and close in West Virginia's gorge
    // country, rolling bluegrass in Kentucky, the Ozarks and the Green Mountains.
    const cfg = { WV: [[3, 58, 40], [9, 66, 60], [16, 72, 80], [26, 76, 110]], KY: [[6, 22, 60], [14, 30, 90], [24, 38, 120]],
                  AR: [[5, 40, 60], [12, 50, 80], [22, 56, 110], [34, 60, 150]], VT: [[6, 54, 60], [14, 74, 80], [24, 86, 110], [36, 70, 160]] }[st];
    habPaintRidges(c, cfg, { shrink: .026, hazeK: .014, vs: 1.1, seed: 541 + st.charCodeAt(0), blue: "#8aa2c8", pines: st === "VT" ? .3 : .15, crownMax: 30 });
    if (st === "WV") habGorgeBridge(c);
    if (st === "VT") habSteeple(c, Math.round(c.W * .7), c.foot - 14);
    return true;
  }
  if (st === "KS" || st === "IA" || st === "OK" || st === "IN" || st === "WI") {
    // Farm country: fields of wheat, corn and soybeans rolling to the horizon
    // (red earth in Oklahoma, the sand dunes of Lake Michigan in Indiana).
    const swell = { KS: 8, IA: 18, OK: 10, IN: 6, WI: 24 }[st];
    const fields = {
      KS: [["#a88a3a", "#c4a44a", "#dcbe60", "#ecd47a"], ["#8a8a3a", "#a2a248", "#b8b858", "#cccc6c"], ["#9a7a40", "#b2924e", "#c8a862", "#dcbe78"]],
      IA: [["#3e6a2a", "#4e8034", "#629840", "#78ae4e"], ["#a08a3e", "#baa24c", "#d0ba60", "#e0ce78"], ["#4e7a30", "#609038", "#76a646", "#8cba56"]],
      OK: [["#8a4a2a", "#a45c36", "#bc7044", "#d08656"], ["#8a8a3a", "#a2a248", "#b8b858", "#cccc6c"], ["#a88a3a", "#c4a44a", "#dcbe60", "#ecd47a"]],
      IN: [["#4e7a30", "#609038", "#76a646", "#8cba56"], ["#a08a3e", "#baa24c", "#d0ba60", "#e0ce78"]],
      WI: [["#3e6a2a", "#4e8034", "#629840", "#78ae4e"], ["#5a7a30", "#6e9038", "#84a646", "#9aba56"], ["#a08a3e", "#baa24c", "#d0ba60", "#e0ce78"]],
    }[st];
    const roll = habRidgeLine(c, [[6, swell, 90], [16, swell * 1.2, 140], [30, swell * 1.4, 200]], 545);
    const fieldCol = habFieldsColor(c, { fields });
    const woods = habForestColor(c, { pines: .1 });
    habTerrain(c, { n: 40, h: (x, z) => roll(x, z) + 2, hazeK: .016,
      color: (x, z, ht, sx, sz, y, dep) => vnoise(x / 24, z / 3, 546) > .7 ? woods(x, z, ht, sx, sz, y, dep) : fieldCol(x, z, ht, sx, sz, y, dep) });
    if (st === "IN") {
      // The dunes: tall sand hills with marram grass, toward the lake.
      // Smooth wind-shaped hills: a gentle back slope and a steeper lee face.
      const dune = (x, z) => {
        let h = 0;
        for (const [cx, cz, hh, w] of [[.55, 4, 40, 60], [.73, 7, 30, 40]]) {
          const d = (x - c.W * cx) / w, dz = Math.abs(z - cz);
          if (dz > 3) continue;
          const k = d < 0 ? Math.max(0, 1 - d * d) : Math.max(0, 1 - d * d * 2.2);
          h = Math.max(h, hh * k * k * (1 - dz / 3.5) * (.92 + .08 * vnoise(x / 9, z, 547)));
        }
        return h;
      };
      const sand = c.P("#b89a6a", "#ccb07e", "#dec496", "#ecd8ae"), grass = c.P("#5e7a34", "#76923e", "#8eaa4c");
      habTerrain(c, { n: 8, h: dune, color: (x, z, ht, sx, sz, y, dep) => dep < 3 + hash2(x, z, 548) * 6 && hash2(x, y, 549) > .5
        ? ramp(grass, .5 - sx * .2, x, y) : ramp(sand, .6 - sx * .25 + (hash2(x, y, 550) - .5) * .2, x, y) });
    }
    habFarm(c, st);
    return true;
  }
  if (st === "WA" || st === "OR") {
    // Mount Rainier's huge glaciated dome, or Mount Hood's sharp cone, over dark forest.
    const wa = st === "WA";
    habTerrain(c, { n: 60, vs: 1.1, h: habMassifs(c, wa
      ? [[.42, 30, 160, 170, 20, 1.7], [.15, 6, 40, 60, 8], [.75, 8, 46, 70, 8], [.5, 14, 52, 110, 8]]
      : [[.4, 26, 150, 100, 18, 1.15], [.15, 6, 40, 70, 8], [.7, 8, 44, 80, 8], [.45, 14, 50, 110, 8]], { seed: wa ? 551 : 552, rough: .35, scale: 30 }),
      color: habMountainColor(c, { rock: HAB_ROCK.blue, snow: wa ? 70 : 84, tree: 54 }) });
    return true;
  }
  if (st === "HI") {
    // Kauai's Na Pali coast: fluted emerald cliffs dropping to the sea, and a waterfall.
    const cliffs = (x, z) => {
      const u = x / c.W, base = 150 * Math.max(0, 1 - Math.pow(Math.max(0, u - .1) / .72, 2.4));
      // Knife-edge ridges of uneven width and height, not a regular row of flutes.
      const flute = .66 + .26 * habRidged(x / (5 + vnoise(x / 40, 0, 557) * 5), z * .15, 553) + .1 * vnoise(x / 13, z, 558);
      return z > 6 && z < 30 ? base * flute * (1 - (z - 6) * .012) : 0;
    };
    const green = c.P("#1e4a22", "#2a6030", "#3a783c", "#4e924a", "#6aac5c"), rock = c.P("#4a3a30", "#6a5040", "#8a6a52");
    habTerrain(c, { n: 30, vs: .9, h: cliffs, color: (x, z, ht, sx, sz, y, dep) => {
      const light = clamp01(.55 - Math.max(-.45, Math.min(.45, sx * .3)) + (habRidged(x / 1.8, y / 7, 554) - .5) * .35 - dep * .004);
      return hash2(x >> 1, y >> 2, 555) > .9 && Math.abs(sx) > 1 ? ramp(rock, light, x, y) : ramp(green, light, x, y);
    } });
    // the waterfall
    const fx = Math.round(c.W * .32);
    for (let y = 70; y < c.foot; y++) {
      if (c.img.get(fx, y) < 0) continue;
      for (let dx = 0; dx < 2; dx++) c.img.set(fx + dx + Math.round(Math.sin(y / 9)), y, c.P(hash2(dx, y >> 1, 556) > .4 ? "#f4fbff" : "#c8e6f2"));
    }
    return true;
  }
  if (st === "ME" || st === "MA" || st === "CT" || st === "RI" || st === "DE" || st === "MD" || st === "SC" || st === "AL" || st === "MN") {
    // Coastal woods: spruce and granite in Maine and on Lake Superior, oak and
    // pine along the Mid-Atlantic, palmettos and live oaks in the Carolina Lowcountry.
    const cfg = { ME: [[4, 26, 50], [12, 40, 70], [24, 46, 110]], MN: [[4, 34, 50], [12, 46, 70], [24, 50, 110]],
                  MA: [[6, 14, 60], [16, 20, 90]], CT: [[6, 22, 60], [14, 30, 80], [26, 38, 120]], RI: [[6, 16, 60], [16, 22, 90]],
                  DE: [[6, 8, 60], [16, 10, 90]], MD: [[6, 14, 60], [16, 20, 90], [28, 30, 130]], SC: [[6, 12, 60], [16, 16, 90]],
                  AL: [[6, 12, 60], [16, 16, 90]] }[st];
    const north = st === "ME" || st === "MN";
    habPaintRidges(c, cfg, { shrink: .022, hazeK: .016, seed: 560 + st.charCodeAt(1), blue: "#8aa2c8", pines: north ? .8 : st === "SC" || st === "AL" ? .6 : .3, crownMax: 30 });
    if (st === "SC" || st === "AL") habPalmettos(c);
    return true;
  }
  if (st === "NH") {
    // The Presidential Range: rounded bare summits over thick hardwood forest.
    habTerrain(c, { n: 50, h: habMassifs(c, [[.5, 10, 76, 110, 16, 1.6], [.2, 8, 54, 70, 12, 1.5], [.8, 8, 56, 80, 12, 1.5],
      [.5, 30, 50, 200, 16]], { seed: 506, rough: .35, scale: 30 }),
      color: habMountainColor(c, { rock: R.granite, snow: 70, tree: 58, forest: ["#1c3422", "#28462c", "#365a36", "#466c40"],
        fall: [["#7a2216", "#9a2e1a", "#bc4222", "#d85a2a"], ["#9a4a14", "#bc5e18", "#d8781e", "#ec9a30"], ["#9a7a14", "#bc9a1e", "#d8b82a", "#ecd048"]], fallShare: .6 }) });
    return true;
  }
  return false;
}

// Landmarks and touches drawn over the water and shore, per state.
function habLandmark(c) {
  const { img, P, W, L, state } = c, sh = (col) => c.atmo(col, .1);
  if (state === "KY") {
    // Bluegrass horse farm: white plank fences along the near pasture.
    const post = P("#c8c4b8", "#f4f2ea"), y0 = L.water + 6;
    for (let x = 0; x < L.sea - 12; x++) {
      const y = y0 + Math.round(x * .02);
      if (x % 9 === 0) for (let k = -1; k < 7; k++) img.set(x, y + k, post[k < 0 ? 1 : 0]);
      img.set(x, y + 1, post[1]); img.set(x, y + 4, post[1]);
    }
    return true;
  }
  return false;
}
// The New River Gorge Bridge: a long rust-brown steel arch across the gorge.
function habGorgeBridge(c) {
  const { img, P, W, foot } = c, steel = P("#3e2a20", "#5a3e2c", "#76543a"), sh = (col) => c.atmo(col, .18);
  const x0 = Math.round(W * .36), x1 = Math.round(W * 1.02), deck = foot - 62, mid = (x0 + x1) / 2, half = (x1 - x0) / 2;
  const archY = (x) => deck + 4 + Math.round(40 * ((x - mid) / half) ** 2);
  for (let x = x0 - 30; x <= x1 + 20; x++) { img.set(x, deck, sh(steel[2])); img.set(x, deck + 1, sh(steel[1])); img.set(x, deck + 2, sh(steel[0])); }
  for (let x = x0; x <= x1; x++) { const y = archY(x); img.set(x, y, sh(steel[1])); img.set(x, y + 1, sh(steel[0])); }
  for (let x = x0; x <= x1; x += 6) for (let y = deck + 3; y < archY(x); y++) img.set(x, y, sh(steel[0]));
  for (let x = x0 - 30; x <= x1 + 20; x += 14) if (x < x0 || x > x1) for (let y = deck + 3; y < foot - 10; y++) img.set(x, y, sh(steel[0]));
}
// A white New England church steeple among the trees.
function habSteeple(c, x, gy) {
  const { img, P } = c, white = P("#b8b4aa", "#e4e0d6", "#fbf9f2"), roof = P("#3a3a40", "#52525a"), win = P("#3a4a5e"), sh = (col) => c.atmo(col, .12);
  // nave with a pitched roof
  for (let y = gy - 12; y < gy; y++) for (let dx = 0; dx < 18; dx++) img.set(x + dx, y, sh(white[dx < 3 ? 2 : 1]));
  for (let k = 0; k < 6; k++) for (let dx = k - 1; dx <= 18 - k; dx++) img.set(x + dx, gy - 13 - k, sh(roof[dx < 9 ? 1 : 0]));
  for (const wx of [8, 13]) for (let y = gy - 9; y < gy - 4; y++) img.set(x + wx, y, sh(win));
  // square tower, belfry, then a tapering spire
  for (let y = gy - 30; y < gy; y++) for (let dx = -6; dx < 0; dx++) img.set(x + dx, y, sh(white[dx === -6 ? 2 : dx === -1 ? 0 : 1]));
  for (let y = gy - 26; y < gy - 22; y++) for (let dx = -4; dx < -2; dx++) img.set(x + dx, y, sh(win));
  for (let y = gy - 8; y < gy; y++) for (let dx = -4; dx < -2; dx++) img.set(x + dx, y, sh(win));
  for (let k = 0; k < 16; k++) { const hw = Math.max(0, 2 - (k / 6 | 0)); for (let dx = -3 - hw; dx <= -3 + hw - (hw ? 1 : 0) + (hw ? 1 : 0); dx++) img.set(x + dx, gy - 31 - k, sh(white[dx < -3 ? 2 : 1])); }
}

function habCloud(phase, i, grey = false) {
  const key = `${phase}/${i}/${grey}`;
  if (habClouds[key]) return habClouds[key];
  const P = pxPalette(phase === "night" && !grey ? "day" : phase), w = [56, 72, 44, 36][i], h = 22;
  const pal = grey ? P("#7c858f", "#959ea8", "#b0b8c0", "#c8ced4")
    : phase === "day" ? P("#b9d3ea", "#d8e8f5", "#f3f8fd", "#ffffff")
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
    data.data[k * 4 + 3] = phase === "day" || grey ? 240 : 215;
  }
  c.putImageData(data, 0, 0);
  return (habClouds[key] = cv);
}

// Things that move without being animals: clouds, surf, kelp, light on the sea.
function habAmbient(c, L, phase) {
  const t = hab.t;
  const sky = hab.wx ? hab.wx.sky : "partly", grey = HAB_GREY.has(sky), gust = habGust();
  if (phase !== "night" || grey) {
    // Clear skies keep two clouds, grey ones fill up, and the wind hurries them along.
    let clouds = [[30, 22, 2.2], [L.w * .45, 8, 1.4], [L.w * .72, 44, 3], [L.w * .2, 58, 2.6]];
    if (sky === "clear") clouds = clouds.slice(0, 2);
    if (grey) clouds = clouds.concat([[L.w * .6, 0, 1.8], [L.w * .9, 26, 2.4], [L.w * .05, 4, 1.6], [L.w * .35, 34, 2]]);
    const span = L.w + 160;
    clouds.forEach(([x0, y, v], i) => {
      const img = habCloud(phase, i % 4, grey);
      const k = gust ? Math.sign(gust) * (Math.abs(gust) * .6 + v) : v;
      const x = Math.round((((x0 + t * k) % span) + span) % span - img.width);
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
  } else if (habState() === "NY" && phase !== "day") {
    // Liberty's torch glows after sundown.
    const [lx, ly] = habLiberty(L).torch, k = .25 + Math.sin(t * 3.1) * .05 + Math.sin(t * 7.3) * .03;
    c.fillStyle = `rgba(255,220,120,${k.toFixed(3)})`; c.fillRect(lx - 4, ly - 5, 10, 8);
    c.fillStyle = `rgba(255,220,120,${(k * .5).toFixed(3)})`; c.fillRect(lx - 8, ly - 3, 18, 4);
  } else if (habState() === "NJ") {
    // The Ferris wheel's gondolas turn slowly; after dark its rim lights up.
    const { cars, hx, hy, r } = habPier(L), lit = phase !== "day";
    cars(t * .25).forEach(([x, y], i) => {
      c.fillStyle = ["#e8402a", "#f0c020", "#2a8ad8", "#3ab85a"][i % 4];
      c.fillRect(Math.round(x) - 1, Math.round(y) + 1, 3, 2);
    });
    if (lit) for (let a = 0; a < 24; a++) {
      if ((a + Math.floor(t * 4)) % 3) continue;
      const u = a / 24 * Math.PI * 2;
      c.fillStyle = "#fff0a0"; c.fillRect(Math.round(hx + Math.cos(u) * r), Math.round(hy + Math.sin(u) * r), 1, 1);
    }
  } else if (habState() === "MI" && phase !== "day") {
    // The Mackinac Bridge's cables are strung with lights after dark.
    const { x0, cable } = habMackinac(L);
    c.fillStyle = "#fff0b0";
    for (let x = x0 + 2; x < L.w; x += 5) c.fillRect(x, Math.round(cable(x)), 1, 1);
  } else if (habState() === "GA" && phase !== "day") {
    // The shrimp boat's masthead light and lit wheelhouse after dark.
    const { bx, wl, mast } = habShrimper(L), k = .3 + Math.sin(t * 2.3) * .05;
    c.fillStyle = `rgba(255,236,150,${k.toFixed(3)})`; c.fillRect(bx - 2, mast - 2, 5, 5); c.fillRect(bx + 6, wl - 11, 7, 3);
    c.fillStyle = "#fff4c0"; c.fillRect(bx, mast, 1, 1);
  } else if (habState() === "OH" && phase !== "day") {
    // Chaser lights run along the coaster track after dark.
    const { pts } = habCoaster(L), k = Math.floor(t * 12);
    pts.forEach(([x, y], i) => {
      if ((i + k) % 8 < 2) { c.fillStyle = (i >> 3) % 2 ? "#fff0a0" : "#ff8ad8"; c.fillRect(Math.round(x), Math.round(y) - 1, 1, 1); }
    });
  } else if (habState() === "IL" && phase !== "day") {
    // Red lights blink on top of the Willis Tower's antennas.
    if (Math.sin(t * 1.8) > 0) {
      c.fillStyle = "#ff4a3a";
      for (const [lx, ly] of habChicago(L).tips) c.fillRect(lx, ly, 1, 1);
    }
  } else if (habState() === "PA" && phase !== "day") {
    // The covered bridge's lanterns glow after sundown.
    const k = .22 + Math.sin(t * 2.7) * .04;
    c.fillStyle = `rgba(255,214,120,${k.toFixed(3)})`;
    for (const [lx, ly] of habBridge(L).lamps) c.fillRect(lx - 3, ly - 3, 7, 7);
  } else if ((habState() === "VA" || habLand(habState()).sea === "lighthouse") && phase !== "day") {
    // Assateague's lighthouse flashes after sundown.
    const [lx, ly] = habAssateague(L).lamp;
    if (Math.sin(t * 2.1) > .3) {
      c.fillStyle = "rgba(255,240,160,.3)"; c.fillRect(lx - 9, ly - 4, 19, 8);
      c.fillStyle = "rgba(255,240,160,.22)"; c.fillRect(lx - 18, ly - 1, 37, 3);
      c.fillStyle = "#fff6c0"; c.fillRect(lx - 1, ly - 2, 3, 4);
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
  if (hab.glowX > L.surf[L.water] + 8 && !grey) {
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
  if (night && !grey) (hab.stars || []).forEach(([x, y], i) => {
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
  if (document.getElementById("hab-wx-here")) $("hab-wx-here").onclick = habWxHere;
  $("hab-peek").onclick = () => { hab.peek = !hab.peek; habNote(); if (habStill) habDraw(); };
  if (!habStill) requestAnimationFrame(habLoop);
}
