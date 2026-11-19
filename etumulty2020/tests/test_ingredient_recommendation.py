from datetime import datetime, timezone
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from food_diary import record_reaction, summarize_reactions
from recommend_ingredient import recommend_ingredient


class IngredientRecommendationTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.diary = Path(temporary.name) / 'private' / 'diary.sqlite3'

    def test_diary_counts_one_outcome_per_meal(self):
        record_reaction('Pasta', 'symptoms', ingredients=['tomatoes', ' Tomatoes '],
                        ate_at=datetime(2026, 11, 1, 12, tzinfo=timezone.utc), database=self.diary)
        record_reaction('Lunch', 'unsure', ingredients=['onions'], database=self.diary)
        self.assertEqual(summarize_reactions('TOMATOES', database=self.diary),
                         {'tolerated': 0, 'symptoms': 1, 'unsure': 0})

    def test_combines_reference_and_diary_without_notes(self):
        record_reaction('Pasta', 'tolerated', ingredients=['tomatoes'],
                        notes='private note', database=self.diary)
        with patch('recommend_ingredient.select_category', return_value='mixed_evidence') as select:
            result = recommend_ingredient('tomatoes', diary_database=self.diary)
        _, evidence, choices = select.call_args.args
        self.assertEqual(choices, ['mixed_evidence', 'insufficient_evidence'])
        self.assertEqual(evidence['diary_counts']['tolerated'], 1)
        self.assertEqual(evidence['reference_status'], 'potential_concern')
        self.assertEqual(evidence['reference_irritation_rating'], 'most_bothersome')
        self.assertNotIn('private note', str(evidence))
        self.assertEqual(result['category'], 'mixed_evidence')
        self.assertIn('source_url', result['reference'])

    def test_no_evidence_does_not_call_model_or_create_diary(self):
        with patch('recommend_ingredient.select_category') as select:
            result = recommend_ingredient('salt', diary_database=self.diary)
        select.assert_not_called()
        self.assertEqual(result['category'], 'insufficient_evidence')
        self.assertFalse(self.diary.exists())

    def test_model_uncertainty_keeps_reference_concern_visible(self):
        with patch('recommend_ingredient.select_category', return_value='insufficient_evidence'):
            result = recommend_ingredient('tomatoes', diary_database=self.diary)
        self.assertIn('Use caution', result['recommendation'])
        self.assertEqual(result['reference']['status'], 'potential_concern')
