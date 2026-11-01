"""Operator dashboard: aggregate, anonymous statistics and account metadata only.

Admins never receive conversation content, mood notes or support summaries. Any
group or bucket with fewer than `aggregate_min_group` people is suppressed, so an
organisation report cannot single anyone out (brief, table 1 and section 2).
"""
import json
import statistics
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import Field

from .models import InputModel

VN = timezone(timedelta(hours=7))
ROLES = ('user', 'expert')  # admin itself is granted only from the operator CLI
PHQ_BANDS = ['Tối thiểu', 'Nhẹ', 'Vừa', 'Khá nặng', 'Nặng']
GAD_BANDS = ['Tối thiểu', 'Nhẹ', 'Vừa', 'Nặng']
REFERRAL_STATUSES = ['pending', 'accepted', 'in_progress', 'resolved', 'declined', 'out_of_hours', 'unavailable']
CONSENTS = ['persist', 'external_ai', 'voice_processing', 'personalization', 'share_support', 'screening_reminders']


class AccountChange(InputModel):
    role: Literal['user', 'expert'] | None = None
    cohort: Annotated[str, Field(max_length=80)] | None = None


def day_of(seconds):
    return datetime.fromtimestamp(seconds, VN).date().isoformat()


def admin_router(store, config, current, ai):
    router = APIRouter(prefix='/api/admin')
    k = config.aggregate_min_group

    def admin(session=Depends(current)):
        if not session.get('account') or session['account']['role'] != 'admin':
            raise HTTPException(403, 'Cần tài khoản quản trị do người vận hành cấp quyền.')
        with store.connection() as db:
            store.validate(db, session)
        return session

    def hide(count):
        """Counts below the threshold are reported as None ("< k")."""
        return count if count >= k else None

    def members(db, cohort):
        rows = db.execute('SELECT owner_id,cohort,created,role,consent FROM accounts JOIN sessions ON sessions.id=accounts.owner_id').fetchall()
        return [r for r in rows if r['role'] == 'user' and (cohort is None or r['cohort'] == cohort)]

    @router.get('/cohorts')
    def cohorts(session=Depends(admin)):
        with store.connection() as db:
            rows = db.execute("SELECT COALESCE(cohort,'') AS cohort,COUNT(*) AS n FROM accounts WHERE role='user' GROUP BY cohort ORDER BY cohort").fetchall()
        return {'min_group': k, 'cohorts': [{'name': r['cohort'], 'members': r['n'], 'reportable': r['n'] >= k}
                                            for r in rows if r['cohort']]}

    @router.get('/overview')
    def overview(days: int = Query(30, ge=7, le=180), cohort: str | None = None, session=Depends(admin)):
        now = time.time()
        since = now - days * 86400
        with store.connection() as db:
            people = members(db, cohort or None)
            if cohort and len(people) < k:
                store.audit(session, 'admin_report_suppressed')
                return {'suppressed': True, 'members': None, 'min_group': k, 'cohort': cohort}
            owners = {r['owner_id'] for r in people}
            records = [r for r in db.execute('SELECT session_id,kind,payload,created FROM records WHERE created>=?', (since,))
                       if r['session_id'] in owners]
            documents = [r for r in db.execute("SELECT owner_id,payload FROM documents WHERE key='safety_events'")
                         if r['owner_id'] in owners]
            referrals = [r for r in db.execute('SELECT owner_id,status,created,updated FROM referrals WHERE created>=?', (since,))
                         if r['owner_id'] in owners]
        days_list = [day_of(now - i * 86400) for i in range(days - 1, -1, -1)]
        active = defaultdict(set)
        kinds = defaultdict(Counter)
        moods = defaultdict(lambda: defaultdict(list))
        latest = {}
        mood_scores = Counter()
        for r in records:
            day = day_of(r['created'])
            active[day].add(r['session_id'])
            kinds[day][r['kind']] += 1
            if r['kind'] in {'mood', 'screening'}:
                payload = json.loads(store.cipher.decrypt(r['payload']))
                if r['kind'] == 'mood':
                    moods[day][r['session_id']].append(payload['score'])
                    mood_scores[payload['score']] += 1
                else:
                    key = (r['session_id'], payload.get('kind'))
                    if key not in latest or latest[key][0] < r['created']:
                        latest[key] = (r['created'], payload.get('band'), payload.get('requires_support', False))
        daily = []
        for day in days_list:
            users = moods[day]
            # Mean of each person's mean, only when enough distinct people reported that day.
            mood = round(statistics.mean(statistics.mean(v) for v in users.values()), 2) if len(users) >= k else None
            daily.append({'day': day, 'active': hide(len(active[day])) if active[day] else 0,
                          'chats': kinds[day]['chat'], 'moods': kinds[day]['mood'],
                          'screenings': kinds[day]['screening'], 'exercises': kinds[day]['reframe'], 'mood_average': mood})

        def bands(kind, labels):
            counts = Counter(band for (owner, name), (_, band, _) in latest.items() if name == kind)
            total = sum(counts.values())
            return {'respondents': hide(total), 'bands': [{'band': b, 'count': hide(counts[b]) if counts[b] else 0} for b in labels]}

        safety = Counter()
        for row in documents:
            for event in store.decrypt(row['payload']):
                if event.get('created', 0) >= since:
                    safety[event['level']] += 1
        follow_up = sum(1 for (_, kind), (_, _, flag) in latest.items() if kind == 'PHQ-9' and flag)
        statuses = Counter(r['status'] for r in referrals)
        responded = [(r['updated'] - r['created']) / 3600 for r in referrals if r['status'] not in {'pending', 'unavailable'}]
        consent = Counter()
        for p in people:
            choices = store.choices(json.loads(p['consent']))
            for key in CONSENTS:
                consent[key] += bool(choices.get(key))
        active_ids = set().union(*active.values()) if active else set()
        week = {r['session_id'] for r in records if r['created'] >= now - 7 * 86400}
        store.audit(session, 'admin_report_viewed')
        return {
            'suppressed': False, 'min_group': k, 'cohort': cohort, 'days': days, 'generated': now,
            'totals': {'members': len(people), 'active_period': hide(len(active_ids)), 'active_week': hide(len(week)),
                       'chats': sum(c['chat'] for c in kinds.values()), 'moods': sum(c['mood'] for c in kinds.values()),
                       'screenings': sum(c['screening'] for c in kinds.values()),
                       'exercises': sum(c['reframe'] for c in kinds.values()),
                       'screening_completion': round(len({o for (o, _) in latest}) / len(people), 3) if people else None},
            'daily': daily,
            'mood_distribution': [{'score': s, 'count': hide(mood_scores[s]) if mood_scores[s] else 0} for s in range(1, 6)],
            'phq9': bands('PHQ-9', PHQ_BANDS), 'gad7': bands('GAD-7', GAD_BANDS),
            'safety': {'high': safety['high'], 'check_in': safety['check_in'], 'unavailable': safety['unavailable'],
                       'phq9_item9_follow_up': follow_up},
            'referrals': {'statuses': [{'status': s, 'count': statuses[s]} for s in REFERRAL_STATUSES],
                          'median_response_hours': round(statistics.median(responded), 1) if responded else None},
            'consent': [{'purpose': key, 'share': round(consent[key] / len(people), 3) if people else None} for key in CONSENTS],
            'ai': {'calls': ai.metrics['calls'], 'failures': ai.metrics['failures'],
                   'average_latency_ms': round(ai.metrics['latency_ms_total'] / ai.metrics['calls']) if ai.metrics['calls'] else None},
        }

    @router.get('/accounts')
    def accounts(session=Depends(admin)):
        with store.connection() as db:
            rows = db.execute('''SELECT a.owner_id,a.alias,a.role,a.cohort,a.retention_days,a.created,
                    (SELECT COUNT(*) FROM records r WHERE r.session_id=a.owner_id) AS records,
                    (SELECT MAX(created) FROM records r WHERE r.session_id=a.owner_id) AS last_record,
                    (SELECT MAX(created) FROM auth_sessions s WHERE s.owner_id=a.owner_id) AS last_login,
                    (SELECT COUNT(*) FROM referrals f WHERE f.owner_id=a.owner_id) AS referrals
                FROM accounts a ORDER BY a.created DESC''').fetchall()
            guests = db.execute('SELECT COUNT(*) FROM sessions WHERE id NOT IN (SELECT owner_id FROM accounts) AND expires>?',
                                (time.time(),)).fetchone()[0]
        store.audit(session, 'admin_accounts_viewed')
        return {'guests_active': guests, 'roles': list(ROLES), 'accounts': [{
            'alias': r['alias'], 'role': r['role'], 'cohort': r['cohort'] or '', 'retention_days': r['retention_days'],
            'created': r['created'], 'records': r['records'], 'referrals': r['referrals'],
            'last_active': max(filter(None, [r['last_record'], r['last_login'], r['created']])),
        } for r in rows]}

    @router.patch('/accounts/{alias}')
    def change_account(alias: str, data: AccountChange, session=Depends(admin)):
        if alias == session['account']['alias']:
            raise HTTPException(409, 'Không tự thay đổi tài khoản quản trị đang dùng.')
        with store.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT owner_id,role FROM accounts WHERE alias=?', (alias,)).fetchone()
            if not row:
                raise HTTPException(404, 'Không tìm thấy tài khoản.')
            if row['role'] == 'admin':
                raise HTTPException(409, 'Quyền quản trị chỉ thay đổi bằng công cụ vận hành.')
            if data.role is not None:
                db.execute('UPDATE accounts SET role=? WHERE owner_id=?', (data.role, row['owner_id']))
                db.execute('INSERT INTO audit(owner_id,action,created) VALUES (?,?,?)', (row['owner_id'], 'admin_role_' + data.role, time.time()))
            if data.cohort is not None:
                db.execute('UPDATE accounts SET cohort=? WHERE owner_id=?', (data.cohort.strip() or None, row['owner_id']))
        store.audit(session, 'admin_account_changed')
        return {'alias': alias, 'updated': True}

    @router.get('/referrals')
    def referrals(session=Depends(admin)):
        # Status and timing only: the user shared the summary with receiving experts, not admins.
        with store.connection() as db:
            rows = db.execute('''SELECT f.id,f.status,f.created,f.updated,e.alias AS expert,a.cohort
                FROM referrals f LEFT JOIN accounts e ON e.owner_id=f.assigned_to
                LEFT JOIN accounts a ON a.owner_id=f.owner_id ORDER BY f.created DESC LIMIT 200''').fetchall()
        return {'cases': [{'id': r['id'][:8], 'status': r['status'], 'created': r['created'], 'updated': r['updated'],
                           'expert': r['expert'] or '', 'cohort': r['cohort'] or ''} for r in rows]}

    @router.get('/audit')
    def audit(limit: int = Query(150, ge=10, le=500), session=Depends(admin)):
        with store.connection() as db:
            rows = db.execute('''SELECT au.action,au.created,a.alias FROM audit au
                LEFT JOIN accounts a ON a.owner_id=au.owner_id ORDER BY au.created DESC LIMIT ?''', (limit,)).fetchall()
        return {'events': [{'action': r['action'], 'created': r['created'], 'actor': r['alias'] or 'Khách'} for r in rows]}

    return router
