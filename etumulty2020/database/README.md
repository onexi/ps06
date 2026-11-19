# IC reference database

This database supports ingredient checking for the barcode app. It stores source-linked IC dietary guidance. Personal tolerance is tracked separately in the food diary.

## Files

- `ic_seed.json`: editable source of truth for reference entries, source details, exact matching terms, and ambiguous terms.
- `ingredient_catalog.json`: names, aliases, definitions, and source links for ingredient identity. Its entries are stored separately from IC evidence in SQLite.
- `schema.sql`: database structure and integrity constraints.
- `ic_reference.sqlite3`: generated SQLite database. Rebuild it after changing the seed; rebuilding replaces this generated file. Do not store user data here.

No external Python packages or API keys are required. From the project folder:

```sh
python3 scripts/build_ic_database.py
python3 scripts/check_ingredients.py "tomatoes" "MSG" "natural flavors" "salt"
python3 -m unittest discover -s tests -v
```

## Source and review

Initial source: [NIDDK dietary guidance](https://www.niddk.nih.gov/health-information/urologic-diseases/interstitial-cystitis-bladder-pain-syndrome/eating-diet-nutrition), last reviewed by its publisher in July 2024, checked for this project on November 10, 2026. Entries paraphrase the guide's examples of possible triggers for some people. NIDDK also discusses hydration, a food diary for identifying personal triggers, and support from a registered dietitian.

The database covers every trigger category and named example on that NIDDK page. The broad entries for high-acid foods, spicy foods, and artificial sweeteners remain reference-only. The checker needs a source that specifically names a food or additive before it can match it.

The [Interstitial Cystitis Network's 2025 IC Food List](https://www.icnetwork.org/wp-content/uploads/2025/01/2025foodlist.pdf) adds specific foods, preparations, spices, and additives. Each ICN entry cites the page in the supplied PDF, counting the cover as page 1. The checker keeps preparation-specific terms such as hot curry powder and raw bulb onions as exact matches. It leaves citric acid reference-only because the source distinguishes by amount and use, and records stevia and the branded Truvia product separately because the guide assigns them different columns.

## Irritation ratings

Each reference stores a rating, its source, and a short explanation. NIDDK supplies general guidance about possible triggers without severity levels. ICN supplies more specific categories and page references where available, including when an item also has a separate NIDDK reference.

| Rating | Meaning |
| --- | --- |
| `most_bothersome` | The item is named in ICN's Most Bothersome Foods table. |
| `foods_to_avoid` | The specific form appears in ICN's Foods to Avoid column. |
| `worth_trying_cautiously` | The specific form appears in ICN's Foods Worth Trying column. |
| `usually_bladder_friendly` | The specific form appears in ICN's Usually Bladder Friendly column. |
| `context_dependent` | The source distinguishes by variety, preparation, amount, or use. |
| `unrated_potential_concern` | The reference identifies a possible concern without a recorded rating. |

These are source categories rather than a measured severity scale. The checker returns the rating alongside the existing match status and a plain-language `display_status`. Context-dependent entries can specify what matters, such as amount or preparation. When a source gives qualitative guidance only, such as small quantities of sea salt, the checker reports that wording and leaves the numeric limit unspecified. The recommendation workflow receives the rating alongside the user's separate diary evidence.

## Matching contract

The checker normalizes already-separated ingredient names and checks exact names and aliases first. It then uses plausible spelling and whole-word phrase matches at a default similarity threshold of 50. An approximate result includes an `applied_match` with the reference name and similarity score. If multiple candidates qualify, a potential irritant takes precedence. Use a threshold of 100 for exact matching.

The product shows **Bladder unfriendly** when an ingredient matches a reference rated Most bothersome, Foods to avoid, or Potential concern. With no irritants flagged, it shows **Try it and tell us how you feel** if there is any match, ambiguous ingredient, or label warning. A usable list with no matches shows **Bladder friendly**. The `assessment_incomplete` field still records evidence gaps for callers. An empty list shows **No ingredients to assess**.

When the catalog recognizes a term, the checker includes an `identity` object with its name, category, description, and source. The separate `ic_evidence_status` field is `reference_match`, `similar_reference_match`, `context_only`, or `unavailable` based on the curated IC references. For example, Reb M is identified as a sweetener with IC evidence unavailable in this database. Sucralose shows the guide's context-only note for the branded Splenda entry. Identity lookups do not change IC match status or assessment completeness.

## Updating the database

1. Add or update a source with its URL, publisher review date or edition, and project access date.
2. Add a reference with a brief supported summary, mapping limitations, and a source-linked rating and explanation.
3. Add only unambiguous, source-supported exact terms. Keep unsupported mappings disabled by leaving `match_terms` empty.
4. Add representative positive and negative checks, rebuild, and run tests.

The reference database has no product records, user accounts, or symptom histories. Barcode lookup and a conservative label parser now connect to the checker through `scripts/lookup_barcode.py`; see the project README for usage. Product records are retrieved on demand and are not persisted in this reference database.

## Expanded ICN coverage

On November 18, 2026, seed version 10 expanded the database from 83 to 391 references. The 308 additions include 169 usually-friendly entries, 101 worth-trying entries, 31 foods-to-avoid entries, and seven entries with amount or context conditions. Entries cover beverages, grains, spices, selected supplement forms, snacks, oils, dairy, proteins, fruits and vegetables from the 2025 ICN tables. Each new entry preserves its PDF page and form-specific guidance. Compound dishes and prepared snacks require exact names, so their ratings do not become close matches for a bare spice.

Quantity-dependent salt varieties, ketchup, strawberries, cantaloupe, tahini and orange extract retain context-dependent ratings. The list gives conflicting guidance for cantaloupe on pages 12 and 13, which is recorded in its entry. The supplement table's folic acid tablets and vitamin B6 supplements retain those explicit forms. The list supplies no numeric irritation thresholds.

Coverage is a curated expansion. Broad recipe descriptions, unspecified brands and ambiguous preparations still require review. Existing NIDDK references remain in use.
