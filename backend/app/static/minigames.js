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
// The game is 200 high. Its width follows the screen while you play (320 to 480), so a
// wide phone is filled edge to edge: the scrolling games just see further ahead, and the
// ones laid out on one screen are centred (mgOx).
let MG_W = 320;
const MG_H = 200, MG_W0 = 320;
const mgOx = () => (MG_W - MG_W0) / 2;
// The canvas has as many real pixels per game pixel as the screen shows, so text stays
// sharp and pixel art isn't squeezed (squeezing dropped pixels and left dark specks).
let MG_RES = 4;
function mgFit(cv) {
  const res = Math.max(1, Math.min(8, Math.ceil((cv.clientWidth || MG_W * 4) * (window.devicePixelRatio || 1) / MG_W)));
  if (res !== MG_RES || cv.width !== MG_W * res) { MG_RES = res; cv.width = MG_W * res; cv.height = MG_H * res; }
}
const MG_GROUND = 172, MG_SURFACE = 34, MG_BED = 186;
const MG_GAMES = [
  { key: "sky", title: "Sky Glide", pose: "fly", kind: "flying animal", thing: ["berry", "berries"],
    how: "Tap to flap through the gaps in the storm clouds, and grab the berries on the way.", tip: "Tap to flap your wings" },
  { key: "trail", title: "Trail Run", pose: "walk", kind: "land animal", thing: ["acorn", "acorns"],
    how: "Tap to hop over rocks and logs, hold for a big jump, and stay low under branches. Land on rocks, logs, stumps and ledges to cross creeks and thorns.", tip: "Tap to jump, hold to jump higher" },
  { key: "river", title: "River Swim", pose: "swim", kind: "water animal", thing: ["point", "points"],
    how: "Hold to swim up, let go to dive. Slip between the rocks and roots, eat snacks and scoop up litter.", tip: "Hold to swim up, let go to dive" },
  { key: "pool", title: "Tide Pool Spin", pose: "idle", kind: "tide pool animal", thing: ["bite", "bites"],
    how: "Cling to your rock and turn around it. Hold the left or right side to turn through the gaps in the waves, and catch food as it washes in.",
    tip: "Hold left or right to turn" },
  { key: "claw", title: "Claw Catch", pose: "idle", kind: "animal with claws, talons or a quick tongue", thing: ["catch", "catches"],
    how: "Food leaps up on the beat: swipe across it to catch it. Don't swipe the bees, and don't let three get away.",
    tip: "Swipe across the food" },
  { key: "slide", title: "Mud Slide", pose: "swim", kind: "slippery animal, like an otter, salamander or snake,", thing: ["fish", "fish"],
    how: "Belly-slide down the muddy chute. Tap the top half of the screen to slide up a lane, the bottom half to slide down. Dodge logs and rocks, and grab the fish.",
    tip: "Tap top or bottom to change lanes" },
  { key: "leap", title: "Branch Leap", pose: "walk", kind: "tree climber or jumper, like a squirrel or tree frog,", thing: ["acorn", "acorns"],
    how: "Hold to wind up a leap and let go to jump to the next branch. The meter fills and then drops again, so let go at the right moment. Some branches sway to the music.",
    tip: "Hold to wind up, let go to leap" },
  { key: "dig", title: "Burrow Dig", pose: "walk", kind: "digging animal, like a mole or gopher,", thing: ["grub", "grubs"],
    how: "Hold your finger where you want to dig and your animal tunnels that way. Steer around rocks, roots and water all the way to your nest.",
    tip: "Hold where you want to dig" },
  { key: "nectar", title: "Nectar Rush", pose: "fly", kind: "hummingbird, bee or butterfly", thing: ["sip", "sips"],
    how: "Flowers open to the beat. Tap each flower right as it opens, and never tap one with a wasp on it. Three missed flowers end the try.",
    tip: "Tap each flower as it opens" },
  { key: "plunge", title: "Plunge Dive", pose: "fly", kind: "diving bird, like a pelican or kingfisher,", thing: ["fish", "fish"],
    how: "Hold to fold your wings and dive into the sea, let go to swim back up and fly. Grab the fish and keep clear of jellyfish and rocks.",
    tip: "Hold to dive, let go to come up" },
  { key: "splash", title: "Big Splash", pose: "swim", kind: "leaping swimmer, like a dolphin, seal or salmon,", thing: ["point", "points"],
    how: "Hold to dive deep, then let go to race up and leap out through the rings. The deeper you dive, the higher you leap. Watch out for floating logs and rocks.",
    tip: "Hold to dive, let go to leap" },
  { key: "call", title: "Call Back", pose: "idle", kind: "animal with a call, like a woodpecker, frog or cricket,", thing: ["note", "notes"],
    how: "A friend calls out a rhythm, then it's your turn: tap the same rhythm back. The dots show it too. Three mistakes end the try.",
    tip: "Listen, then tap it back" },
  { key: "echo", title: "Echo Flight", pose: "fly", kind: "night flier, like a bat, owl or moth,", thing: ["bug", "bugs"],
    how: "A dark cave at night. Hold to fly up, let go to drop. Every tap sends out an echo that lights up the cave for a moment, so tap often and remember the way.",
    tip: "Hold to rise, tap to echo" },
  { key: "feeder", title: "Feeder Rush", pose: "idle", kind: "songbird, like a sparrow, robin or dove,", thing: ["seed", "seeds"],
    how: "Seeds drop onto the feeder's three perches on the beat. Tap a perch to hop there and catch them. When a hawk's shadow darkens a perch, get off it! Three dropped seeds end the try.",
    tip: "Tap a perch to hop to it" },
  { key: "school", title: "School Swim", pose: "swim", kind: "fish", thing: ["bite", "bites"],
    how: "Lead your school of fish. Hold to squeeze together and slip through the gaps in the rocks. Let go to spread out so a hungry pike swims right between you. Grab the plankton.",
    tip: "Hold to squeeze, let go to spread" },
  { key: "freeze", title: "Freeze!", pose: "walk", kind: "land animal", thing: ["clover", "clovers"],
    how: "Hold to sneak along the path to your den, and let go to freeze. When the fox perks its ears it's about to turn round. If it sees you moving, you're caught. Get home before dark!",
    tip: "Hold to sneak, let go to freeze" },
];
const MG_LAND_ROLES = new Set(["walk", "hop", "shore", "beach", "dangle"]);
const MG_SHELL = /(?:^|_)(?:mussel|clam|oyster|scallop|cockle|barnacle|limpet|snail|whelk|periwinkle|nerite|conch|bonnet|turban|abalone|chiton|urchin|star|crab|lobster|crayfish|tortoise|turtle|cooter|slider|terrapin|armadillo|softshell|dogwinkle|slippersnail)(?:_|$)/;
const MG_CLAW = /(?:^|_)(?:bear|raccoon|bobcat|cougar|mountain_lion|lynx|fox|wolf|coyote|otter|badger|wolverine|fisher|marten|ocelot|cat|hawk|eagle|owl|osprey|falcon|kestrel|harrier|kite|crab|lobster|crayfish|mantis|heron|egret|kingfisher|bittern|frog|bullfrog|toad|treefrog)(?:_|$)/;
const MG_WATER_ROLES = new Set(["swim", "jelly", "float", "paddle"]);
// The newer games, by name: [game, who plays it, who doesn't].
const MG_MORE_KINDS = [
  ["slide", /(?:^|_)(?:otter|beaver|muskrat|mink|seal|sea_lion|walrus|salamander|newt|hellbender|mudpuppy|siren|amphiuma|slug|snake|watersnake|rattlesnake|copperhead|cottonmouth|racer|kingsnake|ratsnake|coachwhip|massasauga|boa|eel|lamprey)(?:_|$)/, /sea_slug|sea_hare|skink/],
  ["leap", /(?:^|_)(?:squirrel|chipmunk|treefrog|tree_frog|peeper|chorus_frog|cricket_frog|anole|jumping_spider|grasshopper|katydid|cricket|opossum|raccoon|marten|ringtail|fence_lizard|tree_lizard|gecko|flying_squirrel)(?:_|$)/, /ground_squirrel|antelope_squirrel|rock_squirrel|fish/],
  ["dig", /(?:^|_)(?:mole|gopher|ground_squirrel|antelope_squirrel|rock_squirrel|prairie_dog|badger|armadillo|kangaroo_rat|pocket_mouse|marmot|woodchuck|groundhog|chipmunk|vole|shrew|tortoise|toad|spadefoot|earthworm|cicada|burrowing_owl|mole_cricket|pika)(?:_|$)/, /gopher_snake|mole_crab|horned_toad/],
  ["nectar", /hummingbird|(?:^|_)(?:bee|bumble|butterfly|swallowtail|monarch|moth|skipper|fritillary|sulphur|admiral|hairstreak|painted_lady|buckeye|checkerspot|crescent|longwing|peacock|mourning_cloak|queen|sphinx)(?:_|$)|_(?:blue|white|copper)$/, /beetle|dasher|sawyer/],
  ["plunge", /(?:^|_)(?:pelican|osprey|kingfisher|tern|gannet|booby|loon|grebe|cormorant|anhinga|merganser|puffin|murre|guillemot|auklet|bald_eagle|tropicbird)(?:_|$)/],
  ["splash", /(?:^|_)(?:whale|dolphin|porpoise|orca|seal|sea_lion|walrus|otter|salmon|trout|steelhead|sea_turtle|ridley|loggerhead|leatherback|flying_fish|mullet|tarpon|marlin|sailfish|tuna|mahi|manta|spinner)(?:_|$)/, /river_otter|elephant_seal/],
  ["call", /(?:^|_)(?:woodpecker|flicker|sapsucker|frog|bullfrog|toad|peeper|cricket|katydid|cicada|rattlesnake|massasauga|prairie_dog|beaver|grouse|quail|bobwhite|turkey|loon|elk|coyote|wolf|owl|mockingbird|wren|cardinal|whip_poor_will|chickadee|cuckoo|jay|crow|raven|towhee|sea_lion)(?:_|$)/, /vulture|limpet/],
  ["feeder", /(?:^|_)(?:sparrow|finch|goldfinch|siskin|redpoll|junco|towhee|bunting|cardinal|grosbeak|robin|thrush|bluebird|dove|pigeon|warbler|kinglet|wren|chickadee|titmouse|bushtit|verdin|nuthatch|creeper|jay|magpie|crow|raven|blackbird|grackle|starling|cowbird|oriole|tanager|phoebe|flycatcher|kingbird|pewee|mockingbird|thrasher|catbird|waxwing|vireo|woodpecker|flicker|sapsucker|lark|meadowlark|myna|bulbul|leiothrix|white_eye|canary|longspur|dickcissel|phainopepla|bobolink)(?:_|$)/, /sea_robin|cardinalfish|swallowtail|blue_jay_butterfly/],
  ["school", /(?:^|_)(?:darter|stoneroller|dace|shiner|minnow|chub|sunfish|bluegill|bass|crappie|perch|mosquitofish|guppy|killifish|topminnow|sculpin|garibaldi|surgeonfish|tang|damselfish|sergeant|wrasse|butterflyfish|angelfish|idol|triggerfish|goby|blenny|cichlid|tilapia|trout|salmon|herring|anchovy|sardine|smelt|grunion|silverside|mullet|snapper|grouper|rockfish|halibut|flounder|catfish|bullhead|sucker|carp|goldfish|koi|pupfish|gar|bowfin|shad|goldeye|walleye|pike|pickerel|drum|croaker|opaleye|sheephead|parrotfish|chromis|tetra|cod|mackerel|bonito|pufferfish|puffer|filefish|cardinalfish|hawkfish|sea_chub|halfmoon|blacksmith|kelpfish|mudsucker|stickleback|madtom|logperch|mojarra|pinfish|porgy|sheepshead|tarpon|snook|ladyfish|needlefish|squirrelfish|soldierfish|goatfish|boxfish|cowfish|trunkfish|scorpionfish|lionfish|sandperch|surfperch|lingcod|greenling|cabezon|tautog|cunner|bluefish|pompano|jack|molly|unicornfish|toby)(?:_|$)/, /herring_gull|pickerel_frog|jack_rabbit|jackrabbit/],
  ["echo", /(?:^|_)(?:bat|owl|nighthawk|nightjar|poorwill|whip_poor_will|chuck_will_s_widow|chuck_wills_widow|moth|firefly)(?:_|$)/, /bat_star|bat_ray|batfish|limpet/],
];
const mg = { taps: [], px: MG_W / 2, py: MG_H / 2, entries: [], game: null, slug: null, run: null, raf: 0, last: 0, visible: true, down: false, built: false,
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
  // Animals with a shell or armor (mussels, snails, crabs, turtles, sea stars, urchins)
  // tuck in and turn, and so do the tide pool animals that can't get about at all.
  if (s.category !== "bird" && (MG_SHELL.test(s.slug) || role === "reef")) kinds.push("pool");
  // Claws, talons, pincers, spear beaks and sticky tongues: the swipe game.
  if (MG_CLAW.test(s.slug) && !/fox_squirrel|limpet|butterflyfish/.test(s.slug)) kinds.push("claw");
  for (const [key, re, not] of MG_MORE_KINDS) if (re.test(s.slug) && !(not && not.test(s.slug))) kinds.push(key);
  // Anything that walks or hops on the ground can sneak up on the fox.
  if (["walk", "hop", "dangle", "shore"].includes(role) && s.category !== "bird" && !MG_SHELL.test(s.slug)) kinds.push("freeze");
  if (["hover", "flutter"].includes(role) && !/_bat$|skimmer|dasher|whitetail|pennant|lanternfly|firefly/.test(s.slug) && !kinds.includes("nectar")) kinds.push("nectar");
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
  mgLoadShop();
}

// ---- Coins and the shop ----------------------------------------------------------
// Finished levels pay coins (app/games.py), which buy skins for your animals and
// decorations for your habitat. Logged out or offline, there's no shop.
function mgLoadShop() {
  mgApi("GET", "/games/shop").then(mgShopGot).catch(() => {});
}
function mgShopGot(d) {
  mg.shop = d;
  habLookSet(d);
  if (!mg.run) mgList();
}
function mgShopDo(path, body) {
  mgApi("POST", path, body).then(mgShopGot).catch((e) => alert(e.message));
}

function mgShopBar(list) {
  const d = mg.shop;
  if (!d) return;
  const bar = mgEl("div", "mg-shopbar"), open = mgStore.get("shop") === "1";
  const btn = mgEl("button", "mg-back", open ? "Close shop" : "🛍️ Shop");
  btn.onclick = () => { mgStore.set("shop", open ? "0" : "1"); mgList(); };
  bar.append(mgEl("b", "mg-coins", `🪙 ${d.coins} coins`), btn);
  list.append(bar);
  if (!open) return;
  const shop = mgEl("div", "mg-shop");
  shop.append(mgEl("div", "mg-how", "Finish levels to earn coins. Skins recolor your animal in the games; decorations go in your habitat."));
  for (const it of d.items) {
    const row = mgEl("div", "mg-item");
    row.append(mgEl("span", null, `${it.kind === "skin" ? "🎨" : "🌼"} ${it.name}`), mgEl("span", "muted", it.kind === "skin" ? "Skin" : "Habitat"));
    let b;
    if (!it.owned) {
      b = mgEl("button", "mg-play", `🪙 ${it.price}`);
      b.disabled = d.coins < it.price;
      b.onclick = () => mgShopDo("/games/shop/buy", { item: it.key });
    } else if (it.kind === "decor") {
      b = mgEl("button", "mg-back", it.on ? "Hide" : "Show");
      b.onclick = () => mgShopDo("/games/shop/decor", { item: it.key, on: !it.on });
    } else b = mgEl("span", "muted", "Owned");
    row.append(b);
    shop.append(row);
  }
  list.append(shop);
}

// Under the animal picker: its look, from the skins you own. Picking one recolors the
// animal in the picker straight away (onPick), then saves it on the server.
function mgLooks(slug, onPick) {
  const d = mg.shop, owned = d ? d.items.filter((i) => i.kind === "skin" && i.owned) : [];
  const box = mgEl("div", "mg-looks");
  if (!owned.length) return box;
  const now = d.skins[slug] || null;
  box.append(mgEl("i", null, "Look"));
  for (const [skin, name] of [[null, "Normal"], ...owned.map((i) => [i.key.split(".")[1], i.name])]) {
    const b = mgEl("button", "mg-tab" + (skin === now ? " on" : ""), name);
    b.onclick = () => {
      if (skin) d.skins[slug] = skin; else delete d.skins[slug];
      habLookSet(d);
      box.querySelectorAll("button").forEach((x) => x.classList.toggle("on", x === b));
      onPick?.();
      mgApi("POST", "/games/shop/skin", { species: slug, skin }).then((r) => { mg.shop = r; habLookSet(r); }).catch((e) => alert(e.message));
    };
    box.append(b);
  }
  return box;
}

// A sprite's URL in a skin's colours (a data URL), or the plain sprite; again() runs
// once the sprite has loaded if it wasn't yet.
function mgSkinned(slug, skin, again) {
  const url = `/sprites/${encodeURIComponent(slug)}.png`;
  if (!skin) return url;
  const img = mgImg(mg.imgs, url);
  if (!img.complete || !img.naturalWidth) { img.addEventListener("load", () => again?.(), { once: true }); return url; }
  const cv = habSkin(img, skin);
  return cv === img ? url : (cv.dataUrl ||= cv.toDataURL());
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
    const img = mgEl("img"), skin = e.skin && HAB_SKINS[e.skin] ? e.skin : null;
    if (e.species.slug) {
      // In the skin it wore for the score, like a Frosty bobcat.
      const src = `/sprites/${encodeURIComponent(e.species.slug)}.png`;
      if (skin) { const raw = new Image(); raw.onload = () => { const cv = habSkin(raw, skin); if (cv !== raw) img.src = cv.toDataURL(); }; raw.src = src; }
      else img.src = src;
      img.alt = e.species.common_name;
    } else img.style.visibility = "hidden";
    const name = skin ? `${e.skin[0].toUpperCase()}${e.skin.slice(1)} ${e.species.common_name}` : e.species.common_name;
    li.append(img, mgEl("span", "mg-who", `${e.you ? "You" : e.username} as ${name}`), mgEl("span", "mg-pts", e.points));
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
  .mg-grid { display:grid; grid-template-columns:repeat(4, minmax(0, 1fr)); gap:8px; }
  .mg-tile { font:inherit; color:inherit; background:transparent; border:1px solid var(--line); border-radius:12px; padding:6px 4px 7px;
             cursor:pointer; display:flex; flex-direction:column; align-items:center; gap:4px; min-width:0; }
  .mg-thumb { width:100%; aspect-ratio:1; border-radius:9px; display:flex; align-items:center; justify-content:center;
              font-size:1.6rem; position:relative; }
  .mg-thumb img { width:62%; height:62%; image-rendering:pixelated; }
  .mg-thumb .mg-padlock { position:absolute; right:3px; bottom:2px; font-size:.85rem; }
  .mg-tile b { font-size:.74rem; line-height:1.15; text-align:center; }
  .mg-tile span { font-size:.68rem; color:var(--muted); }
  .mg-tile.mg-locked .mg-thumb { filter:grayscale(.8); }
  .mg-stat-how { margin-top:2px; font-size:.72rem; color:var(--muted); }
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
  .mg-shopbar { display:flex; justify-content:space-between; align-items:center; }
  .mg-coins { font-size:.95rem; }
  .mg-shop { border:1px solid var(--line); border-radius:12px; padding:8px 12px; display:grid; gap:6px; }
  .mg-item { display:grid; grid-template-columns:1fr auto auto; gap:8px; align-items:center; font-size:.85rem; }
  .mg-item .mg-play { padding:3px 12px; }
  .mg-item .mg-play:disabled { opacity:.45; cursor:default; }
  .mg-looks { display:flex; gap:4px; flex-wrap:wrap; align-items:baseline; margin-top:4px; font-size:.75rem; }
  .mg-looks:empty { display:none; }
  .mg-looks i { font-style:normal; color:var(--muted); margin-right:4px; }
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
  .mg-stage canvas { display:block; width:100%; height:auto; border-radius:10px;
                     touch-action:none; user-select:none; -webkit-user-select:none; cursor:pointer; }
  .mg-bar { display:flex; justify-content:space-between; align-items:center; margin-top:6px; font-size:.85rem; }
  /* Playing fills the whole screen. A phone held upright gets the game turned sideways,
     so it's as big as it can be: turn the phone to play. */
  .mg-stage.full { position:fixed; inset:0; z-index:1000; background:#0b120b; color:#e6eee6; }
  .mg-stage.full .mg-turn { position:absolute; inset:0; display:flex; align-items:center; justify-content:center; }
  .mg-stage.full canvas { border-radius:0; }
  /* The buttons sit on the game, small, in the bottom corners. */
  .mg-stage.full .mg-bar { position:absolute; left:8px; right:8px; bottom:6px; margin:0; pointer-events:none; }
  .mg-stage.full .mg-bar > * { pointer-events:auto; }
  .mg-stage.full .mg-bar .mg-back { font-size:.72rem; padding:2px 10px; background:rgba(0,0,0,.35); color:#fff;
                                    border-color:rgba(255,255,255,.35); }
  .mg-stage.full #mg-playing { display:none; }
  @media (orientation: portrait) {
    .mg-stage.full .mg-turn { inset:auto; top:0; left:100vw; width:100vh; width:100dvh; height:100vw;
                              transform-origin:top left; transform:rotate(90deg); }
  }
  .mg-back { font:inherit; font-size:.85rem; padding:4px 12px; border-radius:999px; border:1px solid var(--line);
             background:transparent; color:var(--accent); cursor:pointer; }`;
  document.head.append(css);
  const box = document.getElementById("minigames");
  const list = mgEl("div", "mg-list"), stage = mgEl("div", "mg-stage hidden");
  list.id = "mg-list";
  const cv = mgEl("canvas");
  cv.width = MG_W * MG_RES; cv.height = MG_H * MG_RES; cv.id = "mg-canvas";
  const bar = mgEl("div", "mg-bar"), back = mgEl("button", "mg-back", "← Back"), name = mgEl("span", "muted");
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
  const turn = mgEl("div", "mg-turn");
  turn.append(cv, bar);
  stage.append(turn);
  box.append(list, stage);
  const press = (on, dir, pt) => {
    if (pt) [mg.px, mg.py] = pt;
    // The newer games hear every tap, even one quicker than a frame.
    if (on && mg.run && mg.run.mode === "play" && MG_MORE[mg.game.key]) mg.taps.push(pt || [MG_W / 2, MG_H / 2]);
    if (on && !mg.down) mgTap();
    mg.down = on;
    mg.dir = on ? dir || 0 : 0;  // Tide Pool Spin: -1 turns left (anticlockwise), 1 right
  };
  cv.addEventListener("pointerdown", (e) => {
    e.preventDefault(); try { cv.setPointerCapture(e.pointerId); } catch {}
    mg.swipe = [mgGamePt(cv, e)];
    press(true, mg.swipe[0][0] < MG_W / 2 ? -1 : 1, mg.swipe[0]);
  });
  // Claw Catch: the path of your finger while it's down.
  cv.addEventListener("pointermove", (e) => {
    if (!mg.down) return;
    const pt = mgGamePt(cv, e);
    [mg.px, mg.py] = pt;
    if (mg.swipe) mg.swipe.push(pt);
  });
  ["pointerup", "pointercancel", "lostpointercapture"].forEach((t) => cv.addEventListener(t, () => press(false)));
  cv.addEventListener("contextmenu", (e) => e.preventDefault());
  // Keys stand for a spot on the screen: up and down are its top and bottom, left and
  // right its sides, and 1 to 4 (or the arrows, in Nectar Rush) the four flowers.
  const KEY_AT = { ArrowUp: [200, 30], w: [200, 30], W: [200, 30], ArrowDown: [120, 170], s: [120, 170], S: [120, 170],
                   ArrowLeft: [40, 100], a: [40, 100], A: [40, 100], ArrowRight: [280, 100], d: [280, 100], D: [280, 100],
                   1: [40, 100], 2: [120, 100], 3: [200, 100], 4: [280, 100], " ": [160, 100], Enter: [160, 100] };
  const keys = (e) => e.key in KEY_AT;
  const dirOf = (e) => (["ArrowLeft", "a", "A"].includes(e.key) ? -1 : ["ArrowRight", "d", "D"].includes(e.key) ? 1 : 0);
  addEventListener("keydown", (e) => {
    if (!mg.run || !mg.visible || !keys(e)) return;
    e.preventDefault();
    if (e.repeat) return;
    // A second key while one is held is a tap of its own (two flowers at once).
    const at = [KEY_AT[e.key][0] * MG_W / MG_W0, KEY_AT[e.key][1]];
    if (mg.down && mg.run.mode === "play" && MG_MORE[mg.game.key]) { mg.taps.push(at); [mg.px, mg.py] = at; return; }
    press(true, dirOf(e), at);
  });
  addEventListener("keyup", (e) => { if (mg.run && keys(e)) press(false); });
  // Stop when the tab is switched away or the page is hidden; the round waits.
  new IntersectionObserver(([en]) => { mg.visible = en.isIntersecting; mgWake(); }).observe(cv);
  document.addEventListener("visibilitychange", mgWake);
}

function mgGamePt(cv, e) {
  const b = cv.getBoundingClientRect();
  // Turned sideways (see .mg-stage.full): the game's left is the top of the screen.
  if (mgTurned()) return [(e.clientY - b.top) / b.height * MG_W, (b.right - e.clientX) / b.width * MG_H];
  return [(e.clientX - b.left) / b.width * MG_W, (e.clientY - b.top) / b.height * MG_H];
}
const mgTurned = () => document.getElementById("mg-stage")?.classList.contains("full") && matchMedia("(orientation: portrait)").matches;

// Full screen while playing: the browser's own full screen where it has one (and
// sideways on phones that allow it), else just the page covered. The Android app
// hides its bars too (AndroidMinigames.playing).
function mgFull(on) {
  const stage = document.getElementById("mg-stage");
  stage.classList.toggle("full", on);
  mgFill();
  document.documentElement.style.overflow = on ? "hidden" : "";
  try { window.AndroidMinigames?.playing(on); } catch {}
  try {
    if (on && !document.fullscreenElement && stage.requestFullscreen) {
      stage.requestFullscreen({ navigationUI: "hide" }).then(() => screen.orientation?.lock?.("landscape")).catch(() => {});
    } else if (!on && document.fullscreenElement) {
      screen.orientation?.unlock?.(); document.exitFullscreen().catch(() => {});
    }
  } catch {}
}

// Sizes the game to the screen: as wide as the screen's shape allows, the whole height.
function mgFill() {
  const stage = document.getElementById("mg-stage"), cv = document.getElementById("mg-canvas");
  if (!stage || !cv) return;
  const full = stage.classList.contains("full");
  let w = MG_W0;
  if (full) {
    const turned = matchMedia("(orientation: portrait)").matches;
    const sw = turned ? innerHeight : innerWidth, sh = turned ? innerWidth : innerHeight;
    w = Math.round(mgClamp(MG_H * sw / sh, MG_W0, 480));
    const k = Math.min(sw / w, sh / MG_H);
    cv.style.width = `${Math.floor(w * k)}px`; cv.style.height = `${Math.floor(MG_H * k)}px`;
  } else { cv.style.width = ""; cv.style.height = ""; }
  if (w !== MG_W) { MG_W = w; MG_POOL.cx = MG_W / 2; mgFit(cv); if (mg.run && !mg.raf) mgDraw(); }
}
addEventListener("resize", () => mgFill());

// The Games tab: a grid of games, four to a row. Tapping one opens it to pick an
// animal and a level (mgGame); mg.open remembers which, so a game you quit goes back there.
const MG_TILES = { sky: ["☁️", "#cfe8f7"], trail: ["🌲", "#d6ecc6"], river: ["🌊", "#bfdcef"], pool: ["🐚", "#c7ece6"],
                   claw: ["🐾", "#f6dcc0"], slide: ["🪵", "#e2cfb2"], leap: ["🌳", "#cde6b8"], dig: ["🕳️", "#d8c3a5"],
                   nectar: ["🌸", "#f6d6e6"], plunge: ["🐟", "#c4e2f2"], splash: ["🐬", "#b8d8f0"], call: ["🎵", "#efe2b8"],
                   echo: ["🦇", "#c9c6e0"], feeder: ["🌻", "#f4e4b0"], school: ["🐠", "#b8dcec"], freeze: ["🦊", "#f2d2b8"] };
function mgList() {
  mgBuild();
  const list = document.getElementById("mg-list");
  list.innerHTML = "";
  const g = MG_GAMES.find((x) => x.key === mg.open);
  try { window.AndroidMinigames?.picking?.(!!g); } catch {}
  if (g) return mgGame(list, g);
  mgShopBar(list);
  const grid = mgEl("div", "mg-grid");
  for (const g of MG_GAMES) {
    const players = mgPlayers(g.key), lvls = MG_LEVELS[g.key];
    const cleared = lvls.filter((_, i) => mgRec(g.key, i).pct >= 100).length;
    const tile = mgEl("button", "mg-tile" + (players.length ? "" : " mg-locked"));
    const [icon, bg] = MG_TILES[g.key] || ["🎮", "#ddd"];
    const thumb = mgEl("div", "mg-thumb");
    thumb.style.background = bg;
    if (players.length) {
      const saved = mgStore.get("pick." + g.key), s = players.find((p) => p.slug === saved) || players[0];
      const img = mgEl("img");
      img.src = `/sprites/${encodeURIComponent(s.slug)}.png`; img.alt = "";
      thumb.append(img);
    } else {
      thumb.append(icon, mgEl("span", "mg-padlock", "🔒"));
    }
    tile.append(thumb, mgEl("b", null, g.title),
                mgEl("span", null, players.length ? `${cleared}/${lvls.length} cleared` : "Locked"));
    tile.onclick = () => { mg.open = g.key; mgList(); scrollTo?.(0, 0); };
    grid.append(tile);
  }
  list.append(grid);
}

// Back from a game's page to the grid (the Android back button calls this too).
function mgCloseGame() {
  mg.open = null;
  mgList();
}

function mgGame(list, g) {
  const back = mgEl("button", "mg-back", "← All games");
  back.onclick = mgCloseGame;
  list.append(mgEl("div", "mg-shopbar"));
  list.lastChild.append(back);
  {
    const players = mgPlayers(g.key), card = mgEl("div", "mg-game" + (players.length ? "" : " mg-locked"));
    const h = mgEl("h3", null, g.title), lvls = MG_LEVELS[g.key];
    const cleared = lvls.filter((_, i) => mgRec(g.key, i).pct >= 100).length;
    if (cleared) h.append(mgEl("span", "mg-best", `${cleared} of ${lvls.length} levels cleared`));
    card.append(h, mgEl("div", "mg-how", g.how));
    if (!players.length) {
      card.append(mgEl("div", "mg-lock", `🔒 Capture a ${g.kind} to unlock this game.`));
      list.append(card);
      return;
    }
    const saved = mgStore.get("pick." + g.key);
    let pick = players.find((s) => s.slug === saved) || players[0];
    const row = mgEl("div", "mg-pick"), foot = mgEl("div", "mg-row"), name = mgEl("span", "mg-name", pick.common_name);
    const stats = mgEl("div", "mg-stats"), statHow = mgEl("div", "mg-stat-how");
    let looks = mgEl("div");
    const showStats = () => {
      const fresh = mgLooks(pick.slug, paint);
      looks.replaceWith(fresh); looks = fresh;
      const st = mgStats(pick.slug, g.key);
      stats.innerHTML = "";
      const used = MG_GAME_STATS[g.key] || [];
      used.forEach(([name, field]) => {
        const v = st[field], [label, how] = MG_STAT_INFO[name], cell = mgEl("span", "mg-stat");
        cell.title = `${label}: ${how}`;
        cell.append(mgEl("i", null, label), mgEl("b", null, "●".repeat(v) + "○".repeat(5 - v)));
        stats.append(cell);
      });
      statHow.textContent = used.map(([name]) => `${MG_STAT_INFO[name][0]}: ${MG_STAT_INFO[name][1]}`).join(" · ");
    };
    const play = mgEl("button", "mg-play", "Play");
    const imgs = [];
    // The picked animal in the colour it will play in.
    const paint = () => imgs.forEach(([s, img]) => { img.src = mgSkinned(s.slug, s === pick ? habLook.skins[s.slug] : null, paint); });
    for (const s of players) {
      const img = mgEl("img", s === pick ? "on" : "");
      imgs.push([s, img]);
      img.src = `/sprites/${encodeURIComponent(s.slug)}.png`;
      img.alt = img.title = s.common_name;
      img.onclick = () => {
        pick = s; name.textContent = s.common_name; mgStore.set("pick." + g.key, s.slug); showStats(); paint();
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
               mgEl("span", null, !open(i) ? `🔒 Finish level ${i} first` : rec.pct >= 100 ? `✓ Best ${rec.points || rec.got} points` : rec.pct ? `Best ${rec.pct}%${rec.points ? `, ${rec.points} points` : ""}` : "New"));
      b.disabled = !open(i);
      b.onclick = () => {
        lv = i; mgStore.set("lvl." + g.key, i); levels.querySelectorAll(".mg-lv").forEach((e, j) => e.classList.toggle("on", j === i));
        mgBoard(board, `${g.key}.${i}`, mgStore.get("board") || "all");
      };
      levels.append(b);
    });
    play.onclick = () => mgStart(g, pick, lv);
    foot.append(name, play);
    showStats(); paint();
    const board = mgEl("div", "mg-board");
    mgBoard(board, `${g.key}.${lv}`, mgStore.get("board") || "all");
    card.append(row, stats, statHow, looks, levels, foot, board);
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
  mgFull(true);
  mgReset("ready");
  mgWake();
}

function mgQuit() {
  cancelAnimationFrame(mg.raf); mg.raf = 0;
  mgMusicStop(mg.run);
  mg.run = null; mg.down = false;
  mgFull(false);
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
const MG_SPEED = { sky: 75, trail: 100, river: 70, pool: 60, claw: 60,
                   slide: 110, leap: 60, dig: 70, nectar: 60, plunge: 80, splash: 75, call: 60, echo: 72 };
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
// and low branches you must stay under (don't jump!). Rocks, logs and stumps can be
// stood on, and so can ledges up in the air: they carry you over creeks and thorns,
// or up to acorns.
//   ["ledge", beat, height, width, acorns]  a ledge whose top is that high up
//   ["pit", beat, width]                    a creek to jump; falling in ends the try
//   ["stones", beat, n]                     a wide creek with n stepping stones
//   ["bridge", beat, width, height]         thorns too long to jump, with a ledge over them
function mgTrailLevel(k, list) {
  const out = [], g = MG_GROUND;
  const ledge = (wx, h, w, n) => out.push({ type: "ledge", plat: true, wx, y: g - h + 3, w, h: 6 },
    ...(n ? mgTrail("acorn", wx - w / 2 + 10, g - h - 11, wx + w / 2 - 10, g - h - 11, n) : []));
  for (const [type, b, a, c, n] of list) {
    const wx = b * k;
    if (type === "rock") out.push({ type, plat: true, wx, y: g - 5 }, ...mgTrail("acorn", wx - 18, g - 34, wx + 18, g - 34, 3));
    else if (type === "log") out.push({ type, plat: true, wx, y: g - 4 }, ...mgTrail("acorn", wx - 20, g - 36, wx + 20, g - 36, 3));
    else if (type === "stump") out.push({ type, plat: true, wx, y: g - 10 }, ...mgTrail("acorn", wx - 14, g - 48, wx + 14, g - 48, 2));
    else if (type === "ledge") ledge(wx, a, c, n);
    else if (type === "pit") out.push({ type, wx, y: g + 14, w: a, h: 28 }, ...mgTrail("acorn", wx - 10, g - 40, wx + 10, g - 40, 2));
    else if (type === "stones") {
      const gap = 36, w = 26, span = a * w + (a + 1) * gap;
      out.push({ type: "pit", wx: wx + span / 2, y: g + 14, w: span, h: 28 });
      for (let i = 0; i < a; i++) {
        const x = wx + gap + w / 2 + i * (w + gap);
        out.push({ type: "stone", plat: true, wx: x, y: g + 3, w, h: 6 }, ...mgTrail("acorn", x, g - 26, x, g - 26, 1));
      }
    } else if (type === "bridge") { out.push({ type: "thorns", wx, y: g - 5, w: a, h: 10 }); ledge(wx - 14, c, a + 36, Math.round(a / 22)); }
    else if (type === "branch") out.push({ type, wx, y: g - 35 }, ...mgTrail("acorn", wx - 12, g - 8, wx + 12, g - 8, 2));
    else if (type === "acorns") out.push(...mgTrail("acorn", wx - 20, g - 8, wx + 20, g - 8, 3));
  }
  return out;
}

// Tide Pool Spin, like Super Hexagon: the animal clings to a rock in the middle of the
// pool and turns around it, while rings of waves wash in from the edge. Each ring has
// six sides, some of them foam; slip through an open side. wx is when a ring reaches
// the animal, so a ring's size is how far it still has to come. Food washes in through
// the open sides.
const MG_POOL = { cx: 160, cy: 108, r: 30, thick: 9, turn: 4.4 };
const MG_SIDE = Math.PI / 3;
// Which sides are foam (1) for each kind of ring, before it's turned by g sides.
const MG_RINGS = { c: [0, 1, 1, 1, 1, 1], v: [0, 1, 1, 0, 1, 1], alt: [0, 1, 0, 1, 0, 1], half: [0, 0, 0, 1, 1, 1], two: [0, 0, 1, 1, 1, 1] };

function mgPoolLevel(k, rings) {
  const out = [];
  for (const [b, kind, g] of rings) {
    const wx = b * k, sides = MG_RINGS[kind].map((_, i, a) => a[((i - g) % 6 + 6) % 6]);
    out.push({ type: "wave", wx, sides });
    // A bite in the first open side, half a beat before the ring.
    const open = sides.indexOf(0);
    out.push({ type: "food", good: true, pts: 1, wx: wx - k / 2, ang: (open + .5) * MG_SIDE });
  }
  return out;
}

// Claw Catch, like Fruit Ninja but learnable: food leaps up from the bottom and hangs
// at the top of its leap right on a beat; swipe across it. Bees leap too: swiping one
// ends the try, and so does letting three bites get away. wx is when a thing is at
// the top of its leap.
const MG_CLAW_G = 260;
function mgClawLevel(k, list) {
  return list.map(([b, x, kind, top, vx]) => ({ type: kind === "b" ? "bee" : "prey", good: kind !== "b", pts: 1,
                                                wx: b * k, x0: x, top: top || 60, vx: vx || 0 }));
}
// Where a leaping thing is now (null when it's below the screen).
function mgClawAt(o, r) {
  const tau = (o.wx - r.dist) / MG_SPEED.claw, y = o.top + MG_CLAW_G * tau * tau / 2;
  return y > MG_H + 12 ? null : [o.x0 - o.vx * tau + mgOx(), y, tau];
}

// Levels are written in beats of their song, so every hazard lands on the music:
// the tempo is the difficulty. [beat, gap middle, gap size] for gates.
const MG_LEVELS = {
  sky: [
    { name: "Meadow Breeze", bpm: 122, song: 0, items: (k) => mgSkyLevel(k, [
      [8, 100, 60], [12, 85, 60], [16, 110, 60], [20, 95, 60],
      [24, 70, 60], [28, 60, 58], [32, 75, 58],
      [38, 120, 58], [42, 130, 58], [46, 115, 58],
      [52, 90, 56], [55, 80, 56], [58, 70, 56], [61, 60, 56],
      [66, 100, 56], [70, 130, 56], [74, 95, 56], [78, 60, 56], [82, 100, 56], [86, 110, 56], [90, 80, 56],
      // The second half: closer and tighter.
      [94, 106, 50], [97, 121, 50], [99.5, 92, 50], [102.5, 125, 50], [105.5, 136, 50], [108, 108, 50],
      [110.5, 100, 50], [113.5, 76, 50], [116.5, 94, 50], [119.5, 89, 50], [122.5, 124, 50], [125.5, 96, 50],
      [128, 76, 50], [131, 50, 50], [133.5, 65, 50], [136.5, 58, 50], [139.5, 50, 50], [142.5, 68, 50],
      [145.5, 102, 50], [148.5, 106, 50], [151, 94, 50], [154, 83, 50],
    ], [[14, 145], [26, 140], [40, 52], [64, 140], [76, 140]]) },
    { name: "Storm Front", bpm: 138, song: 1, items: (k) => mgSkyLevel(k, [
      [8, 100, 50], [12, 70, 50], [16, 110, 50], [20, 70, 50], [24, 110, 50],
      [28, 130, 48], [30, 114, 48], [32, 98, 48], [34, 82, 48], [36, 66, 48],
      [40, 60, 48], [43, 100, 48], [46, 60, 48], [49, 100, 48], [52, 60, 48],
      [56, 140, 50], [58, 130, 50], [60, 120, 48], [62, 110, 48],
      [66, 50, 46], [69, 90, 46], [72, 130, 46], [75, 90, 46], [78, 50, 46],
      [82, 100, 46], [84, 100, 46], [86, 100, 46], [90, 70, 46], [94, 120, 46], [98, 95, 46], [102, 95, 46],
      // The second half: closer and tighter.
      [106, 67, 48], [109, 50, 48], [112, 50, 48], [115, 50, 48], [117, 92, 48], [120, 101, 48],
      [122, 115, 48], [125, 128, 48], [127, 121, 48], [129.5, 99, 48], [132.5, 85, 48], [135, 113, 48],
      [137, 135, 48], [139, 133, 48], [142, 145, 48], [144, 145, 48], [146.5, 115, 48], [149.5, 123, 48],
      [152, 121, 48], [154.5, 138, 48], [156.5, 98, 48], [159.5, 62, 48], [162.5, 90, 48], [164.5, 88, 48],
      [167.5, 87, 48], [170.5, 105, 48],
    ], [[38, 100], [54, 100], [64, 75], [80, 120], [88, 50]]) },
  ],
  trail: [
    { name: "Forest Path", bpm: 136, song: 2, items: (k) => mgTrailLevel(k, [
      ["acorns", 4], ["rock", 8], ["rock", 12], ["log", 16], ["acorns", 19],
      // Your first ledge: hop up for the acorns, or run underneath.
      ["ledge", 23, 26, 70, 3], ["rock", 28], ["branch", 31], ["acorns", 34],
      ["pit", 38, 44], ["rock", 42], ["log", 46], ["stump", 50], ["acorns", 53],
      ["ledge", 57, 26, 60, 2], ["ledge", 59.5, 48, 60, 3], ["rock", 64], ["branch", 67.5],
      ["pit", 71, 48], ["log", 75], ["bridge", 80, 66, 26], ["rock", 86], ["rock", 89],
      // The second half: faster combinations.
      ["stump", 93], ["rock", 96], ["stump", 98.5], ["pit", 102, 48], ["branch", 105.5], ["log", 108.5],
      ["stones", 111, 2], ["rock", 117], ["stump", 120], ["ledge", 122.5, 44, 56, 3], ["pit", 126, 52],
      ["branch", 129.5], ["bridge", 133.5, 88, 28], ["stump", 140], ["rock", 142.5], ["pit", 145.5, 52],
      ["ledge", 149.5, 26, 56, 2], ["ledge", 152, 50, 56, 3], ["ledge", 154.5, 26, 56, 2], ["rock", 158],
      ["stones", 160, 3], ["stump", 167], ["rock", 169.5], ["branch", 172.5], ["log", 175.5],
    ]) },
    { name: "Rocky Ridge", bpm: 150, song: 3, items: (k) => mgTrailLevel(k, [
      ["rock", 8], ["rock", 11], ["rock", 14], ["log", 18], ["branch", 22],
      ["stump", 26], ["rock", 30], ["branch", 33], ["log", 37], ["pit", 41, 48],
      ["stump", 44], ["stump", 48], ["branch", 52], ["ledge", 56, 28, 60, 3], ["pit", 59, 52], ["rock", 62],
      ["branch", 66], ["log", 69], ["stump", 73], ["branch", 77], ["bridge", 81, 66, 26], ["log", 87],
      ["stump", 90], ["rock", 93], ["branch", 96], ["stones", 99, 3], ["stump", 106], ["log", 109.5], ["rock", 112.5],
      // The second half: faster combinations.
      ["rock", 116], ["stump", 119], ["branch", 121.5], ["pit", 124.5, 52], ["stump", 127.5], ["stump", 130.5],
      ["ledge", 134, 26, 50, 2], ["ledge", 136.5, 50, 50, 2], ["ledge", 139, 74, 50, 3], ["rock", 143],
      ["bridge", 146, 100, 30], ["branch", 152], ["pit", 155, 52], ["log", 158], ["rock", 160.5],
      ["stones", 163, 4], ["stump", 172], ["rock", 174.5], ["branch", 177.5], ["pit", 180.5, 54],
      ["stump", 183.5], ["bridge", 187, 76, 28], ["rock", 192.5], ["stump", 195.5], ["branch", 198], ["rock", 201],
    ]) },
    { name: "Creek Canyon", bpm: 144, song: 7, items: (k) => mgTrailLevel(k, [
      ["acorns", 4], ["pit", 8, 44], ["pit", 12, 48], ["stones", 15, 2], ["rock", 21], ["log", 24],
      ["ledge", 28, 26, 56, 2], ["ledge", 30.5, 50, 56, 3], ["ledge", 33, 74, 56, 3], ["ledge", 35.5, 50, 56, 2],
      ["pit", 39.5, 52], ["branch", 43], ["bridge", 47, 88, 28], ["stump", 53], ["pit", 56, 52],
      ["stones", 59, 3], ["branch", 65.5], ["stump", 68.5], ["ledge", 71, 44, 50, 3], ["pit", 74.5, 56],
      ["rock", 78], ["bridge", 81.5, 100, 30], ["pit", 88, 52], ["log", 91], ["branch", 94],
      // The second half: the canyon gets steep.
      ["stones", 97, 4], ["stump", 106], ["pit", 109, 54], ["ledge", 112.5, 26, 48, 2], ["ledge", 115, 50, 48, 2],
      ["ledge", 117.5, 74, 48, 3], ["ledge", 120, 98, 48, 3], ["ledge", 122.5, 74, 48, 2], ["ledge", 125, 50, 48, 2],
      ["pit", 128.5, 56], ["stump", 131.5], ["branch", 134.5], ["bridge", 138, 110, 30], ["pit", 144.5, 54],
      ["stones", 147.5, 4], ["rock", 156], ["stump", 158.5], ["pit", 161.5, 56], ["branch", 165], ["log", 168],
      ["bridge", 171.5, 88, 28], ["stump", 178], ["pit", 181, 56], ["rock", 184.5], ["branch", 187.5],
    ]) },
  ],
  river: [
    { name: "Lazy Creek", bpm: 112, song: 4, items: (k) => mgRiverLevel(k,
      [[8, 110, 62], [13, 90, 62], [18, 130, 62], [24, 110, 62], [30, 80, 62],
       [36, 120, 62], [42, 140, 62], [48, 100, 60], [53, 70, 60], [59, 110, 60],
       [65, 140, 60], [71, 100, 60], [76, 120, 60],
       [81, 81, 54], [85, 79, 54], [89, 90, 54], [93, 100, 54], [97, 133, 54], [101, 150, 54], [104.5, 143, 54], [108.5, 132, 54], [112.5, 148, 54], [116.5, 142, 54], [120.5, 150, 54], [124, 150, 54], [128, 118, 54], [132, 118, 54], [135.5, 116, 54], [139.5, 125, 54], [143, 134, 54], [146.5, 109, 54]],
      [[10.5, 70], [15.5, 150], [21, 80], [33, 150], [39, 70], [50.5, 150], [62, 70], [68, 80], [83.5, 150], [87.5, 150], [91.5, 150], [95.5, 60], [99.5, 60], [103, 60], [107, 60], [111, 60], [115, 60], [119, 60], [122.5, 60], [126.5, 60], [130.5, 60], [134, 60], [138, 60], [141.5, 60], [145, 60]],
      [[15.5, 100], [27, 90], [45, 120], [56, 90], [73.5, 110], ]) },
    { name: "Rapids", bpm: 128, song: 5, items: (k) => mgRiverLevel(k,
      [[8, 110, 54], [12, 80, 54], [16, 120, 54], [20, 150, 54], [24, 120, 54], [28, 80, 54],
       [33, 60, 52], [36, 90, 52], [39, 120, 52], [42, 150, 52],
       [47, 110, 52], [50, 110, 52], [53, 70, 52], [56, 110, 52], [59, 150, 52],
       [64, 100, 50], [67, 70, 50], [70, 100, 50], [73, 130, 50], [76, 100, 50],
       [81, 73, 46], [84, 88, 46], [87, 86, 46], [90, 102, 46], [93.5, 135, 46], [96.5, 150, 46], [100, 149, 46], [103.5, 114, 46], [107, 84, 46], [110, 64, 46], [113, 60, 46], [116, 96, 46], [119, 62, 46], [122.5, 67, 46], [125.5, 73, 46], [129, 60, 46], [132.5, 60, 46], [135.5, 60, 46], [138.5, 60, 46], [142, 74, 46], [145.5, 60, 46], [149, 91, 46]],
      [[10, 150], [14, 60], [22, 60], [30.5, 150], [44.5, 70], [61.5, 70], [74.5, 60], [82.5, 150], [85.5, 150], [88.5, 150], [92, 60], [95, 60], [98.5, 60], [102, 60], [105.5, 150], [108.5, 150], [111.5, 150], [114.5, 150], [117.5, 150], [121, 150], [124, 150], [127.5, 150], [131, 150], [134, 150], [137, 150], [140.5, 150], [144, 150], [147.5, 150]],
      [[18, 140], [34.5, 150], [48.5, 150], [68.5, 130], [79, 90], ]) },
  ],
  // [beat, x, "f" food or "b" bee, height of the leap, sideways drift]
  claw: [
    { name: "Salmon Run", bpm: 112, song: 8, items: (k) => mgClawLevel(k, [
      [6, 160, "f"], [8, 100, "f"], [10, 220, "f"], [12, 160, "f", 50],
      [14, 90, "f"], [14, 230, "f"], [16, 160, "b", 70], [18, 110, "f"], [18, 210, "f"],
      [20, 80, "f", 60, 20], [21, 160, "f", 50], [22, 240, "f", 60, -20],
      [24, 120, "b", 70], [24, 220, "f"], [26, 100, "f"], [26, 230, "b", 70],
      [28, 140, "f", 45], [29, 180, "f", 45], [30, 220, "f", 45], [32, 160, "b", 80],
      [34, 90, "f"], [34, 160, "f"], [34, 230, "f"], [36, 160, "f", 40],
      [38, 120, "f"], [38, 200, "b", 70], [40, 240, "f"], [40, 80, "b", 70],
      [42, 100, "f", 55, 15], [43, 160, "f", 50], [44, 220, "f", 55, -15], [46, 160, "f", 40],
      [11, 80, "b", 70], [20, 240, "b", 80], [30, 80, "b", 75], [36, 250, "b", 70], [45, 70, "b", 70],
      // The second half: faster, with more bees.
      [49, 80, "f", 50, 15], [50, 200, "f", 60, -15], [51, 240, "f", 70, 15], [51, 70, "b", 75],
      [51.5, 80, "f", 50, -15], [52.5, 150, "f", 40, 0], [53, 90, "f", 50, 0], [53, 230, "b", 75],
      [54, 210, "f", 40, 15], [55.5, 150, "f", 50, 0], [56.5, 100, "f", 50, 15], [56.5, 200, "b", 75],
      [57.5, 130, "f", 60, 15], [58.5, 160, "f", 70, 0], [59, 180, "f", 40, 15], [59, 60, "b", 75],
      [60, 70, "f", 50, -15], [61, 210, "f", 40, -15], [62.5, 240, "f", 70, 15], [62.5, 90, "b", 75],
      [63.5, 170, "f", 50, 0], [65, 180, "f", 40, 0], [66, 90, "f", 60, -15], [66, 210, "b", 75],
      [67, 90, "f", 70, 15], [68, 160, "f", 40, -15], [69, 120, "f", 60, -15], [69, 220, "b", 75],
      [69.5, 180, "f", 60, 15], [70.5, 80, "f", 60, 0], [71, 120, "f", 40, 15], [71, 250, "b", 75],
      [72, 220, "f", 60, 0], [73, 230, "f", 40, 0],
    ]) },
    { name: "Waterfall", bpm: 130, song: 9, items: (k) => mgClawLevel(k, [
      [6, 120, "f"], [7, 200, "f"], [8, 120, "f"], [9, 200, "f"], [10, 160, "b", 60],
      [12, 80, "f", 50, 20], [12, 240, "f", 50, -20], [13, 160, "f", 40],
      [14, 100, "b", 70], [14, 220, "b", 70], [15, 160, "f", 50],
      [16, 70, "f"], [16.5, 130, "f"], [17, 190, "f"], [17.5, 250, "f"],
      [19, 160, "b", 55], [19, 90, "f", 70], [19, 230, "f", 70],
      [21, 120, "f", 45, 10], [21, 200, "f", 45, -10], [22, 160, "b", 80],
      [23, 100, "f"], [23.5, 160, "f"], [24, 220, "f"], [24.5, 160, "f", 40],
      [26, 80, "b", 70], [26, 160, "f"], [26, 240, "b", 70], [27, 160, "f", 40],
      [28, 110, "f", 60, 25], [28, 210, "f", 60, -25], [29, 160, "b", 70],
      [30, 70, "f"], [30.5, 120, "f"], [31, 170, "f"], [31.5, 220, "f"], [32, 260, "f"],
      [34, 160, "f", 40], [34, 100, "b", 75], [34, 220, "b", 75], [36, 130, "f"], [36, 190, "f"],
      [8, 250, "b", 70], [13, 70, "b", 75], [17, 60, "b", 80], [25, 250, "b", 70], [31, 70, "b", 80], [33, 160, "b", 60],
      // The second half: faster, with more bees.
      [39, 90, "f", 50, -15], [39.5, 190, "f", 40, 15], [40, 140, "f", 40, 0], [40, 260, "b", 75],
      [40.75, 170, "f", 70, 0], [41.25, 110, "f", 40, -15], [42.25, 230, "f", 40, 0], [42.25, 70, "b", 75],
      [42.75, 80, "f", 50, 15], [43.25, 190, "f", 70, 0], [43.75, 240, "f", 50, -15], [43.75, 100, "b", 75],
      [44.25, 210, "f", 40, 0], [44.75, 220, "f", 60, 0], [45.25, 140, "f", 50, 0], [45.25, 260, "b", 75],
      [46, 220, "f", 70, 0], [46.75, 160, "f", 40, 0], [47.25, 110, "f", 60, 15], [47.25, 260, "b", 75],
      [47.75, 250, "f", 50, 0], [48.5, 80, "f", 70, 15], [49, 130, "f", 70, 15], [49, 250, "b", 75],
      [49.75, 210, "f", 70, 0], [50.75, 160, "f", 40, -15], [51.25, 160, "f", 70, 0], [51.25, 260, "b", 75],
      [51.75, 190, "f", 50, 0], [52.25, 250, "f", 40, 0], [52.75, 180, "f", 50, 15], [52.75, 60, "b", 75],
      [53.25, 140, "f", 70, -15], [54, 70, "f", 50, 0], [54.75, 210, "f", 70, 15], [54.75, 110, "b", 75],
      [55.75, 200, "f", 60, -15], [56.25, 100, "f", 60, 0], [56.75, 170, "f", 70, 0], [56.75, 60, "b", 75],
      [57.25, 160, "f", 60, 15], [57.75, 190, "f", 70, 0], [58.25, 200, "f", 60, 0], [58.25, 80, "b", 75],
      [58.75, 80, "f", 60, 0],
    ]) },
  ],
  // [beat, ring kind, turned by g sides]
  pool: [
    { name: "Low Tide", bpm: 108, song: 6, items: (k) => mgPoolLevel(k, [
      [8, "c", 0], [12, "c", 1], [16, "c", 2], [20, "c", 3], [24, "v", 1], [28, "v", 2],
      [32, "c", 3], [36, "c", 0], [40, "half", 4], [44, "half", 1], [48, "alt", 0], [50, "alt", 1], [52, "alt", 0],
      [56, "c", 3], [58, "c", 4], [60, "c", 5], [62, "c", 0], [64, "v", 0], [66, "v", 1], [68, "c", 2], [70, "c", 5],
      [72, "half", 3], [74, "half", 0], [76, "c", 0], [78, "c", 1], [80, "c", 3], [82, "alt", 0], [83.5, "alt", 1], [85, "alt", 0],
      // The second half: the waves come faster.
      [89, "two", 2], [91, "alt", 4], [93, "c", 0], [94.5, "two", 0], [96, "two", 1],
      [98, "c", 1], [100, "v", 1], [102, "alt", 1], [103.5, "v", 2], [105, "half", 1],
      [107, "two", 2], [109, "two", 4], [110.5, "half", 4], [112.5, "alt", 1], [114, "alt", 0],
      [116, "c", 4], [118, "c", 1], [120, "half", 4], [121.5, "c", 4], [123.5, "v", 5],
      [125, "alt", 4], [127, "c", 4], [129, "c", 1], [131, "c", 0],
    ]) },
    { name: "Rising Tide", bpm: 126, song: 7, items: (k) => mgPoolLevel(k, [
      [8, "c", 0], [10, "c", 1], [12, "c", 2], [14, "c", 3], [16, "c", 4], [18, "c", 5],
      [22, "alt", 0], [23.5, "alt", 1], [25, "alt", 0], [26.5, "alt", 1], [28, "alt", 0],
      [32, "two", 3], [34, "two", 5], [36, "two", 1], [38, "two", 3],
      [42, "c", 0], [44, "c", 5], [46, "c", 4], [48, "c", 3], [50, "c", 2], [52, "c", 1],
      [56, "v", 0], [58, "v", 1], [60, "v", 2], [62, "half", 0], [65, "half", 3], [68, "c", 4],
      [71, "alt", 1], [72.5, "alt", 0], [74, "alt", 1], [76, "c", 3], [78, "two", 0], [80, "c", 0], [82, "c", 3],
      [84, "c", 2], [85.5, "c", 1], [87, "c", 0], [88.5, "c", 5], [90, "v", 2], [92, "half", 5], [94, "two", 2], [96, "c", 5],
      // The second half: the waves come faster.
      [100, "half", 4], [101.5, "c", 3], [103, "alt", 4], [105, "alt", 1], [107, "v", 3],
      [109, "alt", 3], [111, "c", 5], [113, "v", 4], [114.5, "half", 1], [116, "c", 3],
      [117.5, "v", 0], [119.5, "c", 3], [121, "c", 5], [122.5, "c", 1], [124.5, "two", 5],
      [126, "c", 2], [127.5, "half", 1], [129.5, "c", 3], [131, "c", 5], [132.5, "c", 5],
      [134, "alt", 3], [135.5, "half", 1], [137, "v", 0], [139, "v", 0], [140.5, "alt", 3],
      [142, "two", 0], [143.5, "v", 4], [145.5, "v", 4], [147, "c", 1], [148.5, "c", 2],
    ]) },
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

// The animal you're playing as, with its skin when it wears one: "Frosty Bobcat".
function mgWho() {
  const s = mg.species, skin = habLook.skins[s.slug];
  return skin && HAB_SKINS[skin] ? `${skin[0].toUpperCase()}${skin.slice(1)} ${s.common_name}` : s.common_name;
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
  { root: 63, prog: [0, 4, 5, 3], lead: [4, 2, 0, 2, 4, -1, 7, -1], scale: [0, 2, 4, 7, 9, 12, 14] },
  { root: 58, prog: [0, 5, 6, 4], lead: [0, 2, 3, 5, 7, 5, 3, 2], scale: [0, 2, 3, 5, 7, 8, 10] },
  { root: 62, prog: [0, 3, 4, 0], lead: [0, -1, 4, 2, 7, -1, 4, 2], scale: [0, 2, 4, 7, 9, 12, 14] },
  { root: 57, prog: [0, 6, 3, 4], lead: [7, 4, 2, 4, 0, 2, 4, 7], scale: [0, 2, 3, 5, 7, 8, 10] },
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
// The stats each game uses, named for what they do there; the rest don't show.
// Agility is how hard a flier flaps, a swimmer swims up or a shell turns; Size is how
// big a target you are, except in Claw Catch, where a big paw reaches further.
const MG_STAT_INFO = {
  speed: ["Speed", "faster tempo, more points"],
  jump: ["Jump", "jumps higher"],
  flap: ["Flap", "flaps lift you higher"],
  swim: ["Swim", "swims up faster"],
  turn: ["Turn", "turns faster"],
  size: ["Size", "smaller slips through tighter gaps"],
  reach: ["Reach", "bigger paws swipe wider"],
  grip: ["Grip", "lands on more of a branch"],
  dig: ["Dig", "tunnels up and down faster"],
  hover: ["Hover", "more time to hit each flower"],
  dive: ["Dive", "dives and swims faster"],
  echo: ["Echo", "echoes light the cave longer"],
  hop: ["Hop", "hops between perches faster"],
  school: ["Swim", "squeezes and spreads faster"],
  freeze: ["Freeze", "more time to stop when the fox turns"],
};
const MG_GAME_STATS = {
  sky: [["speed", "speed"], ["flap", "agility"], ["size", "size"]],
  trail: [["speed", "speed"], ["jump", "jump"], ["size", "size"]],
  river: [["speed", "speed"], ["swim", "agility"], ["size", "size"]],
  pool: [["speed", "speed"], ["turn", "agility"], ["size", "size"]],
  claw: [["speed", "speed"], ["reach", "size"]],
  slide: [["speed", "speed"], ["turn", "agility"]],
  leap: [["speed", "speed"], ["jump", "jump"], ["grip", "agility"]],
  dig: [["speed", "speed"], ["dig", "agility"], ["size", "size"]],
  nectar: [["speed", "speed"], ["hover", "agility"]],
  plunge: [["speed", "speed"], ["dive", "agility"], ["size", "size"]],
  splash: [["speed", "speed"], ["swim", "agility"], ["size", "size"]],
  call: [["speed", "speed"]],
  echo: [["speed", "speed"], ["echo", "agility"], ["size", "size"]],
  feeder: [["speed", "speed"], ["hop", "agility"]],
  school: [["speed", "speed"], ["school", "agility"], ["size", "size"]],
  freeze: [["speed", "speed"], ["freeze", "agility"]],
};

// Speed depends on the game: a seal is slow on land (Trail Run) and fast in the water.
// The newer games use the speed of the place they're set in (games.py has the same table).
const MG_PLACE = { slide: "trail", leap: "trail", dig: "trail", nectar: "sky", plunge: "sky", splash: "river", echo: "sky",
                   feeder: "sky", school: "river", freeze: "trail" };
function mgStats(slug, game) {
  const v = (mgStatsIdx && mgStatsIdx.stats[slug]) || [3, 3, 3, 3];
  const place = (mgStatsIdx && mgStatsIdx.speed && mgStatsIdx.speed[slug]) || {};
  return { speed: place[MG_PLACE[game] || game] || v[0], jump: v[1], agility: v[2], size: v[3] };
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
  const st = mgStats(mg.species.slug, g.key);
  mg.run = { mode, t: 0, rt: 0, acc: 0, st, p: mgPhysOf(st), score: 0, litter: 0, fx: [], dist: 0, phase: 0, len: lvl.len, lvl,
             things: lvl.things.map((o) => Object.assign({ x: MG_W + 99 }, o)),
             x: g.key === "trail" ? 70 : 72, y: g.key === "trail" ? MG_GROUND : g.key === "sky" ? 90 : 110, vy: 0,
             flap: 0, ground: true, held: false, overAt: 0, rec, newBest: false, total: mgTreats(lvl),
             ang: -Math.PI / 2 + MG_SIDE / 2, dir: 0, missed: 0, trail: [], why: null };
  const P = MG_MORE[g.key];
  if (P) { mg.taps = []; mg.run.py = MG_H / 2; P.init(mg.run); }
}

// A press: flap, jump or start swimming up. Shared by touch, keys and the level checker.
function mgPress(r, key, on) {
  if (MG_MORE[key]) { r.fresh = r.fresh || !on; r.held = on; return; }  // a press only counts once it started in play
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
    const was = r.y;
    if (!r.ground) {
      // Let go early for a small hop.
      r.vy += (r.vy < 0 && !r.held ? 760 * 2.2 : 760) * dt;
      r.y += r.vy * dt;
    }
    // Land on whatever is under your feet, or fall when it runs out.
    const floor = mgTrailFloor(r, was);
    if (r.ground) { if (floor === null || floor > r.y + .5) { r.ground = false; r.vy = 0; } }
    else if (r.vy >= 0 && floor !== null && r.y >= floor) { r.y = floor; r.vy = 0; r.ground = true; }
  } else if (key === "pool") {
    r.ang += r.dir * MG_POOL.turn * r.p.power * dt;
  } else if (key === "claw") {
    // nothing moves but the food and your swipe
  } else {
    r.vy += (r.held ? -260 * r.p.power : 200) * dt;
    r.vy = Math.max(-95, Math.min(85, r.vy));
    r.y += r.vy * dt;
    if (r.y < MG_SURFACE + 12) { r.y = MG_SURFACE + 12; r.vy = Math.max(0, r.vy); }
    if (r.y > MG_BED - 12) { r.y = MG_BED - 12; r.vy = Math.min(0, r.vy); }
  }
}

// Trail Run: the highest thing to stand on under the animal's feet that it was above
// a moment ago (the trail, a rock, a ledge), or null over a creek.
function mgTrailFloor(r, was) {
  const plats = r.plats || (r.plats = r.things.filter((o) => o.plat || o.type === "pit").sort((a, b) => a.wx - b.wx));
  let floor = Infinity, pit = false;
  for (const o of plats) {
    const x = o.wx - r.dist + r.x;
    if (x - o.w / 2 > r.x + 10) break;
    if (o.type === "pit") { if (r.x - 5 > x - o.w / 2 && r.x + 5 < x + o.w / 2) pit = true; continue; }
    // Ledges and stones need your feet on them; rocks, logs and stumps your body.
    const top = o.y - o.h / 2, reach = o.w / 2 + (o.type === "ledge" || o.type === "stone" ? 5 : 8 - r.p.shrink);
    if (Math.abs(x - r.x) < reach && top >= was - .01) floor = Math.min(floor, top);
  }
  if (!pit && MG_GROUND >= was - .01) floor = Math.min(floor, MG_GROUND);
  return floor === Infinity ? null : floor;
}

// What of the player touches things: a box around its body, a bit smaller than the
// sprite so near misses count as misses. On the trail r.y is where its feet are.
function mgBox(key, r, pad) {
  const p = (pad || 0) - r.p.shrink;
  return key === "trail" ? [r.x - 8 - p, r.y - 21 - p, r.x + 8 + p, r.y - 1 + p] : [r.x - 8 - p, r.y - 7 - p, r.x + 8 + p, r.y + 7 + p];
}
const mgTouches = (b, o, x) => !(x + o.w / 2 < b[0] || x - o.w / 2 > b[2] || o.y + o.h / 2 < b[1] || o.y - o.h / 2 > b[3]);

const mgAngDiff = (a, b) => { const d = ((a - b) % (2 * Math.PI) + 3 * Math.PI) % (2 * Math.PI) - Math.PI; return Math.abs(d); };
// How far out a pool thing is now.
const mgPoolR = (o, r) => MG_POOL.r + (o.wx - r.dist);

// Tide Pool Spin: is the animal inside a foam side of a ring that's reaching it?
function mgPoolHit(r, things, pad) {
  const half = (5 + (pad || 0) - r.p.shrink) / MG_POOL.r;  // the animal's width, as an angle
  for (const o of things) {
    if (o.good) continue;
    const d = o.wx - r.dist;
    if (d > 8) break;
    if (d < -MG_POOL.thick - 4) continue;
    for (let i = 0; i < 6; i++) {
      if (!o.sides[i]) continue;
      const mid = (i + .5) * MG_SIDE;
      if (mgAngDiff(r.ang, mid) < MG_SIDE / 2 + half) return true;
    }
  }
  return false;
}

// Does the animal hit a hazard right now? (Used by the game and the level checker.)
function mgHit(r, key, things, pad) {
  if (key === "pool") return mgPoolHit(r, things, pad);
  if (key === "trail" && r.y > MG_GROUND + 12) return true;  // fell in the creek
  const b = mgBox(key, r, pad);
  for (const o of things) {
    if (o.good || o.type === "ledge" || o.type === "stone" || o.type === "pit") continue;
    const x = o.wx - r.dist + r.x;
    if (x > b[2] + 40) break;  // things are in course order
    if (mgTouches(b, o, x)) return true;
  }
  return false;
}

// Claw Catch, one step: swipe through what's in the air. True when the try is over.
const mgSegDist = (p, a, b) => {
  const dx = b[0] - a[0], dy = b[1] - a[1], L = dx * dx + dy * dy;
  const u = L ? Math.max(0, Math.min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L)) : 0;
  return Math.hypot(a[0] + dx * u - p[0], a[1] + dy * u - p[1]);
};
function mgClawStep(r) {
  const pts = mg.down && mg.swipe ? mg.swipe : null;
  const reach = 8 + r.st.size * 1.2;  // a bear's big paw sweeps wider than a mantis
  if (pts && pts.length > 1) for (const q of pts) r.trail.push([q[0], q[1], r.rt]);
  for (const o of r.things) {
    if (o.gone) continue;
    const at = mgClawAt(o, r);
    if (!at) {
      if (o.good && !o.missed && o.wx < r.dist) {
        o.missed = true; r.missed++;
        r.fx.push({ kind: "text", x: o.x0 + mgOx(), y: MG_H - 14, text: "Got away!", life: .9 });
        if (r.missed >= 3) { r.why = "missed"; return true; }
      }
      continue;
    }
    o.x = at[0]; o.y = at[1];
    if (!pts || pts.length < 2) continue;
    let hit = false;
    for (let i = 1; i < pts.length && !hit; i++) hit = mgSegDist(at, pts[i - 1], pts[i]) < (o.good ? reach : 6);
    if (!hit) continue;
    if (!o.good) { r.why = "bee"; r.x = o.x; r.y = o.y; return true; }
    o.gone = true;
    r.score += o.pts;
    mgSfx("treat");
    r.fx.push({ kind: "text", x: o.x, y: o.y - 8, text: `+${o.pts}`, life: .8 });
    for (let i = 0; i < 5; i++) r.fx.push({ kind: "spark", x: o.x, y: o.y, vx: (i - 2) * 18, vy: -20 - (i % 3) * 18, life: .5 });
  }
  if (pts && pts.length) mg.swipe = [pts[pts.length - 1]];
  r.trail = r.trail.filter((q) => r.rt - q[2] < .15);
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
    r.dir = mg.down ? mg.dir || 0 : 0;
    const P = MG_MORE[key];
    if (P) {
      r.py = mg.py ?? r.py;
      for (const [x, y] of mg.taps.splice(0)) P.press(r, x, y);
      r.t += MG_DT; r.flap = Math.max(0, r.flap - MG_DT);
      if (!P.ownDist) r.dist += MG_SPEED[key] * MG_DT;
      const why = P.step(r, MG_DT);
      if (why) { r.why = why; mgEnd(r, false); }
      else if (r.dist >= r.len) mgEnd(r, true);
      continue;
    }
    mgPhys(r, key, MG_DT);
    if (key === "claw") {
      if (mgClawStep(r)) mgEnd(r, false);
      else if (r.dist >= r.len) mgEnd(r, true);
      continue;
    }
    for (const o of r.things) o.x = o.wx - r.dist + r.x;
    const b = mgBox(key, r);
    if (key === "pool") {
      r.x = MG_POOL.cx + Math.cos(r.ang) * MG_POOL.r; r.y = MG_POOL.cy + Math.sin(r.ang) * MG_POOL.r;
      for (const o of r.things) if (o.good) { const rr = mgPoolR(o, r); o.x = MG_POOL.cx + Math.cos(o.ang) * rr; o.y = MG_POOL.cy + Math.sin(o.ang) * rr; }
    }
    for (const o of r.things) {
      if (!o.good || o.gone) continue;
      if (key === "pool" ? Math.abs(o.wx - r.dist) > 5 || mgAngDiff(o.ang, r.ang) > .4 : o.x > b[2] + 20 || !mgTouches(b, o, o.x)) continue;
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
  if (r.score > 0) {
    // Points for every try, finished or not: every treat counts, times the animal's speed.
    // A fast animal is harder to steer through, so it earns more. Best overall, and per animal.
    const pts = mgPoints(r.score, r.p), slug = mg.species.slug, mine = +(mgStore.get(`${rec.k}.p.${slug}`) || 0);
    r.points = pts;
    r.animalBest = pts > mine;
    if (r.animalBest) mgStore.set(`${rec.k}.p.${slug}`, pts);
    // The server works the points out again from the treats and the animal.
    mg.posting = mgApi("POST", "/games/scores", { level: `${mg.game.key}.${mg.level}`, species: slug, treats: r.score })
      .then((d) => { r.coins = d.coins_earned; if (mg.shop) mg.shop.coins = d.coins; }).catch(() => {});
    if (pts > rec.points) { r.newBest = true; rec.points = pts; mgStore.set(rec.k + ".points", pts); mgStore.set(rec.k + ".who", mgWho()); }
    else if (cleared) r.newBest = false;
    r.bestPoints = pts >= rec.points;
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
  mgFit(cv);
  const c = cv.getContext("2d");
  c.setTransform(MG_RES, 0, 0, MG_RES, 0, 0);
  c.imageSmoothingEnabled = false;
  const key = mg.game.key;
  if (key === "pool") {
    // The whole pool sways round, like Super Hexagon; the waves and you turn with it.
    const { cx, cy } = MG_POOL, view = r.t * .5 + Math.sin(r.t * .9) * .5;
    c.save(); c.translate(cx, cy); c.rotate(view); c.translate(-cx, -cy);
    mgPoolDraw(c, r);
    for (const f of r.fx) mgFxDraw(c, f);
    c.restore();
    mgHud(c, r);
    return;
  }
  if (MG_MORE[key]) {
    MG_MORE[key].draw(c, r);
    for (const f of r.fx) mgFxDraw(c, f);
    mgHud(c, r);
    return;
  }
  if (key === "claw") {
    mgClawDraw(c, r);
    for (const f of r.fx) mgFxDraw(c, f);
    mgHud(c, r);
    return;
  }
  if (key === "sky") mgSkyBg(c, r); else if (key === "trail") mgTrailBg(c, r); else mgRiverBg(c, r);
  // Creeks first, so the stepping stones sit in them.
  for (const o of r.things) if (o.type === "pit" && o.x > -o.w && o.x < MG_W + o.w) mgThing(c, o, r);
  for (const o of r.things) if (!o.gone && o.type !== "pit") mgThing(c, o, r);
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
    case "ledge": {
      // A mossy stone shelf: grass on top, dark underneath, a few roots hanging down.
      const w = o.w, l = x - Math.round(w / 2), t = y - 3;
      c.fillStyle = "#7d6a55"; c.fillRect(l + 1, t + 2, w - 2, 5); c.fillRect(l + 4, t + 7, w - 8, 2);
      c.fillStyle = "#5e4f40"; c.fillRect(l + 4, t + 8, w - 8, 1);
      c.fillStyle = "#58a662"; c.fillRect(l, t, w, 3);
      c.fillStyle = "#7cc47f"; c.fillRect(l + 1, t, w - 2, 1);
      c.fillStyle = "#3f8d58";
      for (let dx = 5; dx < w - 3; dx += 9) c.fillRect(l + dx, t + 7, 1, 3 + (dx % 4));
      break;
    }
    case "stone":
      box(-13, -3, 26, 5, "#8a8f9e"); box(-11, -4, 22, 2, "#a3a8b5"); box(-9, -4, 5, 1, "#c4c8d2"); box(-13, 2, 26, 2, "#5e6372");
      c.fillStyle = "rgba(255,255,255,.7)"; c.fillRect(x - 15 + Math.round(Math.sin(r.phase * 3 + o.wx) * 1.5), y + 3, 30, 1);
      break;
    case "pit": {
      // A creek across the trail: earth banks, and water at the bottom.
      const l = x - Math.round(o.w / 2), w = Math.round(o.w), g = MG_GROUND;
      c.fillStyle = "#6b4a2e"; c.fillRect(l, g - 10, w, MG_H - g + 10);
      c.fillStyle = "#4f3620"; c.fillRect(l + 3, g - 10, w - 6, 8);
      c.fillStyle = "#2f7fa8"; c.fillRect(l + 3, g - 2, w - 6, MG_H - g + 2);
      c.fillStyle = "#3a8fb8"; c.fillRect(l + 3, g + 6, w - 6, 4);
      c.fillStyle = "rgba(255,255,255,.6)";
      for (let dx = 6; dx < w - 8; dx += 12) c.fillRect(l + dx + Math.round(Math.sin(r.phase * 2 + dx) * 2), g - 1, 5, 1);
      break;
    }
    case "thorns": {
      // A long, low bramble with sharp spikes and red berries.
      const l = x - Math.round(o.w / 2), w = Math.round(o.w);
      c.fillStyle = "#3b5a2e"; c.fillRect(l, y - 3, w, 8);
      c.fillStyle = "#2c4423";
      for (let dx = 0; dx < w; dx += 7) { c.beginPath(); c.arc(l + dx + 3, y - 3, 4, 0, Math.PI * 2); c.fill(); }
      c.fillStyle = "#d8cfb0";
      for (let dx = 2; dx < w - 1; dx += 5) { c.fillRect(l + dx, y - 8 - (dx % 3), 1, 3); c.fillRect(l + dx + 2, y + ((dx * 3) % 4) - 2, 2, 1); }
      c.fillStyle = "#c0392b";
      for (let dx = 4; dx < w - 2; dx += 11) c.fillRect(l + dx, y - 2 + (dx % 3), 2, 2);
      break;
    }
    case "snag":
      box(-13, -3, 26, 6, "#5b4030"); box(-13, -3, 26, 1, "#7a5a40"); box(-6, -8, 2, 5, "#5b4030"); box(4, 3, 2, 5, "#5b4030");
      box(-8, -9, 4, 2, "#5b4030"); break;
  }
}

// What each tide pool animal eats: [name pattern, food, colour].
const MG_FOODS = [
  [/mussel|clam|oyster|scallop|barnacle/, "plankton", "#9be59b"], [/(^|_)star(_|$)/, "mussels", "#3d4a7a"],
  [/urchin/, "kelp", "#5a8f3a"], [/dogwinkle|whelk/, "barnacles", "#e8e0c8"], [/scotch_bonnet/, "sand dollars", "#d8c49a"],
  [/anemone/, "shrimp", "#f08a7a"], [/hopkins/, "moss animals", "#c8a0e0"], [/crayfish/, "worms", "#d98a8a"],
  [/crab|lobster/, "clams", "#d8c8a8"], [/loggerhead/, "jellies", "#e0b0e8"], [/sea_turtle/, "seagrass", "#5aa84a"],
  [/snapping|softshell/, "fish", "#9ab8d0"], [/tortoise|box_turtle/, "flowers", "#f2c14e"], [/armadillo/, "beetles", "#6a5040"],
  [/garden_snail|giant_snail|brown_lipped/, "leaves", "#6aae6e"], [/turtle|cooter|slider|terrapin/, "snails", "#c8a070"],
  [/./, "algae", "#4f9a5a"],
];
const mgFood = (slug) => MG_FOODS.find(([re]) => re.test(slug));

// What each hunter catches: [name pattern, prey].
const MG_PREY = [
  [/bear/, "salmon"], [/osprey|bald_eagle|kingfisher|heron|egret|bittern|otter/, "fish"], [/raccoon/, "crayfish"],
  [/crab|lobster|crayfish/, "snails"], [/frog|toad|mantis/, "flies"], [/./, "mice"],
];
const mgPrey = (slug) => MG_PREY.find(([re]) => re.test(slug))[1];

function mgClawDraw(c, r) {
  // A stream at the foot of a little waterfall, in the evening.
  const sky = c.createLinearGradient(0, 0, 0, MG_H);
  sky.addColorStop(0, "#f2b880"); sky.addColorStop(.55, "#9ad3ee"); sky.addColorStop(1, "#5aa0c8");
  c.fillStyle = sky; c.fillRect(0, 0, MG_W, MG_H);
  mgHills(c, r, 0, 130, 30, 70, "#6aae6e");
  const ox = Math.round(mgOx());
  c.fillStyle = "#8a8f9e"; c.fillRect(196 + ox, 96, 70, 64); c.fillStyle = "#9fa4b2"; c.fillRect(196 + ox, 96, 70, 6);
  c.fillStyle = "#7cc4e8"; c.fillRect(212 + ox, 96, 38, 64);
  c.fillStyle = "#e8f8ff";
  for (let i = 0; i < 5; i++) c.fillRect(215 + ox + i * 7, 96 + ((r.phase * 70 + i * 17) % 56), 2, 8);
  c.fillStyle = "rgba(255,255,255,.7)"; c.fillRect(206 + ox, 156, 50, 4);
  c.fillStyle = "#3a8fb8"; c.fillRect(0, 160, MG_W, MG_H - 160);
  c.fillStyle = "#7cc4e8";
  for (let x = -mgScroll(r, 0, 20) + Math.floor(r.phase * 30) % 20; x < MG_W; x += 20) c.fillRect(x, 166 + (x % 3) * 8, 8, 2);
  const prey = mgPrey(mg.species.slug);
  for (const o of r.things) {
    if (o.gone) continue;
    const at = mgClawAt(o, r);
    if (!at) continue;
    const x = Math.round(at[0]), y = Math.round(at[1]), box = (dx, dy, w, h, col) => { c.fillStyle = col; c.fillRect(x + dx, y + dy, w, h); };
    if (!o.good) {  // a bee
      const flap = Math.floor(r.phase * 20) % 2;
      box(-2, -6 - flap, 3, 3, "rgba(255,255,255,.85)"); box(1, -6 + flap, 3, 3, "rgba(255,255,255,.85)");
      box(-4, -2, 9, 5, "#f2c14e"); box(-2, -2, 2, 5, "#2a2a2a"); box(2, -2, 2, 5, "#2a2a2a"); box(5, 0, 2, 1, "#2a2a2a");
      continue;
    }
    if (prey === "salmon" || prey === "fish") {
      const body = prey === "salmon" ? "#e8806a" : "#8fb0c8";
      box(-6, -2, 11, 5, body); box(-8, -3, 3, 7, body); box(3, -1, 1, 1, "#222"); box(-4, 1, 8, 1, "rgba(255,255,255,.5)");
    } else if (prey === "mice") {
      box(-4, -2, 8, 5, "#9a9a9a"); box(3, -3, 2, 2, "#c8a0a0"); box(4, -1, 1, 1, "#222"); box(-7, 1, 3, 1, "#c8a0a0");
    } else if (prey === "flies") {
      box(-2, -1, 4, 3, "#2a2a2a"); box(-3, -3, 3, 2, "rgba(220,240,255,.85)"); box(1, -3, 3, 2, "rgba(220,240,255,.85)");
    } else if (prey === "crayfish") {
      box(-5, -1, 9, 3, "#c84a3a"); box(4, -3, 3, 2, "#c84a3a"); box(4, 2, 3, 2, "#c84a3a");
    } else {  // snails
      box(-4, -3, 7, 6, "#c8a070"); box(-2, -1, 3, 2, "#8a6040"); box(-6, 2, 11, 2, "#d8c8a8");
    }
  }
  // Your claw marks: three streaks along the swipe.
  if (r.trail.length > 1) {
    for (const off of [-3, 0, 3]) {
      c.strokeStyle = "rgba(255,255,255,.85)"; c.lineWidth = 1.5; c.beginPath();
      r.trail.forEach(([x, y], i) => (i ? c.lineTo(x + off, y + off) : c.moveTo(x + off, y + off)));
      c.stroke();
    }
  }
  // You, on the bank, watching the stream.
  const s = mg.species, raw = habSkin(mg.imgs[`/sprites/${encodeURIComponent(s.slug)}.png`], habLook.skins[s.slug]);
  if (raw && raw.complete && raw.naturalWidth && !(r.mode === "over" && Math.floor(r.phase * 12) % 3 === 0)) {
    c.fillStyle = "#7a9a50"; c.fillRect(0, 168, 60, 32);
    c.save(); c.translate(30, 182); c.scale(-1, 1); c.drawImage(raw, -raw.naturalWidth / 2, -raw.naturalWidth); c.restore();
  }
}

// The rock's lumpy outline: how far each of its 16 points sticks out.
const MG_ROCK = [1, .93, 1.06, 1.1, .96, .9, 1.02, 1.08, .97, 1.04, .92, .98, 1.09, 1.01, .94, 1.05];

function mgPoolDraw(c, r) {
  const { cx, cy, thick } = MG_POOL, far = 240;
  const at = (a, d) => [cx + Math.cos(a) * d, cy + Math.sin(a) * d];
  // A ring of water from angle a0 to a1, between radius d0 and d1; each edge may wobble.
  const band = (a0, a1, d0, d1, w0, w1, col) => {
    const n = Math.max(2, Math.ceil((a1 - a0) / .06));
    c.fillStyle = col; c.beginPath();
    for (let k = 0; k <= n; k++) { const a = a0 + (a1 - a0) * k / n; c.lineTo(...at(a, Math.max(0, d1 + w1(a)))); }
    for (let k = n; k >= 0; k--) { const a = a0 + (a1 - a0) * k / n; c.lineTo(...at(a, Math.max(0, d0 + w0(a)))); }
    c.closePath(); c.fill();
  };
  const flat = () => 0;
  // Deep water, with soft ripples spreading out from the rock.
  c.fillStyle = "#2f7fa8"; c.fillRect(-far, -far, MG_W + far * 2, 200 + far * 2);
  c.strokeStyle = "#3a8fb8"; c.lineWidth = 3;
  for (let d = (r.t * 14) % 22 + 26; d < far; d += 22) { c.beginPath(); c.arc(cx, cy, d, 0, Math.PI * 2); c.stroke(); }
  for (const o of r.things) {
    const d = mgPoolR(o, r);
    if (d > far || d + thick < 0) continue;
    if (o.good) {
      if (o.gone) continue;
      const [x, y] = at(o.ang, d), col = mgFood(mg.species.slug)[2];
      c.fillStyle = "rgba(0,0,0,.25)"; c.fillRect(Math.round(x) - 2, Math.round(y) - 1, 5, 4);
      c.fillStyle = col; c.fillRect(Math.round(x) - 3, Math.round(y) - 3, 5, 5);
      c.fillStyle = "rgba(255,255,255,.6)"; c.fillRect(Math.round(x) - 2, Math.round(y) - 2, 2, 2);
      continue;
    }
    // A wave rolling in: a teal swell behind a white, frothy crest that curls and wobbles.
    const curl = a => Math.sin(a * 14 + r.t * 7 + o.wx * .05) * 1.5;
    const back = a => Math.sin(a * 9 - r.t * 4) * 2;
    for (let i = 0; i < 6; i++) {
      if (!o.sides[i]) continue;
      const a0 = i * MG_SIDE, a1 = (i + 1) * MG_SIDE;
      band(a0, a1, d, d + thick + 3, curl, back, "#7cc3e0");
      band(a0, a1, d, d + 4, curl, curl, "#f4fbff");
      // Flecks of foam left behind the crest.
      c.fillStyle = "#e9f6ff";
      for (let k = 0; k < 6; k++) {
        const a = a0 + (k + .5) * MG_SIDE / 6, [x, y] = at(a, d + 6 + ((k * 5 + i * 3) % 4));
        if (d + 6 > 0) c.fillRect(Math.round(x) - 1, Math.round(y) - 1, 2, 2);
      }
    }
  }
  // The rock in the middle, a little bigger on every beat: a lumpy grey stone with a
  // wet dark rim, a lighter top, barnacles and a tuft of seaweed.
  const beat = r.lvl.spb ? (r.t / r.lvl.spb) % 1 : 0, rock = 20 + (beat < .15 ? 2 : 0);
  const lump = (rad, dx, dy, col) => {
    c.fillStyle = col; c.beginPath();
    MG_ROCK.forEach((j, i) => { const a = i / MG_ROCK.length * Math.PI * 2; c.lineTo(cx + dx + Math.cos(a) * rad * j, cy + dy + Math.sin(a) * rad * j); });
    c.closePath(); c.fill();
  };
  c.fillStyle = "rgba(233,246,255,.5)"; c.beginPath(); c.arc(cx, cy, rock + 3, 0, Math.PI * 2); c.fill();
  lump(rock, 0, 0, "#4f545e");
  lump(rock - 3, -1, -1, "#6e7380");
  lump(rock - 9, -3, -3, "#8a8f9e");
  lump(rock - 15, -5, -5, "#a3a8b5");
  c.fillStyle = "#3f7a4a";
  for (const [a, d] of [[2.2, rock - 4], [2.5, rock - 3], [2.8, rock - 5]]) { const [x, y] = at(a, d); c.fillRect(Math.round(x) - 1, Math.round(y) - 2, 3, 4); }
  c.fillStyle = "#d9d4c4";
  for (const [a, d] of [[5.3, rock - 5], [5.6, rock - 7], [.4, rock - 5], [3.9, rock - 6]]) { const [x, y] = at(a, d); c.fillRect(Math.round(x) - 1, Math.round(y) - 1, 3, 3); }
  c.fillStyle = "#8f8a7c";
  for (const [a, d] of [[5.3, rock - 5], [5.6, rock - 7], [.4, rock - 5], [3.9, rock - 6]]) { const [x, y] = at(a, d); c.fillRect(Math.round(x), Math.round(y), 1, 1); }
  // You, clinging to the rock with your back to the waves.
  const s = mg.species, raw = habSkin(mg.imgs[`/sprites/${encodeURIComponent(s.slug)}.png`], habLook.skins[s.slug]);
  if (!raw || !raw.complete || !raw.naturalWidth || (r.mode === "over" && Math.floor(r.phase * 12) % 3 === 0)) return;
  const [x, y] = at(r.ang, MG_POOL.r - 9), F = raw.naturalWidth, k = 26 / F;
  c.save(); c.translate(x, y); c.rotate(r.ang + Math.PI / 2); c.scale(k, k);
  c.drawImage(raw, -F / 2, -F * .75);
  c.restore();
}

const mgFrames = {};
function mgFrame(sheet, slug, row, frame, F) {
  const key = `${slug}/${row}/${frame}`;
  if (!mgFrames[key]) {
    const cv = document.createElement("canvas");
    cv.width = F; cv.height = F;
    cv.getContext("2d").drawImage(sheet, frame * F, row * F, F, F, 0, 0, F, F);
    mgFrames[key] = cv;
  }
  return mgFrames[key];
}

function mgPlayer(c, r) {
  const s = mg.species, key = mg.game.key;
  const raw = habSkin(mg.imgs[`/sprites/${encodeURIComponent(s.slug)}.png`], habLook.skins[s.slug]);
  const sheet = habSkin(mg.sheets[`/sprites/anim/${encodeURIComponent(s.slug)}.png`], habLook.skins[s.slug]);
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
    c.fillStyle = "rgba(20,32,10,.25)"; c.fillRect(x - 9, y - 1, 18, 2);
  }
  c.save();
  // Sprites face left; the games run to the right.
  if (key === "trail") c.translate(x, y + 2);  // feet on the trail
  else c.translate(x, y + F * .4);
  c.scale(-1, 1);
  if (key === "sky" && moving) c.rotate(Math.max(-.35, Math.min(.35, r.vy / 400)));
  if (key === "river" && moving) c.rotate(Math.max(-.3, Math.min(.3, r.vy / 350)));
  if (framed) c.drawImage(mgFrame(sheet, `${s.slug}~${habLook.skins[s.slug] || ""}`, habAnimIdx.rows.indexOf(pose), frame, F), -F / 2, -F + bob);
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
  const food = g.key === "pool" ? mgFood(mg.species.slug)[1] : "";
  const word = g.key === "claw" ? mgPrey(mg.species.slug) : food;
  const P = MG_MORE[g.key], cap = (w) => w[0].toUpperCase() + w.slice(1);
  const label = `${P ? cap(g.thing[1]) : g.key === "river" ? "Score" : g.key === "sky" ? "Berries" : g.key === "trail" ? "Acorns" : cap(word)} ${r.score}` +
    (g.key === "claw" || (P && P.misses) ? `  ${"✕".repeat(Math.min(3, r.missed))}${"·".repeat(Math.max(0, 3 - r.missed))}` : "");
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
    const lines = [[(P && P.why && P.why[r.why]) || (r.why === "bee" ? "Ouch, a bee!" : r.why === "missed" ? "Three got away!" : "Bump!"), 15], [`You made it ${r.pct}% of the way`, 12, "#ffd28a"]];
    if (r.points) lines.push([`${r.points} points${r.coins ? `  +${r.coins} coins 🪙` : ""}`, 11, "#ffd28a"]);
    lines.push([r.newBest ? "That's your best yet!" : `Best: ${r.rec.pct}%`, 11, r.newBest ? "#9be59b" : "#fff"]);
    lines.push(["Tap to try again", 10, "#cfe"]);
    mgPanel(c, lines, Math.min(top, MG_H - 8 - (lines.length * 16 + 14)));
  } else if (r.mode === "done") {
    const lines = [["Level complete!", 15, "#9be59b"], [`${r.points} points as a ${mg.species.common_name}`, 12, "#ffd28a"],
                   [`${r.score} of ${r.total} ${g.key === "pool" || g.key === "claw" ? word : g.thing[1]} × ${r.p.tempo} speed bonus`, 10]];
    if (g.key === "river" && r.litter) lines.push([`You cleaned up ${r.litter} piece${r.litter === 1 ? "" : "s"} of litter`, 10]);
    if (r.score >= r.total) lines.push(["You got every one!", 11, "#9be59b"]);
    if (r.coins) lines.push([`+${r.coins} coins 🪙`, 11, "#ffd28a"]);
    if (r.newBest) lines.push(["Your best score yet!", 11, "#9be59b"]);
    else if (r.animalBest) lines.push([`Your best with this animal! (Best ever: ${r.rec.points})`, 10, "#9be59b"]);
    else lines.push([`Best: ${r.rec.points} as a ${r.rec.who}`, 10]);
    if (mg.level + 1 < MG_LEVELS[g.key].length) lines.push([`Level ${mg.level + 2} is unlocked!`, 10, "#cfe"]);
    lines.push(["Tap to play again", 10, "#cfe"]);
    mgPanel(c, lines, Math.min(top, MG_H - 8 - (lines.length * 16 + 14)));
  }
}

// ==== More games ====================================================================
// Eight more games, each a plug-in to the loop above. init(r) sets up a try; press(r, x, y)
// is a tap at that spot (queued, so a tap quicker than a frame still counts); step(r, dt)
// moves one fixed step and returns why the try ended, if it did; draw(c, r) paints it.
// r.held says a finger or key is down and r.py is how high it is. ownDist games move
// r.dist themselves (how far you've got); the rest scroll on their own. Levels, music,
// scores, coins and the HUD are the same as the games above.
const MG_MORE = {};

// A fixed random sequence: a level built from it comes out the same every time.
function mgRand(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6D2B79F5) >>> 0;
    let t = Math.imul(a ^ (a >>> 15), a | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const mgClamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));

// A treat: points, a sound and a sparkle where it was.
function mgGot(r, o, x, y) {
  o.gone = true; r.score += o.pts; mgSfx("treat");
  r.fx.push({ kind: "text", x, y: y - 6, text: `+${o.pts}`, life: .8 });
  for (let i = 0; i < 5; i++) r.fx.push({ kind: "spark", x, y, vx: (i - 2) * 18, vy: -20 - (i % 3) * 18, life: .5 });
}

// The animal you play as, feet at (x, y): the first of the poses its frames have, else
// its picture. Sprites face left, so it's flipped to face the way the games run.
function mgAnimal(c, r, x, y, poses, o = {}) {
  if (r.mode === "over" && Math.floor(r.phase * 12) % 3 === 0) return;  // blink after a bump
  const s = mg.species, skin = habLook.skins[s.slug];
  const raw = habSkin(mg.imgs[`/sprites/${encodeURIComponent(s.slug)}.png`], skin);
  const sheet = habSkin(mg.sheets[`/sprites/anim/${encodeURIComponent(s.slug)}.png`], skin);
  const acts = (habAnimIdx && habAnimIdx.acts[s.slug]) || [];
  const pose = poses.find((p) => acts.includes(p));
  const framed = pose && sheet && sheet.complete && sheet.naturalWidth;
  const img = framed ? sheet : raw;
  if (!img || !img.complete || !img.naturalWidth) return;
  const F = framed ? sheet.naturalWidth / habAnimIdx.frames : raw.naturalWidth;
  const frame = ((Math.floor(o.frame ?? r.phase * 8) % 4) + 4) % 4, k = o.scale || 1;
  c.save();
  c.translate(Math.round(x), Math.round(y));
  if (o.rot) c.rotate(o.rot);
  c.scale(o.flip === false ? k : -k, k);
  if (framed) c.drawImage(mgFrame(sheet, `${s.slug}~${skin || ""}`, habAnimIdx.rows.indexOf(pose), frame, F), -F / 2, -F);
  else c.drawImage(raw, -F / 2, -F + (r.mode === "play" && !o.still ? Math.round(Math.sin(r.phase * 8) * 2) : 0));
  c.restore();
}

function mgSky(c, top, bottom) {
  const g = c.createLinearGradient(0, 0, 0, MG_H);
  g.addColorStop(0, top); g.addColorStop(1, bottom);
  c.fillStyle = g; c.fillRect(0, 0, MG_W, MG_H);
}

// ---- Mud Slide: three lanes down a muddy chute ----------------------------------
// Each row of logs and rocks leaves at least one lane open; the rows come closer as
// the level goes on, so you have to be in the right lane early.
const MG_LANES = [100, 136, 172];
const MG_SLIDE_SWITCH = 0.2;  // seconds to change one lane at Turn 1
function mgSlideLevel(k, seed, rows, start, gap0, gap1, two0, two1) {
  const rnd = mgRand(seed), out = [];
  let b = start, free = 1;
  for (let i = 0; i < rows; i++) {
    const u = i / (rows - 1);
    const next = mgClamp(free + [-2, -1, -1, 0, 1, 1, 2][Math.floor(rnd() * 7)], 0, 2), moved = Math.abs(next - free);
    b += (gap0 + (gap1 - gap0) * u) + moved * .5;
    free = next;
    const two = rnd() < two0 + (two1 - two0) * u;
    const blocked = [0, 1, 2].filter((l) => l !== free);
    const shut = two ? blocked : [blocked[Math.floor(rnd() * 2)]];
    for (const lane of shut) {
      const rock = rnd() < .4;
      out.push({ type: rock ? "m_rock" : "m_log", wx: b * k, lane, w: rock ? 14 : 24 });
    }
    out.push({ type: "m_fish", good: true, pts: 1, wx: b * k, lane: free, w: 10 });
    if (rnd() < .5) out.push({ type: "m_fish", good: true, pts: 1, wx: (b - .9) * k, lane: free, w: 10 });
  }
  return out;
}

MG_MORE.slide = {
  why: { bump: "Splat!" },
  init(r) { r.lane = 1; r.ly = MG_LANES[1]; r.x = 70; r.y = r.ly - 10; },
  press(r, x, y) { r.lane = mgClamp(r.lane + (y < MG_H / 2 ? -1 : 1), 0, 2); },
  step(r, dt) {
    const sp = (MG_LANES[1] - MG_LANES[0]) / (MG_SLIDE_SWITCH - (r.st.agility - 1) * .02);
    r.ly += mgClamp(MG_LANES[r.lane] - r.ly, -sp * dt, sp * dt);
    r.y = r.ly - 10;
    for (const o of r.things) {
      if (o.gone) continue;
      const dx = o.wx - r.dist;
      if (dx > 40) break;
      if (Math.abs(dx) > o.w / 2 + 6 || Math.abs(r.ly - MG_LANES[o.lane]) > 14) continue;
      if (!o.good) return "bump";
      mgGot(r, o, r.x + dx, MG_LANES[o.lane] - 8);
    }
  },
  draw(c, r) {
    mgSky(c, "#9ad3ee", "#e4f4e0");
    mgHills(c, r, .1, 64, 22, 70, "#8fb9a8");
    mgHills(c, r, .3, 78, 12, 40, "#6aae6e");
    // The chute: a bank, three lanes of mud with ripples, a bank.
    c.fillStyle = "#58a662"; c.fillRect(0, 76, MG_W, 6);
    c.fillStyle = "#8a6440"; c.fillRect(0, 82, MG_W, MG_H - 82);
    c.fillStyle = "#9c7450";
    for (const ly of MG_LANES) c.fillRect(0, ly - 12, MG_W, 20);
    c.fillStyle = "#6e4e30";
    for (const ly of MG_LANES.slice(1)) for (let x = -mgScroll(r, 1, 20); x < MG_W; x += 20) c.fillRect(x, ly - 18, 10, 2);
    c.fillStyle = "#b08860";
    for (let i = 0; i < 12; i++) c.fillRect((i * 53 - mgScroll(r, 1.2, 640) + 640) % 640 - 20, 88 + (i * 37) % 100, 6, 1);
    c.fillStyle = "#58a662"; c.fillRect(0, MG_H - 6, MG_W, 6);
    for (const o of r.things) {
      if (o.gone) continue;
      const x = Math.round(o.wx - r.dist + r.x), y = MG_LANES[o.lane];
      if (x < -30 || x > MG_W + 30) continue;
      const box = (dx, dy, w, h, col) => { c.fillStyle = col; c.fillRect(x + dx, y + dy, w, h); };
      if (o.type === "m_log") {
        box(-12, -9, 24, 12, "#7a5232"); box(-12, -9, 24, 3, "#a8744a"); box(-12, 1, 24, 2, "#5b3c22");
        box(9, -9, 4, 12, "#d8b07a"); box(10, -6, 2, 5, "#a8744a"); box(-14, 3, 28, 2, "rgba(0,0,0,.25)");
      } else if (o.type === "m_rock") {
        box(-7, -8, 14, 11, "#8a8f9e"); box(-5, -11, 10, 4, "#9fa4b2"); box(-4, -10, 3, 2, "#c4c8d2"); box(-8, 3, 16, 2, "rgba(0,0,0,.25)");
      } else {
        const hop = Math.round(Math.abs(Math.sin(r.phase * 6 + o.wx)) * 3);
        box(-5, -8 - hop, 9, 5, "#8fb0c8"); box(-8, -9 - hop, 3, 7, "#8fb0c8"); box(2, -7 - hop, 1, 1, "#222"); box(-4, -5 - hop, 7, 1, "#d8e8f0");
      }
    }
    // Mud flicks up behind you.
    if (r.mode === "play") {
      c.fillStyle = "#6e4e30";
      for (let i = 0; i < 4; i++) c.fillRect(r.x - 14 - ((r.phase * 60 + i * 9) % 26), r.ly - 2 - ((i * 5 + Math.floor(r.phase * 30)) % 7), 2, 2);
    }
    mgAnimal(c, r, r.x, r.ly + 6, ["swim", "idle", "walk"], { rot: .12, frame: r.phase * 6 });
  },
};

// ---- Nectar Rush: four flowers that open on the beat --------------------------------
const MG_FLOWER_X = [52, 124, 196, 268];
const MG_FLOWERS = { forEach: (fn) => MG_FLOWER_X.forEach((x, f) => fn(x + mgOx(), f)) };
const mgFlower = (f) => MG_FLOWER_X[f] + mgOx();
const MG_PETALS = ["#e86a8a", "#f2c14e", "#b58ae0", "#f08a4a"];
// notes: [beat, flower, "w" for a wasp]. Notes come from a fixed pattern of beats, with
// wasps put where no nectar is due on that flower for a while.
function mgNectarLevel(k, seed, len, start, busy0, busy1, wasp0, wasp1, chords) {
  const rnd = mgRand(seed), out = [], last = [-9, -9, -9, -9];
  for (let b = start; b < len; b += .5) {
    const u = (b - start) / (len - start), onBeat = b % 1 === 0;
    const p = onBeat ? .55 + .35 * u : busy0 + (busy1 - busy0) * u;
    if (rnd() >= p) continue;
    let f = Math.floor(rnd() * 4);
    out.push({ type: "m_bloom", good: true, pts: 1, wx: b * k, f, beat: b });
    last[f] = b;
    if (chords && onBeat && rnd() < chords * u) {
      const g = (f + 1 + Math.floor(rnd() * 3)) % 4;
      out.push({ type: "m_bloom", good: true, pts: 1, wx: b * k, f: g, beat: b });
      last[g] = b;
    }
    if (b > start + 8 && rnd() < wasp0 + (wasp1 - wasp0) * u) {
      const w = [0, 1, 2, 3].filter((g) => b + .5 - last[g] >= 1.5);
      if (w.length) { const g = w[Math.floor(rnd() * w.length)]; out.push({ type: "m_wasp", wx: (b + .5) * k, f: g, beat: b + .5 }); }
    }
  }
  // No nectar right after a wasp on the same flower, either.
  return out.filter((o) => !o.good || !out.some((w) => !w.good && w.f === o.f && Math.abs(w.beat - o.beat) < 1.5));
}
const mgNectarWin = (r) => (0.11 + (r.st.agility - 1) * .015) * MG_SPEED.nectar;  // how close, in course pixels

MG_MORE.nectar = {
  misses: true,
  why: { wasp: "Ouch, a wasp!", missed: "Three flowers missed!" },
  init(r) { r.ax = mgFlower(1); r.to = mgFlower(1); r.x = r.ax; r.y = 96; r.open = [0, 0, 0, 0]; },
  press(r, x) {
    // The flower in that quarter of the screen.
    const f = mgClamp(Math.floor(x / (MG_W / 4)), 0, 3), win = mgNectarWin(r);
    r.to = mgFlower(f); r.open[f] = .15;
    let best = null;
    for (const o of r.things) {
      if (o.f !== f || o.gone || o.missed) continue;
      const d = Math.abs(o.wx - r.dist);
      if (d <= win && (!best || d < Math.abs(best.wx - r.dist))) best = o;
    }
    if (!best) return;
    if (!best.good) { r.stung = true; return; }
    mgGot(r, best, mgFlower(f), 112);
  },
  step(r, dt) {
    if (r.stung) return "wasp";
    r.ax += mgClamp(r.to - r.ax, -400 * dt, 400 * dt); r.x = r.ax;
    r.open = r.open.map((v) => Math.max(0, v - dt));
    const win = mgNectarWin(r);
    for (const o of r.things) {
      if (o.wx - r.dist > win) break;
      if (!o.good || o.gone || o.missed || r.dist - o.wx <= win) continue;
      o.missed = true; r.missed++;
      r.fx.push({ kind: "text", x: mgFlower(o.f), y: 104, text: "Missed!", life: .9 });
      if (r.missed >= 3) return "missed";
    }
  },
  draw(c, r) {
    mgSky(c, "#a8daf0", "#f4f0d0");
    mgHills(c, r, .05, 150, 20, 90, "#9fcf9a");
    c.fillStyle = "#6aae6e"; c.fillRect(0, 172, MG_W, MG_H - 172);
    const k = MG_SPEED.nectar * r.lvl.spb;
    MG_FLOWERS.forEach((x, f) => {
      c.fillStyle = "#3f8d58"; c.fillRect(x - 1, 126, 3, 50);
      c.fillRect(x - 8, 150, 7, 3); c.fillRect(x + 2, 140, 7, 3);
      // The next thing due on this flower: a bud that opens as it comes, a ring that shrinks
      // onto it right on the beat.
      let next = null;
      for (const o of r.things) if (o.f === f && !o.gone && !o.missed && o.wx - r.dist > -mgNectarWin(r)) { next = o; break; }
      const u = next ? (next.wx - r.dist) / k : 9;  // beats until it's due
      const open = r.open[f] > 0 ? 1 : u < 2 ? mgClamp(1 - u / 2, 0, 1) : 0;
      const pet = 3 + Math.round(open * 5), col = MG_PETALS[f];
      c.fillStyle = col;
      for (const [dx, dy] of [[-1, -1], [1, -1], [-1, 1], [1, 1], [0, -1.4], [0, 1.4], [-1.4, 0], [1.4, 0]])
        c.fillRect(x + Math.round(dx * pet) - 2, 120 + Math.round(dy * pet) - 2, 5, 5);
      c.fillStyle = "#f8e08a"; c.fillRect(x - 2, 118, 5, 5);
      if (next && u < 2) {
        const rad = 8 + u * 14;
        c.strokeStyle = next.good ? "rgba(255,255,255,.9)" : "rgba(230,60,60,.9)"; c.lineWidth = 1.5;
        c.beginPath(); c.arc(x + .5, 120.5, rad, 0, Math.PI * 2); c.stroke();
        if (!next.good) {  // a wasp buzzing in to sit on the flower
          const wy = 120 - 14 - u * 20, wx = x + Math.sin(r.phase * 9 + f) * 4, flap = Math.floor(r.phase * 24) % 2;
          c.fillStyle = "rgba(255,255,255,.85)"; c.fillRect(wx - 3, wy - 5 - flap, 3, 3); c.fillRect(wx + 1, wy - 5 + flap, 3, 3);
          c.fillStyle = "#f2c14e"; c.fillRect(wx - 5, wy - 2, 10, 5);
          c.fillStyle = "#2a2a2a"; c.fillRect(wx - 3, wy - 2, 2, 5); c.fillRect(wx + 1, wy - 2, 2, 5); c.fillRect(wx + 5, wy, 2, 1);
        }
      }
      c.fillStyle = "rgba(0,0,0,.25)"; c.font = "bold 8px system-ui, sans-serif"; c.textAlign = "center";
      c.fillText(String(f + 1), x, 192);
    });
    mgAnimal(c, r, r.ax, 102 + Math.round(Math.sin(r.phase * 5) * 2), ["fly", "idle"], { frame: r.phase * 14, flip: r.to >= r.ax });
  },
};

// ---- Call Back: hear a rhythm, tap it back ------------------------------------------
// A call is one bar (4 beats) from your friend, then a bar for you to tap the same
// rhythm. Patterns are in beats from the start of the bar.
const MG_CALLS = [
  [0, 1, 2, 3], [0, 2], [0, 1, 2], [0, 2, 3], [0, 1, 3], [0, .5, 1, 2], [0, 1, 1.5, 2], [0, 2, 2.5, 3],
  [0, .5, 1, 1.5, 2], [0, 1.5, 3], [0, .5, 2, 2.5], [0, .75, 1.5, 2, 3], [0, 1, 1.5, 2.5, 3], [0, .5, 1, 2, 2.5, 3],
  [0, 1.5, 2, 2.5, 3], [0, .5, 1.5, 2, 3, 3.5], [0, .25, .5, 2, 2.25, 2.5], [0, .75, 1.5, 2.25, 3],
];
function mgCallLevel(k, seed, calls, from0, from1, to0, to1) {
  const rnd = mgRand(seed), out = [];
  for (let i = 0; i < calls; i++) {
    const u = i / (calls - 1), lo = Math.round(from0 + (from1 - from0) * u), hi = Math.round(to0 + (to1 - to0) * u);
    // A quiet lead-in, then each round: listen for a bar, two quiet beats to get ready,
    // your bar, and two more quiet beats before the next call.
    const pat = MG_CALLS[lo + Math.floor(rnd() * (hi - lo + 1))], b = 6 + i * 12, a = b + 6;
    for (const t of pat) {
      out.push({ type: "m_call", wx: (b + t) * k, beat: b + t, bar: b, call: i });
      out.push({ type: "m_answer", good: true, pts: 1, wx: (a + t) * k, beat: a + t, bar: a, lis: b, call: i });
    }
  }
  return out;
}
const mgCallWin = () => 0.12 * MG_SPEED.call;

// What your animal sounds like: a woodpecker drums, a frog croaks, a cricket chirps.
function mgCallKind(slug) {
  if (/woodpecker|flicker|sapsucker|grouse|beaver/.test(slug)) return "drum";
  if (/frog|toad|peeper/.test(slug)) return "croak";
  if (/cricket|katydid|cicada/.test(slug)) return "chirp";
  if (/rattlesnake|massasauga/.test(slug)) return "rattle";
  if (/coyote|wolf|elk|loon|owl/.test(slug)) return "hoot";
  if (/prairie_dog|sea_lion|jay|crow|raven/.test(slug)) return "bark";
  return "whistle";
}
function mgCallSfx(kind, low) {
  const ctx = mgAudio.ctx;
  if (!ctx || mgAudio.muted) return;
  const out = ctx.destination, at = ctx.currentTime, f = low ? .8 : 1;
  if (kind === "drum") { mgHit16(ctx, out, at, .06, .5, 700); mgNote(ctx, out, "square", 180 * f, at, .05, .12, 90); }
  else if (kind === "croak") mgNote(ctx, out, "sawtooth", 160 * f, at, .16, .12, 90);
  else if (kind === "chirp") [0, .04, .08].forEach((d) => mgNote(ctx, out, "sine", 4200 * f, at + d, .03, .08));
  else if (kind === "rattle") mgHit16(ctx, out, at, .18, .3, 4000);
  else if (kind === "hoot") mgNote(ctx, out, "sine", 420 * f, at, .22, .15, 300 * f);
  else if (kind === "bark") mgNote(ctx, out, "square", 700 * f, at, .08, .1, 400 * f);
  else mgNote(ctx, out, "sine", 1800 * f, at, .12, .1, 2600 * f);
}

MG_MORE.call = {
  misses: true,
  why: { missed: "Three mistakes!" },
  init(r) { r.x = 230; r.y = 150; r.heard = 0; r.wrong = []; },
  press(r) {
    const win = mgCallWin();
    let best = null;
    for (const o of r.things) {
      if (!o.good || o.gone || o.missed) continue;
      const d = Math.abs(o.wx - r.dist);
      if (d <= win && (!best || d < Math.abs(best.wx - r.dist))) best = o;
    }
    mgCallSfx(mgCallKind(mg.species.slug));
    r.flap = .15;
    if (best) { mgGot(r, best, 230 + mgOx(), 120); return; }
    // A tap in your bar that isn't in the rhythm is a mistake. Taps between calls are fine.
    const k = MG_SPEED.call * r.lvl.spb;
    const mine = r.things.some((o) => o.good && r.dist >= o.bar * k - win && r.dist <= (o.bar + 4) * k);
    if (mine) { r.missed++; r.wrong.push(r.dist); r.fx.push({ kind: "text", x: 230 + mgOx(), y: 112, text: "Oops!", life: .8 }); }
  },
  step(r) {
    if (r.missed >= 3) return "missed";
    const win = mgCallWin();
    for (const o of r.things) {
      if (o.wx - r.dist > win) break;
      if (o.type === "m_call" && !o.heard && r.dist >= o.wx) { o.heard = true; r.heard = r.t; mgCallSfx(mgCallKind(mg.species.slug), true); }
      if (!o.good || o.gone || o.missed || r.dist - o.wx <= win) continue;
      o.missed = true; r.missed++;
      r.fx.push({ kind: "text", x: 230 + mgOx(), y: 112, text: "Missed!", life: .8 });
      if (r.missed >= 3) return "missed";
    }
  },
  draw(c, r) {
    mgSky(c, "#f2b880", "#f6e2b8");
    mgHills(c, r, 0, 150, 26, 80, "#9fb87a");
    c.fillStyle = "#6a8a4a"; c.fillRect(0, 160, MG_W, MG_H - 160);
    // Two stumps: your friend on the left, you on the right.
    const ox = Math.round(mgOx());
    for (const x of [90 + ox, 230 + ox]) {
      c.fillStyle = "#7a5232"; c.fillRect(x - 14, 150, 28, 18); c.fillStyle = "#d8b07a"; c.fillRect(x - 14, 148, 28, 4);
    }
    const k = MG_SPEED.call * r.lvl.spb, beat = r.dist / k;
    // The bar being played now: a row of beats with the rhythm's dots on it.
    const now = r.things.find((o) => o.good && beat < o.bar + 4 + .5) || r.things[r.things.length - 1];
    const call = now ? now.call : 0, lis = now ? now.lis : 0, mine = now ? now.bar : 4, yours = beat >= mine - .25;
    const x0 = 40 + ox, w = 240, at = (t) => x0 + t / 4 * w;
    c.fillStyle = "rgba(20,30,24,.55)"; c.fillRect(x0 - 10, 30, w + 20, 46);
    c.font = "bold 9px system-ui, sans-serif"; c.textAlign = "left"; c.fillStyle = "#fff";
    c.fillText(yours ? "Your turn!" : beat >= lis + 4 ? "Get ready…" : "Listen…", x0 - 4, 42);
    for (let t = 0; t <= 4; t++) { c.fillStyle = "rgba(255,255,255,.35)"; c.fillRect(Math.round(at(t)), 48, 1, 22); }
    for (const o of r.things) {
      if (o.call !== call) continue;
      const t = o.beat - o.bar, x = Math.round(at(t));
      if (o.type === "m_call") {
        c.fillStyle = o.heard ? "#ffd28a" : "rgba(255,210,138,.35)"; c.fillRect(x - 3, 51, 6, 6);
      } else {
        c.fillStyle = o.gone ? "#9be59b" : o.missed ? "#e86a6a" : "rgba(255,255,255,.4)";
        if (o.gone || o.missed) c.fillRect(x - 3, 61, 6, 6);
        else { c.fillRect(x - 3, 61, 6, 1); c.fillRect(x - 3, 66, 6, 1); c.fillRect(x - 3, 61, 1, 6); c.fillRect(x + 2, 61, 1, 6); }
      }
    }
    // Where in the bar we are.
    const t = yours ? beat - mine : beat - lis;
    if (t >= 0 && t <= 4) { c.fillStyle = "#fff"; c.fillRect(Math.round(at(t)), 46, 2, 26); }
    // Notes rising from whoever is calling.
    const sing = r.t - r.heard < .25, tapped = r.flap > 0;
    c.fillStyle = "#fff"; c.font = "bold 12px system-ui, sans-serif"; c.textAlign = "center";
    if (sing) c.fillText("♪", 100 + ox, 112 - (r.t - r.heard) * 40);
    if (tapped) c.fillText("♪", 240 + ox, 112 - (.15 - r.flap) * 60);
    mgAnimal(c, r, 90 + ox, 150, ["idle", "walk"], { frame: sing ? r.phase * 12 : 0, flip: true, still: true });
    mgAnimal(c, r, 230 + ox, 150 - (tapped ? 2 : 0), ["idle", "walk"], { frame: tapped ? r.phase * 12 : 0, flip: false, still: true });
  },
};

// ---- Burrow Dig: steer a tunnel through the ground ---------------------------------
// The level is built around a way through: a path that never turns more steeply than
// the slowest digger can follow, with rocks, roots and pockets of water put close to it.
const MG_SOIL = 40;
function mgDigLevel(k, seed, beats, clear0, clear1) {
  const rnd = mgRand(seed), out = [], spb = k / MG_SPEED.dig, way = [[0, 110]];
  for (let b = 3; b < beats; ) {
    const step = 1.5 + rnd() * 1.5, dx = step * k, [, y0] = way[way.length - 1];
    const most = dx / MG_SPEED.dig * 60 * .5;  // half of what the slowest digger can climb
    way.push([b * k, mgClamp(y0 + (rnd() * 2 - 1) * most, 62, 172)]);
    b += step;
  }
  const at = (x) => {
    let i = 1;
    while (i < way.length - 1 && way[i][0] < x) i++;
    const [x0, y0] = way[i - 1], [x1, y1] = way[i];
    return y0 + (y1 - y0) * mgClamp((x - x0) / (x1 - x0 || 1), 0, 1);
  };
  const end = way[way.length - 1][0];
  for (let x = 4 * k; x < end - k; x += k * (.8 + rnd() * .7)) {
    const u = x / end, clear = clear0 + (clear1 - clear0) * u, y = at(x), kind = rnd();
    const up = rnd() < .5;
    if (kind < .35 && up) {  // a root hanging down to just above the way
      out.push({ type: "m_root", wx: x, top: MG_SOIL, bot: y - clear, w: 6 });
    } else {
      const rad = 7 + rnd() * 6, water = kind > .75;
      out.push({ type: water ? "m_water" : "m_stone", wx: x, y: y + (up ? -1 : 1) * (clear + rad), rad });
    }
    if (rnd() < .45) {  // and often one on the other side too
      const rad = 7 + rnd() * 5;
      out.push({ type: "m_stone", wx: x + (rnd() - .5) * 10, y: y + (up ? 1 : -1) * (clear + rad), rad });
    }
  }
  for (let x = 2 * k; x < end; x += k) out.push({ type: "m_grub", good: true, pts: 1, wx: x, y: at(x) });
  out.way = way;
  return out;
}

MG_MORE.dig = {
  why: { bump: "Bonk! A rock", wet: "Splash! Water", root: "Tangled in a root" },
  init(r) { r.x = 80; r.y = 110; r.tunnel = []; },
  press() {},
  step(r, dt) {
    const vmax = 60 * (1 + (r.st.agility - 1) * .1), ty = r.held && r.fresh ? mgClamp(r.py, 48, 186) : r.y;
    r.y = mgClamp(r.y + mgClamp((ty - r.y) * 10, -vmax, vmax) * dt, 48, 186);
    if (!r.tunnel.length || r.dist - r.tunnel[r.tunnel.length - 1][0] > 3) r.tunnel.push([r.dist, r.y]);
    if (r.tunnel.length > 140) r.tunnel.shift();
    const half = 6 - r.p.shrink * .6;
    for (const o of r.things) {
      if (o.gone) continue;
      const dx = o.wx - r.dist;
      if (dx > 30) break;
      if (dx < -30) continue;
      if (o.good) { if (Math.abs(dx) < 8 && Math.abs(o.y - r.y) < 9) mgGot(r, o, r.x + dx, o.y); continue; }
      if (o.type === "m_root") {
        if (Math.abs(dx) < o.w / 2 + half && r.y - half < o.bot) return "root";
      } else if (Math.hypot(dx, o.y - r.y) < o.rad + half) return o.type === "m_water" ? "wet" : "bump";
    }
  },
  draw(c, r) {
    mgSky(c, "#9ad3ee", "#c8e8f0");
    c.fillStyle = "#58a662"; c.fillRect(0, MG_SOIL - 8, MG_W, 8);
    c.fillStyle = "#3f8d58";
    for (let x = -mgScroll(r, 1, 8); x < MG_W; x += 8) c.fillRect(x, MG_SOIL - 10, 2, 3);
    // Layers of soil, darker the deeper.
    const soil = c.createLinearGradient(0, MG_SOIL, 0, MG_H);
    soil.addColorStop(0, "#9a7048"); soil.addColorStop(1, "#5e4028");
    c.fillStyle = soil; c.fillRect(0, MG_SOIL, MG_W, MG_H - MG_SOIL);
    c.fillStyle = "rgba(0,0,0,.12)";
    for (let i = 0; i < 18; i++) c.fillRect((i * 61 - mgScroll(r, 1, 1100) + 1100) % 1100 - 20, 50 + (i * 43) % 140, 3, 2);
    // Your tunnel so far.
    c.fillStyle = "#3e2a18";
    for (const [wx, y] of r.tunnel) c.fillRect(Math.round(wx - r.dist + r.x) - 3, Math.round(y) - 6, 6, 12);
    for (const o of r.things) {
      if (o.gone) continue;
      const x = Math.round(o.wx - r.dist + r.x);
      if (x < -30 || x > MG_W + 30) continue;
      if (o.type === "m_root") {
        c.fillStyle = "#c8a070"; c.fillRect(x - 3, o.top, 6, o.bot - o.top);
        c.fillStyle = "#a07a50"; c.fillRect(x - 3, o.top, 2, o.bot - o.top);
        c.fillRect(x - 6, o.bot - 6, 3, 6); c.fillRect(x + 3, o.bot - 10, 3, 8);
      } else if (o.type === "m_grub") {
        const y = Math.round(o.y), wig = Math.round(Math.sin(r.phase * 8 + o.wx) * 1);
        c.fillStyle = "#f4ead0"; c.fillRect(x - 4, y - 2 + wig, 8, 4); c.fillStyle = "#c8a070"; c.fillRect(x + 3, y - 2 + wig, 2, 3);
        c.fillStyle = "rgba(0,0,0,.2)"; c.fillRect(x - 2, y - 2 + wig, 1, 4); c.fillRect(x + 1, y - 2 + wig, 1, 4);
      } else {
        const water = o.type === "m_water";
        c.fillStyle = water ? "#3d8cc0" : "#8a8f9e";
        c.beginPath(); c.ellipse(x, o.y, o.rad + (water ? 2 : 0), o.rad, 0, 0, Math.PI * 2); c.fill();
        c.fillStyle = water ? "#7cc4e8" : "#a8adb8";
        c.fillRect(x - Math.round(o.rad / 2), Math.round(o.y - o.rad / 2), Math.round(o.rad / 2), 2);
      }
    }
    // The nest at the end of the course.
    const nx = Math.round(r.len - r.dist + r.x + 30);
    if (nx < MG_W + 40) {
      c.fillStyle = "#3e2a18"; c.beginPath(); c.ellipse(nx, 130, 26, 18, 0, 0, Math.PI * 2); c.fill();
      c.fillStyle = "#c8a860"; c.fillRect(nx - 16, 140, 32, 6);
    }
    mgAnimal(c, r, r.x, r.y + 10, ["walk", "idle"], { frame: r.dist / 6, scale: .8 });
  },
};

// ---- Echo Flight: a dark cave, lit only by your echoes ----------------------------
function mgEchoLevel(k, seed, gates, start, gap0, gap1, beat0, beat1) {
  const rnd = mgRand(seed), out = [], spb = k / MG_SPEED.echo;
  let b = start, c = 100;
  for (let i = 0; i < gates; i++) {
    const u = i / (gates - 1), gap = gap0 + (gap1 - gap0) * u, db = beat0 + (beat1 - beat0) * u + rnd() * .5;
    const most = db * spb * 80 * .55;
    b += db;
    c = mgClamp(c + (rnd() * 2 - 1) * most, 22 + gap / 2 + 4, 178 - gap / 2 - 4);
    const a = c - gap / 2, z = c + gap / 2;
    out.push({ type: "m_tite", wx: b * k, y0: 0, y1: a, w: 20 }, { type: "m_mite", wx: b * k, y0: z, y1: MG_H, w: 20 });
    out.push({ type: "m_moth", good: true, pts: 1, wx: b * k, y: c });
    if (rnd() < .6) out.push({ type: "m_moth", good: true, pts: 1, wx: (b - db / 2) * k, y: c + (rnd() - .5) * 20 });
  }
  return out;
}

MG_MORE.echo = {
  why: { bump: "Bonk! A rock" },
  init(r) { r.x = 72; r.y = 100; r.vy = 0; r.pings = []; },
  press(r) { r.pings.push([r.dist, r.y, r.t]); if (r.pings.length > 8) r.pings.shift(); mgCallSfx("chirp", true); },
  step(r, dt) {
    const pw = r.p.power;
    r.vy = mgClamp(r.vy + (r.held && r.fresh ? -260 * pw : 200) * dt, -95, 85);
    r.y += r.vy * dt;
    if (r.y < 22) { r.y = 22; r.vy = Math.max(0, r.vy); }
    if (r.y > 178) { r.y = 178; r.vy = Math.min(0, r.vy); }
    const b = [r.x - 7 + r.p.shrink, r.y - 6 + r.p.shrink, r.x + 7 - r.p.shrink, r.y + 6 - r.p.shrink];
    for (const o of r.things) {
      if (o.gone) continue;
      const x = o.wx - r.dist + r.x;
      if (x > b[2] + 30) break;
      if (o.good) { if (Math.abs(x - r.x) < 9 && Math.abs(o.y - r.y) < 10) mgGot(r, o, x, o.y); continue; }
      if (x + o.w / 2 > b[0] && x - o.w / 2 < b[2] && o.y1 > b[1] && o.y0 < b[3]) return "bump";
    }
  },
  draw(c, r) {
    // The cave as it really is…
    c.fillStyle = "#4a4270"; c.fillRect(0, 0, MG_W, MG_H);
    c.fillStyle = "#5a5288";
    for (let i = 0; i < 10; i++) c.fillRect((i * 71 - mgScroll(r, .4, 700) + 700) % 700 - 20, 20 + (i * 53) % 160, 14, 3);
    c.fillStyle = "#8a80a8"; c.fillRect(0, 0, MG_W, 14); c.fillRect(0, MG_H - 14, MG_W, 14);
    for (const o of r.things) {
      if (o.gone) continue;
      const x = Math.round(o.wx - r.dist + r.x);
      if (x < -20 || x > MG_W + 20) continue;
      if (o.good) {
        const y = Math.round(o.y + Math.sin(r.phase * 6 + o.wx) * 2), f = Math.floor(r.phase * 16) % 2;
        c.fillStyle = "#e8dcc0"; c.fillRect(x - 3, y - 2 - f, 3, 3); c.fillRect(x + 1, y - 2 + f, 3, 3); c.fillStyle = "#8a7a60"; c.fillRect(x - 1, y - 1, 2, 4);
        continue;
      }
      // A spike of rock, pointing at the gap.
      const down = o.type === "m_tite", tip = down ? o.y1 : o.y0, base = down ? o.y0 : o.y1;
      c.fillStyle = "#b0a4d0";
      for (let y = Math.min(tip, base); y < Math.max(tip, base); y += 2) {
        const u = Math.abs(y - base) / Math.max(1, Math.abs(tip - base)), w = Math.max(2, Math.round(o.w * (1 - u * .7)));
        c.fillRect(x - Math.floor(w / 2), y, w, 2);
      }
      c.fillStyle = "#d8d0f0"; c.fillRect(x - Math.floor(o.w / 2), Math.min(tip, base), 3, Math.abs(tip - base));
    }
    // …and the dark over it, with holes where your echoes are. Every echo is a ring that
    // spreads out and fades.
    const D = 1.1 + (r.st.agility - 1) * .15;
    const dark = mg.dark || (mg.dark = document.createElement("canvas"));
    dark.width = MG_W; dark.height = MG_H;
    const d = dark.getContext("2d");
    d.globalCompositeOperation = "source-over";
    d.fillStyle = "rgba(6,4,14,.95)"; d.fillRect(0, 0, MG_W, MG_H);
    d.globalCompositeOperation = "destination-out";
    const hole = (x, y, rad, a) => {
      const g = d.createRadialGradient(x, y, 0, x, y, rad);
      g.addColorStop(0, `rgba(0,0,0,${a})`); g.addColorStop(.7, `rgba(0,0,0,${a * .8})`); g.addColorStop(1, "rgba(0,0,0,0)");
      d.fillStyle = g; d.beginPath(); d.arc(x, y, rad, 0, Math.PI * 2); d.fill();
    };
    hole(r.x, r.y, 30, .9);
    for (const [wx, y, t] of r.pings) {
      const age = r.t - t;
      if (age > D) continue;
      hole(wx - r.dist + r.x, y, 30 + age * 240, 1 - age / D);
    }
    c.drawImage(dark, 0, 0);
    // The echo rings themselves.
    for (const [wx, y, t] of r.pings) {
      const age = r.t - t;
      if (age > .5) continue;
      c.strokeStyle = `rgba(200,220,255,${.6 * (1 - age / .5)})`; c.lineWidth = 1;
      c.beginPath(); c.arc(wx - r.dist + r.x, y, 8 + age * 240, -1, 1); c.stroke();
    }
    mgAnimal(c, r, r.x, r.y + 10, ["fly", "idle"], { frame: r.held ? r.phase * 14 : r.phase * 6, rot: mgClamp(r.vy / 350, -.3, .3), scale: .8 });
  },
};

// ---- Plunge Dive and Big Splash: between the air and the water -------------------
// Both are built from a plan of dives played through the game's own physics at the
// lowest stats: fish go where that dive reaches, jellies and rocks just past it.
function mgSeaPhys(game, r, held, dt, pw) {
  if (game === "plunge") {
    const W = 100;
    if (r.y <= W) {
      if (held) r.vy = Math.min(240, r.vy + 900 * pw * dt);
      else r.vy += ((52 - r.y) * 10 - r.vy * 5) * dt;  // glide back up to cruising height
    } else r.vy += ((held ? 70 * pw : -170 * pw) - r.vy) * 5 * dt;
    r.y += r.vy * dt;
    if (r.y < 18) { r.y = 18; r.vy = Math.max(0, r.vy); }
    if (r.y > 184) { r.y = 184; r.vy = Math.min(0, r.vy); }
  } else {
    const W = 104;
    if (r.y < W) r.vy += 420 * dt;  // in the air: just falling
    else {
      r.vy += (held ? 420 : -560 * pw) * dt;
      r.vy = mgClamp(r.vy * (1 - 1.2 * dt), -300, 150);
    }
    const was = r.y;
    r.y += r.vy * dt;
    // Too slow to leave the water: float at the top.
    if (was >= W && r.y < W && r.vy > -90) { r.y = W; r.vy = 0; }
    if (r.y > 184) { r.y = 184; r.vy = Math.min(0, r.vy); }
  }
}

// plan: [beat, seconds held]. Returns the path at every step: [course x, y].
function mgSeaPath(game, k, plan, beats) {
  const spb = k / MG_SPEED[game], r = { y: game === "plunge" ? 52 : 104, vy: 0 }, path = [];
  let i = 0;
  for (let t = 0; t < beats * spb; t += MG_DT) {
    while (i < plan.length && t > plan[i][0] * spb + plan[i][1]) i++;
    const held = i < plan.length && t >= plan[i][0] * spb;
    mgSeaPhys(game, r, held, MG_DT, 1);
    path.push([t * MG_SPEED[game], r.y]);
  }
  return path;
}

function mgPlungeLevel(k, seed, dives, start, gap0, gap1, hold0, hold1) {
  const rnd = mgRand(seed), plan = [], out = [];
  let b = start;
  for (let i = 0; i < dives; i++) {
    const u = i / (dives - 1);
    plan.push([b, hold0 + (hold1 - hold0) * u * rnd() + rnd() * .15]);
    b += gap0 + (gap1 - gap0) * u + Math.round(rnd() * 2) / 2;
  }
  const path = mgSeaPath("plunge", k, plan, b + 4), W = 100;
  for (const [pb] of plan) {
    // The deepest point of this dive.
    const step = MG_SPEED.plunge * MG_DT, i0 = Math.round(pb * k / step), seg = path.slice(i0, i0 + Math.round(2.5 * k / step));
    let deep = seg[0];
    for (const p of seg) if (p[1] > deep[1]) deep = p;
    if (!deep || deep[1] < W + 8) continue;
    out.push({ type: "m_fishy", good: true, pts: 2, wx: deep[0], y: deep[1] });
    const into = seg.find((p) => p[1] > W + 12);
    if (into) out.push({ type: "m_fishy", good: true, pts: 1, wx: into[0], y: into[1] });
    // A jelly just below the bottom of the dive, a little after it.
    out.push({ type: "m_jelly", wx: deep[0] + 6 + rnd() * 10, y: Math.min(176, deep[1] + 22 + rnd() * 6), rad: 7 });
    if (rnd() < .5) out.push({ type: "m_jelly", wx: deep[0] - 26 - rnd() * 8, y: Math.min(176, deep[1] + 24), rad: 7 });
  }
  // Rocks between the dives: dive there and you hit one.
  for (let i = 0; i < plan.length - 1; i++) {
    const a = (plan[i][0] + 2.2) * k, z = plan[i + 1][0] * k - 10;
    if (z - a < 30) continue;
    const x = a + (z - a) * (.3 + rnd() * .4);
    const p = path[Math.min(path.length - 1, Math.round(x / MG_SPEED.plunge / MG_DT))];
    if (p && p[1] < W - 10) out.push({ type: "m_seastack", wx: x, y0: W + 16 + rnd() * 20, y1: MG_H, w: 18 });
  }
  return out;
}

function mgSplashLevel(k, seed, leaps, start, gap0, gap1, hold0, hold1) {
  const rnd = mgRand(seed), plan = [], out = [], W = 104;
  let b = start;
  for (let i = 0; i < leaps; i++) {
    const u = i / (leaps - 1);
    plan.push([b, hold0 + (hold1 - hold0) * (.4 + .6 * rnd()) * (.5 + .5 * u)]);
    b += gap0 + (gap1 - gap0) * u + Math.round(rnd() * 2) / 2;
  }
  const path = mgSeaPath("splash", k, plan, b + 4), step = MG_SPEED.splash * MG_DT;
  const idx = (x) => Math.min(path.length - 1, Math.max(0, Math.round(x / step)));
  for (let i = 0; i < plan.length; i++) {
    const i0 = idx(plan[i][0] * k), i1 = idx(i + 1 < plan.length ? plan[i + 1][0] * k : path.length * step);
    const seg = path.slice(i0, i1);
    let deep = seg[0], high = seg[0];
    for (const p of seg) { if (p[1] > deep[1]) deep = p; if (p[1] < high[1]) high = p; }
    out.push({ type: "m_snack", good: true, pts: 1, wx: deep[0], y: deep[1] });
    if (high[1] < W - 16) out.push({ type: "m_ring", good: true, pts: 3, wx: high[0], y: high[1] });
    // A log floating over the dive: leap too soon and you bump into it.
    const under = seg.filter((p) => p[1] > W + 24);
    if (under.length > 10) { const p = under[Math.floor(under.length * (.3 + rnd() * .3))]; out.push({ type: "m_float", wx: p[0], y0: W - 5, y1: W + 5, w: 26 }); }
    // A rock from the bottom where you float between leaps.
    const flat = seg.filter((p, j) => j > seg.length * .6 && Math.abs(p[1] - W) < 1);
    if (flat.length > 20 && rnd() < .7) {
      const p = flat[Math.floor(flat.length / 2)];
      out.push({ type: "m_seastack", wx: p[0], y0: W + 26 + rnd() * 16, y1: MG_H, w: 18 });
    }
  }
  return out;
}

// Shared by both: what you bump into or pick up, and how the sea looks.
function mgSeaStep(r, game) {
  const s = r.p.shrink, b = [r.x - 7 + s, r.y - 6 + s, r.x + 7 - s, r.y + 6 - s];
  for (const o of r.things) {
    if (o.gone) continue;
    const x = o.wx - r.dist + r.x;
    if (x > b[2] + 30) break;
    if (x < b[0] - 30) continue;
    if (o.good) {
      const near = o.type === "m_ring" ? Math.abs(x - r.x) < 7 && Math.abs(o.y - r.y) < 11 : Math.abs(x - r.x) < 9 && Math.abs(o.y - r.y) < 10;
      if (near) mgGot(r, o, x, o.y);
    } else if (o.type === "m_jelly") {
      const y = o.y + Math.sin(r.t * 2 + o.wx) * 3;
      if (Math.hypot(x - r.x, y - r.y) < o.rad + 6 - s) return "jelly";
    } else if (x + o.w / 2 > b[0] && x - o.w / 2 < b[2] && o.y1 > b[1] && o.y0 < b[3]) return o.type === "m_float" ? "log" : "bump";
  }
}

function mgSeaDraw(c, r, W) {
  mgSky(c, "#8ccbea", "#d8f0f8");
  for (let i = 0; i < 3; i++) mgCloud(c, (i * 131 - mgScroll(r, .1, 420) + 420) % 420 - 40, 14 + i * 14, 1, "rgba(255,255,255,.9)");
  mgHills(c, r, .08, W - 2, 10, 70, "#7aa8a0");
  const sea = c.createLinearGradient(0, W, 0, MG_H);
  sea.addColorStop(0, "#3d9cc9"); sea.addColorStop(1, "#16507a");
  c.fillStyle = sea; c.fillRect(0, W, MG_W, MG_H - W);
  c.fillStyle = "rgba(255,255,255,.6)";
  for (let x = -mgScroll(r, .9, 16); x < MG_W; x += 16) c.fillRect(x, W, 8, 1);
  c.fillStyle = "#d9c18a"; c.fillRect(0, 186, MG_W, 14);
  for (const o of r.things) {
    if (o.gone) continue;
    const x = Math.round(o.wx - r.dist + r.x);
    if (x < -30 || x > MG_W + 30) continue;
    const box = (dx, dy, w, h, col) => { c.fillStyle = col; c.fillRect(x + dx, Math.round(o.y) + dy, w, h); };
    if (o.type === "m_fishy" || o.type === "m_snack") {
      box(-5, -2, 9, 5, o.type === "m_snack" ? "#f2a541" : "#c8d8e8"); box(-8, -3, 3, 7, o.type === "m_snack" ? "#f2a541" : "#c8d8e8");
      box(2, -1, 1, 1, "#222"); box(-4, 1, 7, 1, "rgba(255,255,255,.5)");
    } else if (o.type === "m_ring") {
      c.strokeStyle = "#f2c14e"; c.lineWidth = 2; c.beginPath(); c.ellipse(x, o.y, 4, 11, 0, 0, Math.PI * 2); c.stroke();
      c.strokeStyle = "rgba(255,255,255,.7)"; c.lineWidth = 1; c.beginPath(); c.ellipse(x - 1, o.y, 3, 9, 0, Math.PI * .6, Math.PI * 1.4); c.stroke();
    } else if (o.type === "m_jelly") {
      const y = Math.round(o.y + Math.sin(r.t * 2 + o.wx) * 3);
      c.fillStyle = "rgba(230,170,230,.85)"; c.fillRect(x - 6, y - 5, 12, 6); c.fillRect(x - 4, y - 7, 8, 2);
      c.fillStyle = "rgba(230,170,230,.6)";
      for (const dx of [-5, -2, 1, 4]) c.fillRect(x + dx, y + 1, 1, 5 + Math.round(Math.sin(r.phase * 4 + dx) * 2));
    } else if (o.type === "m_float") {
      c.fillStyle = "#7a5232"; c.fillRect(x - 13, o.y0, 26, o.y1 - o.y0); c.fillStyle = "#a8744a"; c.fillRect(x - 13, o.y0, 26, 2);
      c.fillStyle = "#d8b07a"; c.fillRect(x + 10, o.y0, 3, o.y1 - o.y0);
    } else if (o.type === "m_seastack") {
      c.fillStyle = "#6e7380"; c.fillRect(x - 9, o.y0 + 3, 18, o.y1 - o.y0);
      c.fillStyle = "#8a8f9e"; c.fillRect(x - 7, o.y0, 14, 5); c.fillRect(x - 9, o.y0 + 3, 4, o.y1 - o.y0);
      c.fillStyle = "#3f8d58"; c.fillRect(x - 4, o.y0 + 8, 2, 6); c.fillRect(x + 3, o.y0 + 14, 2, 5);
    }
  }
}

MG_MORE.plunge = {
  why: { jelly: "Ouch, a jellyfish!", bump: "Bonk! A rock" },
  init(r) { r.x = 80; r.y = 52; r.vy = 0; },
  press() {},
  step(r, dt) {
    const wasIn = r.y > 100;
    mgSeaPhys("plunge", r, r.held && r.fresh, dt, 1 + (r.st.agility - 1) * .06);
    if (wasIn !== r.y > 100) for (let i = 0; i < 4; i++) r.fx.push({ kind: "spark", x: r.x, y: 100, vx: (i - 1.5) * 30, vy: -50, life: .4 });
    return mgSeaStep(r, "plunge");
  },
  draw(c, r) {
    mgSeaDraw(c, r, 100);
    const diving = r.vy > 60;
    mgAnimal(c, r, r.x, r.y + 12, ["fly", "swim", "idle"], { frame: diving ? 1 : r.phase * (r.y > 100 ? 6 : 10), rot: mgClamp(r.vy / 220, -.5, 1.2) * (diving ? 1.2 : .4) });
  },
};

MG_MORE.splash = {
  why: { log: "Bonk! A log", bump: "Bonk! A rock" },
  init(r) { r.x = 84; r.y = 104; r.vy = 0; },
  press() {},
  step(r, dt) {
    const wasIn = r.y >= 104;
    mgSeaPhys("splash", r, r.held && r.fresh, dt, 1 + (r.st.agility - 1) * .05);
    if (wasIn !== r.y >= 104 || (wasIn && r.y < 104)) for (let i = 0; i < 6; i++) r.fx.push({ kind: "spark", x: r.x, y: 104, vx: (i - 2.5) * 28, vy: -60, life: .5 });
    return mgSeaStep(r, "splash");
  },
  draw(c, r) {
    mgSeaDraw(c, r, 104);
    mgAnimal(c, r, r.x, r.y + 12, ["swim", "idle"], { frame: r.phase * (r.held ? 8 : 4), rot: mgClamp(r.vy / 300, -.8, .8) });
  },
};

// ---- Branch Leap: hold to wind up, let go to jump ----------------------------------
// The meter fills for 0.9 s and drains again, so how far you leap is all timing. Some
// branches bob or sway on the beat. You move yourself here: r.dist is how far you've got.
const MG_LEAP = { g: 520, ang: 52 * Math.PI / 180, v0: 120, v1: 175, fill: .9 };
const mgTri = (u) => 1 - Math.abs((u % 2) - 1);
const mgLeapV = (charge, jump) => (MG_LEAP.v0 + MG_LEAP.v1 * charge) * (1 + (jump - 1) * .04);
function mgPerchAt(p, t, spb) {
  if (!p.amp && !p.ax) return [p.wx, p.y];
  const a = 2 * Math.PI * t / (p.per * spb) + p.ph;
  return [p.wx + (p.ax || 0) * Math.sin(a), p.y + (p.amp || 0) * Math.sin(a)];
}

function mgLeapLevel(k, seed, n, gap0, gap1, move0, move1, w0, w1) {
  const rnd = mgRand(seed), out = [{ type: "m_perch", wx: 0, y: 150, w: 56 }];
  let x = 0, y = 150;
  for (let i = 1; i < n; i++) {
    const u = i / (n - 1), w = Math.round(w0 + (w1 - w0) * u + rnd() * 6);
    const dx = gap0 + (gap1 - gap0) * u * rnd() + rnd() * 20;
    const ny = mgClamp(y + (rnd() * 2 - 1) * 38, 74, 164);
    const p = { type: "m_perch", wx: x + dx, y: ny, w };
    if (i > 2 && rnd() < move0 + (move1 - move0) * u) {
      if (rnd() < .6) p.amp = 10 + Math.round(rnd() * 10); else p.ax = 10 + Math.round(rnd() * 8);
      p.per = rnd() < .5 ? 2 : 4; p.ph = Math.round(rnd() * 3) * Math.PI / 2;
    }
    out.push(p);
    // An acorn at the top of the leap that lands in the middle of a still branch.
    if (!p.amp && !p.ax && !out[out.length - 2].amp && !out[out.length - 2].ax) {
      const top = mgLeapApex(x, y, p.wx, p.y);
      if (top) out.push({ type: "m_nut", good: true, pts: 2, wx: top[0], y: top[1] - 6 });
    }
    if (!p.amp && !p.ax) out.push({ type: "m_nut", good: true, pts: 1, wx: p.wx + (rnd() - .5) * (w - 12), y: ny - 8 });
    x = p.wx; y = ny;
  }
  return out;
}
// The top of the leap from (x0, y0) that comes down at (x1, y1), at Jump 1.
function mgLeapApex(x0, y0, x1, y1) {
  const land = (c) => {
    const v = mgLeapV(c, 1), vx = v * Math.cos(MG_LEAP.ang), vy = -v * Math.sin(MG_LEAP.ang);
    // Coming down through y1: y0 + vy t + g t²/2 = y1, the later root.
    const disc = vy * vy + 2 * MG_LEAP.g * (y1 - y0);
    if (disc < 0) return null;
    const t = (-vy + Math.sqrt(disc)) / MG_LEAP.g;
    return [x0 + vx * t, vx, vy];
  };
  let lo = 0, hi = 1;
  for (let i = 0; i < 30; i++) { const m = (lo + hi) / 2, l = land(m); if (!l || l[0] < x1) lo = m; else hi = m; }
  const l = land(hi);
  if (!l || Math.abs(l[0] - x1) > 3) return null;
  const t = -l[2] / MG_LEAP.g;
  return [x0 + l[1] * t, y0 + l[2] * t + MG_LEAP.g * t * t / 2];
}

MG_MORE.leap = {
  ownDist: true,
  why: { fall: "Whoops, missed the branch!" },
  init(r) {
    r.perches = r.things.filter((o) => o.type === "m_perch");
    r.len = r.perches[r.perches.length - 1].wx;
    r.on = 0; r.off = 0; r.wx = 0; r.y = r.perches[0].y; r.vx = 0; r.vy = 0;
    r.holdT = 0; r.charge = 0; r.was = false; r.x = 110; r.cam = -110;
  },
  press() {},
  step(r, dt) {
    const spb = r.lvl.spb, held = r.held && r.fresh;
    if (r.on >= 0) {
      const [px, py] = mgPerchAt(r.perches[r.on], r.t, spb);
      r.wx = px + r.off; r.y = py;
      if (held) { r.holdT += dt; r.charge = mgTri(r.holdT / MG_LEAP.fill); }
      else if (r.was) {
        const v = mgLeapV(r.charge, r.st.jump);
        r.vx = v * Math.cos(MG_LEAP.ang); r.vy = -v * Math.sin(MG_LEAP.ang); r.on = -1; r.holdT = 0; r.charge = 0;
        mgSfx("treat");
      }
    } else {
      const y0 = r.y;
      r.vy += MG_LEAP.g * dt; r.wx += r.vx * dt; r.y += r.vy * dt;
      if (r.vy > 0) {
        const grip = 2 + (r.st.agility - 1) * 1.5;
        for (let i = 0; i < r.perches.length; i++) {
          const p = r.perches[i];
          if (Math.abs(p.wx - r.wx) > 80) continue;
          const [px, py] = mgPerchAt(p, r.t, spb);
          if (y0 <= py + 2 && r.y >= py && Math.abs(r.wx - px) <= p.w / 2 + grip) {
            r.on = i; r.off = mgClamp(r.wx - px, -p.w / 2, p.w / 2); r.y = py; r.vx = r.vy = 0;
            break;
          }
        }
      }
      if (r.y > MG_H + 20) return "fall";
    }
    r.was = held;
    r.dist = r.on === r.perches.length - 1 ? r.len : Math.min(r.len - 1, Math.max(0, r.wx));
    r.cam += (r.wx - 110 - r.cam) * Math.min(1, dt * 5);
    for (const o of r.things) {
      if (!o.good || o.gone || Math.abs(o.wx - r.wx) > 9 || Math.abs(o.y - (r.y - 10)) > 12) continue;
      mgGot(r, o, o.wx - r.cam, o.y);
    }
  },
  draw(c, r) {
    mgSky(c, "#9ad3ee", "#e8f4dc");
    const scr = { dist: r.cam, phase: r.phase };
    mgHills(c, scr, .15, 120, 30, 80, "#8fb9a8");
    // Far trunks, then the forest floor far below.
    c.fillStyle = "#7a9a7a";
    for (let x = -mgScroll(scr, .4, 70); x < MG_W + 70; x += 70) c.fillRect(x, 0, 10, MG_H);
    c.fillStyle = "#4f7d4f"; c.fillRect(0, 190, MG_W, 10);
    for (const o of r.things) {
      if (o.type !== "m_perch") continue;
      const [px, py] = mgPerchAt(o, r.t, r.lvl.spb), x = Math.round(px - r.cam), y = Math.round(py);
      if (x < -60 || x > MG_W + 60) continue;
      const left = Math.round(x - o.w / 2), moving = o.amp || o.ax;
      if (moving) { c.fillStyle = "#3f8d58"; c.fillRect(x - 1, 0, 2, y); }
      else { c.fillStyle = "#6a4a2e"; c.fillRect(left - 6, 0, 7, MG_H); }
      c.fillStyle = "#7a5232"; c.fillRect(left, y, o.w, 5); c.fillStyle = "#a8744a"; c.fillRect(left, y, o.w, 2);
      c.fillStyle = "#3f8d58"; c.fillRect(left + o.w - 8, y - 5, 10, 5); c.fillStyle = "#2f7d4f"; c.fillRect(left + o.w - 2, y - 3, 6, 6);
    }
    for (const o of r.things) {
      if (!o.good || o.gone) continue;
      const x = Math.round(o.wx - r.cam), y = Math.round(o.y);
      c.fillStyle = "#62402a"; c.fillRect(x - 3, y - 4, 7, 3); c.fillRect(x, y - 6, 1, 2);
      c.fillStyle = "#c78a3e"; c.fillRect(x - 2, y - 1, 5, 4); c.fillRect(x - 1, y + 3, 3, 1);
    }
    const x = r.wx - r.cam;
    // The leap meter while you wind up.
    if (r.on >= 0 && r.held && r.fresh) {
      c.fillStyle = "rgba(0,0,0,.4)"; c.fillRect(x - 22, r.y - 36, 6, 30);
      c.fillStyle = r.charge > .85 ? "#ffd28a" : "#9be59b"; c.fillRect(x - 21, r.y - 7 - Math.round(28 * r.charge), 4, Math.round(28 * r.charge));
      c.strokeStyle = "rgba(255,255,255,.8)"; c.lineWidth = 1; c.beginPath();
      c.moveTo(x + 6, r.y - 14); c.lineTo(x + 6 + Math.cos(MG_LEAP.ang) * (10 + 14 * r.charge), r.y - 14 - Math.sin(MG_LEAP.ang) * (10 + 14 * r.charge)); c.stroke();
    }
    mgAnimal(c, r, x, r.y + 1, ["walk", "idle"], { frame: r.on >= 0 ? (r.held ? 0 : r.phase * 4) : 1, scale: .85 });
  },
};

// The newer games' levels: built from a seed, so each is the same every time. Every one
// is checked to be finishable at the lowest stats.
Object.assign(MG_LEVELS, {
  slide: [
    { name: "Muddy Creek", bpm: 118, song: 2, items: (k) => mgSlideLevel(k, 11, 60, 6, 2.5, 1.5, .2, .6) },
    { name: "Mudslide Mountain", bpm: 132, song: 3, items: (k) => mgSlideLevel(k, 12, 84, 6, 2, 1.25, .4, .8) },
  ],
  leap: [
    { name: "Oak Woods", bpm: 100, song: 0, items: (k) => mgLeapLevel(k, 81, 40, 60, 95, .1, .45, 38, 28) },
    { name: "Redwood Heights", bpm: 116, song: 2, items: (k) => mgLeapLevel(k, 82, 50, 70, 110, .3, .7, 32, 22) },
  ],
  dig: [
    { name: "Garden Soil", bpm: 110, song: 5, items: (k) => mgDigLevel(k, 41, 140, 24, 17) },
    { name: "Rocky Ground", bpm: 124, song: 1, items: (k) => mgDigLevel(k, 42, 160, 20, 14) },
  ],
  nectar: [
    { name: "Spring Meadow", bpm: 104, song: 4, items: (k) => mgNectarLevel(k, 21, 150, 4, .1, .35, .05, .2, 0) },
    { name: "Wildflower Storm", bpm: 120, song: 6, items: (k) => mgNectarLevel(k, 22, 170, 4, .2, .5, .1, .3, .25) },
  ],
  plunge: [
    { name: "Pelican Bay", bpm: 108, song: 4, items: (k) => mgPlungeLevel(k, 61, 34, 6, 4, 3, .4, .7) },
    { name: "Kelp Coast", bpm: 120, song: 8, items: (k) => mgPlungeLevel(k, 62, 44, 6, 3.5, 2.5, .45, .85) },
  ],
  splash: [
    { name: "Dolphin Cove", bpm: 104, song: 6, items: (k) => mgSplashLevel(k, 71, 30, 6, 5, 4, .5, 1) },
    { name: "Whale Waters", bpm: 116, song: 8, items: (k) => mgSplashLevel(k, 72, 38, 6, 4.5, 3.5, .6, 1.2) },
  ],
  call: [
    { name: "Woodland Chat", bpm: 96, song: 0, items: (k) => mgCallLevel(k, 31, 15, 0, 4, 4, 10) },
    { name: "Night Chorus", bpm: 108, song: 7, items: (k) => mgCallLevel(k, 32, 17, 4, 9, 10, 17) },
  ],
  echo: [
    { name: "Bat Cave", bpm: 112, song: 1, items: (k) => mgEchoLevel(k, 51, 55, 6, 64, 50, 2.5, 1.75) },
    { name: "Deep Cavern", bpm: 126, song: 9, items: (k) => mgEchoLevel(k, 52, 75, 6, 56, 46, 2.25, 1.5) },
  ],
});

// ---- Feeder Rush: hop between the perches of a bird feeder --------------------------
// Seeds drop onto the three perches on the beat: be on the right perch when one lands.
// A hawk's shadow sweeps over one perch now and then; don't be on it when it dives.
const mgPerchX = (f) => MG_W / 2 + (f - 1) * 80;
const MG_PERCH_Y = 132;
// [beat, perch]. Seeds half a beat apart are on the same or the next perch, so even
// the slowest hopper can get there; hawks come where no seed is due for a beat.
function mgFeederLevel(k, seed, len, start, busy0, busy1, hawk0, hawk1) {
  const rnd = mgRand(seed), out = [], last = [-9, -9, -9];
  let prev = null;
  for (let b = start; b < len; b += .5) {
    const u = (b - start) / (len - start), onBeat = b % 1 === 0;
    if (rnd() >= (onBeat ? .6 + .3 * u : busy0 + (busy1 - busy0) * u)) continue;
    let f = Math.floor(rnd() * 3);
    if (prev && b - prev.beat < 1 && Math.abs(f - prev.f) > 1) f = 1;
    out.push({ type: "m_seed", good: true, pts: 1, wx: b * k, f, beat: b });
    last[f] = b; prev = { f, beat: b };
    if (b > start + 6 && rnd() < hawk0 + (hawk1 - hawk0) * u) {
      const free = [0, 1, 2].filter((g) => b + .5 - last[g] >= 1 && g !== f);
      if (free.length) { const g = free[Math.floor(rnd() * free.length)]; out.push({ type: "m_hawk", wx: (b + .5) * k, f: g, beat: b + .5 }); }
    }
  }
  return out.filter((o) => !o.good || !out.some((h) => !h.good && h.f === o.f && Math.abs(h.beat - o.beat) < 1));
}

MG_MORE.feeder = {
  misses: true,
  why: { hawk: "Eek, a hawk!", missed: "Three seeds dropped!" },
  init(r) { r.f = 1; r.ax = 0; r.y = MG_PERCH_Y; r.x = mgPerchX(1); },
  press(r, x) { r.f = x < MG_W / 2 - 40 ? 0 : x > MG_W / 2 + 40 ? 2 : 1; },
  step(r, dt) {
    // r.ax is how far you are from the middle perch; hopping gets quicker with Hop.
    const hop = 520 * (1 + (r.st.agility - 1) * .12), want = (r.f - 1) * 80;
    r.ax += mgClamp(want - r.ax, -hop * dt, hop * dt);
    r.x = MG_W / 2 + r.ax;
    for (const o of r.things) {
      if (o.wx > r.dist) break;
      if (o.gone || o.missed) continue;
      const near = Math.abs(r.ax - (o.f - 1) * 80);
      if (!o.good) { o.gone = true; if (near < 22) return "hawk"; continue; }
      if (near < 18) mgGot(r, o, mgPerchX(o.f), MG_PERCH_Y - 10);
      else {
        o.missed = true; r.missed++;
        r.fx.push({ kind: "text", x: mgPerchX(o.f), y: MG_PERCH_Y + 18, text: "Missed!", life: .8 });
        if (r.missed >= 3) return "missed";
      }
    }
  },
  draw(c, r) {
    mgSky(c, "#a8daf0", "#eef6e0");
    mgHills(c, r, 0, 168, 18, 90, "#9fcf9a");
    c.fillStyle = "#6aae6e"; c.fillRect(0, 176, MG_W, MG_H - 176);
    const mid = MG_W / 2, k = MG_SPEED.feeder * r.lvl.spb;
    // The feeder: a post, a little roof, a tray of seed and a long perch.
    c.fillStyle = "#7a5232"; c.fillRect(mid - 3, 60, 6, 120);
    c.fillStyle = "#b5523b"; c.beginPath(); c.moveTo(mid - 34, 66); c.lineTo(mid, 46); c.lineTo(mid + 34, 66); c.closePath(); c.fill();
    c.fillStyle = "#d8b07a"; c.fillRect(mid - 26, 66, 52, 22); c.fillStyle = "#a8744a"; c.fillRect(mid - 26, 84, 52, 4);
    c.fillStyle = "#c78a3e"; for (let i = 0; i < 9; i++) c.fillRect(mid - 22 + i * 5, 80 - (i % 2), 2, 2);
    c.fillStyle = "#8a5a35"; c.fillRect(mid - 110, MG_PERCH_Y, 220, 4); c.fillStyle = "#a8744a"; c.fillRect(mid - 110, MG_PERCH_Y, 220, 1);
    for (let f = 0; f < 3; f++) {
      const x = mgPerchX(f);
      c.fillStyle = "#6e4e30"; c.fillRect(x - 6, MG_PERCH_Y + 4, 12, 2);
      c.fillStyle = "rgba(0,0,0,.25)"; c.font = "bold 8px system-ui, sans-serif"; c.textAlign = "center"; c.fillText(String(f + 1), x, 192);
    }
    for (const o of r.things) {
      if (o.gone || o.missed) continue;
      const u = (o.wx - r.dist) / k;  // beats until it lands
      if (u > 2) break;
      const x = mgPerchX(o.f);
      if (o.good) {
        // A seed tumbling down onto its perch.
        const y = Math.round(MG_PERCH_Y - 4 - u * 46);
        c.fillStyle = "#6e4e30"; c.fillRect(x - 2, y - 3, 4, 5); c.fillStyle = "#e6c48a"; c.fillRect(x - 1, y - 2, 2, 2);
      } else {
        // The hawk's shadow sweeps in and darkens the perch, then it swoops.
        const a = mgClamp(1 - u / 2, 0, 1);
        c.fillStyle = `rgba(30,30,50,${(.15 + .35 * a).toFixed(2)})`;
        c.beginPath(); c.ellipse(x, MG_PERCH_Y + 6, 10 + a * 18, 3 + a * 3, 0, 0, Math.PI * 2); c.fill();
        const hy = Math.round(20 + a * (MG_PERCH_Y - 40)), wing = Math.round(12 + Math.sin(r.phase * 10) * 3);
        c.fillStyle = "#5b4636"; c.fillRect(x - 3, hy - 3, 6, 8);
        c.fillRect(x - wing, hy - 2, wing - 3, 3); c.fillRect(x + 3, hy - 2, wing - 3, 3);
        c.fillStyle = "#f2c14e"; c.fillRect(x - 1, hy + 5, 2, 2);
        c.fillStyle = "rgba(230,60,60,.9)"; c.font = "bold 10px system-ui, sans-serif"; c.textAlign = "center"; c.fillText("!", x, MG_PERCH_Y - 26);
      }
    }
    mgAnimal(c, r, r.x, MG_PERCH_Y + 1, ["idle", "fly"], { frame: Math.abs(r.ax - (r.f - 1) * 80) > 2 ? r.phase * 14 : 0, still: true, flip: r.f >= 1 });
  },
};

// ---- School Swim: lead a little school of fish -----------------------------------
// Hold to squeeze the school tight and slip through gaps in the rocks; let go and it
// spreads into two bunches that let a hungry pike swim right through the middle.
const MG_SCHOOL_Y = 110;
// The two bunches: how far each is from the middle, and how tall each is.
const mgSchoolOff = (r) => 3 + 29 * r.s;
const mgSchoolHalf = (r) => 5 + r.st.size * .5;
function mgSchoolLevel(k, seed, n, start, gap0, gap1) {
  const rnd = mgRand(seed), out = [], c = MG_SCHOOL_Y;
  let b = start, was = null;
  for (let i = 0; i < n; i++) {
    const u = i / (n - 1), kind = rnd() < .5 ? "rocks" : "pike";
    b += kind === was ? Math.max(1, gap1 - .5) : gap0 + (gap1 - gap0) * u;
    const wx = b * k;
    if (kind === "rocks") {
      out.push({ type: "m_rocks", wx, w: 22 });
      out.push({ type: "m_plankton", good: true, pts: 1, wx: wx - 26, y: c, w: 8 });
    } else {
      out.push({ type: "m_pike", wx, w: 26 });
      const y = rnd() < .5 ? c - 32 : c + 32;
      out.push({ type: "m_plankton", good: true, pts: 1, wx: wx - 24, y, w: 8 }, { type: "m_plankton", good: true, pts: 1, wx: wx + 24, y: 2 * c - y, w: 8 });
    }
    was = kind;
  }
  return out;
}

MG_MORE.school = {
  why: { rock: "Bonk! Squeeze tighter", pike: "The pike got close! Spread out" },
  init(r) { r.s = 1; r.x = 92; r.y = MG_SCHOOL_Y; },
  press() {},
  step(r, dt) {
    const rate = 1 / (.28 - (r.st.agility - 1) * .03);
    r.s = mgClamp(r.s + (r.held ? -rate : rate) * dt, 0, 1);
    const off = mgSchoolOff(r), half = mgSchoolHalf(r), c = MG_SCHOOL_Y;
    const bands = [[c - off - half, c - off + half], [c + off - half, c + off + half]];
    for (const o of r.things) {
      if (o.gone) continue;
      const dx = o.wx - r.dist;
      if (dx > 40) break;
      if (Math.abs(dx) > o.w / 2 + 8) continue;
      if (o.type === "m_rocks" && bands.some(([a, b]) => a < c - 14 || b > c + 14)) return "rock";
      if (o.type === "m_pike" && bands.some(([a, b]) => b > c - 12 && a < c + 12)) return "pike";
      if (o.good && bands.some(([a, b]) => o.y > a - 4 && o.y < b + 4)) mgGot(r, o, r.x + dx, o.y);
    }
  },
  draw(c, r) {
    const w = c.createLinearGradient(0, 0, 0, MG_H);
    w.addColorStop(0, "#5fb4d6"); w.addColorStop(1, "#1d5d86");
    c.fillStyle = w; c.fillRect(0, 0, MG_W, MG_H);
    c.fillStyle = "rgba(255,255,255,.07)";
    for (let i = 0; i < 4; i++) { const x = (i * 90 - mgScroll(r, .2, 360) + 360) % 360 - 20; c.beginPath(); c.moveTo(x, 0); c.lineTo(x + 18, 0); c.lineTo(x + 50, MG_H); c.lineTo(x + 26, MG_H); c.fill(); }
    c.fillStyle = "#d9c18a"; c.fillRect(0, 186, MG_W, 14);
    c.fillStyle = "#3f8d58";
    for (let x = -mgScroll(r, 1, 34); x < MG_W + 34; x += 34) for (let k = 0; k < 18; k += 2) c.fillRect(x + Math.round(Math.sin(r.phase * 2 + k * .4 + x) * 2), 186 - k, 2, 2);
    const cy = MG_SCHOOL_Y;
    for (const o of r.things) {
      if (o.gone) continue;
      const x = Math.round(o.wx - r.dist + r.x);
      if (x < -40 || x > MG_W + 40) continue;
      if (o.type === "m_rocks") {
        // Rocks from the top and the bottom, with a narrow gap in the middle.
        c.fillStyle = "#6e7380"; c.fillRect(x - 11, 0, 22, cy - 14); c.fillRect(x - 11, cy + 14, 22, MG_H - cy - 14);
        c.fillStyle = "#8a8f9e"; c.fillRect(x - 11, 0, 5, cy - 14); c.fillRect(x - 11, cy + 14, 5, MG_H - cy - 14);
        c.fillStyle = "#3f8d58"; c.fillRect(x - 8, cy - 16, 6, 2); c.fillRect(x + 1, cy + 14, 7, 2);
      } else if (o.type === "m_pike") {
        // A long hungry pike swimming at you through the middle.
        const y = cy + Math.round(Math.sin(r.phase * 3 + o.wx) * 1.5);
        c.fillStyle = "#6b8a4a"; c.fillRect(x - 13, y - 4, 26, 8); c.fillRect(x + 11, y - 6, 5, 12);
        c.fillStyle = "#a8c47a"; c.fillRect(x - 11, y + 1, 20, 2);
        c.fillStyle = "#fff"; c.fillRect(x - 9, y - 3, 3, 3); c.fillStyle = "#222"; c.fillRect(x - 9, y - 2, 2, 2);
        c.fillStyle = "#e6e6e6"; c.fillRect(x - 14, y + 1, 4, 1);
      } else {
        // A little cloud of plankton.
        c.fillStyle = "rgba(200,240,170,.85)";
        for (let i = 0; i < 6; i++) c.fillRect(x - 4 + ((i * 5) % 9), o.y - 4 + ((i * 7) % 9), 2, 2);
      }
    }
    // Your school: three of you in each bunch, wiggling.
    const off = mgSchoolOff(r);
    for (const [dy, dx, k] of [[-off - 4, 6, 0], [-off + 3, -4, 1], [-off - 1, -14, 2], [off - 3, 2, 3], [off + 4, -9, 4], [off, 12, 5]])
      mgAnimal(c, r, r.x + dx + Math.round(Math.sin(r.phase * 6 + k) * 1.5), cy + dy + 5, ["swim", "idle"], { scale: .45, frame: r.phase * 8 + k, still: true });
  },
};

// ---- Freeze!: sneak up while the fox looks away ------------------------------------
// Hold to sneak along the path, and let go to freeze. The fox perks its ears a beat
// before it turns round; if it sees you moving, it's over. Reach your den before dark.
// [the beats it looks from and to]: a walk, the warning beat, then a look.
function mgFreezeLevel(k, seed, looks, start, walk0, walk1, look0, look1, fakes) {
  const rnd = mgRand(seed), out = [];
  let b = start, walked = start;
  for (let i = 0; i < looks; i++) {
    const u = i / (looks - 1), walk = Math.round((walk0 + (walk1 - walk0) * u + rnd() * 1.5) * 2) / 2;
    const look = Math.round((look0 + (look1 - look0) * u + rnd()) * 2) / 2;
    if (fakes && i > 2 && rnd() < fakes) out.push({ type: "m_twitch", wx: 0, beat: b + Math.max(1, walk - 2) });
    b += walk; walked += walk;
    out.push({ type: "m_look", wx: 0, b0: b, b1: b + look });
    b += look;
  }
  // The den is a little short of where you'd get walking every free beat, and clover
  // grows along the way.
  const spb = k / MG_SPEED.freeze, den = (walked - 1.5) * k;
  for (let x = k * 2; x < den - k; x += k * .75) out.push({ type: "m_clover", good: true, pts: 1, wx: x, w: 8 });
  out.push({ type: "m_den", wx: den, w: 20, dark: b + 3, spb });
  return out;
}
const mgFreezeGrace = (r) => .1 + (r.st.agility - 1) * .03;  // seconds to stop when it turns

MG_MORE.freeze = {
  ownDist: true,
  why: { seen: "Spotted! Freeze sooner", dark: "It got dark. Keep moving!" },
  init(r) {
    r.x = 70; r.y = 160; r.moving = false;
    r.looks = r.things.filter((o) => o.type === "m_look");
    r.den = r.things.find((o) => o.type === "m_den"); r.len = r.den.wx;
  },
  press() {},
  step(r, dt) {
    r.moving = r.held && r.fresh;
    if (r.moving) r.dist = Math.min(r.len, r.dist + MG_SPEED.freeze * dt);
    const beat = r.t / r.lvl.spb, grace = mgFreezeGrace(r) / r.lvl.spb;
    if (r.moving && r.looks.some((o) => beat >= o.b0 + grace && beat < o.b1)) return "seen";
    for (const o of r.things) {
      if (o.wx > r.dist) break;
      if (o.good && !o.gone) mgGot(r, o, r.x, r.y - 20);
    }
    if (r.dist < r.len && beat > r.den.dark) return "dark";
  },
  draw(c, r) {
    const beat = r.t / r.lvl.spb, dusk = mgClamp(beat / r.den.dark, 0, 1);
    mgSky(c, dusk < .7 ? "#9ad3ee" : "#e8a070", dusk < .7 ? "#e4f4e0" : "#f6d6a8");
    mgHills(c, r, .1, 130, 22, 80, "#8fb9a8");
    c.fillStyle = "#6aae6e"; c.fillRect(0, 150, MG_W, MG_H - 150);
    c.fillStyle = "#c79a64"; c.fillRect(0, 160, MG_W, 16);
    c.fillStyle = "#a87c4c"; for (let x = -mgScroll(r, 1, 18); x < MG_W; x += 18) c.fillRect(x, 166, 3, 1);
    c.fillStyle = "#3f8d58"; for (let x = -mgScroll(r, 1, 12); x < MG_W; x += 12) { c.fillRect(x, 156, 1, 3); c.fillRect(x + 5, 178, 1, 3); }
    for (const o of r.things) {
      const x = Math.round(o.wx - r.dist + r.x);
      if (o.wx === 0 || x < -30 || x > MG_W + 30 || o.gone) continue;
      if (o.type === "m_clover") {
        c.fillStyle = "#3f9d48"; c.fillRect(x - 3, 152, 3, 3); c.fillRect(x, 152, 3, 3); c.fillRect(x - 1, 149, 3, 3); c.fillRect(x, 155, 1, 4);
      } else if (o.type === "m_den") {
        c.fillStyle = "#7a5a40"; c.beginPath(); c.arc(x, 170, 18, Math.PI, 0); c.fill();
        c.fillStyle = "#2a1c12"; c.beginPath(); c.arc(x, 172, 10, Math.PI, 0); c.fill();
      }
    }
    // Darkness creeping in.
    if (dusk > .6) { c.fillStyle = `rgba(20,20,60,${((dusk - .6) * .9).toFixed(2)})`; c.fillRect(0, 0, MG_W, MG_H); }
    // The fox on its rock at the right: back turned, ears up as a warning, or looking.
    const look = r.looks.find((o) => beat >= o.b0 && beat < o.b1), warn = r.looks.find((o) => beat >= o.b0 - 1 && beat < o.b0);
    const twitch = r.things.some((o) => o.type === "m_twitch" && beat >= o.beat && beat < o.beat + .5);
    const fx = MG_W - 50, fy = 110;
    c.fillStyle = "#8a8f9e"; c.fillRect(fx - 20, fy + 14, 40, 26); c.fillStyle = "#9fa4b2"; c.fillRect(fx - 16, fy + 10, 32, 6);
    c.fillStyle = "#d9733a"; c.fillRect(fx - 9, fy - 6, 18, 18); c.fillRect(fx + (look ? -14 : 6), fy - 14, 10, 10);
    c.fillStyle = "#f4e6d4"; c.fillRect(fx + (look ? -14 : 10), fy - 7, 4, 3); c.fillRect(fx - 12, fy + 8, 8, 5);
    const up = look || warn || twitch ? 4 : 1;
    c.fillStyle = "#b85a28"; c.fillRect(fx + (look ? -13 : 7), fy - 14 - up, 3, up); c.fillRect(fx + (look ? -8 : 12), fy - 14 - up, 3, up);
    if (look) { c.fillStyle = "#222"; c.fillRect(fx - 12, fy - 11, 2, 2); }
    c.fillStyle = "#d9733a"; c.fillRect(fx + 8, fy + 4, 12, 5); c.fillStyle = "#f4e6d4"; c.fillRect(fx + 17, fy + 4, 3, 5);
    c.font = "bold 12px system-ui, sans-serif"; c.textAlign = "center";
    if (look) { c.fillStyle = "rgba(255,240,200,.25)"; c.beginPath(); c.moveTo(fx - 12, fy - 9); c.lineTo(0, 120); c.lineTo(0, 190); c.closePath(); c.fill(); }
    else if (warn) { c.fillStyle = "#e84a4a"; c.fillText("!", fx, fy - 26); }
    else if (twitch) { c.fillStyle = "#fff"; c.fillText("?", fx, fy - 26); }
    c.font = "bold 9px system-ui, sans-serif"; c.fillStyle = "#fff";
    c.fillText(look ? "Freeze!" : warn ? "Get ready to stop…" : r.moving ? "" : "Hold to sneak", MG_W / 2, 64);
    mgAnimal(c, r, r.x, 170, r.moving ? ["walk", "idle"] : ["idle", "walk"], { frame: r.moving ? r.dist / 6 : 0, still: !r.moving });
  },
};

MG_SPEED.feeder = 60; MG_SPEED.school = 70; MG_SPEED.freeze = 55;
Object.assign(MG_LEVELS, {
  feeder: [
    { name: "Backyard Feeder", bpm: 100, song: 0, items: (k) => mgFeederLevel(k, 91, 60, 4, .1, .35, .08, .22) },
    { name: "Busy Morning", bpm: 112, song: 5, items: (k) => mgFeederLevel(k, 92, 76, 4, .2, .5, .12, .3) },
  ],
  school: [
    { name: "Reed Bed", bpm: 100, song: 4, items: (k) => mgSchoolLevel(k, 93, 34, 4, 3, 1.75) },
    { name: "Rocky Reef", bpm: 112, song: 6, items: (k) => mgSchoolLevel(k, 94, 48, 4, 2.5, 1.75) },
  ],
  freeze: [
    { name: "Meadow Sneak", bpm: 96, song: 2, items: (k) => mgFreezeLevel(k, 95, 12, 3, 4, 2.5, 1.5, 2, 0) },
    { name: "Foxy Woods", bpm: 108, song: 3, items: (k) => mgFreezeLevel(k, 96, 16, 3, 3.5, 1.5, 1.5, 2.5, .4) },
  ],
});
