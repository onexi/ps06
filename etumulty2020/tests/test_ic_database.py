from contextlib import closing
import sys
import tempfile
from pathlib import Path
import sqlite3
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from build_ic_database import build
from check_ingredients import check

class ReferenceTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.path = build(Path(self.folder.name) / 'test.sqlite3')

    def tearDown(self):
        self.folder.cleanup()

    def test_alias_and_source(self):
        result = check(['  MSG ', 'Monosodium   glutamate'], self.path)
        self.assertTrue(result['concerns_found'])
        self.assertTrue(all(r['source_url'].startswith('https://www.niddk.nih.gov/') for r in result['ingredients']))

    def test_niddk_covers_named_triggers_and_preserves_broad_categories(self):
        with closing(sqlite3.connect(self.path)) as db:
            niddk_ids = {row[0] for row in db.execute(
                'SELECT id FROM ic_references WHERE source_id = ?', ('niddk_diet_2024',)
            )}
        self.assertTrue({
            'citrus_juices_and_drinks', 'orange_juice', 'grapefruit_juice', 'coffee', 'tea',
            'soda', 'alcohol', 'high_acid_foods', 'tomato', 'tomato_sauce', 'spicy_food',
            'artificial_sweeteners', 'chocolate', 'msg',
        }.issubset(niddk_ids))
        rows = check(['citrus juice', 'tomato-based sauce', 'high-acid foods'], self.path)['ingredients']
        self.assertEqual([row['ic_evidence_status'] for row in rows],
                         ['reference_match', 'reference_match', 'unavailable'])
        self.assertEqual(rows[0]['irritation_rating'], 'unrated_potential_concern')

    def test_no_inferred_matches(self):
        result = check(['citric acid', 'cocoa butter', 'tea extract',
                        'curry powder', 'onion powder'], self.path, match_threshold=100)
        self.assertFalse(result['concerns_found'])
        self.assertTrue(result['assessment_incomplete'])
        self.assertTrue(all(r['status']=='unknown' for r in result['ingredients']))

    def test_icn_matches_specific_forms_with_page_provenance(self):
        result = check(['aspArtame', 'apple cider vinegar', 'hot curry powder',
                        'raw bulb onion', 'yeast extract'], self.path)
        rows = result['ingredients']
        self.assertTrue(all(row['status'] == 'potential_concern' for row in rows))
        self.assertTrue(all('2025foodlist.pdf' in row['source_url'] for row in rows))
        self.assertIn('PDF p. 9', rows[0]['summary'])
        self.assertEqual(rows[-1]['name'], 'Yeast extract')

    def test_irritation_rating_preserves_source_and_qualified_forms(self):
        rows = check(['MSG', 'soy sauce', 'low-salt soy sauce', 'chocolate'], self.path)['ingredients']
        self.assertEqual([row['irritation_rating'] for row in rows],
                         ['most_bothersome', 'foods_to_avoid', 'worth_trying_cautiously',
                          'context_dependent'])
        self.assertIn('niddk.nih.gov', rows[0]['source_url'])
        self.assertIn('2025foodlist.pdf', rows[0]['rating_source_url'])
        self.assertIn('small quantities', rows[2]['rating_basis'])

    def test_concerns_and_gaps_coexist(self):
        result = check(['tomatoes', 'natural flavors', 'salt'], self.path, match_threshold=100)
        self.assertTrue(result['concerns_found'])
        self.assertTrue(result['assessment_incomplete'])
        self.assertEqual([r['status'] for r in result['ingredients']], ['potential_concern','ambiguous','unknown'])

    def test_empty_is_incomplete(self):
        self.assertTrue(check([], self.path)['assessment_incomplete'])

    def test_summary_distinguishes_concerns_from_evidence_gaps(self):
        cases = [
            ([], 'no_ingredients', False, True),
            (['unlisted test ingredient'], 'bladder_friendly', False, True),
            (['sugar'], 'try_and_report', False, False),
            (['honey'], 'try_and_report', False, False),
            (['tomato paste'], 'bladder_unfriendly', True, False),
            (['tomato paste', 'salt'], 'bladder_unfriendly', True, True),
        ]
        for ingredients, status, concerns, incomplete in cases:
            with self.subTest(ingredients=ingredients):
                result = check(ingredients, self.path)
                self.assertEqual(result['assessment_status'], status)
                self.assertEqual(result['concerns_found'], concerns)
                self.assertEqual(result['assessment_incomplete'], incomplete)

    def test_honey_matches_general_guidance_without_flagging_a_concern(self):
        result = check(['Honey'], self.path)
        honey = result['ingredients'][0]
        self.assertEqual(honey['status'], 'general_guidance')
        self.assertEqual(honey['irritation_rating'], 'usually_bladder_friendly')
        self.assertFalse(result['concerns_found'])
        self.assertFalse(result['assessment_incomplete'])
        self.assertEqual(result['display_status'], 'Try it and tell us how you feel')
        self.assertTrue(check(['honey', 'honey powder'], self.path)['assessment_incomplete'])
        self.assertEqual(check(['honey', 'honey powder'], self.path)['display_status'], 'Try it and tell us how you feel')
        mixed = check(['honey', 'tomato paste'], self.path)
        self.assertTrue(mixed['concerns_found'])
        self.assertEqual(mixed['display_status'], 'Bladder unfriendly')

    def test_identity_and_ic_evidence_are_independent(self):
        result = check([' REB M ', 'Rebaudioside M', 'Sucralose', 'Natural Flavors', 'MSG'], self.path)
        reb_m, full_name, sucralose, flavors, msg = result['ingredients']
        self.assertEqual(reb_m['identity'], full_name['identity'])
        self.assertEqual(reb_m['identity']['name'], 'Rebaudioside M')
        self.assertEqual(reb_m['status'], 'unknown')
        self.assertEqual(reb_m['ic_evidence_status'], 'unavailable')
        self.assertEqual(sucralose['status'], 'unknown')
        self.assertEqual(sucralose['ic_evidence_status'], 'context_only')
        self.assertIn('Splenda', sucralose['rating_basis'])
        self.assertNotEqual(sucralose['identity']['source_url'], sucralose['rating_source_url'])
        self.assertEqual(flavors['status'], 'ambiguous')
        self.assertEqual(flavors['identity']['category'], 'collective label term')
        self.assertEqual(msg['ic_evidence_status'], 'reference_match')

    def test_tuna_label_retains_preparation_and_amount_limits(self):
        result = check(['Chunky light tuna', 'water', 'sea salt'], self.path)
        tuna, water, salt = result['ingredients']
        self.assertEqual(result['assessment_status'], 'try_and_report')
        self.assertFalse(result['concerns_found'])
        self.assertEqual(tuna['ic_evidence_status'], 'context_only')
        self.assertEqual(tuna['display_status'], 'Depends on preparation')
        self.assertIn('packed in water', tuna['rating_basis'])
        self.assertEqual(water['irritation_rating'], 'usually_bladder_friendly')
        self.assertEqual(water['display_status'], 'Usually bladder friendly')
        self.assertEqual(salt['ic_evidence_status'], 'context_only')
        self.assertEqual(salt['display_status'], 'Depends on amount')
        self.assertIn('no numeric limit', salt['rating_basis'])
        self.assertIn('no quantity', salt['rating_basis'])

    def test_rolled_oats_match_plain_oat_guidance(self):
        result = check(['Whole grain rolled oats', 'oat bran'], self.path)
        oats, bran = result['ingredients']
        self.assertEqual(oats['display_status'], 'Usually bladder friendly')
        self.assertEqual(oats['ic_evidence_status'], 'reference_match')
        self.assertEqual(bran['ic_evidence_status'], 'similar_reference_match')
        self.assertEqual(result['assessment_status'], 'try_and_report')

    def test_expanded_icn_foods_preserve_source_and_quantity_conditions(self):
        rows = check(['rice flour', 'canola oil', 'whole grain oats', 'baking soda',
                      'garlic powder', 'nutmeg', 'ascorbic acid', 'stevia',
                      'table salt', 'ketchup', 'strawberries'], self.path)['ingredients']
        self.assertEqual([row['irritation_rating'] for row in rows], [
            'usually_bladder_friendly', 'usually_bladder_friendly',
            'usually_bladder_friendly', 'usually_bladder_friendly',
            'usually_bladder_friendly', 'worth_trying_cautiously',
            'foods_to_avoid', 'foods_to_avoid',
            'context_dependent', 'context_dependent', 'context_dependent',
        ])
        self.assertTrue(all(row['ic_evidence_status'] == 'reference_match' for row in rows))
        self.assertTrue(all('2025foodlist.pdf' in row['source_url'] for row in rows))
        self.assertIn('No numeric cutoff', rows[-1]['rating_basis'])
        self.assertIn('PDF p. 7', rows[6]['rating_basis'])

    def test_cinnamon_uses_spice_variants_and_keeps_candy_separate(self):
        row = check(['cinnamon'], self.path)['ingredients'][0]
        self.assertEqual(row['applied_match']['matched_term'], 'chinese cassia cinnamon')
        self.assertNotIn('hot cinnamon candy', [item['matched_term'] for item in row['possible_matches']])
        candy = check(['hot cinnamon candy'], self.path)['ingredients'][0]
        self.assertEqual(candy['ic_evidence_status'], 'reference_match')

    def test_links_and_repeat_build(self):
        build(self.path)
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
            self.assertEqual(db.execute('PRAGMA foreign_key_check').fetchall(), [])
            self.assertEqual(db.execute('SELECT count(*) FROM ic_references').fetchone()[0], 391)

if __name__ == '__main__':
    unittest.main()
