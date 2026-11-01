import hashlib
import hmac
import json
import secrets
import sqlite3
import time
import uuid
import threading
from contextlib import contextmanager
from functools import wraps

from cryptography.fernet import Fernet
from fastapi import HTTPException

from .config import Settings
from .migrations import migrate


def synchronized(method):
    @wraps(method)
    def wrapped(self,*args,**kwargs):
        with self.safety_lock:
            return method(self,*args,**kwargs)
    return wrapped


class Store:
    """Owner vaults survive auth expiry. Content and derived documents are encrypted."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.volatile = {}
        self.safety_lock=threading.RLock()
        settings.data_dir.mkdir(parents=True, exist_ok=True)
        key_path = settings.data_dir / ".key"
        if settings.encryption_key:
            key = settings.encryption_key.encode()
        else:
            if settings.environment == "production":
                raise RuntimeError("Production requires COGAI_ENCRYPTION_KEY from a secret store.")
            try:
                with key_path.open("xb") as file:
                    file.write(Fernet.generate_key())
            except FileExistsError:
                pass
            key = key_path.read_bytes()
        self.cipher = Fernet(key)
        self.key_fingerprint=hashlib.sha256(key).hexdigest()
        self.path = settings.data_dir / "cogai.sqlite3"
        with self.connection() as db:
            db.execute("PRAGMA journal_mode=WAL")
            migrate(db)

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=10)
        try:
            db.row_factory = sqlite3.Row
            db.execute("PRAGMA foreign_keys=ON")
            with db:
                yield db
        finally:
            db.close()

    @staticmethod
    def token_hash(token: str):
        return hashlib.sha256(token.encode()).hexdigest()

    def session(self, token: str | None):
        if not token:
            raise HTTPException(401, "Phiên đã kết thúc. Hãy bắt đầu lại để tiếp tục.")
        with self.connection() as db:
            self._expire(db)
            token_hash = self.token_hash(token)
            auth = db.execute("SELECT * FROM auth_sessions WHERE token_hash=?", (token_hash,)).fetchone()
            row = db.execute("SELECT * FROM sessions WHERE id=?", (auth['owner_id'],)).fetchone() if auth else db.execute(
                "SELECT * FROM sessions WHERE token_hash=? AND id NOT IN (SELECT owner_id FROM accounts)", (token_hash,)).fetchone()
            account = db.execute("SELECT alias,role,retention_days,cohort FROM accounts WHERE owner_id=?", (row['id'],)).fetchone() if row else None
        if not row:
            raise HTTPException(401, "Phiên đã kết thúc. Hãy bắt đầu lại để tiếp tục.")
        return {"id": row["id"], "consent": self.choices(json.loads(row["consent"])),
                "expires": auth['expires'] if auth else row['expires'], "revision": row['revision'],
                "auth_hash": token_hash, "account": dict(account) if account else None}

    @staticmethod
    def choices(consent):
        return {"personalization": False, "share_support": False, "screening_reminders": False, "voice_processing":False, **consent}

    def _expire(self, db):
        db.execute("DELETE FROM auth_sessions WHERE expires < ?", (time.time(),))
        db.execute("DELETE FROM sessions WHERE expires < ? AND id NOT IN (SELECT owner_id FROM accounts)", (time.time(),))

    def validate(self, db, session):
        row = db.execute('SELECT * FROM sessions WHERE id=?', (session['id'],)).fetchone()
        if not row or session['expires'] < time.time():
            raise HTTPException(401, 'Phiên đã kết thúc.')
        has_account=db.execute('SELECT 1 FROM accounts WHERE owner_id=?',(session['id'],)).fetchone()
        if has_account and not db.execute('SELECT 1 FROM auth_sessions WHERE token_hash=? AND owner_id=? AND expires>?', (session['auth_hash'],session['id'], time.time())).fetchone():
            raise HTTPException(401, 'Phiên đã kết thúc.')
        if row['revision'] != session.get('revision', 0):
            raise HTTPException(409, 'Quyền dữ liệu vừa thay đổi. Hãy tải lại trước khi tiếp tục.')
        return row

    def create_session(self, consent: dict):
        token = secrets.token_urlsafe(32)
        sid = str(uuid.uuid4())
        expires = time.time() + 86400
        with self.connection() as db:
            self._expire(db)
            consent = self.choices(consent)
            db.execute("INSERT INTO sessions(id,token_hash,consent,expires) VALUES (?,?,?,?)", (sid, self.token_hash(token), json.dumps(consent), expires))
            db.execute('INSERT INTO consent_events(owner_id,revision,choices,created) VALUES (?,?,?,?)', (sid,0,json.dumps(consent),time.time()))
        return token, self.session(token)

    def save(self, session: dict, kind: str, payload: dict):
        record_id = str(uuid.uuid4())
        # Check even without persistence: deletion while an AI call was in flight revokes it.
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            self.validate(db, session)
            if session["consent"]["persist"]:
                encrypted = self.cipher.encrypt(json.dumps(payload, ensure_ascii=False).encode())
                db.execute("INSERT INTO records VALUES (?,?,?,?,?)", (record_id, session["id"], kind, encrypted, time.time()))
        return record_id

    def records(self, session: dict, limit: int | None = 500):
        with self.connection() as db:
            query = "SELECT * FROM records WHERE session_id=? ORDER BY created DESC"
            if limit is not None:
                query += f" LIMIT {int(limit)}"
            rows = db.execute(query, (session["id"],)).fetchall()
        return [{"id": r["id"], "kind": r["kind"], "created": r["created"],
                 "payload": json.loads(self.cipher.decrypt(r["payload"]))} for r in rows]

    def owns_record(self, session: dict, record_id: str):
        with self.connection() as db:
            return db.execute("SELECT 1 FROM records WHERE session_id=? AND id=?", (session["id"], record_id)).fetchone() is not None

    def chat_history(self, session: dict):
        # rowid orders messages even when timestamps coincide. Reset preserves the diary.
        with self.connection() as db:
            rows = db.execute("""SELECT payload FROM records
                WHERE session_id=? AND kind='chat' AND rowid > COALESCE(
                    (SELECT MAX(rowid) FROM records WHERE session_id=? AND kind='chat_reset'), 0)
                ORDER BY rowid DESC LIMIT 6""", (session["id"], session["id"])).fetchall()
        turns = []
        risk = None
        for row in reversed(rows):
            payload = json.loads(self.cipher.decrypt(row["payload"]))
            turns.extend([{"role": "user", "content": payload["message"]},
                          {"role": "assistant", "content": payload["reply"]}])
            risk = payload.get("risk")
        return {"turns": turns, "risk": risk}

    def delete(self, session: dict):
        with self.connection() as db:
            db.execute("DELETE FROM sessions WHERE id=?", (session["id"],))
        self.volatile.pop(session['id'], None)

    def encrypt(self, payload):
        return self.cipher.encrypt(json.dumps(payload, ensure_ascii=False).encode())

    def decrypt(self, payload):
        return json.loads(self.cipher.decrypt(payload))

    @synchronized
    def document(self, session, key, default=None):
        with self.connection() as db:
            self.validate(db,session)
        if key in {'safety','safety_events'}:
            item=self.volatile.get(session['id'],{})
            if item.get('_expires',0)>time.time() and key in item:
                return item[key]
        if not session['consent']['persist']:
            item = self.volatile.get(session['id'], {})
            return item.get(key, default) if item.get('_expires', 0) > time.time() else default
        with self.connection() as db:
            self.validate(db, session)
            row = db.execute('SELECT payload FROM documents WHERE owner_id=? AND key=?', (session['id'], key)).fetchone()
        return self.decrypt(row['payload']) if row else default

    @synchronized
    def put_document(self, session, key, kind, payload):
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            self.validate(db, session)
            if session['consent']['persist']:
                now = time.time()
                db.execute('''INSERT INTO documents VALUES (?,?,?,?,?,?) ON CONFLICT(owner_id,key)
                    DO UPDATE SET payload=excluded.payload,updated=excluded.updated''',
                    (session['id'],key,kind,self.encrypt(payload),now,now))
                if key in {'safety','safety_events'}:
                    self.volatile.get(session['id'],{}).pop(key,None)
            else:
                volatile=self.volatile.setdefault(session['id'], {'_expires': session['expires'],'_kinds':{}})
                volatile[key] = payload
                volatile.setdefault('_kinds',{})[key]=kind

    def documents(self, session, kind=None):
        with self.connection() as db:
            self.validate(db, session)
            rows = db.execute('SELECT key,kind,payload FROM documents WHERE owner_id=? ORDER BY created', (session['id'],)).fetchall()
        return [{"key": r['key'], "kind": r['kind'], "payload": self.decrypt(r['payload'])} for r in rows if kind is None or r['kind'] == kind]

    @synchronized
    def remove_documents(self, session, kind):
        with self.connection() as db:
            self.validate(db, session)
            db.execute('DELETE FROM documents WHERE owner_id=? AND kind=?', (session['id'],kind))
        volatile=self.volatile.get(session['id'],{})
        for key in list(volatile.get('_kinds',{})):
            if volatile['_kinds'][key]==kind:
                volatile.pop(key,None)
                volatile['_kinds'].pop(key,None)

    def audit(self, session, action):
        with self.connection() as db:
            self.validate(db, session)
            db.execute('INSERT INTO audit(owner_id,action,created) VALUES (?,?,?)', (session['id'], action, time.time()))

    def record_safety(self,session,event,risk,resolve_check_in=False):
        # Read, compare and write in one SQLite transaction. Concurrent low events
        # cannot overwrite a high event from another channel or process. Only a
        # context-aware model answer may resolve check_in; high is never lowered here.
        with self.safety_lock, self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            self.validate(db,session)
            volatile=self.volatile.get(session['id'],{})
            def read(key,default):
                if key in volatile and volatile.get('_expires',0)>time.time():
                    return volatile[key]
                row=db.execute('SELECT payload FROM documents WHERE owner_id=? AND key=?',(session['id'],key)).fetchone()
                return self.decrypt(row['payload']) if row else default
            events=read('safety_events',[])
            active=read('safety',{})
            rank={'low':0,'unavailable':0,'check_in':1,'high':2}
            values={'safety_events':(events+[event])[-100:]}
            if (rank[risk['level']]>=rank.get(active.get('level','low'),0) or
                    (resolve_check_in and active.get('level')=='check_in' and risk['level']=='low')):
                values['safety']=risk
            now=time.time()
            if session['consent']['persist']:
                for key,value in values.items():
                    db.execute('''INSERT INTO documents VALUES (?,?,?,?,?,?) ON CONFLICT(owner_id,key)
                        DO UPDATE SET payload=excluded.payload,updated=excluded.updated''',
                        (session['id'],key,'safety',self.encrypt(value),now,now))
                    volatile.pop(key,None)
            else:
                volatile=self.volatile.setdefault(session['id'],{'_expires':session['expires'],'_kinds':{}})
                for key,value in values.items():
                    volatile[key]=value
                    volatile.setdefault('_kinds',{})[key]='safety'

    @staticmethod
    def password_hash(password, salt):
        return hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1).hex()

    def register(self, session, alias, password):
        salt = secrets.token_hex(16)
        hashed = self.password_hash(password, salt)
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            self.validate(db, session)
            if session.get('account'):
                raise HTTPException(409, 'Đã có tài khoản.')
            try:
                db.execute('INSERT INTO accounts(owner_id,alias,password_hash,salt,created) VALUES (?,?,?,?,?)', (session['id'],alias,hashed,salt,time.time()))
            except sqlite3.IntegrityError:
                raise HTTPException(409, 'Bí danh không khả dụng.')
            db.execute('INSERT INTO auth_sessions VALUES (?,?,?,?)', (session['auth_hash'],session['id'],session['expires'],time.time()))
            db.execute('UPDATE sessions SET expires=? WHERE id=?', (253402300799,session['id']))
        self.audit(session, 'account_created')

    def login(self, alias, password):
        with self.connection() as db:
            row = db.execute('SELECT * FROM accounts WHERE alias=?', (alias,)).fetchone()
        # Perform the same expensive hash for unknown aliases.
        actual = self.password_hash(password, row['salt'] if row else '00'*16)
        if not row or not hmac.compare_digest(actual, row['password_hash']):
            raise HTTPException(401, 'Bí danh hoặc mật khẩu không đúng.')
        token = secrets.token_urlsafe(32)
        with self.connection() as db:
            db.execute('INSERT INTO auth_sessions VALUES (?,?,?,?)', (self.token_hash(token),row['owner_id'],time.time()+86400,time.time()))
        return token, self.session(token)

    def logout(self, session, all_sessions=False):
        if not session.get('account'):
            self.delete(session)
            return
        with self.connection() as db:
            if all_sessions:
                db.execute('DELETE FROM auth_sessions WHERE owner_id=?', (session['id'],))
            else:
                db.execute('DELETE FROM auth_sessions WHERE token_hash=?', (session['auth_hash'],))
        self.volatile.pop(session['id'], None)

    @synchronized
    def consent(self, session, changes):
        safety={key:self.document(session,key) for key in ('safety','safety_events')}
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            self.validate(db, session)
            consent = {**session['consent'], **changes}
            if consent['personalization'] and not consent['persist']:
                raise HTTPException(422, 'Cá nhân hóa nhiều phiên cần quyền lưu lịch sử.')
            revision = session['revision']+1
            db.execute('UPDATE sessions SET consent=?,revision=? WHERE id=?', (json.dumps(consent),revision,session['id']))
            db.execute('INSERT INTO consent_events(owner_id,revision,choices,created) VALUES (?,?,?,?)', (session['id'],revision,json.dumps(consent),time.time()))
            if not consent['persist']:
                db.execute('DELETE FROM records WHERE session_id=?', (session['id'],))
                db.execute('DELETE FROM documents WHERE owner_id=?', (session['id'],))
            if not consent['personalization']:
                db.execute("DELETE FROM documents WHERE owner_id=? AND kind IN ('personality','personality_job')", (session['id'],))
            if not consent['screening_reminders']:
                db.execute("DELETE FROM documents WHERE owner_id=? AND kind='reminder'", (session['id'],))
            if not consent['share_support']:
                db.execute('DELETE FROM referrals WHERE owner_id=?', (session['id'],))
        if changes.get('persist') is False or changes.get('persist') is True:
            self.volatile.pop(session['id'], None)
            # Keep only the current safety branch in temporary memory. Turning
            # persistence on does not retroactively persist private session content.
            volatile={'_expires':session['expires'],'_kinds':{}}
            for key,value in safety.items():
                if value:
                    volatile[key]=value
                    volatile['_kinds'][key]='safety'
            self.volatile[session['id']]=volatile
        return {**session, 'consent': consent, 'revision': revision}

    def cleanup(self):
        now = time.time()
        with self.connection() as db:
            self._expire(db)
            for account in db.execute('SELECT owner_id,retention_days FROM accounts').fetchall():
                cutoff = now-account['retention_days']*86400
                removed=db.execute('DELETE FROM records WHERE session_id=? AND created<?', (account['owner_id'],cutoff)).rowcount
                # Delete derived state as well; otherwise a fresh summary could retain expired sources.
                stale = db.execute('SELECT 1 FROM documents WHERE owner_id=? AND created<? LIMIT 1', (account['owner_id'],cutoff)).fetchone()
                if stale or removed:
                    db.execute('DELETE FROM documents WHERE owner_id=?', (account['owner_id'],))
                db.execute('DELETE FROM referrals WHERE owner_id=? AND created<?', (account['owner_id'],cutoff))
            db.execute('DELETE FROM audit WHERE created<?', (now-90*86400,))
        for owner in list(self.volatile):
            if self.volatile[owner].get('_expires',0) < now:
                self.volatile.pop(owner, None)
