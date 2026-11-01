import asyncio
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
import contextlib
import httpx

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse

from .ai import AI, external_guard
from .config import Settings
from .models import ChatInput, Consent, FeedbackInput, MoodInput, ReframeInput, ScreeningInput
from .safety import rule_risk
from .screening import QUESTIONNAIRES, SOURCE, score_screening
from .storage import Store
from .core_api import core_router, public_session
from .admin import admin_router
from .dialogue import Dialogue, draft_ready
from .migrations import MIGRATIONS
from .models import Risk, SafetyCheckIn
from .personality import run_job
from .voice import speech_ready, voice_router
from .xiaozhi import xiaozhi_router

COOKIE = "cogai_session"


def create_app(settings: Settings | None = None):
    config = settings or Settings()
    store = Store(config)
    ai = AI(config)
    dialogue = Dialogue(store,ai,config)
    metrics = {'requests':0,'errors':0,'latency_ms_total':0}
    limits: dict[str, deque] = defaultdict(deque)
    locks: dict[str, asyncio.Lock] = {}
    def history_for(session):
        state = store.document(session,'conversation')
        return state if state else store.chat_history(session)

    async def maintenance():
        while True:
            await asyncio.sleep(max(5,config.maintenance_seconds))
            try:
                await asyncio.to_thread(store.cleanup)
            except Exception:
                metrics['errors']+=1

    @asynccontextmanager
    async def lifespan(app):
        if config.mode == "live" and not config.llm_api_key:
            raise RuntimeError("COGAI_MODE=live requires COGAI_LLM_API_KEY; no silent demo fallback.")
        if config.environment == 'production' and not config.cookie_secure:
            raise RuntimeError('Production requires Secure cookies and HTTPS.')
        store.cleanup()
        previous_client=ai.http_client
        client=httpx.AsyncClient(timeout=40,limits=httpx.Limits(max_connections=12,max_keepalive_connections=6))
        ai.http_client=client
        worker=asyncio.create_task(maintenance())
        try:
            yield
        finally:
            await client.aclose()
            if ai.http_client is client:
                ai.http_client=previous_client
            worker.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await worker

    app = FastAPI(title="CogAI development API", version="0.1.0", lifespan=lifespan)
    app.state.store = store
    app.state.ai = ai
    app.state.dialogue = dialogue
    app.state.metrics = metrics

    @app.middleware("http")
    async def boundary(request: Request, call_next):
        started=time.monotonic()
        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
            origin = request.headers.get("origin")
            if origin and origin not in config.allowed_origins:
                return JSONResponse({"detail": "Nguồn yêu cầu không được phép."}, status_code=403)
            if request.headers.get("sec-fetch-site") == "cross-site":
                return JSONResponse({"detail": "Yêu cầu khác nguồn bị từ chối."}, status_code=403)
            chunks, size = [], 0
            async for chunk in request.stream():
                size += len(chunk)
                if size > (2_000_000 if request.url.path in {'/api/voice/transcribe','/api/voice/turn'} else 32768):
                    return JSONResponse({"detail": "Nội dung quá dài."}, status_code=413)
                chunks.append(chunk)
            request._body = b"".join(chunks)
        if request.url.path.startswith("/api"):
            key = request.client.host if request.client else "local"
            now = time.monotonic()
            # Per-browser quota plus the separate IP cap for expensive operations.
            # Different signed-in users behind one proxy do not share read quotas.
            browser=request.cookies.get(COOKIE)
            quota_key=key+(':'+store.token_hash(browser) if browser else '')
            queue = limits[quota_key]
            while queue and queue[0] <= now - 60:
                queue.popleft()
            if len(queue) >= 90:
                return JSONResponse({"detail": "Bạn đang thao tác quá nhanh. Hãy thử lại sau một phút."}, status_code=429, headers={"Retry-After": "60"})
            queue.append(now)
            if ((request.method=='POST' and request.url.path in {"/api/chat", "/api/reframe", '/api/safety/check-in','/api/voice/transcribe','/api/voice/speak','/api/voice/turn'})
                    or (request.method=='GET' and request.url.path=='/api/voice/stream')):
                costly = limits["ai:" + quota_key]
                while costly and costly[0] <= now - 60:
                    costly.popleft()
                if len(costly) >= 10:
                    return JSONResponse({"detail": "Đã đạt giới hạn 10 yêu cầu AI/phút. Hãy thử lại sau."}, status_code=429, headers={"Retry-After": "60"})
                costly.append(now)
                shared=limits['ai-ip:'+key]
                while shared and shared[0]<=now-60:
                    shared.popleft()
                if len(shared)>=60:
                    return JSONResponse({'detail':'Đã đạt giới hạn xử lý chung. Hãy thử lại sau một phút.'},status_code=429,headers={'Retry-After':'60'})
                shared.append(now)
            if len(limits) > 1000:
                for stale in [k for k, q in limits.items() if not q or q[-1] < now - 60]:
                    del limits[stale]
            if request.url.path in {'/api/login','/api/account'} and request.method=='POST':
                auth_queue=limits['auth:'+key]
                while auth_queue and auth_queue[0]<=now-60:
                    auth_queue.popleft()
                if len(auth_queue)>=10:
                    return JSONResponse({'detail':'Hãy chờ một phút trước khi thử đăng nhập lại.'},status_code=429)
                auth_queue.append(now)
        try:
            response = await call_next(request)
        except Exception:
            metrics['errors']+=1
            # Avoid provider/SQL exception details or request content in HTTP output.
            return JSONResponse({'detail':'Dịch vụ tạm thời chưa sẵn sàng.'},status_code=503)
        metrics['requests']+=1
        metrics['errors']+=int(response.status_code>=500)
        metrics['latency_ms_total']+=round((time.monotonic()-started)*1000,2)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response

    def current(request: Request):
        store.cleanup()
        return store.session(request.cookies.get(COOKIE))

    app.include_router(core_router(store,config,current,COOKIE))
    app.include_router(admin_router(store,config,current,ai))

    def external_consent(session: dict):
        if config.mode == "live" and not session["consent"]["external_ai"]:
            raise HTTPException(403, "Bạn chưa đồng ý gửi nội dung tới dịch vụ AI ngoài hệ thống.")

    async def limited_ai(session: dict, operation):
        sid = session["id"]
        lock = locks.setdefault(sid, asyncio.Lock())
        if lock.locked():
            operation.close()
            raise HTTPException(409, "Đang xử lý một yêu cầu. Hãy chờ phản hồi.")
        try:
            async with lock:
                def guard():
                    with store.connection() as db:
                        store.validate(db,session)
                    external_consent(session)
                context_token=external_guard.set(guard)
                try:
                    return await asyncio.wait_for(operation, timeout=110)
                finally:
                    external_guard.reset(context_token)
        except TimeoutError:
            raise HTTPException(503, "Thời gian xử lý quá lâu. Hãy thử lại sau.")
        finally:
            if not lock.locked():
                locks.pop(sid, None)

    voice=voice_router(store,config,current,dialogue,limited_ai)
    app.state.voice = voice
    app.include_router(voice)
    if config.device_gateway:
        app.include_router(xiaozhi_router(store,config,dialogue,limited_ai,voice))

    @app.get("/api/health")
    def health():
        return {"status": "ok", "mode": config.mode, "version": "0.2.0", "clinical_validation": False}

    @app.get('/api/ready')
    def ready():
        with store.connection() as db:
            db.execute('SELECT 1').fetchone()
        return {'status':'ready','schema':len(MIGRATIONS),'research_reproduced':False}

    @app.get('/api/metrics')
    def operational_metrics(session=Depends(current)):
        if not session.get('account') or session['account']['role']!='expert':
            raise HTTPException(403,'Cần quyền vận hành.')
        return {**metrics,'ai':ai.metrics}

    @app.get("/api/config")
    def public_config():
        return {"mode": config.mode, "consent_version": "2026-10-22.v1", "session_hours": 24,
                'voice':{'transcription':bool(config.mode=='live' and config.transcription_model and config.llm_api_key),
                         'speech':bool(config.mode=='live' and speech_ready(config) and config.llm_api_key),
                         'max_audio_bytes':2_000_000,'max_recording_seconds':config.voice_max_recording_seconds},
                "screening_status": "vi-draft-1", "screening_review_status":"draft", "referral_connected": config.support_accepting,
                "research":{"care":"text-adapter-only","cograg":"semantic-adapter-configured" if config.embedding_model else "semantic-adapter-unavailable","eviocean":"adapter-unavailable"},
                "support": {"name": config.support_name, "phone": config.support_phone, "hours": config.support_hours}}

    @app.post("/api/session", status_code=201)
    def start(data: Consent, request: Request, response: Response):
        if config.mode == "live" and not data.external_ai:
            raise HTTPException(403, "Chế độ AI thật cần đồng ý xử lý qua nhà cung cấp. Bạn có thể dùng bản demo cục bộ.")
        old = request.cookies.get(COOKIE)
        if old:
            try:
                store.session(old)
                raise HTTPException(409, "Đã có phiên. Hãy kết thúc phiên trước khi đổi lựa chọn dữ liệu.")
            except HTTPException as exc:
                if exc.status_code != 401:
                    raise
        token, session = store.create_session(data.model_dump())
        response.set_cookie(COOKIE, token, httponly=True, secure=config.cookie_secure, samesite="strict", max_age=86400, path="/api")
        return public_session(session)

    @app.get("/api/session")
    def session_info(session=Depends(current)):
        return public_session(session)

    @app.delete("/api/session")
    def end(response: Response, session=Depends(current)):
        store.delete(session)
        response.delete_cookie(COOKIE, path="/api", secure=config.cookie_secure, httponly=True, samesite="strict")
        return {"deleted": True}

    @app.get("/api/records")
    def records(session=Depends(current)):
        return {"records": store.records(session)}

    @app.get("/api/export")
    def export(session=Depends(current)):
        with store.connection() as db:
            consent_events=[dict(r) for r in db.execute('SELECT revision,choices,created FROM consent_events WHERE owner_id=?',(session['id'],))]
            referrals=[{k:r[k] for k in ('id','status','created','updated')} | store.decrypt(r['summary'])
                       for r in db.execute('SELECT * FROM referrals WHERE owner_id=?',(session['id'],))]
            audit=[dict(r) for r in db.execute('SELECT action,created FROM audit WHERE owner_id=? ORDER BY id',(session['id'],))]
        store.audit(session,'data_exported')
        return {**public_session(session), "records": store.records(session, limit=None),'documents':store.documents(session),
                'consent_events':consent_events,'referrals':referrals,'audit':audit,
                "note": "Bản xuất chứa nội dung riêng tư. Tài khoản giữ dữ liệu theo thời hạn bạn chọn; phiên khách tối đa 24 giờ."}

    @app.post("/api/chat")
    async def chat(data: ChatInput, tasks: BackgroundTasks, session=Depends(current)):
        external_consent(session)
        async def execute():
            token=draft_ready.set((lambda draft:voice.prefetch(session,draft)) if data.speak and session['consent'].get('voice_processing') else None)
            try:
                return await dialogue.chat(session,data)
            finally:
                draft_ready.reset(token)
        result=await limited_ai(session, execute())
        if data.speak and session['consent'].get('voice_processing'):
            voice.prefetch(session)
        if session['consent']['personalization']:
            store.put_document(session,'personality_job','personality_job',{'status':'pending','revision':session['revision']})
            tasks.add_task(run_job,store,session)
        return result

    @app.get("/api/chat")
    def restore_chat(session=Depends(current)):
        history = history_for(session)
        active=store.document(session,'safety',{})
        support=active.get('level') in {'high','check_in'}
        return {"turns": history["turns"], "risk": active if support else history['risk'],
                'step':'support' if support else history.get('step','listen'),'conversation_id':history.get('conversation_id'),
                'situation':history.get('situation',''),'thought':history.get('thought','')}

    @app.post("/api/chat/reset")
    async def reset_chat(session=Depends(current)):
        async def execute():
            store.save(session, "chat_reset", {})
            store.remove_documents(session,'conversation')
            return {"reset": True}
        return await limited_ai(session, execute())

    @app.post('/api/safety/check-in')
    async def safety_check_in(data: SafetyCheckIn, session=Depends(current)):
        external_consent(session)
        async def execute():
            risk=await ai.risk(data.message)
            previous=store.document(session,'safety',{})
            dialogue.safety_event(session,'safety_check_in',risk)
            if previous.get('level')=='high' or risk.level!='low':
                return {'status':'support_required','risk':previous if previous.get('level')=='high' else risk.model_dump()}
            # This resolves an ambiguous phrase using explicit self-report, not a
            # clinical clearance. High-risk events are never cleared by this route.
            store.put_document(session,'safety','safety',risk.model_dump())
            store.save(session,'chat_reset',{})
            store.remove_documents(session,'conversation')
            store.audit(session,'ambiguous_safety_clarified')
            return {'status':'self_reported_no_current_danger','risk':risk.model_dump()}
        return await limited_ai(session,execute())

    @app.post("/api/reframe")
    async def reframe(data: ReframeInput, session=Depends(current)):
        external_consent(session)
        return await limited_ai(session, dialogue.reframe(session,data))

    @app.post("/api/moods", status_code=201)
    def mood(data: MoodInput, session=Depends(current)):
        # No external service is needed to save a check-in.
        risk = rule_risk(data.note)
        dialogue.safety_event(session,'mood',risk)
        record_id = store.save(session, "mood", data.model_dump())
        return {"record_id": record_id, "saved": session["consent"]["persist"], "risk": risk.model_dump()}

    @app.get("/api/questionnaires")
    def questionnaires(session=Depends(current)):
        return {"items": QUESTIONNAIRES, "version": "vi-draft-1", "review_status":"draft", "source": SOURCE,
                "notice": "Bản Việt hóa phục vụ phát triển, chưa được chuyên gia xác nhận cho thí điểm."}

    @app.post("/api/screenings")
    def screen(data: ScreeningInput, session=Depends(current)):
        try:
            result = score_screening(data)
        except ValueError as exc:
            raise HTTPException(422, str(exc))
        risk=Risk(level='check_in' if result['requires_support'] else 'low',reason='PHQ-9 item 9 needs follow-up' if result['requires_support'] else 'Deterministic questionnaire scoring',source='rules',requires_support=result['requires_support'])
        dialogue.safety_event(session,'screening',risk)
        result['review_status']='draft'
        result["record_id"] = store.save(session, "screening", {"answers": data.answers, **result})
        reminder=store.document(session,'reminder')
        if reminder and session['consent']['screening_reminders']:
            reminder['next_due']=time.time()+reminder['days']*86400
            store.put_document(session,'reminder','reminder',reminder)
        return result

    @app.post("/api/feedback", status_code=201)
    def feedback(data: FeedbackInput, session=Depends(current)):
        if not session["consent"]["persist"]:
            raise HTTPException(409, "Chế độ không lưu lịch sử không lưu phản hồi. Bạn có thể tải kết quả về máy.")
        if not store.owns_record(session, data.record_id):
            raise HTTPException(404, "Không tìm thấy kết quả trong phiên của bạn.")
        dialogue.safety_event(session,'exercise_feedback',rule_risk(data.comment))
        record_id = store.save(session, "feedback", data.model_dump())
        return {"record_id": record_id, "saved": True}

    return app


app = create_app()
