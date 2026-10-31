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
const habState = () => (hab.visit ? hab.visit.state : myState.code);
const habImgs = {};
// Animation sheets (species/sprites/anim): a row of four frames for each pose, and
// an index of the poses each species really draws. Without them the scene falls
// back to the single sprite, squashed and bobbed.
const habSheets = {};
let habAnimIdx = null;
fetch("/sprites/anim/index.json").then((r) => (r.ok ? r.json() : null)).then((j) => { habAnimIdx = j; }).catch(() => {});
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
  const state = habState(), here = !hab.visit && hab.here && hab.here.state === state && hab.here;
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
  const phase = habPhase(), n = hab.animals.length;
  const asleep = hab.animals.filter((a) => !habAwake(a, phase)).length;
  const who = hab.visit ? `${hab.visit.username}'s habitat` : "here";
  $("hab-note").textContent = !n ? (hab.visit ? `No animals in ${who} yet.` : "Capture animals and they'll move in here.")
    : `${n} animal${n > 1 ? "s" : ""} live${n > 1 ? "" : "s"} ${hab.visit ? "in " + who : "here"}` + (asleep ? `, ${asleep} asleep` : "")
      + (hab.wx ? ". " + habWxLine() : ". Tap one to say hi.") + ` ${HAB_SEASON_ICON[habSeason()]} ${habSeason()[0].toUpperCase() + habSeason().slice(1)}.`;
  const night = phase === "night";
  if (night) $("hab-note").textContent += ` ${habMoonName().join(" ")}.`;
  const here = document.getElementById("hab-wx-here");
  if (here) here.hidden = !(hab.wxAsk && hab.wx && !hab.visit);
  $("hab-peek").textContent = hab.peek ? "Back to now" : night || phase === "dusk" ? "☀️ Peek at daytime" : "🌙 Peek at night";
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
  habWxReact(a, dt, awake);
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
    a.rest = habRestPose();
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
  const visiting = habDecorPose(a, awake);
  if (visiting) return visiting;
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
  // Shaking off the rain or shivering, and jumping at thunder.
  if (a.shake > 0) x += Math.floor(a.shake * 28) % 2 ? 1 : -1;
  if (a.jump > 0) y -= Math.sin(a.jump / .35 * Math.PI) * 7;
  return [x, y, sx, sy, tilt];
}

// What a ground animal does while it stands still: just stand, sit up on its
// haunches, turn its head to look at you, or glance back over its shoulder
// (only the animals whose sheets draw that pose).
function habRestPose() {
  return ["idle", "idle", "sit", "look", "back"][Math.floor(Math.random() * 5)];
}

// Which pose of the animation sheet to show, and which of its four frames:
// [pose, frame], or null when the species has no sheet.
function habAnim(a, awake, roost) {
  const acts = habAnimIdx && habAnimIdx.acts[a.s.slug];
  if (!acts) return null;
  const has = (k) => acts.includes(k);
  const cyc = (t) => ((Math.floor(t) % 4) + 4) % 4;
  if (!awake) return ["sleep", cyc(a.phase * 1.2)];
  if (roost || habDecorAnim(a, awake)) return ["idle", 0];  // sheltering from the rain, or perched on a decoration
  if (a.mode === "perched") return ["idle", 0];
  if (a.mode === "toPerch") return has("fly") ? ["fly", cyc(a.phase * 9 / (2 * Math.PI) * 4)] : ["idle", 0];
  switch (a.role) {
    case "walk": case "shore": case "wade": case "beach": case "hop": {
      if (a.peck > 0) return ["idle", 0];
      if (a.pause > 0 || !has("walk")) {
        const r = a.rest && has(a.rest) ? a.rest : "idle";
        return [r, r === "sit" ? cyc(a.phase * 2.5) : 0];  // sitting up, it nibbles
      }
      return ["walk", a.role === "hop" ? cyc((a.odo % 18) / 18 * 4) : cyc(a.odo / 3)];
    }
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
  const L = hab.L, phase = habPhase(), lights = habLights(L, phase);
  habDecorPlace();
  // The sun and moon creep across the sky, so the scenery is redrawn every few pixels they move.
  const spot = (b) => (b ? b.xy.map((v) => v >> 2).join(",") + (b.lit ? "/" + Math.round(b.lit * 40) : "") : "-");
  const key = `${L.w}/${phase}/${habState()}/${habSeason()}/${spot(lights.sun)}/${spot(lights.moon)}`;
  if (cv.width !== L.w) { cv.width = L.w; cv.height = HAB_H; }
  if (hab.bgKey !== key) { hab.bg = habBackground(L, phase, habState(), lights); hab.bgKey = key; }
  const c = cv.getContext("2d");
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
    // The frames already beat the wings, step the legs and breathe, so drop the
    // squash that stood in for them (hops and jellies keep theirs).
    if (anim && anim[0] !== "idle" && a.role !== "hop" && a.role !== "jelly" && a.mode !== "rise" && !(roost && roost[2])) sx = sy = 1;
    const perched = awake && a.mode === "perched";
    // Landed on a decoration: drawn with it, not in the sky (unless it's the balloon).
    const landed = habDecorLanded(a) && a.dv.d.it.area !== "sky";
    return { a, awake, phase, anim, roost: !!roost || perched, x: Math.round(x), y: Math.round(y), sx, sy, tilt,
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

function habSprite(c, p) {
  const raw = habImgs[p.a.s.slug];
  if (!raw || !raw.complete || !raw.naturalWidth) return;
  const { a, x, y } = p, sheet = habSheets[a.s.slug];
  const framed = p.anim && sheet && sheet.complete && sheet.naturalWidth;
  const img = framed ? habTinted(sheet, `${a.s.slug}@anim`, p.phase) : habTinted(raw, a.s.slug, p.phase);
  // Frame size from the image (40 px: a 32 px drawing with room for wings, tails
  // and antlers), feet on its bottom row.
  const F = framed ? sheet.naturalWidth / habAnimIdx.frames : raw.naturalWidth;
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
  if (p.tilt) c.rotate(-p.tilt);
  if (p.sx !== 1 || p.sy !== 1) c.scale(p.sx, p.sy);
  if (framed) c.drawImage(habFrame(img, habAnimIdx.rows.indexOf(p.anim[0]), p.anim[1], F), -F / 2, mid - F);
  else c.drawImage(img, -F / 2, mid - F);
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
  name.textContent = a.s.common_name + (mood ? ` · ${mood}` : awake ? "" : " 💤");
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
  // A different fact first each time you come back to it.
  hab.factIdx = Math.floor(Math.random() * 3);
  habSay(h.a);
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
  if (!hab.L || w !== hab.w) habitatSet(hab.animals.map((a) => ({ caught: true, species: a.s, activity: a.activity, num: a.num })));
  const dt = hab.last ? Math.min((now - hab.last) / 1000, .1) : 0;
  hab.last = now;
  const phase = habPhase();
  hab.t += dt;
  habWeather();
  habDecorTick(dt);
  hab.animals.forEach((a) => habStep(a, dt, habAwake(a, phase)));
  habFxStep(dt);
  habWxStep(dt);
  habDraw();
}

// ---- Weather: the real sky outside right now (GET /weather/{state}, from the
// National Weather Service) as clouds, rain, snow, fog, wind and thunderstorms.
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
  const state = habState(), now = Date.now();
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
  const w = hab.wx, moon = habPhase() === "night" && (w.sky === "clear" || w.sky === "partly");
  let line = `${moon ? habMoonName()[0] : HAB_WX_ICON[w.sky]} ${HAB_WX_WORDS[w.sky]}`;
  if (w.wind === "windy") line += " and windy";
  if (w.place) line += ` ${w.near ? "near" : "in"} ${w.place}`;
  if (w.temp_f != null) line += `, ${w.temp_f}°F`;
  return line + ".";
}

// What a tapped animal is up to in this weather, or null.
function habWxMood(a, awake) {
  if (!hab.wx) return null;
  if (habTuckedIn(a)) return habCold() ? "tucked in from the cold 💤" : "hibernating till spring 💤";
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

const HAB_GLYPHS = { note: ["..###", "..#.#", "..#..", "###..", "###.."], "!": ["##", "##", "##", "..", "##"] };
function habGlyph(c, kind, x, y) {
  const rows = HAB_GLYPHS[kind];
  const dots = (dx, dy) => rows.forEach((r, j) => [...r].forEach((ch, i) => ch === "#" && c.fillRect(x + i + dx, y + j + dy, 1, 1)));
  c.fillStyle = "#1c2a1c";
  [[-1, 0], [1, 0], [0, -1], [0, 1]].forEach(([dx, dy]) => dots(dx, dy));
  c.fillStyle = kind === "!" ? "#ff6a4a" : "#ffffff";
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
  for (const p of poses) {
    const r = p.a.react;
    if (!r || p.hidden) continue;
    const k = 1 - r.life / (r.kind === "!" ? 1.2 : 1.6);
    c.globalAlpha = Math.min(1, r.life * 2);
    habGlyph(c, r.kind, p.x + 6, Math.round(p.y - 36 - k * 6));
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
  const coastEnd = L.sea + 10;
  // Mountains and hills sink toward the coast instead of stopping in a wall.
  const env = (x, len) => { const k = clamp01((coastEnd - 14 - x) / len); return k * k * (3 - 2 * k); };
  // Mountains reach down to the sea's horizon so none of them float over the coast.
  const foot = L.water + 1;
  const fade = (x, h) => Math.round(foot - (foot - h) * env(x, 90));
  const atmo = (col, k) => pxMix(col, 0xcdeefb, k);
  if (state === "CA" || land.far === "peaks") {
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
      const h = fade(x, Math.round(mtop + e * 36));
      for (let y = h; y < foot; y++) {
        const v = .62 - u * .35 + (vnoise(x / 6, y / 3, 51) - .5) * .25 - (y - h) * .004;
        img.set(x, y, atmo(ramp(rock, v + ((x * 3 + y) % 11 === 0 ? -.2 : 0), x, y), .22));
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
  } else if (state === "PA") {
    // The Ridge-and-Valley Appalachians: long ridges with flat, even crests, one
    // behind another, each notched once where a river cuts through.
    [[90, "#b4c8dc", "#c4d4e6"], [104, "#8eaac4", "#a2bcd2"], [118, "#6a8ca8", "#7e9eb8"]].forEach(([base, a, b], i) => {
      const pal = P(a, b), notch = Math.round(coastEnd * [.62, .3, .5][i]);
      for (let x = 0; x < coastEnd; x++) {
        const d = Math.abs(x - notch), gap = d < 7 ? Math.round((7 - d) * 1.6) : 0;
        const h = fade(x, Math.round(base + gap + (vnoise(x / 70, i, 31 + i) - .5) * 4));
        for (let y = h; y < foot; y++) img.set(x, y, y === h ? pal[1] : ramp(pal, .7 - (y - h) / 30, x, y));
      }
    });
  } else if (state === "NC" || state === "VA" || land.far === "ridges") {
    // The Blue Ridge: ridges fading into the haze.
    [[96, "#9fb6dc", "#b4c8e8"], [108, "#8199c8", "#98aedb"], [121, "#6683b8", "#7c97c9"]].forEach(([base, a, b], i) => {
      const pal = P(a, b);
      for (let x = 0; x < coastEnd; x++) {
        const h = fade(x, Math.round(base - fbm(x / 40, i * 3, 11 + i) * 18 + Math.sin(x / 23 + i) * 2));
        for (let y = h; y < foot; y++) img.set(x, y, y === h ? pal[1] : ramp(pal, .7 - (y - h) / 30, x, y));
      }
    });
  } else if (state === "FL" || land.far === "cypress") {
    // Cypress domes and cabbage palms on the far edge of the sawgrass.
    const dome = P("#3d5a44", "#4b6b4f", "#5b7d5a", "#6d8f66"), far = pxLayer(W, H);
    for (let i = 0; i < 9; i++) {
      const x = Math.round((i + .3 + hash2(i, 41) * .5) * coastEnd / 9), rx = 10 + Math.round(hash2(i, 42) * 12);
      pxBlob(far, x, 152, rx, 7 + Math.round(hash2(i, 43) * 6), dome, { flat: true, rough: .7, grain: 1, seed: i });
    }
    far.onto(img);
    const pf = P("#4f7a4a", "#6a9658"), trunk = P("#7a6a52");
    for (let i = 0; i < 12; i++) {
      const x = Math.round(hash2(i, 44) * (coastEnd - 10)) + 4, h = 10 + Math.round(hash2(i, 45) * 6), y0 = 152;
      for (let j = 0; j < h; j++) img.set(x, y0 - j, atmo(trunk[0], .2));
      for (const [dx, dy] of [[-3, 1], [-2, 0], [-1, -1], [1, -1], [2, 0], [3, 1], [0, -2], [-4, 2], [4, 2]])
        img.set(x + dx, y0 - h + dy, atmo(pf[dy < 0 ? 1 : 0], .2));
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
    // Mesas and buttes: flat caprock tops over red-and-tan banded cliffs.
    const rock = P("#9a5e44", "#b47456", "#c98c68", "#dca77f"), cap = P("#b88e6a", "#e6cba4");
    const hm = [];
    for (let x = -1; x <= coastEnd + 1; x++) {
      // Thresholded noise gives flat tops with steep sides; two layers make a big
      // mesa and smaller buttes in front of the haze.
      const n = vnoise(x / 30, 0, 21), k = clamp01((n - .45) * 9), k2 = clamp01((vnoise(x / 13, 0, 24) - .62) * 10);
      const step = k * k * (3 - 2 * k), step2 = k2 * k2 * (3 - 2 * k2);
      hm[x + 1] = fade(x, Math.round(140 - Math.max(step * 34 + (n > .68 ? 7 : 0), step2 * 22)));
    }
    for (let x = 0; x < coastEnd; x++) {
      const h = hm[x + 1], s = hm[x + 2] - hm[x];
      if (h >= 139) continue;
      for (let y = h; y < foot; y++) {
        const band = Math.floor((y - 100 + vnoise(x / 20, 0, 22) * 2) / 4) % 3;
        const lit = s > 1 ? -.3 : s < -1 ? .2 : 0;
        const v = .66 + lit - band * .14 + (vnoise(x / 5, y / 3, 23) - .5) * .22 - (y - h) * .006;
        img.set(x, y, atmo(y - h < 2 && Math.abs(s) < 2 ? cap[1 - (y - h)] : ramp(rock, v, x, y), .16));
      }
    }
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
  const hills = sc.flat ? [[150, 3, .021, sc.far, 20], [158, 2, .034, sc.near, 21]]
    : [[132, 12, .021, sc.far, 20], [150, 9, .034, sc.near, 21]];
  hills.forEach(([base, amp, k, hex, seed], li) => {
    const pal = P(...hex);
    for (let x = 0; x < L.sea - 10; x++) {
      const raw = base + Math.sin(x * k + base) * amp + Math.sin(x * k * 2.7) * 3;
      const h = Math.round(L.water + 10 - (L.water + 10 - raw) * env(x + 10, 60));
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
      : dots === "maple" ? (li ? 34 : 46) : (li ? 10 : 6);
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
      const h = Math.round(L.water + 10 - (L.water + 10 - raw) * env(x + 10, 60));
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
      if (dots === "oak") pxBlob(tl, x, y - 2, Math.round(5 * s + tr() * 2), Math.round(3 * s + 1), leaf, { rough: .5, seed: i });
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
    const n = fbm(x / 16, y / 7, 17);
    if (sc.snow && n + (fbm(x / 5, y / 3, 27) - .5) * .3 > .42) img.set(x, y, ramp(snowPal, .4 + (n - .42) * 3, x, y));
    else img.set(x, y, ramp(mead, .35 + (n - .5) * 1.1 + (y < L.water + 8 ? .2 : 0), x, y));
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
  for (let i = 0; i < sc.flowerCount; i++) {
    const cx = Math.floor(r() * (L.land - 16)) + 6, cy = L.water + 12 + Math.floor(r() * (H - L.water - 16));
    const [petal, mid] = flowerSets[Math.floor(r() * flowerSets.length)];
    for (let j = 0; j < 3 + r() * 3; j++) {
      const x = cx + Math.round((r() - .5) * 12), y = cy + Math.round((r() - .5) * 6);
      img.set(x, y + 1, blade[0]); img.set(x, y + 2, blade[0]);
      img.set(x - 1, y, petal); img.set(x + 1, y, petal); img.set(x, y - 1, petal); img.set(x, y + 1, petal); img.set(x, y, mid);
    }
  }
  if (sc.leaves === "fall") {
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
      pads.forEach(([dx, dy], i) => pxBlob(cac, cx + dx, fy + dy - 5, 3, 4 + (i === 0 ? 1 : 0), pad, { seed: i + fx * 10 }));
      pads.forEach(([dx, dy], i) => {
        if (i % 2) { cac.set(cx + dx, fy + dy - 10, P("#ffd94a")); cac.set(cx + dx + 1, fy + dy - 10, P("#ffe98a")); }
        else if (i) cac.set(cx + dx + 2, fy + dy - 9, P("#c8304a"));
        for (const [sx, sy] of [[-1, -6], [1, -4], [-2, -3], [2, -7]]) if (hash2(dx + sx, dy + sy, i) > .4) cac.set(cx + dx + sx, fy + dy + sy, P("#e8e4b8"));
      });
    }
    cac.onto(img, P("#22401f"));
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
  // The tree for roosting birds and a spider's thread: a big leafy oak, or in
  // North Carolina a longleaf pine.
  const tree = pxLayer(W, H), tx = L.tree, kind = sc.tree, ground = 194;
  for (let y = ground - 5; y <= ground + 6; y++) for (let x = tx - 30; x <= tx + 40; x++)
    if (((x - tx - 6) / 34) ** 2 + ((y - ground) / 6) ** 2 <= 1 && dith(x, y, .5)) img.set(x, y, pxMix(img.get(x, y), 0x1e3a14, .45));
  const bark = P("#4a3020", "#6e4a2e", "#8f6840", "#a98050");
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
    // Oaks stay green all year; other leafy trees turn in fall and are bare in a
    // snowy winter (New York's sugar maple is the reddest).
    const turn = kind !== "oak" && sc.leaves === "fall";
    const leaf = kind === "oak" ? P("#24391c", "#344f25", "#486b2f", "#62893c", "#86ab55")
      : turn && kind === "maple" ? P("#6a1a12", "#9a2a16", "#c8441c", "#e8702a", "#f6b040")
      : turn ? P("#7a3a14", "#a8561a", "#d07a24", "#e8a032", "#f6c850")
      : P("#22492a", "#2f6633", "#41863d", "#5aa548", "#84c55c");
    const crown = kind !== "oak" && sc.leaves === "bare" ? [] : [[-20, 88, 12], [22, 86, 13], [-8, 74, 14], [12, 70, 13], [2, 58, 11], [0, 92, 18],
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
