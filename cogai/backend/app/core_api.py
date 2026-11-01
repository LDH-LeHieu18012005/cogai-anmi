import time
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response

from .models import CaseUpdate, ConsentChange, Credentials, ReferralInput, ReminderInput, RetentionInput, SafetyPlanInput
from .personality import run_job


def public_session(session):
    return {k: session[k] for k in ('consent', 'expires', 'account')}


def core_router(store, config, current, cookie):
    router = APIRouter(prefix='/api')

    def set_cookie(response, token):
        response.set_cookie(cookie,token,httponly=True,secure=config.cookie_secure,samesite='strict',max_age=86400,path='/api')

    def require(session, purpose):
        if not session['consent'][purpose]:
            raise HTTPException(403, 'Chưa có đồng ý cho mục đích này.')

    def expert(session=Depends(current)):
        if not session.get('account') or session['account']['role'] != 'expert':
            raise HTTPException(403, 'Cần tài khoản chuyên gia được người vận hành cấp quyền.')
        return session

    @router.post('/account', status_code=201)
    def register(data: Credentials, request: Request, session=Depends(current)):
        store.register(session, data.alias, data.password)
        return public_session(store.session(request.cookies.get(cookie)))

    @router.post('/login')
    def login(data: Credentials, request: Request, response: Response):
        # Do not silently orphan an active guest or replace another signed-in account.
        try:
            store.session(request.cookies.get(cookie))
        except HTTPException as exc:
            if exc.status_code != 401:
                raise
        else:
            raise HTTPException(409, 'Hãy đăng xuất phiên hiện tại trước khi đăng nhập.')
        token, session = store.login(data.alias, data.password)
        set_cookie(response, token)
        store.audit(session, 'login')
        return public_session(session)

    @router.post('/logout')
    def logout(response: Response, session=Depends(current)):
        store.audit(session, 'logout')
        store.logout(session)
        response.delete_cookie(cookie, path='/api')
        return {'logged_out': True}

    @router.post('/logout-all')
    def logout_all(response: Response, session=Depends(current)):
        store.logout(session, all_sessions=True)
        response.delete_cookie(cookie,path='/api')
        return {'logged_out': True}

    @router.delete('/account')
    def delete_account(response: Response, session=Depends(current)):
        store.delete(session)
        response.delete_cookie(cookie,path='/api')
        return {'deleted': True}

    @router.patch('/consent')
    def consent(data: ConsentChange, session=Depends(current)):
        changes = data.model_dump(exclude_none=True)
        if changes.get('persist') is False:
            changes['personalization'] = False
        return public_session(store.consent(session, changes))

    @router.put('/retention')
    def retention(data: RetentionInput, session=Depends(current)):
        if not session.get('account'):
            raise HTTPException(409, 'Phiên khách hết hạn sau 24 giờ. Hãy tạo tài khoản để chọn thời hạn.')
        with store.connection() as db:
            store.validate(db, session)
            db.execute('UPDATE accounts SET retention_days=? WHERE owner_id=?', (data.days,session['id']))
        store.cleanup()
        store.audit(session, 'retention_changed')
        return {'days': data.days}

    @router.get('/safety')
    def safety(session=Depends(current)):
        return {'state': store.document(session,'safety',{}),
                'events': store.document(session,'safety_events',[])}

    @router.get('/safety-plan')
    def safety_plan(session=Depends(current)):
        return store.document(session,'safety_plan',{}) or {'empty':True}

    @router.put('/safety-plan')
    def save_safety_plan(data: SafetyPlanInput, session=Depends(current)):
        # The user's own plan; kept like other private records (encrypted, deleted with the account).
        plan={**data.model_dump(),'updated':time.time()}
        store.put_document(session,'safety_plan','safety_plan',plan)
        store.audit(session,'safety_plan_saved')
        return {**plan,'saved':session['consent']['persist']}

    @router.get('/reminders')
    def reminders(session=Depends(current)):
        return store.document(session,'reminder',{'enabled':False}) if session['consent']['screening_reminders'] else {'enabled':False}

    @router.put('/reminders')
    def reminder(data: ReminderInput, session=Depends(current)):
        require(session, 'screening_reminders')
        result = {'enabled':True, 'days': data.days, 'next_due':time.time()+data.days*86400,
                  'delivery':'in_app', 'version':'vi-draft-1'}
        store.put_document(session,'reminder','reminder',result)
        return result

    @router.get('/personality')
    def personality(session=Depends(current)):
        if not session['consent']['personalization']:
            return {'status':'disabled'}
        return store.document(session,'personality',{'status':'insufficient_evidence','traits':{}})

    @router.post('/personality/jobs', status_code=202)
    def queue_personality(tasks: BackgroundTasks, session=Depends(current)):
        require(session,'personalization')
        store.put_document(session,'personality_job','personality_job',{'status':'pending','revision':session['revision']})
        tasks.add_task(run_job, store, session)
        return {'status':'pending'}

    def case_rows(session, professional=False):
        with store.connection() as db:
            store.validate(db,session)
            if professional:
                rows = db.execute('''SELECT r.* FROM referrals r JOIN sessions s ON s.id=r.owner_id
                    WHERE (r.assigned_to=? OR (r.assigned_to IS NULL AND r.status='pending'))''', (session['id'],)).fetchall()
            else:
                rows = db.execute('SELECT * FROM referrals WHERE owner_id=? ORDER BY created DESC', (session['id'],)).fetchall()
        return [{**{k:r[k] for k in ('id','status','created','updated')}, 'summary':store.decrypt(r['summary'])['summary']} for r in rows]

    @router.get('/referrals')
    def referrals(session=Depends(current)):
        return {'cases':case_rows(session)}

    @router.post('/referrals', status_code=201)
    def referral(data: ReferralInput, session=Depends(current)):
        require(session,'share_support')
        cid, now = str(uuid.uuid4()), time.time()
        # accepting is an operator assertion about a real service, false by default.
        status = 'pending' if config.support_accepting else 'unavailable'
        with store.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            store.validate(db,session)
            db.execute('INSERT INTO referrals VALUES (?,?,?,?,?,?,?)',
                       (cid,session['id'],None,status,store.encrypt({'summary':data.summary}),now,now))
        store.audit(session, 'support_requested')
        return {'id':cid,'status':status,'summary':data.summary,'created':now,'updated':now}

    @router.delete('/referrals/{cid}')
    def cancel_case(cid: str, session=Depends(current)):
        with store.connection() as db:
            store.validate(db,session)
            db.execute('DELETE FROM referrals WHERE id=? AND owner_id=?', (cid,session['id']))
        return {'deleted':True}

    @router.get('/expert/cases')
    def expert_cases(session=Depends(expert)):
        store.audit(session,'case_queue_viewed')
        return {'cases':case_rows(session,True)}

    @router.patch('/expert/cases/{cid}')
    def update_case(cid: str, data: CaseUpdate, session=Depends(expert)):
        with store.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            store.validate(db,session)
            row = db.execute('SELECT * FROM referrals WHERE id=?', (cid,)).fetchone()
            if not row or row['assigned_to'] not in (None,session['id']):
                raise HTTPException(404,'Không có quyền với yêu cầu này.')
            transitions = {'pending':{'accepted','declined','unavailable','out_of_hours'},
                           'accepted':{'in_progress','resolved','declined'}, 'in_progress':{'resolved','declined'}}
            if data.status not in transitions.get(row['status'],set()):
                raise HTTPException(409,'Chuyển trạng thái không hợp lệ; cần xác nhận tiếp nhận trước.')
            db.execute('UPDATE referrals SET status=?,assigned_to=?,updated=? WHERE id=?', (data.status,session['id'],time.time(),cid))
        store.audit(session,'case_'+data.status)
        return {'id':cid,'status':data.status}

    return router
