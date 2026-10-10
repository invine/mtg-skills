"""Worked outcomes test the calculator JSON boundary, not its algorithm."""
import unittest


class ProbabilityTests(unittest.TestCase):
    def test_joint_draws_use_without_replacement_and_overlap_is_explicit(self):
        from limited_math import calculate
        result = calculate({"kind": "draw", "model": "uniform_without_replacement", "draws": 2,
            "groups": [{"count": 1, "tags": ["blue", "white"]}, {"count": 1, "tags": ["blue"]},
                       {"count": 2, "tags": []}], "minimum": {"blue": 1, "white": 1}})
        # Six equally likely pairs, three contain the dual source.
        self.assertEqual(result["fraction"], "1/2")
        self.assertEqual(result["interpretation"], "Cards seen, not spell castability or a keep verdict.")
        self.assertEqual(calculate({"kind": "draw", "model": "arena_smoothed", "draws": 7})["status"], "unsupported")


class ManaTests(unittest.TestCase):
    def test_sequence_preserves_future_color_and_utility_tap_cannot_pay_twice(self):
        from limited_math import calculate
        data = {"kind": "mana", "assumptions_verified": True, "sources": [
            {"id": "dual", "produces": ["W", "U"], "ready": True},
            {"id": "island", "produces": ["U"], "ready": True}],
            "steps": [{"cost": "{U}"}, {"cost": "{W}"}]}
        result = calculate(data)
        self.assertTrue(result["feasible"])
        self.assertEqual(result["payments"][0]["mana"], [{"source": "island", "color": "U"}])
        data["steps"] = [{"cost": "{1}{W}", "tap_sources": ["island"]}]
        self.assertFalse(calculate(data)["feasible"])
        data["steps"] = [{"cost": "{X}{U}"}]
        self.assertEqual(calculate(data)["status"], "unsupported")


class CombatTests(unittest.TestCase):
    def test_damage_through_blocks_and_dead_creatures_are_reported(self):
        from limited_math import calculate
        data = {"kind": "combat", "declarations_verified": True,
            "attackers": [{"id": "flyer", "power": 6, "toughness": 6, "keywords": ["flying"]}] +
                         [{"id": f"cadet{i}", "power": 2, "toughness": 2} for i in range(5)],
            "blockers": [{"id": "guard", "power": 7, "toughness": 6, "keywords": ["reach"]}],
            "blocks": {"flyer": ["guard"]}}
        result = calculate(data)
        self.assertEqual(result["damage_to_targets"], {"opponent": 10})
        self.assertEqual(set(result["dead"]), {"flyer", "guard"})
        data["attackers"][0]["keywords"].append("double strike")
        self.assertEqual(calculate(data)["status"], "unsupported")

    def test_blocked_creature_stays_blocked_when_blocker_has_left(self):
        from limited_math import calculate
        data = {"kind": "combat", "declarations_verified": True,
                "attackers": [{"id": "a", "power": 5, "toughness": 5, "blocked": True}],
                "blockers": [], "blocks": {}}
        self.assertEqual(calculate(data)["damage_to_targets"], {"opponent": 0})
        data["attackers"][0]["keywords"] = ["trample"]
        self.assertEqual(calculate(data)["damage_to_targets"], {"opponent": 5})


if __name__ == "__main__":
    unittest.main()
