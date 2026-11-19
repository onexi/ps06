CREATE TABLE IF NOT EXISTS food_entries (
    id INTEGER PRIMARY KEY,
    food TEXT NOT NULL,
    outcome TEXT NOT NULL CHECK(outcome IN ('tolerated', 'symptoms', 'unsure')),
    notes TEXT NOT NULL,
    portion TEXT NOT NULL,
    ate_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS food_entry_ingredients (
    entry_id INTEGER NOT NULL REFERENCES food_entries(id) ON DELETE CASCADE,
    ingredient TEXT NOT NULL,
    normalized_ingredient TEXT NOT NULL,
    PRIMARY KEY (entry_id, normalized_ingredient)
);

CREATE INDEX IF NOT EXISTS food_entry_ingredients_lookup
    ON food_entry_ingredients (normalized_ingredient, entry_id);

CREATE TABLE IF NOT EXISTS food_entry_products (
    entry_id INTEGER PRIMARY KEY REFERENCES food_entries(id) ON DELETE CASCADE,
    barcode TEXT NOT NULL
);
