"""Regression positions and hostile ledger mutations exercise reviewer-visible failures."""
import copy
import json
import unittest
from pathlib import Path

from decision_audit import FACETS, calculation_ids, decision_template, fingerprint, snapshot
from limited_math import calculate
from review_tools import context, make_review, validate_review

CASES = json.loads((Path(__file__).parent / 'fixtures/review-regressions.json').read_text())


def position_ledger(case='g7_t5'):
    state = copy.deepcopy(CASES[case]['state'])
    game, event = CASES[case]['source']['game'], state['event']
    report = {'seat_id': 2, 'history_sha256': 'fixture', 'decoder_version': 'fixture',
              'positions': [], 'event_count': event + 10, 'coverage': 'complete'}
    reports, states = {game: report}, {(game, event): state}
    ledger = make_review(reports, [(game, event)])
    for check in ledger['checks']:
        check.update(status='reviewed', note='Decision-specific records attached.')
    # Test scaffold only: production reviews must justify each inapplicable facet.
    for kind in FACETS['position']:
        record = decision_template(game, kind, context(report, state), snapshot(state, 2))
        record.update(status='not_applicable', window_end_event=event + 1,
                      basis=[{'id': 'turn', 'field': 'turnNumber', 'value': state['turn']['turnNumber']}],
                      note=f'Test scaffold for {kind}; replaced by evaluated candidates in arithmetic tests.')
        ledger['decisions'].append(record)
        ledger['checks'][1]['decision_ids'].append(record['id'])
    return ledger, reports, states, [(game, event)]


def reviewed_land_record(ledger):
    record = next(d for d in ledger['decisions'] if d['kind'] == 'land')
    data = copy.deepcopy(CASES['g7_t5']['land_options'])
    candidates = []
    for land in ['239', '218']:
        data = {**data, 'chosen': land}
        candidates.append({'id': land, 'information': 'known_at_snapshot', 'line': f'Play {land}, attack Jace, pass.',
            'actions': [{'source': land, 'action': 'play land'}, {'source': '204', 'action': 'attack Jace'}],
            'tradeoff': 'Compare black access with the extra white source; no mana expenditure is planned.',
            'next_opponent_turn': {'untapped_sources': ['219', '210', '203', '199', land],
                'held_interaction': ['162', '160'] + (['164'] if land == '218' else []), 'exposed': ['220'],
                'assessment': 'Reserve responses until the next untap; a legal removal target may arise.'},
            'calculations': [{'input': data, 'bindings': {i: i for i in calculation_ids(data)}, 'result': calculate(data)}]})
    record.update(status='reviewed', candidates=candidates, selected='218',
        basis=[{'id': '218', 'field': 'name', 'value': 'Swamp'}],
        actual={'line': 'Plains, Crier attacks Jace, pass.', 'comparison': 'Swamp preserves the attack and adds Absence access.'},
        note='The land choice remains separate from the preceding Chandra activation.')
    return record


class RegressionPositions(unittest.TestCase):
    def test_danitha_first_strike_does_not_survive_three_two_threes(self):
        data = copy.deepcopy(CASES['g1_t7']['combat'])
        result = calculate(data)
        self.assertEqual(result['damage_to_targets'], {'294': 0, 'opponent': 7})
        self.assertEqual(set(result['dead']), {'258', '313'})
        self.assertEqual(result['steps'][0]['died'], ['313'])
        self.assertEqual(result['damage_to_creatures']['258'], 4)
        # Two blockers instead: first strike kills one, remaining two damage is not lethal.
        data['blocks']['258'] = ['313', '273']
        self.assertNotIn('258', calculate(data)['dead'])

    def test_precombat_evasion_finds_thirteen_without_new_draw_or_chandra(self):
        data = copy.deepcopy(CASES['g3_t8']['lethal'])
        result = calculate(data)
        self.assertTrue(result['lethal_found'])
        self.assertEqual(set(result['attackers']), {'290', '208'})
        self.assertEqual(result['minimum_net_damage'], 13)
        self.assertEqual(result['effects'], [{'effect': '379', 'choice': 0}, {'effect': '368', 'choice': 0}])
        # Negative: granting Ghalta reach defeats the certified aerial line.
        data['blockers'][0]['keywords'].append('reach')
        self.assertFalse(calculate(data)['lethal_found'])
        # Negative: Ascent is unaffordable with no available white source.
        data = copy.deepcopy(CASES['g3_t8']['lethal'])
        for source in data['sources']:
            if source['produces'] == ['W']:
                source['ready'] = False
        self.assertFalse(calculate(data)['lethal_found'])

    def test_swamp_opens_absence_without_losing_the_planned_line(self):
        data = copy.deepcopy(CASES['g7_t5']['land_options'])
        result = calculate(data)
        self.assertEqual(result['preserves_sequence_adds_interaction'], [{'land': '218', 'adds': ['164']}])
        # Spending the turn's mana removes the reserve; no free untap is assumed.
        data['sequence'] = [{'cost': '{3}{W}'}]
        result = calculate(data)
        self.assertEqual(result['preserves_sequence_adds_interaction'], [])
        self.assertTrue(all('164' not in o['available_interaction'] for o in result['options']))
        # A tapped Swamp also cannot reserve Absence this turn cycle.
        data['sequence'] = []
        data['lands'][1]['ready'] = False
        self.assertEqual(calculate(data)['preserves_sequence_adds_interaction'], [])

    def test_unsupported_mechanics_and_search_bounds_are_explicit(self):
        data = copy.deepcopy(CASES['g3_t8']['lethal'])
        data['attackers'][0]['keywords'].append('infect')
        self.assertEqual(calculate(data)['status'], 'unsupported')
        data = copy.deepcopy(CASES['g3_t8']['lethal'])
        data['blockers'] *= 2
        self.assertEqual(calculate(data)['status'], 'unsupported')


class CombatRules(unittest.TestCase):
    def test_double_strike_trample_lifelink_and_deaths_between_steps(self):
        data = {'kind': 'combat', 'declarations_verified': True,
            'attackers': [{'id': 'a', 'power': 4, 'toughness': 4, 'keywords': ['double strike', 'trample', 'lifelink']}],
            'blockers': [{'id': 'b', 'power': 9, 'toughness': 3}], 'blocks': {'a': ['b']}}
        result = calculate(data)
        self.assertEqual(result['damage_to_targets']['opponent'], 5)
        self.assertEqual(result['dead'], ['b'])
        self.assertEqual(result['life_gained']['attacking'], 8)
        data['blockers'][0]['keywords'] = ['first strike']
        result = calculate(data)
        self.assertEqual(set(result['dead']), {'a', 'b'})
        self.assertEqual(result['damage_to_targets']['opponent'], 1)

    def test_modern_allocation_may_split_damage_without_killing_either_blocker(self):
        data = {'kind': 'combat', 'declarations_verified': True,
            'attackers': [{'id': 'a', 'power': 3, 'toughness': 5}],
            'blockers': [{'id': 'b', 'power': 1, 'toughness': 3}, {'id': 'c', 'power': 1, 'toughness': 3}],
            'blocks': {'a': ['b', 'c']}, 'allocations': {'normal': {'a': {'blockers': {'b': 1, 'c': 2}}}}}
        self.assertEqual(calculate(data)['dead'], [])
        data['allocations']['normal']['a']['target'] = 1
        with self.assertRaises(ValueError):
            calculate(data)

    def test_marked_damage_deathtouch_and_illegal_flying_block(self):
        data = {'kind': 'combat', 'declarations_verified': True,
            'attackers': [{'id': 'a', 'power': 2, 'toughness': 1, 'keywords': ['first strike', 'deathtouch']}],
            'blockers': [{'id': 'b', 'power': 9, 'toughness': 9}, {'id': 'c', 'power': 9, 'toughness': 9}],
            'blocks': {'a': ['b', 'c']}}
        self.assertEqual(calculate(data)['dead'], ['b', 'c'])
        data['attackers'][0]['keywords'] = ['first strike']
        data['blockers'][0]['damage'] = 8
        self.assertEqual(set(calculate(data)['dead']), {'a', 'b'})
        data['attackers'][0]['keywords'] = ['flying']
        with self.assertRaises(ValueError):
            calculate(data)


class AuditContract(unittest.TestCase):
    def test_generic_coverage_cannot_certify_a_review(self):
        ledger, reports, states, scope = position_ledger()
        ledger['decisions'] = []
        for check in ledger['checks']:
            check.update(note='Reviewed.', decision_ids=[])
        result = validate_review(ledger, reports, states, positions=scope)
        self.assertFalse(result['ok'])
        self.assertTrue(any('missing independent decisions' in e for e in result['errors']))

    def test_calculations_are_recomputed_and_a_land_finding_does_not_cover_other_decisions(self):
        ledger, reports, states, scope = position_ledger()
        record = reviewed_land_record(ledger)
        self.assertTrue(validate_review(ledger, reports, states, positions=scope)['ok'])
        record['candidates'][0]['calculations'][0]['result']['preserves_sequence_adds_interaction'] = []
        self.assertFalse(validate_review(ledger, reports, states, positions=scope)['ok'])
        reviewed_land_record(ledger)
        ledger['checks'][1]['decision_ids'] = [record['id']]
        self.assertFalse(validate_review(ledger, reports, states, positions=scope)['ok'])

    def test_later_draw_cannot_enter_a_start_of_turn_baseline(self):
        ledger, reports, states, scope = position_ledger('g1_t7')
        record = next(d for d in ledger['decisions'] if d['kind'] == 'development')
        later = {'id': 'future_ascent', 'information': 'known_at_snapshot', 'line': 'Cast newly drawn Academic Ascent.',
            'actions': [{'source': 'future:Academic Ascent', 'action': 'cast'}], 'tradeoff': 'Tests forbidden future information.',
            'calculations': [], 'next_opponent_turn': {'untapped_sources': [], 'held_interaction': [], 'exposed': [], 'assessment': 'Unknown.'}}
        record.update(status='reviewed', candidates=[later, {**later, 'id': 'hold', 'actions': [], 'line': 'Hold.'}],
                      selected='future_ascent', actual={'line': 'Attack.', 'comparison': 'Invalid baseline.'})
        result = validate_review(ledger, reports, states, positions=scope)
        self.assertTrue(any('unavailable resource' in e for e in result['errors']))
        view = snapshot(states[scope[0]], 2)
        self.assertNotIn('Academic Ascent', json.dumps(view))
        self.assertNotIn('Sideboard', view['zones'])
        self.assertNotIn('Library', view['zones'])
        # A future-revealed identity in the raw hand must not leak past viewer knowledge.
        state = copy.deepcopy(states[scope[0]])
        state['zones']['Hand'].append({'instance_id': 999, 'owner': 1, 'name': 'Secret future card'})
        state['hand_knowledge']['2'].append({'instance_id': 999, 'owner': 1, 'name': 'Secret future card', 'learned_event': 9999})
        self.assertNotIn('Secret future card', json.dumps(snapshot(state, 2)))

    def test_stale_state_and_outside_window_records_fail(self):
        ledger, reports, states, scope = position_ledger()
        ledger['decisions'][0]['basis'][0]['value'] += 1
        self.assertFalse(validate_review(ledger, reports, states, positions=scope)['ok'])
        ledger, reports, states, scope = position_ledger()
        ledger['decisions'][0]['snapshot_sha256'] = fingerprint({})
        self.assertFalse(validate_review(ledger, reports, states, positions=scope)['ok'])

    def test_position_recommendation_needs_no_invented_future_action(self):
        from decision_audit import validate_decision
        ledger, reports, states, scope = position_ledger()
        record = reviewed_land_record(ledger)
        del record['window_end_event']
        record['actual'] = {'status': 'not_supplied'}
        self.assertTrue(validate_review(ledger, reports, states, positions=scope)['ok'])
        game, event = scope[0]
        errors = validate_decision(record, reports[game], states[game, event], record['context'])
        self.assertTrue(any('only for a position-only' in e for e in errors))

    def test_unsupported_calculation_cannot_silently_replace_checked_arithmetic(self):
        ledger, reports, states, scope = position_ledger()
        record = reviewed_land_record(ledger)
        for candidate in record['candidates']:
            data = {'kind': 'manual', 'mechanics': 'Source has an unmodeled restriction.'}
            candidate['calculations'] = [{'input': data, 'bindings': {}, 'result': calculate(data)}]
        self.assertFalse(validate_review(ledger, reports, states, positions=scope)['ok'])
        for candidate in record['candidates']:
            candidate['calculations'][0]['manual'] = {
                'applies_to': 'land_options', 'assumptions': ['Illustrative manual branch; restriction is verified.'],
                'steps': ['Count available sources after the restriction and planned payments.'],
                'result': {'castable_responses': ['164'] if candidate['id'] == '218' else []},
                'uncertainties': [], 'conclusion': 'This record explicitly relies on reviewer-checked arithmetic.'}
        self.assertTrue(validate_review(ledger, reports, states, positions=scope)['ok'])

    def test_unresolved_evidence_is_explicit_and_not_complete(self):
        ledger, reports, states, scope = position_ledger()
        check = ledger['checks'][1]
        check.update(status='insufficient_evidence', missing='Land drop availability.', impact='Cannot establish legal land alternatives.')
        result = validate_review(ledger, reports, states, positions=scope)
        self.assertTrue(result['ok'])
        self.assertFalse(result['complete'])
        del check['impact']
        self.assertFalse(validate_review(ledger, reports, states, positions=scope)['ok'])


if __name__ == '__main__':
    unittest.main()
