import io
import json
from pathlib import Path
import sys
import unittest
from urllib.error import HTTPError, URLError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from lookup_barcode import assess_label, assess_product, fetch_product, LookupFailure, validate_barcode
from parse_ingredients import parse_label

class PipelineTests(unittest.TestCase):
    def test_barcode_validation_preserves_zeros(self):
        self.assertEqual(validate_barcode('0012345678905'), '0012345678905')
        for value in ['0012345678906', '../123', '123', '１２３４５６７８']:
            with self.assertRaises(ValueError):
                validate_barcode(value)

    def test_nested_label_and_original(self):
        label = 'Ingredients: sauce (tomatoes, seasoning [MSG, salt]), natural flavors.'
        result = assess_label(label)
        self.assertEqual(result['original_label'], label)
        statuses = {r['ingredient']:r['status'] for r in result['assessment']['ingredients']}
        self.assertEqual(statuses['tomatoes'], 'potential_concern')
        self.assertEqual(statuses['MSG'], 'potential_concern')
        self.assertEqual(statuses['natural flavors'], 'ambiguous')
        self.assertTrue(result['assessment']['assessment_incomplete'])

    def test_malformed_label_warns(self):
        self.assertTrue(parse_label('sauce (tomatoes, salt')['warnings'])
        self.assertTrue(parse_label('sauce [tomatoes), salt')['warnings'])
        result = assess_label('honey (')
        self.assertEqual(result['assessment']['ingredients'][0]['status'], 'general_guidance')
        self.assertEqual(result['assessment']['assessment_status'], 'try_and_report')
        self.assertTrue(result['assessment']['assessment_incomplete'])

    def test_html_and_windows_newlines(self):
        self.assertEqual(parse_label('salt\r\n\r\nMSG &lt;2%')['candidates'], ['salt', 'MSG'])

    def test_water_mineral_profile_is_preserved_and_unassessed(self):
        label = 'Eau de source Noemie\r\n\r\nCalcium Ca2+ 113 mg/l\r\nFluor F - &lt;1 mg/l\r\npH 7.3'
        result = assess_product('3274080005003', {'ingredients_text_en': label})
        self.assertEqual(result['original_label'], label)
        self.assertEqual(result['candidates'], [])
        self.assertIn('mineral measurements', result['warnings'][0])
        self.assertTrue(result['assessment']['assessment_incomplete'])
        self.assertFalse(result['assessment']['concerns_found'])
        self.assertEqual(parse_label('Spring water, tomato paste')['candidates'], ['Spring water', 'tomato paste'])

    def test_allergen_cross_contact_not_ingredient(self):
        self.assertEqual(parse_label('salt. May contain chocolate')['candidates'], ['salt'])

    def test_color_annotation_and_context_dependent_reference(self):
        label = 'Spirulina (for Color), Reb M (Stevia), Citric Acid, Natural Flavors'
        result = assess_label(label)
        self.assertEqual(result['original_label'], label)
        self.assertEqual(result['candidates'], ['Spirulina', 'Reb M', 'Citric Acid', 'Natural Flavors'])
        assessment = result['assessment']
        citric_acid = assessment['ingredients'][2]
        self.assertEqual(citric_acid['status'], 'unknown')
        self.assertEqual(citric_acid['irritation_rating'], 'context_dependent')
        self.assertFalse(assessment['concerns_found'])
        self.assertTrue(assessment['assessment_incomplete'])
        self.assertEqual(assessment['display_status'], 'Try it and tell us how you feel')

    def test_reb_m_annotation_keeps_separately_listed_stevia(self):
        result = parse_label('Rebaudioside M (stevia), Stevia, Monk Fruit Extract')
        self.assertEqual(result['candidates'], ['Rebaudioside M', 'Stevia', 'Monk Fruit Extract'])

    def test_oatmeal_treatment_list_preserves_ingredients_and_original_label(self):
        label = ('Whole grain rolled oats (with oat bran), dehydrated apples '
                 '(treated with ascorbic acid, citric acid and calcium chloride to preserve color), '
                 'ferric orthophosphate (source of iron), macaroni and cheese')
        result = assess_label(label)
        self.assertEqual(result['original_label'], label)
        self.assertEqual(result['candidates'], [
            'Whole grain rolled oats', 'oat bran', 'dehydrated apples', 'ascorbic acid',
            'citric acid', 'calcium chloride', 'ferric orthophosphate', 'macaroni and cheese',
        ])
        citric_acid = result['assessment']['ingredients'][4]
        self.assertEqual(citric_acid['ic_evidence_status'], 'context_only')

    def test_barcode_assessment_applies_close_match_by_default(self):
        product = {'ingredients_text_en': 'tomatoe paste'}
        strict = assess_product('0012345678905', product, match_threshold=100)
        relaxed = assess_product('0012345678905', product)
        self.assertNotIn('possible_matches', strict['assessment']['ingredients'][0])
        assessment = relaxed['assessment']
        row = assessment['ingredients'][0]
        self.assertEqual(row['possible_matches'][0]['matched_term'], 'tomato paste')
        self.assertGreaterEqual(row['possible_matches'][0]['similarity_percent'], 50)
        self.assertEqual(row['irritation_rating'], 'foods_to_avoid')
        self.assertEqual(assessment['display_status'], 'Bladder unfriendly')
        self.assertTrue(assessment['concerns_found'])
        with self.assertRaises(ValueError):
            assess_label('tomato paste', match_threshold=101)

    def test_low_threshold_excludes_unrelated_ingredients(self):
        result = assess_label(
            'Whole grain rolled oats, oat bran, sugar, dehydrated apples, ascorbic acid, cinnamon, salt',
            match_threshold=50,
        )
        rows = {row['ingredient']: row for row in result['assessment']['ingredients']}
        for term in ('sugar', 'dehydrated apples', 'ascorbic acid'):
            with self.subTest(term=term):
                self.assertNotIn('possible_matches', rows[term])
        self.assertEqual(rows['Whole grain rolled oats']['ic_evidence_status'], 'reference_match')
        self.assertEqual(rows['oat bran']['ic_evidence_status'], 'similar_reference_match')
        self.assertEqual([row['reference_name'] for row in rows['oat bran']['possible_matches']],
                         ['Plain oats'])
        self.assertEqual([row['matched_term'] for row in rows['cinnamon']['possible_matches']],
                         ['ceylon cinnamon', 'chinese cassia cinnamon'])
        self.assertEqual(rows['cinnamon']['applied_match']['matched_term'], 'chinese cassia cinnamon')
        self.assertEqual(rows['salt']['irritation_rating'], 'context_dependent')
        self.assertNotIn('applied_match', rows['salt'])

    def test_quantity_evidence_and_generic_salt(self):
        result = assess_label(
            'Oats, honey (4.5%), contains 2% or less of: salt, mix (citric acid), baking soda'
        )['assessment']
        rows = {row['ingredient']: row for row in result['ingredients']}
        self.assertEqual(result['display_status'], 'Try it and tell us how you feel')
        self.assertEqual(rows['honey']['quantity_evidence']['value'], 4.5)
        self.assertEqual(rows['salt']['quantity_evidence']['upper_bound_percent'], 2)
        self.assertEqual(rows['citric acid']['quantity_evidence']['status'], 'unknown')
        self.assertNotIn('applied_match', rows['baking soda'])
        row = assess_label('salt 30 mg per serving')['assessment']['ingredients'][0]
        self.assertEqual(row['quantity_evidence']['value'], 30)
        self.assertEqual(row['quantity_evidence']['unit'], 'mg')

    def test_missing_product_and_missing_english(self):
        for product in [None, {}, {'lang':'fr','ingredients_text':'tomates'},
                        {'product_name': 'Caffè', 'ingredients_text': None}]:
            result = assess_product('0012345678905', product)
            self.assertTrue(result['assessment']['assessment_incomplete'])
            self.assertFalse(result['assessment']['concerns_found'])
            self.assertIn('No ingredients were available to assess', result['assessment']['message'])
        self.assertEqual(assess_product('0012345678905', None)['lookup_status'], 'not_found')

    def test_english_label_and_metadata(self):
        result = assess_product('0012345678905', {'product_name':'Example', 'ingredients_text_en':'MSG, salt'})
        self.assertEqual(result['product_name'], 'Example')
        self.assertTrue(result['assessment']['concerns_found'])
        self.assertTrue(result['requires_package_confirmation'])

    def test_request_and_response(self):
        def opener(request, timeout):
            self.assertIn('/api/v3.6/product/0012345678905.json', request.full_url)
            self.assertEqual(timeout, 15)
            self.assertIn('Authorization', request.headers)
            return io.StringIO(json.dumps({'product':{'ingredients_text_en':'MSG'}}))
        self.assertEqual(fetch_product('0012345678905', opener=opener)['ingredients_text_en'], 'MSG')

    def test_service_failures(self):
        for error in [URLError('offline'), TimeoutError(), HTTPError('url',429,'limited',{},None)]:
            def opener(*args, **kwargs):
                raise error
            with self.assertRaises(LookupFailure):
                fetch_product('0012345678905', opener=opener)
        self.assertIsNone(fetch_product('0012345678905', opener=lambda *a,**kw:io.StringIO('{"status":0}')))
        with self.assertRaises(LookupFailure):
            fetch_product('0012345678905', opener=lambda *a,**kw:io.StringIO('invalid'))

if __name__ == '__main__':
    unittest.main()
