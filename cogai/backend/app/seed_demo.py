"""Synthetic demo data for exploring the user, expert and admin views.

Every person, organisation and sentence here is invented. Data goes into its own
data directory (default ./data-demo) and never into the real ./data store.

    python -m app.seed_demo                 # create ./data-demo
    python -m app.seed_demo --reset         # rebuild it from scratch
"""
import argparse
import json
import random
import secrets
import shutil
import time
import uuid
from pathlib import Path

from .config import Settings
from .models import ScreeningInput
from .screening import score_screening
from .storage import Store

PASSWORD = 'cogai2026demo'
DAYS = 45
CONSENT_VERSION = '2026-10-22.v1'
# (alias prefix, members, life situation). The last group is deliberately below
# the anonymity threshold so the admin view shows a suppressed report.
COHORTS = {
    'Doanh nghiệp A – may mặc, KCN (mẫu)': ('dna', 24, 'worker'),
    'Doanh nghiệp B – điện tử, KCN (mẫu)': ('dnb', 18, 'worker'),
    'Trường đại học (mẫu) – Khóa 22': ('sv', 22, 'student'),
    'Nhóm thử nghiệm nhỏ (mẫu)': ('tn', 3, 'student'),
}
NOTES = {
    'worker': ['Hết ca đêm, mệt nhưng ổn', 'Tổ trưởng nhắc nhở trước cả tổ', 'Gọi điện được cho mẹ', 'Tăng ca tới 9 giờ tối',
               'Ngủ bù được buổi chiều', 'Lo tiền gửi về nhà tháng này', 'Ăn cơm với bạn cùng phòng', ''],
    'student': ['Ôn thi muộn, khó ngủ', 'Thuyết trình nhóm suôn sẻ', 'Nhớ nhà', 'Chưa tìm được chỗ thực tập',
                'Đi chạy bộ buổi tối', 'Cãi nhau với bạn cùng phòng', 'Được điểm tốt môn cơ sở', ''],
}
CHATS = {
    'worker': [('Hôm nay mình làm ca đêm về không ngủ được.', 'Làm ca đêm rồi về lại khó ngủ thật sự rất mệt. Điều gì đang làm bạn trằn trọc nhất lúc này?'),
               ('Tổ trưởng mắng mình trước cả tổ, mình thấy xấu hổ.', 'Bị nhắc nhở trước mọi người dễ khiến mình thấy xấu hổ. Lúc đó trong đầu bạn nghĩ gì về bản thân?'),
               ('Tháng này tăng ca nhiều quá, không có thời gian nghỉ.', 'Tăng ca liên tục làm cơ thể và tinh thần khó hồi phục. Tuần này có khoảng nào bạn nghỉ được dù ngắn không?'),
               ('Mình lo không đủ tiền gửi về cho bố mẹ.', 'Lo chuyện tiền bạc cho gia đình là một áp lực lớn. Bạn muốn mình cùng tách ra phần nào đã chắc và phần nào còn đang lo không?')],
    'student': [('Mai thi rồi mà mình chưa ôn xong.', 'Sát ngày thi mà còn nhiều phần chưa ôn dễ làm mình hoảng. Phần nào bạn thấy cần ưu tiên nhất tối nay?'),
                ('Mình thấy cô đơn từ khi lên thành phố học.', 'Xa nhà và chưa có nhiều bạn thân có thể rất cô đơn. Có lúc nào trong tuần bạn thấy dễ chịu hơn một chút không?'),
                ('Mình sợ ra trường không xin được việc.', 'Lo về việc làm sau khi ra trường là điều nhiều bạn gặp. Điều gì khiến bạn nghĩ mình sẽ không xin được việc?'),
                ('Bạn cùng phòng hay về muộn, mình không ngủ được.', 'Thiếu ngủ vì sinh hoạt chung khó chịu thật. Bạn đã từng thử nói chuyện với bạn ấy về giờ giấc chưa?')],
}
REFERRAL_SUMMARIES = [
    'Mất ngủ kéo dài sau ca đêm khoảng ba tuần, PHQ-9 ở mức vừa. Muốn trao đổi với chuyên gia về giấc ngủ.',
    'Áp lực thi cử và cảm thấy cô đơn, mong được nói chuyện với người tư vấn của trường.',
    'Căng thẳng với quản lý trực tiếp, lo mất việc. Muốn được tư vấn cách xử lý.',
    'Lo âu kéo dài, GAD-7 mức vừa. Muốn biết nên bắt đầu từ đâu.',
    'Buồn chán sau khi chia tay, ảnh hưởng tới việc học. Đồng ý chia sẻ tóm tắt này.',
    'Đã có lúc nghĩ tới việc không muốn sống, hiện an toàn và đang ở cùng bạn. Cần người thật liên hệ.',
    'Mệt mỏi và mất hứng thú gần một tháng, muốn được đánh giá thêm.',
]


def clamp(value, low, high):
    return max(low, min(high, value))


class Seeder:
    def __init__(self, store: Store, rng: random.Random):
        self.store, self.rng, self.now = store, rng, time.time()
        self.salt = secrets.token_hex(16)
        self.hash = Store.password_hash(PASSWORD, self.salt)  # one shared demo password, hashed once

    def account(self, db, alias, role='user', cohort=None, created=None, consent=None):
        owner = str(uuid.uuid4())
        created = created or self.now - DAYS * 86400
        choices = Store.choices({'accepted': True, 'adult': True, 'persist': True, 'external_ai': True,
                                 'version': CONSENT_VERSION, **(consent or {})})
        db.execute('INSERT INTO sessions(id,token_hash,consent,expires) VALUES (?,?,?,?)',
                   (owner, Store.token_hash(secrets.token_urlsafe(32)), json.dumps(choices), 253402300799))
        db.execute('INSERT INTO consent_events(owner_id,revision,choices,created) VALUES (?,?,?,?)', (owner, 0, json.dumps(choices), created))
        db.execute('INSERT INTO accounts(owner_id,alias,password_hash,salt,role,retention_days,created,cohort) VALUES (?,?,?,?,?,?,?,?)',
                   (owner, alias, self.hash, self.salt, role, 365, created, cohort))
        self.audit(db, owner, 'account_created', created)
        return owner

    def record(self, db, owner, kind, payload, created):
        db.execute('INSERT INTO records VALUES (?,?,?,?,?)',
                   (str(uuid.uuid4()), owner, kind, self.store.encrypt({**payload, 'synthetic': True}), created))

    def document(self, db, owner, key, kind, payload):
        db.execute('INSERT OR REPLACE INTO documents VALUES (?,?,?,?,?,?)',
                   (owner, key, kind, self.store.encrypt(payload), self.now, self.now))

    def audit(self, db, owner, action, created):
        db.execute('INSERT INTO audit(owner_id,action,created) VALUES (?,?,?)', (owner, action, created))

    def screening(self, kind, severity, item9=0):
        count = 9 if kind == 'PHQ-9' else 7
        answers = [clamp(round(severity * 3 + self.rng.gauss(0, .6)), 0, 3) for _ in range(count)]
        if kind == 'PHQ-9':
            answers[8] = item9
        result = score_screening(ScreeningInput(kind=kind, answers=answers))
        return {'answers': answers, **result, 'review_status': 'draft'}

    def person(self, db, owner, situation, severity, activity, rich=False):
        """45 days of check-ins, chats, exercises and fortnightly screenings."""
        events = []
        start = self.now - DAYS * 86400
        for day in range(DAYS):
            base = start + day * 86400
            weekday = time.localtime(base).tm_wday
            if self.rng.random() > (activity if not rich else .85):
                continue
            at = base + self.rng.uniform(7, 22) * 3600
            if at > self.now:
                continue
            # Shift work and exam weeks pull mood down; weekends lift it slightly.
            strain = .5 if situation == 'worker' and weekday in (1, 3) else .6 if situation == 'student' and DAYS - day < 12 else 0
            score = clamp(round(4.2 - 2.6 * severity - strain + (.4 if weekday >= 5 else 0) + self.rng.gauss(0, .7)), 1, 5)
            self.record(db, owner, 'mood', {'score': score, 'note': self.rng.choice(NOTES[situation])}, at)
            events.append(('mood', 'low', at))
            if self.rng.random() < (.55 if rich else .3):
                conversation = str(uuid.uuid4())
                for turn in self.rng.sample(CHATS[situation], k=self.rng.randint(1, 2)):
                    at += self.rng.uniform(60, 400)
                    self.record(db, owner, 'chat', {'message': turn[0], 'reply': turn[1], 'mode': 'demo', 'step': 'listen',
                                                    'conversation_id': conversation,
                                                    'risk': {'level': 'low', 'reason': 'Dữ liệu mẫu', 'source': 'rules', 'requires_support': False}}, at)
                    events.append(('chat', 'low', at))
            if self.rng.random() < (.12 if rich else .05):
                situation_text, thought = CHATS[situation][self.rng.randrange(4)][0], 'Chắc mình không làm được gì ra hồn.'
                self.record(db, owner, 'reframe', {'input': {'situation': situation_text, 'thought': thought, 'lenses': ['CBT']},
                    'blocked': False, 'mode': 'demo', 'risk': {'level': 'low', 'reason': 'Dữ liệu mẫu', 'source': 'rules', 'requires_support': False},
                    'candidates': [{'lens': 'CBT', 'reframe': 'Một ngày khó khăn chưa nói lên toàn bộ khả năng của mình.',
                                    'rationale': 'Tách sự kiện và kết luận.', 'next_step': 'Viết ra một việc mình đã làm được hôm nay.',
                                    'review': 'Nội dung minh họa.'}]}, at + 120)
                events.append(('exercise', 'low', at + 120))
        # Fortnightly screening (brief 1.2), two rounds inside the window.
        for days_ago in (self.rng.randint(30, 42), self.rng.randint(4, 16)):
            if self.rng.random() < (.95 if rich else .75):
                at = self.now - days_ago * 86400 + self.rng.uniform(8, 20) * 3600
                for kind in ('PHQ-9', 'GAD-7'):
                    result = self.screening(kind, clamp(severity + self.rng.gauss(0, .08), 0, 1))
                    self.record(db, owner, 'screening', result, at)
                    events.append(('screening', 'check_in' if result['requires_support'] else 'low', at))
        if events:
            self.audit(db, owner, 'login', min(e[2] for e in events) - 60)
            self.audit(db, owner, 'login', max(e[2] for e in events) - 60)
        return events

    def safety(self, db, owner, events, active=None):
        log = [{'id': str(uuid.uuid4()), 'channel': channel, 'level': level, 'source': 'rules', 'created': at,
                'policy_version': 'demo', 'status': {'low': 'no_signal', 'check_in': 'needs_clarification', 'high': 'needs_support'}[level]}
               for channel, level, at in sorted(events, key=lambda e: e[2])][-100:]
        self.document(db, owner, 'safety_events', 'safety', log)
        if active:
            self.document(db, owner, 'safety', 'safety', {'level': active, 'reason': 'Dữ liệu mẫu', 'source': 'rules', 'requires_support': True})


def seed(data_dir: Path, reset=False, seed_value=2026):
    if (data_dir / 'cogai.sqlite3').exists():
        if not reset:
            raise SystemExit(f'{data_dir} đã có dữ liệu. Thêm --reset để tạo lại bộ dữ liệu mẫu.')
        if data_dir.resolve().name != 'data-demo':
            raise SystemExit('Chỉ xóa thư mục tên data-demo; không đụng tới dữ liệu thật.')
        shutil.rmtree(data_dir)
    store = Store(Settings(data_dir=data_dir))
    # The knowledge index holds no personal data; reuse a prepared one so CogRAG works on demo data too.
    prepared = Path(__file__).resolve().parents[1] / 'data' / 'knowledge.sqlite3'
    if prepared.exists() and data_dir.resolve() != prepared.parent:
        shutil.copy2(prepared, data_dir / 'knowledge.sqlite3')
    rng = random.Random(seed_value)
    seeder = Seeder(store, rng)
    people = []
    with store.connection() as db:
        admin = seeder.account(db, 'admin', role='admin')
        expert = seeder.account(db, 'expert', role='expert')
        demo = seeder.account(db, 'user', cohort=next(iter(COHORTS)),
                              consent={'share_support': True, 'voice_processing': True, 'screening_reminders': True})
        events = seeder.person(db, demo, 'worker', .45, .85, rich=True)
        seeder.safety(db, demo, events)
        for cohort, (prefix, size, situation) in COHORTS.items():
            for index in range(1, size + 1):
                consent = {'share_support': rng.random() < .35, 'voice_processing': rng.random() < .4,
                           'screening_reminders': rng.random() < .5, 'personalization': rng.random() < .2}
                created = seeder.now - rng.uniform(DAYS, DAYS + 30) * 86400
                owner = seeder.account(db, f'{prefix}-{index:02d}', cohort=cohort, created=created, consent=consent)
                severity = clamp(rng.betavariate(2, 4.5) + (.08 if situation == 'worker' else .05), 0, .95)
                events = seeder.person(db, owner, situation, severity, rng.uniform(.25, .7))
                people.append((owner, severity, events, consent))
        # A few safety signals and referrals so the support and safety views have content.
        people.sort(key=lambda p: -p[1])
        for rank, (owner, severity, events, consent) in enumerate(people[:8]):
            at = seeder.now - rng.uniform(1, 20) * 86400
            level = 'high' if rank < 2 else 'check_in'
            events.append(('chat', level, at))
        for owner, _, events, _ in people:
            active = 'high' if any(e[1] == 'high' for e in events) else None
            seeder.safety(db, owner, events, active)
        statuses = ['pending', 'pending', 'accepted', 'in_progress', 'resolved', 'resolved', 'declined']
        for (owner, _, _, _), status, summary in zip(people[:7], statuses, REFERRAL_SUMMARIES):
            db.execute('UPDATE sessions SET consent=? WHERE id=?', (json.dumps(Store.choices({
                'accepted': True, 'adult': True, 'persist': True, 'external_ai': True, 'version': CONSENT_VERSION, 'share_support': True})), owner))
            created = seeder.now - rng.uniform(.5, 14) * 86400
            updated = created if status == 'pending' else created + rng.uniform(.5, 30) * 3600
            db.execute('INSERT INTO referrals VALUES (?,?,?,?,?,?,?)', (str(uuid.uuid4()), owner, None if status == 'pending' else expert,
                       status, store.encrypt({'summary': summary}), created, updated))
            seeder.audit(db, owner, 'support_requested', created)
            if status != 'pending':
                seeder.audit(db, expert, 'case_' + status, updated)
        seeder.audit(db, admin, 'login', seeder.now - 3600)
    return {'accounts': len(people) + 3, 'data_dir': str(data_dir)}


def main():
    parser = argparse.ArgumentParser(description='Tạo dữ liệu mẫu tổng hợp cho CogAI (không phải dữ liệu thật).')
    parser.add_argument('--data-dir', type=Path, default=Path('data-demo'))
    parser.add_argument('--reset', action='store_true', help='Xóa và tạo lại thư mục data-demo')
    args = parser.parse_args()
    result = seed(args.data_dir, args.reset)
    print(f"Đã tạo {result['accounts']} tài khoản mẫu tại {result['data_dir']}.")
    print(f'Mật khẩu chung: {PASSWORD}')
    print('  admin   -> trang Quản trị (thống kê, tài khoản, nhật ký)')
    print('  expert  -> trang Tiếp nhận hỗ trợ')
    print('  user    -> giao diện người dùng có sẵn 45 ngày dữ liệu')


if __name__ == '__main__':
    main()
