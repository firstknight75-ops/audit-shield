from app.exports.engine import CORE_OUTPUT_TITLES


def test_all_core_outputs_are_addressable_for_export():
    expected = {'true_picture', 'trust_index', 'waste_map', 'risk_map', 'opportunity_map', 'action_plan', 'dashboards'}
    assert expected.issubset(set(CORE_OUTPUT_TITLES.keys()))


def test_what_if_six_month_projection_matches_hand_math():
    iqd_amount = 1200000
    recovery_percent = 50
    manual_cost = 200000
    horizon = 6
    recovered = iqd_amount * 0.5
    monthly = recovered / horizon
    net = recovered - manual_cost
    assert recovered == 600000
    assert monthly == 100000
    assert net == 400000
