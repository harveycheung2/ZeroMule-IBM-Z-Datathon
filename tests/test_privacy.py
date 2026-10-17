import base64
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import copy
import json
import math
import secrets
import sqlite3

import numpy as np
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from src.privacy.psi_hasher import PSIHasher, CentralPSICoordinator
from src.privacy.dp_perturbation import DPPerturbation, RDPAccountant
from src.privacy.budget import PrivacyBudgetLedger, PrivacyBudgetExceeded
from src.privacy.bank_exporter import BankPrivacyExporter, canonical_bytes, validate_protected_payload
from src.models.enclave_aggregator import EnclaveAggregator


@pytest.fixture
def setup_bank(tmp_path):
    key = Ed25519PrivateKey.generate()
    ledger = PrivacyBudgetLedger.provision(tmp_path / 'budget.sqlite', 'Bank_A')
    exporter = BankPrivacyExporter('Bank_A', ledger, key, PSIHasher(secrets.token_bytes(32)), sigma=3)
    return exporter, key, ledger


def release(exporter, edges=True):
    records = [{'source_account': 'secret-alice', 'target_account': 'secret-bob',
                'amount': 12345, 'timestamp': 'secret-time', 'nested': {'PII': 'private'}}] if edges else []
    return exporter.export(records, {'secret-alice': np.ones(8), 'secret-bob': np.zeros(8)})


def test_key_required_and_runtime_configuration(monkeypatch):
    monkeypatch.delenv('ZEROMULE_HMAC_KEY_B64', raising=False)
    with pytest.raises(ValueError):
        PSIHasher()
    for value in ('not base64!', base64.b64encode(b'short').decode()):
        monkeypatch.setenv('ZEROMULE_HMAC_KEY_B64', value)
        with pytest.raises(ValueError):
            PSIHasher()
    key = secrets.token_bytes(32)
    monkeypatch.setenv('ZEROMULE_HMAC_KEY_B64', base64.b64encode(key).decode())
    assert PSIHasher().hash_account('alice') == PSIHasher(key).hash_account('alice')
    assert PSIHasher(secrets.token_bytes(32)).hash_account('alice') != PSIHasher(key).hash_account('alice')


def test_redaction_allowlist_and_no_input_mutation(setup_bank):
    exporter, key, _ = setup_bank
    original = {'source_account': 'alice', 'target_account': 'bob', 'nested': {'name': 'PII'}, 'Account': 'extra'}
    before = copy.deepcopy(original)
    record = exporter._hasher.create_blinded_ledger_records([original], 'Bank_A')[0]
    assert set(record) == {'orig_account_hash', 'dest_account_hash', 'originating_bank'}
    assert original == before
    payload = release(exporter)
    encoded = json.dumps(payload)
    for private in ('secret-alice', 'secret-bob', 'amount', 'timestamp', 'nested', 'avg_original_norm'):
        assert private not in encoded
    validate_protected_payload(payload, {'Bank_A': key.public_key()}, 8)


def test_gaussian_noise_statistics_and_freshness():
    mechanism = DPPerturbation(clip_norm=1, sigma=4)
    zeros = np.zeros((2000, 8))
    first, metadata = mechanism.perturb_embeddings(zeros)
    second, _ = DPPerturbation(1, 4).perturb_embeddings(zeros)
    assert metadata == {'clip_norm_C': 1, 'sigma': 4, 'noise_std': 8}
    assert abs(first.mean()) < 0.3
    assert 7.7 < first.std() < 8.3
    assert not np.array_equal(first, second)
    assert np.linalg.norm(mechanism.clip_embeddings(np.full((30, 8), 1e300))) == pytest.approx(1)
    source = np.full((2, 8), 10.0)
    before = source.copy()
    assert np.linalg.norm(mechanism.clip_embeddings(source)) <= 1.000000001
    assert np.array_equal(source, before)


@pytest.mark.parametrize('value', [0, -1, float('nan'), float('inf')])
def test_invalid_gaussian_parameters(value):
    with pytest.raises(ValueError):
        DPPerturbation(sigma=value)
    with pytest.raises(ValueError):
        DPPerturbation(clip_norm=value)


@pytest.mark.parametrize('matrix', [[], [1, 2], [[float('nan')]], [[float('inf')]]])
def test_invalid_embeddings(matrix):
    with pytest.raises(ValueError):
        DPPerturbation().perturb_embeddings(matrix)


def test_rdp_gaussian_formula_composition_and_calibration():
    accountant = RDPAccountant([2, 4, 8, 16, 32, 64])
    assert accountant.get_privacy_spent()[0] == 0
    accountant.step(4, 2)
    assert np.allclose(accountant.rdp, accountant.orders / 16)
    expected = min(accountant.orders / 16 + math.log(1e5) / (accountant.orders - 1))
    assert accountant.get_privacy_spent()[0] == pytest.approx(expected)
    sigma = accountant.calibrate_sigma(steps=100)
    check = RDPAccountant(accountant.orders)
    check.step(sigma, 100)
    assert check.get_privacy_spent()[0] <= 2


def test_exhaustion_persists_across_instances_and_key_changes(setup_bank):
    exporter, _, ledger = setup_bank
    first = release(exporter)
    assert first['body']['privacy']['epsilon_spent'] <= 2
    reloaded = PrivacyBudgetLedger(ledger.path, 'Bank_A')
    other = BankPrivacyExporter('Bank_A', reloaded, Ed25519PrivateKey.generate(), PSIHasher(secrets.token_bytes(32)), sigma=3)
    with pytest.raises(PrivacyBudgetExceeded):
        release(other)
    with pytest.raises(FileExistsError):
        PrivacyBudgetLedger.provision(ledger.path, 'Bank_A')
    with pytest.raises(ValueError):
        PrivacyBudgetLedger(ledger.path, 'Bank_B')
    with sqlite3.connect(ledger.path) as db:
        assert db.execute('SELECT COUNT(*) FROM releases').fetchone()[0] == 1
        with pytest.raises(sqlite3.IntegrityError):
            db.execute('DELETE FROM releases')


def reserve_once(path):
    try:
        PrivacyBudgetLedger(path, 'Bank_A').reserve(3)
        return True
    except PrivacyBudgetExceeded:
        return False


@pytest.mark.parametrize('executor', [ThreadPoolExecutor, ProcessPoolExecutor])
def test_concurrent_reservations_cannot_overspend(tmp_path, executor):
    path = tmp_path / 'budget.sqlite'
    PrivacyBudgetLedger.provision(path, 'Bank_A')
    with executor(max_workers=4) as pool:
        assert sum(pool.map(reserve_once, [str(path)] * 8)) == 1


def test_missing_or_corrupt_ledger_fails_closed(tmp_path):
    missing = tmp_path / 'missing.sqlite'
    with pytest.raises(sqlite3.OperationalError):
        PrivacyBudgetLedger(missing, 'Bank_A')
    assert not missing.exists()
    missing.write_text('broken')
    with pytest.raises(sqlite3.DatabaseError):
        PrivacyBudgetLedger(missing, 'Bank_A')


def test_failure_after_reservation_burns_budget(setup_bank, monkeypatch):
    exporter, _, ledger = setup_bank
    def fail(_):
        raise RuntimeError('noise generation failed')
    monkeypatch.setattr(exporter._dp, 'perturb_embeddings', fail)
    with pytest.raises(RuntimeError):
        release(exporter)
    with pytest.raises(PrivacyBudgetExceeded):
        ledger.reserve(3)


def test_rejected_budget_does_not_generate_noise(setup_bank, monkeypatch):
    exporter, _, _ = setup_bank
    release(exporter)
    def fail(_):
        pytest.fail('Noise must not be generated after budget rejection')
    monkeypatch.setattr(exporter._dp, 'perturb_embeddings', fail)
    with pytest.raises(PrivacyBudgetExceeded):
        release(exporter)


def test_under_noised_export_is_rejected_before_first_release(tmp_path):
    ledger = PrivacyBudgetLedger.provision(tmp_path / 'ledger', 'Bank_A')
    exporter = BankPrivacyExporter('Bank_A', ledger, Ed25519PrivateKey.generate(), PSIHasher(secrets.token_bytes(32)), sigma=1.25)
    with pytest.raises(PrivacyBudgetExceeded):
        release(exporter)


@pytest.mark.parametrize('mutation', ['plaintext', 'metadata', 'dimension', 'nonfinite', 'epsilon', 'delta', 'cost', 'noise', 'extra'])
def test_signed_invalid_input_is_rejected(setup_bank, mutation):
    exporter, key, _ = setup_bank
    payload = release(exporter)
    body = payload['body']
    token = next(iter(body['embeddings']))
    if mutation == 'plaintext':
        body['embeddings']['RAW_ACCOUNT'] = body['embeddings'].pop(token)
    elif mutation == 'metadata':
        body['edges'][0]['amount'] = 9999
    elif mutation == 'dimension':
        body['embeddings'][token] = [1.0]
    elif mutation == 'nonfinite':
        body['embeddings'][token][0] = float('inf')
    elif mutation == 'epsilon':
        body['privacy']['epsilon_spent'] = 2.01
    elif mutation == 'delta':
        body['privacy']['delta'] = 1e-4
    elif mutation == 'cost':
        body['privacy']['cumulative_rho'] = 0.0001
    elif mutation == 'noise':
        body['privacy']['noise_std'] = 0.1
    else:
        body['Account'] = 'RAW_ACCOUNT'
    # Invalid nonfinite JSON is itself rejected before verification.
    if mutation != 'nonfinite':
        payload['signature'] = key.sign(canonical_bytes(body)).hex()
    model = EnclaveAggregator({'Bank_A': key.public_key()}, embedding_dim=8)
    with pytest.raises(ValueError):
        model.process_cross_bank_transactions([payload])


def test_unsigned_tampered_unknown_and_legacy_input_rejected(setup_bank):
    exporter, key, _ = setup_bank
    payload = release(exporter)
    model = EnclaveAggregator({'Bank_A': key.public_key()}, embedding_dim=8)
    with pytest.raises(ValueError):
        model.process_cross_bank_transactions({'Account': ['secret-alice']})
    with pytest.raises(ValueError):
        model.process_cross_bank_transactions([payload['body']])
    wrong = EnclaveAggregator({'Bank_A': Ed25519PrivateKey.generate().public_key()}, embedding_dim=8)
    with pytest.raises(ValueError):
        wrong.process_cross_bank_transactions([payload])
    payload['body']['embeddings'][next(iter(payload['body']['embeddings']))][0] += 1
    with pytest.raises(ValueError):
        model.process_cross_bank_transactions([payload])


@pytest.mark.parametrize('edges', [True, False])
def test_end_to_end_protected_scoring_and_replay_postprocessing(setup_bank, edges):
    exporter, key, _ = setup_bank
    payload = release(exporter, edges)
    model = EnclaveAggregator({'Bank_A': key.public_key()}, embedding_dim=8)
    result = model.process_cross_bank_transactions([json.loads(json.dumps(payload))])
    assert len(result['scored_boundary_df']) == int(edges)
    assert result['privacy_metrics']['Bank_A']['epsilon_spent'] <= 2
    assert 'secret-alice' not in result['scored_boundary_df'].to_json()
    repeat = model.process_cross_bank_transactions([payload])
    assert np.array_equal(result['scored_boundary_df'].enclave_risk_score, repeat['scored_boundary_df'].enclave_risk_score)
    with pytest.raises(ValueError):
        model.process_cross_bank_transactions([payload, payload])


def test_matching_rejects_plaintext():
    with pytest.raises(ValueError):
        CentralPSICoordinator().register_bank_hashes('Bank_A', {'RAW_ACCOUNT'})


def test_successive_releases_compose_until_exhaustion(tmp_path):
    ledger = PrivacyBudgetLedger.provision(tmp_path / 'budget', 'Bank_A')
    previous = 0
    releases = 0
    while True:
        try:
            receipt = PrivacyBudgetLedger(ledger.path, 'Bank_A').reserve(8)
        except PrivacyBudgetExceeded:
            break
        assert previous < receipt['epsilon_spent'] <= 2
        previous = receipt['epsilon_spent']
        releases += 1
        assert releases < 100
    assert releases > 1
    accountant = RDPAccountant()
    accountant.step(8, releases)
    assert previous == pytest.approx(accountant.get_privacy_spent()[0])
    accountant.step(8)
    assert accountant.get_privacy_spent()[0] > 2


def test_two_bank_matching_uses_shared_pseudonyms_without_coordinator_key(tmp_path):
    hasher = PSIHasher(secrets.token_bytes(32))
    keys, payloads = {}, []
    for bank in ('Bank_A', 'Bank_B'):
        key = Ed25519PrivateKey.generate()
        keys[bank] = key.public_key()
        ledger = PrivacyBudgetLedger.provision(tmp_path / bank, bank)
        exporter = BankPrivacyExporter(bank, ledger, key, hasher)
        payloads.append(release(exporter))
    model = EnclaveAggregator(keys, embedding_dim=8)
    result = model.process_cross_bank_transactions(payloads)
    assert result['matching_metrics']['pairwise_intersections']['Bank_A_x_Bank_B'] == 2
    assert len(result['scored_boundary_df']) == 2
    assert not hasattr(model, 'hasher')
    with pytest.raises(ValueError):
        EnclaveAggregator({'Bank_C': Ed25519PrivateKey.generate().public_key()}, embedding_dim=8).process_cross_bank_transactions(payloads)


def test_bank_training_returns_only_protected_payload(tmp_path):
    import pandas as pd
    from src.models.train_local_gins import train_and_export_bank
    local_ledger = pd.DataFrame({
        'Account': ['private-a', 'private-b'], 'Account.1': ['private-b', 'private-a'],
        'From Bank': ['Bank_A', 'Bank_A'], 'To Bank': ['Bank_B', 'Bank_B'],
        'Amount Paid': [10, 20], 'Payment Format': ['Wire', 'Wire'],
        'Receiving Currency': ['US Dollar', 'US Dollar'], 'Is Laundering': [0, 1]})
    key = Ed25519PrivateKey.generate()
    ledger = PrivacyBudgetLedger.provision(tmp_path / 'budget', 'Bank_A')
    exporter = BankPrivacyExporter('Bank_A', ledger, key, PSIHasher(secrets.token_bytes(32)))
    private_dir = tmp_path / 'bank-private-checkpoints'
    payload = train_and_export_bank('Bank_A', local_ledger, exporter, private_dir, epochs=1)
    validate_protected_payload(payload, {'Bank_A': key.public_key()}, 128)
    assert 'private-a' not in json.dumps(payload)
    assert list(private_dir.iterdir()) == [private_dir / 'bank_a_gin.pt']
    assert not list(tmp_path.rglob('*node_embs.pkl'))
    result = EnclaveAggregator({'Bank_A': key.public_key()}).process_cross_bank_transactions([payload])
    assert len(result['scored_boundary_df']) == 2
