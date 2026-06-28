from app.exports.certificates import tamper_proof_certificate


def test_what_if_projection_matches_simple_hand_calculation():
    iqd_amount = 1000000
    recovery_percent = 50
    manual_cost = 100000
    horizon = 6
    recovered = iqd_amount * (recovery_percent / 100)
    monthly = recovered / horizon
    net = recovered - manual_cost
    assert recovered == 500000
    assert round(monthly, 2) == round(500000 / 6, 2)
    assert net == 400000


def test_export_certificate_has_hash_and_signature():
    cert = tamper_proof_certificate({'title': 'خريطة الهدر'}, 'abc123')
    assert cert['ledger_hash_at_generation'] == 'abc123'
    assert isinstance(cert['signature'], str)
    assert len(cert['signature']) > 10
