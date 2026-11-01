import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.seed_demo import PASSWORD, REFERRAL_SUMMARIES, seed


@pytest.fixture(scope='module')
def demo(tmp_path_factory):
    data_dir = tmp_path_factory.mktemp('admin') / 'data-demo'
    seed(data_dir)
    return data_dir


def login(data_dir, alias):
    client = TestClient(create_app(Settings(data_dir=data_dir)))
    client.__enter__()
    assert client.post('/api/login', json={'alias': alias, 'password': PASSWORD}).status_code == 200
    return client


def test_only_admin_reaches_admin_api(demo):
    for alias in ('user', 'expert'):
        client = login(demo, alias)
        for path in ('/api/admin/overview', '/api/admin/accounts', '/api/admin/audit', '/api/admin/referrals'):
            assert client.get(path).status_code == 403
    assert TestClient(create_app(Settings(data_dir=demo))).get('/api/admin/overview').status_code == 401


def test_overview_is_aggregate_and_never_contains_content(demo):
    client = login(demo, 'admin')
    response = client.get('/api/admin/overview?days=30')
    body = response.json()
    assert body['totals']['members'] >= 60 and body['totals']['moods'] > 0
    assert len(body['daily']) == 30
    for summary in REFERRAL_SUMMARIES:
        assert summary not in response.text
    assert 'Tổ trưởng' not in response.text and 'note' not in response.text
    referrals = client.get('/api/admin/referrals')
    assert 'summary' not in referrals.text and all(len(c['id']) == 8 for c in referrals.json()['cases'])


def test_small_groups_and_buckets_are_suppressed(demo):
    client = login(demo, 'admin')
    cohorts = client.get('/api/admin/cohorts').json()
    small = next(c for c in cohorts['cohorts'] if not c['reportable'])
    report = client.get('/api/admin/overview', params={'cohort': small['name']}).json()
    assert report == {'suppressed': True, 'members': None, 'min_group': 5, 'cohort': small['name']}
    body = client.get('/api/admin/overview').json()
    for bucket in body['phq9']['bands'] + body['gad7']['bands']:
        assert bucket['count'] is None or bucket['count'] == 0 or bucket['count'] >= 5
    assert all(d['mood_average'] is None or d['active'] >= 5 for d in body['daily'])


def test_admin_manages_expert_role_and_cohort_but_not_admins(demo):
    client = login(demo, 'admin')
    assert client.patch('/api/admin/accounts/dna-02', json={'role': 'expert', 'cohort': 'Nhóm mới'}).status_code == 200
    changed = next(a for a in client.get('/api/admin/accounts').json()['accounts'] if a['alias'] == 'dna-02')
    assert changed['role'] == 'expert' and changed['cohort'] == 'Nhóm mới'
    assert client.patch('/api/admin/accounts/admin', json={'role': 'user'}).status_code == 409
    assert client.patch('/api/admin/accounts/dna-02', json={'role': 'admin'}).status_code == 422
    assert client.patch('/api/admin/accounts/khong-ton-tai', json={'role': 'user'}).status_code == 404
    assert any(e['action'] == 'admin_role_expert' for e in client.get('/api/admin/audit').json()['events'])


def test_demo_user_and_expert_have_working_views(demo):
    user = login(demo, 'user')
    kinds = {r['kind'] for r in user.get('/api/records').json()['records']}
    assert {'mood', 'screening', 'chat'} <= kinds
    expert = login(demo, 'expert')
    assert any(c['status'] == 'pending' for c in expert.get('/api/expert/cases').json()['cases'])


def test_seed_refuses_to_touch_other_data(tmp_path):
    real = tmp_path / 'data'
    seed(real)
    with pytest.raises(SystemExit):
        seed(real)
    with pytest.raises(SystemExit):
        seed(real, reset=True)
