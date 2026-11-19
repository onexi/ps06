PRAGMA foreign_keys = ON;
CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE sources (
 id TEXT PRIMARY KEY, organization TEXT NOT NULL, title TEXT NOT NULL,
 url TEXT NOT NULL, source_reviewed TEXT NOT NULL, accessed TEXT NOT NULL,
 evidence_type TEXT NOT NULL, notes TEXT NOT NULL
);
CREATE TABLE ic_references (
 id TEXT PRIMARY KEY, name TEXT NOT NULL,
 kind TEXT NOT NULL CHECK(kind IN ('ingredient','food_category')),
 classification TEXT NOT NULL CHECK(classification IN ('potential_concern', 'general_guidance')),
 summary TEXT NOT NULL, source_id TEXT NOT NULL REFERENCES sources(id),
 reviewed_on TEXT NOT NULL, review_status TEXT NOT NULL, mapping_note TEXT NOT NULL,
 irritation_rating TEXT NOT NULL CHECK(irritation_rating IN (
  'most_bothersome', 'foods_to_avoid', 'worth_trying_cautiously',
  'context_dependent', 'unrated_potential_concern', 'usually_bladder_friendly'
 )),
 rating_source_id TEXT NOT NULL REFERENCES sources(id),
 rating_basis TEXT NOT NULL,
 display_status TEXT
);
CREATE TABLE match_terms (
 term TEXT PRIMARY KEY, reference_id TEXT NOT NULL REFERENCES ic_references(id),
 match_method TEXT NOT NULL DEFAULT 'normalized_exact' CHECK(match_method='normalized_exact')
);
CREATE TABLE ambiguous_terms (term TEXT PRIMARY KEY);
CREATE TABLE ingredient_identities (
 id TEXT PRIMARY KEY, name TEXT NOT NULL, category TEXT NOT NULL,
 description TEXT NOT NULL, source_url TEXT NOT NULL
);
CREATE TABLE ingredient_identity_terms (
 term TEXT PRIMARY KEY, identity_id TEXT NOT NULL REFERENCES ingredient_identities(id)
);
