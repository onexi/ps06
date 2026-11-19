# IC Food App

The first working backend connects a packaged-food barcode to an ingredient label and the local IC reference database. Python 3.10+ is required; no external dependencies or API key are needed.

The barcode workflow calls `fetch_product.py` to validate and retrieve a product, then `assess_product.py` to coordinate label parsing and IC matching. `lookup_barcode.py` is the command-line entry point.

## Try it

Run these commands from this folder:

```sh
python3 scripts/build_ic_database.py
python3 scripts/lookup_barcode.py --label "Ingredients: sauce (tomatoes, MSG, salt), natural flavors"
python3 scripts/lookup_barcode.py --barcode 3274080005003
```

Barcode requests default to Open Food Facts' staging service for development. For actual grocery products use `--production`:

```sh
python3 scripts/lookup_barcode.py --barcode 3017620422003 --production
```

Before production use, set `IC_APP_USER_AGENT` to `ICFoodApp/0.1 (your actual contact email or project URL)` and complete the provider's usage form. Do not commit personal contact details. The lookup performs a single request, has a 15 second timeout, and does not automatically retry. Keep usage within the provider's current limits. Nothing is uploaded or written back to Open Food Facts.

## Results

Outputs include the original label, candidate ingredient names, parsing warnings, source attribution, retrieval time, and the IC checker results. Always confirm the product and ingredients against the package: product records may be outdated or incomplete. Missing products and unavailable English labels produce incomplete assessments. Network failures produce an explicit error and unsuccessful exit status, never a reassuring assessment.

The parser splits English labels on commas, semicolons, grouping brackets, and newlines. It retains compound names and subingredients. It does not translate labels, infer missing ingredients, understand every label grammar, or treat unknown ingredients as safe. Amount qualifiers and alternatives may remain unresolved. It excludes trailing “may contain” cross-contact statements from ingredient matching. Full allergen checking is outside this app's scope. Language selection relies on provider metadata: even a field labeled English can contain another language or nutrition text. Verify the original label; unsupported text remains unresolved.

The parser recognizes common wording in parenthetical ingredient lists, such as `with oat bran` or `treated with ascorbic acid and citric acid to preserve color`. It keeps the actual listed ingredients and preserves the original label.

The checker uses exact names and aliases first. For unresolved ingredient names, it accepts close spelling matches and shared whole-word phrases at a default similarity threshold of 50. If any close candidate is listed as a potential irritant, it uses that candidate. The ingredient result shows the applied reference and similarity score. Use `--match-threshold 100` for exact matching.

Ingredient results record disclosed percentages or weights per serving, label order and percentage limits, or an unknown quantity. The local IC references currently give qualitative amount guidance. To have the local Ollama model explain the evidence, add `--explain-quantities` to a barcode or label command.

The product reads **Bladder unfriendly** if any ingredient is flagged as an irritant. It reads **Try it and tell us how you feel** if no irritants are flagged and the checker finds a database match, an ambiguous ingredient, or a label warning. **Bladder friendly** means a usable ingredient list had no matches in the local database. Personal tolerance can vary.

There is no camera scanner or graphical interface yet. This command-line workflow establishes the backend connection that those will call. Barcode input currently accepts GTIN-8, UPC-A, EAN-13, and GTIN-14 with checksum validation; UPC-E expansion is not supported.

### Planned ingredient photo fallback

When a barcode lookup returns no usable ingredient list, offer to photograph the ingredient panel on the package. A dedicated function will read the photo and show the extracted text for the user to review and correct before sending it to the existing ingredient checker. Keep manual entry available if the photo is unreadable.

### Planned offline barcode lookup

- Create a separate local SQLite product database keyed by barcode. Save successful Open Food Facts lookups with the product name, original ingredient label, source, and retrieval date.
- Check saved records first and use Open Food Facts for a local miss when online. Add an `--offline` option to test lookups without network access.
- If an offline lookup has no usable saved label, offer manual entry or the planned ingredient photo fallback.
- For broader offline coverage later, preload a subset of the [Open Food Facts dataset export](https://openfoodfacts.github.io/openfoodfacts-python/usage/#using-the-dataset).

## Food diary and ingredient recommendations

Log how you felt after eating with `tolerated`, `symptoms`, or `unsure`. List each known ingredient with its own `--ingredient` flag so that the entry can contribute to later ingredient checks.

```sh
python3 scripts/food_diary.py --food "Pasta with sauce" --outcome symptoms \
  --ingredient tomatoes --ingredient pasta --portion "1 bowl" --notes "Symptoms later that evening"
python3 scripts/recommend_ingredient.py tomatoes
```

Add `--ate-at "2026-11-08T12:30:00-05:00"` for a past meal. If omitted, the command records the current time. Diary entries live in `database/private/food_diary.sqlite3`, a separate, single-user database excluded from Git.

Start Ollama with the local `gemma3:1b` model available (`ollama pull gemma3:1b` if needed). Recommendations use the local model to select a category supported by the matching diary outcomes and the IC reference entry. Only the proposed ingredient, aggregate outcome counts, and the matching IC guidance go to Ollama on this computer. Free-text diary notes stay in SQLite.

Diary matching uses exact ingredient names after case and whitespace normalization. Use the same ingredient name when logging and checking. The result shows the diary counts and source link where available. Whole-meal reports can suggest patterns, but cannot identify the cause of symptoms or predict your next reaction.

## Data and attribution

- [IC database guide](database/README.md): NIDDK and IC Network references, matching rules, and update instructions.
- Product data: [Open Food Facts](https://world.openfoodfacts.org), licensed under [ODbL](https://opendatacommons.org/licenses/odbl/1-0/). Individual contents have separate database-content licensing. No product images are downloaded or cached.
- [API documentation and usage requirements](https://openfoodfacts.github.io/openfoodfacts-server/api/). The integration uses the documented v3.6 product endpoint, staging authentication, and a custom User-Agent.

## Verify

```sh
python3 -m unittest discover -s tests -v
```

Tests use controlled service responses so they work without internet access. Live product coverage and camera behavior require separate real-device trials.

## Local photo upload interface

Start the connected website from this project folder:

```bash
python3 scripts/serve_ui.py
```

Open http://127.0.0.1:8765 and drop a JPG, PNG or WebP photo of a single barcode (up to 20 MB). The app reads it with macOS Vision, retrieves the live Open Food Facts record, and displays the existing IC checker's product status and ingredient results. Image processing stays on the Mac. The detected barcode is sent to Open Food Facts. The uploaded image is removed after barcode reading.

The sample buttons show example results. Uploaded photos run through the live checker. Leave the Terminal server running while using the website.
