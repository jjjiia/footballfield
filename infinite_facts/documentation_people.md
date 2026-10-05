# How the "Count of People" Dataset Was Built

A plain-language record of the process, for reference.

## Finding the full list of possible data types

- Wikidata organizes every type of fact as a "property" — think of a property
  as a category, like "population" or "elevation" or "mass." Each property is
  tagged internally with what kind of value it holds (plain text, a date, a
  link to another entry, a number, etc.).
- We asked Wikidata directly for the full list of number-type properties.
  Rather than guessing which properties might exist, we sent one direct
  request to Wikidata's own public database asking, essentially, "give me
  every single property whose value is a measurable quantity." This came
  back with **695** properties — genuinely all of them, not a sample.
  Wikidata also maintains a live, browsable version of this same list:
  <https://www.wikidata.org/wiki/Special:ListProperties/quantity>
- We cross-checked that count against a second, independent source — a
  separately maintained community report page on Wikidata that lists every
  property along with how often it's actually used. That gave a very similar
  number (679), confirming the first list was accurate; the tiny difference
  is just because Wikidata keeps growing slightly over time and that report
  page is a periodic snapshot rather than always up-to-the-second.
- Both sources also gave us how often each property is actually used — some
  are used millions of times (like population), others just a handful of
  times — which mattered later for deciding what was worth pursuing.
- This became the master shopping list: the complete official set of 695
  "quantity" properties Wikidata currently supports, obtained by directly
  querying Wikidata's own records for "everything tagged as a quantity," not
  a partial or guessed list.

## Building the "count of people" theme

- **Started broad, then focused.** The original idea was a page that chains
  through interesting numbers (like neal.fun-style sites). We first tried a
  general newsletter-scraping approach, then switched to Wikidata — a free,
  structured public database — as a much better source, since its facts
  already come with clean numbers and categories attached.
- **Manually reviewed the full list.** From the 695 quantity properties
  above, we manually reviewed all of them by hand (using a small review tool
  built for exactly that) to pick out which were actually interesting and
  usable — most were too obscure or scientific (like atomic properties) to
  be interesting.
- **Picked a clear theme.** Rather than mixing many unrelated types of facts
  together, we settled on one focused theme: raw counts of people —
  population, employees, voters, followers, disaster victims, and similar.
  This gave the project a coherent identity instead of a scattered grab-bag.
- **Built an automated fetching tool.** A script that pulls this data
  directly and repeatedly from Wikidata's public database, rather than doing
  it by hand.
- **Found and fixed real data problems along the way**, including:
  - Filtering out obscure/meaningless entries so the "biggest" results are
    actually recognizable (e.g., countries and cities, not random tiny
    villages).
  - Catching and removing placeholder "fake" numbers that Wikidata
    sometimes uses as filler.
  - Fixing cases where a property was scoped too narrowly and returned
    almost no results.
  - Handling the data source's rate limits so large pulls don't get cut off.
- **Built a visual tool to double-check the data.** A simple interactive
  page (dot plots per category) that let us actually see the numbers and
  confirm they looked right before trusting them.
- **Expanded where the first pass was too shallow.** For several categories,
  our first pull only grabbed the top 500 entries even though thousands more
  existed — we identified those cases and pulled deeper so the data isn't
  artificially cut short.

## End result

A verified dataset covering **42 different "count of people" facts**
(population, elections, organizations, disasters, venues, and more),
spanning tens of thousands of real, checked entries.
