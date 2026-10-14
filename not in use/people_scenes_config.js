// Configuration for people.html's number-line scrolly.
//
// Everything that describes *what happens in the story* lives here, kept
// separate from the engine (physics, canvas drawing, scroll handling) in
// people_numberline_template.html. Loaded as a plain global via a <script>
// tag before that engine script runs.
//
// CATEGORIES: one entry per Wikidata dataset the scrolly draws from --
// just the display metadata (dot color, legend-style label). Which scenes
// introduce a category, and in what order, is entirely described by SCENES
// below, not here.
//
// SCENES: one entry per scroll step, in order. Each scene has:
//   domain  - the axis's [lo, hi] range for this scene (a zoom happens
//             whenever this differs from the previous scene's domain).
//   caption - { title, subtitle } shown while this scene is active.
//   reveal  - an array of what becomes visible this scene, one entry per
//             category touched (usually just one, but a scene can reveal
//             from more than one category at once, and a category can be
//             added to across more than one scene -- e.g. one continent's
//             countries, then another's). Each entry:
//               category - which CATEGORIES key this entry's dots belong to
//               anchors  - specific item QIDs to reveal now, each with a
//                          permanent name+value label
//               include  - specific item QIDs to reveal now, hover-only
//                          (no permanent label)
//               all      - true: reveal every remaining item in the
//                          category that no scene (this one or an earlier
//                          one) has already named via `anchors`/`include`,
//                          hover-only. Only meaningful with neither
//                          `anchors` nor `include` also given -- combining
//                          them would be redundant, since the point of
//                          `all` is to catch everything *not* individually
//                          named.
//   search  - (optional, true) shows a search box (instead of, or in
//             addition to, `reveal`) that lets the viewer type to find any
//             item in the whole dataset and add it themselves, labeled,
//             regardless of category or scene. Only one scene needs this;
//             it doesn't need its own `reveal` entries.
//
// Visibility is sticky: once any scene names an item (`anchors`, `include`,
// or a bare `all` sweep), it stays visible forever, even once later scenes
// move on to a different category. The permanent label is NOT sticky,
// though -- every scene that touches the same category re-decides it from
// scratch, so an item only keeps its label while the *most recent*
// category-touching scene actually lists it under `anchors`. That means
// demoting an old anchor needs no special handling: a later scene for the
// same category just doesn't re-list it (whether or not it lists that item
// under `include`), and its label lapses on its own.

const CATEGORIES = {
  population: { color: "#e03131", label: "Population" },
  languages: { color: "#0c8599", label: "Language speakers" },
  followers: { color: "#2a78d6", label: "Social media followers" },
  visitors: { color: "#2f9e44", label: "Visitors per year" },
  venues: { color: "#9c36b5", label: "Venue capacity" },
  subscribers: { color: "#f08c00", label: "Subscribers" },
  vaccinations: { color: "#0ca678", label: "Vaccinations" },
  viewers: { color: "#c2255c", label: "Views/listens" },
  deaths: { color: "#495057", label: "Deaths" },
  registered_users: { color: "#5c7cfa", label: "Registered users" },
};

const SCENES = [
  {
    domain: [300e6, 400e6],
    caption: { title: "Population of Nations", subtitle: "" },
    reveal: [{ category: "population", anchors: ["Q30"] }], // United States
  },
  {
    domain: [0, 400e6],
    caption: { title: "+ Mexico and Canada", subtitle: "" },
    reveal: [{ category: "population", anchors: ["Q30", "Q96", "Q16"] }],
  },
  {
    domain: [0, 400e6],
    caption: { title: "The Americas", subtitle: "largest (United States), smallest (Sint Maarten), and Brazil — the rest are unlabeled" },
    // Only the largest and smallest countries in the Americas (by
    // population), plus Brazil, keep permanent labels -- Mexico and Canada,
    // already shown, simply aren't re-listed as anchors here, so their
    // labels lapse automatically.
    reveal: [
      {
        category: "population",
        anchors: ["Q30", "Q26273", "Q155"], // United States (largest), Sint Maarten (smallest), Brazil
        include: [
          "Q781", "Q414", "Q21203", "Q244", "Q242", "Q750", "Q298", "Q739", "Q800",
          "Q241", "Q25279", "Q784", "Q786", "Q736", "Q792", "Q769", "Q774", "Q734", "Q790",
          "Q783", "Q766", "Q811", "Q804", "Q733", "Q419", "Q763", "Q760", "Q757",
          "Q730", "Q778", "Q754", "Q77", "Q717", "Q223",
        ],
      },
    ],
  },
  {
    domain: [0, 400e6],
    caption: { title: "Africa", subtitle: "largest (Nigeria) and smallest (Seychelles) — the rest are unlabeled" },
    // Every African country not already shown -- only the largest (Nigeria)
    // and smallest (Seychelles) get permanent labels, plus the U.S. (kept by
    // re-listing it). Sint Maarten and Brazil, anchored in the previous
    // scene, simply aren't re-listed here, so their labels lapse
    // automatically.
    reveal: [
      {
        category: "population",
        anchors: ["Q30", "Q1033", "Q1042"], // United States, Nigeria (largest in Africa), Seychelles (smallest in Africa)
        include: [
          "Q262", "Q916", "Q962", "Q963", "Q965", "Q967", "Q1009", "Q1011", "Q929", "Q657",
          "Q970", "Q974", "Q977", "Q79", "Q983", "Q986", "Q1050", "Q115", "Q1000", "Q117",
          "Q1006", "Q1007", "Q1008", "Q114", "Q1013", "Q1014", "Q1016", "Q1019", "Q1020", "Q912",
          "Q1025", "Q1027", "Q1028", "Q1029", "Q1030", "Q1032", "Q971", "Q1037", "Q1039",
          "Q1041", "Q1044", "Q1045", "Q34754", "Q258", "Q958", "Q1049", "Q924", "Q1005",
          "Q945", "Q948", "Q1036", "Q953", "Q954",
        ],
      },
    ],
  },
  {
    domain: [0, 400e6],
    caption: { title: "Europe", subtitle: "largest (Russia) and smallest (Vatican City) — the rest are unlabeled" },
    // Every European country not already shown -- only the largest (Russia)
    // and smallest (Vatican City) get permanent labels. San Marino is
    // included here too (unlabeled) since it's no longer the anchor for
    // smallest now that Vatican City (which never got its own dedicated
    // scene) is included in this continent instead.
    reveal: [
      {
        category: "population",
        anchors: ["Q159", "Q237"], // Russia (largest in Europe), Vatican City (smallest in Europe)
        include: [
          "Q238", // San Marino
          "Q347", "Q235", "Q228", "Q189", "Q23681", "Q233", "Q236", "Q32", "Q229", "Q191",
          "Q1246", "Q221", "Q211", "Q215", "Q217", "Q222", "Q37", "Q225", "Q224", "Q27",
          "Q214", "Q20", "Q33", "Q35", "Q219", "Q403", "Q40", "Q184", "Q39", "Q28",
          "Q45", "Q41", "Q34", "Q213", "Q31", "Q55", "Q218", "Q36", "Q212", "Q29",
          "Q38", "Q145", "Q142", "Q183",
        ],
      },
    ],
  },
  {
    domain: [0, 400e6],
    caption: { title: "Australia", subtitle: "population — 27,614,411" },
    // Just Australia, labeled alone -- Russia and Vatican City aren't
    // re-listed here, so their labels lapse automatically.
    reveal: [{ category: "population", anchors: ["Q408"] }],
  },
  {
    domain: [0, 400e6],
    caption: {
      title: "Asia",
      subtitle: "largest of the rest (Indonesia) and smallest (Maldives) — 2 even bigger countries are still coming",
    },
    // Every Asian country except China and India, which get their own
    // scene right after this one -- only Indonesia (largest of these) and
    // the Maldives (smallest) get permanent labels.
    reveal: [
      {
        category: "population",
        anchors: ["Q252", "Q826"], // Indonesia, Maldives
        include: [
          "Q889", "Q399", "Q227", "Q398", "Q902", "Q917", "Q921", "Q424", "Q230", "Q794",
          "Q796", "Q801", "Q17", "Q810", "Q232", "Q817", "Q813", "Q819", "Q822", "Q833",
          "Q711", "Q836", "Q837", "Q423", "Q842", "Q843", "Q219060", "Q928", "Q846", "Q851",
          "Q334", "Q884", "Q854", "Q858", "Q863", "Q869", "Q574", "Q43", "Q874", "Q878",
          "Q265", "Q881", "Q805",
        ],
      },
    ],
  },
  {
    domain: [0, 1500e6],
    caption: { title: "China and India", subtitle: "the only 2 countries bigger than everything shown so far" },
    // The scale has to zoom out for these two -- everything else on screen
    // is under 400M, and these are both well over a billion.
    reveal: [{ category: "population", anchors: ["Q148", "Q668"] }],
  },
  {
    domain: [0, 1500e6],
    caption: { title: "Ariana Grande", subtitle: "most social media followers — 371,000,000" },
    reveal: [{ category: "followers", anchors: ["Q151892"] }],
  },
  {
    domain: [0, 1500e6],
    caption: { title: "+ Kendall Jenner and Miley Cyrus", subtitle: "2nd and 3rd most social media followers" },
    reveal: [{ category: "followers", anchors: ["Q151892", "Q1375057", "Q4235"] }],
  },
  {
    domain: [0, 1500e6],
    caption: { title: "Top 3 Languages", subtitle: "by number of speakers, writers, or signers" },
    // Fits the existing 0-1.5B domain (Mandarin, the largest, is 918M).
    reveal: [
      { category: "languages", anchors: ["Q9192", "Q1860", "Q13955"] }, // Mandarin, English, Arabic
    ],
  },
  {
    domain: [0, 1500e6],
    caption: { title: "Narendra Modi Stadium", subtitle: "largest stadium — 132,000 capacity" },
    // The largest *built, functioning* stadium in the data. Technically the
    // "maximum capacity" property's single biggest value belongs to the
    // Deutsches Stadion (400,000) -- a Nazi-era stadium that was never
    // finished or used -- so this uses the largest real one instead.
    reveal: [{ category: "venues", anchors: ["Q3531421"] }],
  },
  {
    domain: [0, 1500e6],
    caption: { title: "China Mobile", subtitle: "most subscribers of any company — 851,000,000" },
    reveal: [{ category: "subscribers", anchors: ["Q741618"] }],
  },
  {
    domain: [0, 1500e6],
    caption: { title: "The Black Death", subtitle: "75,000,000 deaths — the deadliest pandemic on record" },
    reveal: [{ category: "deaths", anchors: ["Q42005"] }],
  },
  {
    domain: [0, 1500e6],
    caption: { title: "mastodon.social", subtitle: "2,753,131 registered users — the largest Mastodon server" },
    reveal: [{ category: "registered_users", anchors: ["Q112059294"] }],
  },
  {
    domain: [0, 1500e6],
    caption: { title: "Your turn", subtitle: "search the 2,109 quantities of people records in Wikidata" },
    search: true,
    reveal: [],
  },
];
