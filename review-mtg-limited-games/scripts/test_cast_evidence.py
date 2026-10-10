import unittest

from cast_evidence import audit, classify


def attempt(kinds, **extra):
    return {"attempt_id": "g4-a1", "card": "Example Sorcery",
            "events": [{"kind": kind, "source": f"game4.json:event{i}"}
                       for i, kind in enumerate(kinds)], **extra}


class CastEvidenceTests(unittest.TestCase):
    def test_canceled_payment_is_not_a_cast(self):
        value = attempt(["selected", "stack_entered", "payment_started", "costs_paid", "canceled"],
                        claimed_cast=True)
        result = classify(value)
        self.assertEqual(result["status"], "canceled")
        self.assertTrue(result["issues"])

    def test_countered_spell_was_cast(self):
        self.assertEqual(classify(attempt(["selected", "countered"]))["status"], "committed")

    def test_truncated_attempt_remains_unresolved(self):
        result = classify(attempt(["stack_entered", "costs_paid"], claimed_cast=True))
        self.assertEqual(result["status"], "unresolved")
        self.assertTrue(result["issues"])

    def test_free_spell_does_not_require_mana_evidence(self):
        self.assertEqual(classify(attempt(["cast_completed", "resolved"]))["status"], "committed")

    def test_cancellation_then_separate_recast(self):
        first = attempt(["selected", "canceled"], claimed_cast=False)
        second = attempt(["selected", "priority_after_cast"], attempt_id="g4-a2", claimed_cast=True)
        result = audit({"attempts": [first, second]})
        self.assertTrue(result["ok"])
        self.assertEqual([item["status"] for item in result["attempts"]], ["canceled", "committed"])

    def test_conflicting_attempts_are_not_guessed(self):
        result = classify(attempt(["canceled", "cast_completed"]))
        self.assertEqual(result["status"], "unresolved")
        self.assertTrue(result["issues"])

    def test_unknown_schema_and_missing_provenance(self):
        for value in (attempt(["some_new_action"]),
                      attempt([], events=[{"kind": "resolved", "source": ""}]),
                      attempt([], claimed_cast="false")):
            with self.assertRaises(ValueError):
                classify(value)

    def test_duplicate_attempt_ids(self):
        with self.assertRaises(ValueError):
            audit({"attempts": [attempt(["canceled"]), attempt(["resolved"])]})


if __name__ == "__main__":
    unittest.main()
