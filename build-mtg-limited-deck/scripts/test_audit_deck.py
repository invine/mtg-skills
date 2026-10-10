import json
import unittest

from audit_deck import audit, unique_object


class DeckAuditTests(unittest.TestCase):
    def example(self):
        return {
            "deck": {"Island": 8, "Mountain": 7, "Plains": 1, "Dual": 1, "Spell": 23},
            "pool": {"Dual": 1, "Spell": 23},
            "land_names": ["Island", "Mountain", "Plains", "Dual"],
        }

    def test_complete_deck_and_basic_swap(self):
        data = self.example()
        data["previous"] = dict(data["deck"], Island=7, Mountain=8)
        result = audit(data)
        self.assertTrue(result["ok"])
        self.assertEqual((result["total"], result["lands"], result["nonlands"]), (40, 17, 23))
        self.assertEqual(result["changes"], {
            "added": {"Island": 1}, "removed": {"Mountain": 1}, "net_cards": 0})

    def test_extra_card_and_unavailable_copy(self):
        data = self.example()
        data["deck"]["Dual"] = 2
        result = audit(data)
        self.assertFalse(result["ok"])
        self.assertEqual(len(result["errors"]), 2)

    def test_special_basic_requires_pool_copy(self):
        data = self.example()
        del data["deck"]["Plains"]
        data["deck"]["Snow-Covered Island"] = 1
        data["land_names"].append("Snow-Covered Island")
        self.assertFalse(audit(data)["ok"])
        data["pool"]["Snow-Covered Island"] = 1
        self.assertTrue(audit(data)["ok"])

    def test_landcycling_is_not_a_land(self):
        data = self.example()
        data["deck"]["Spell"] = 22
        data["deck"]["Landcycling Spell"] = 1
        data["pool"]["Landcycling Spell"] = 1
        self.assertEqual(audit(data)["lands"], 17)

    def test_missing_land_classification(self):
        data = self.example()
        data["land_names"].remove("Island")
        self.assertFalse(audit(data)["ok"])

    def test_invalid_and_duplicate_counts(self):
        for invalid in (True, -1, 0, 1.5):
            data = self.example()
            data["deck"]["Island"] = invalid
            with self.assertRaises(ValueError):
                audit(data)
        with self.assertRaises(ValueError):
            json.loads('{"Island": 8, "Island": 9}', object_pairs_hook=unique_object)

    def test_format_override_and_net_change(self):
        data = {"deck": {"Wastes": 30}, "pool": {}, "land_names": ["Wastes"],
                "unlimited_basics": ["Wastes"], "size": 30, "previous": {"Wastes": 29}}
        self.assertTrue(audit(data)["ok"])
        self.assertEqual(audit(data)["changes"]["net_cards"], 1)


if __name__ == "__main__":
    unittest.main()
