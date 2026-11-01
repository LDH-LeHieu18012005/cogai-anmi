"""Persisted request allowance. Contains counts only, never prompts or keys."""
import sqlite3
from datetime import datetime, timezone

from fastapi import HTTPException


def utc_day():
    return datetime.now(timezone.utc).date().isoformat()


class ProviderBudget:
    def __init__(self,settings):
        self.limit=settings.external_daily_call_limit
        self.path=settings.data_dir/'provider-budget.sqlite3'

    def reserve(self):
        if not self.limit:
            return
        try:
            self.path.parent.mkdir(parents=True,exist_ok=True)
            with sqlite3.connect(self.path,timeout=10) as db:
                db.execute('CREATE TABLE IF NOT EXISTS daily_calls (day TEXT PRIMARY KEY, calls INTEGER NOT NULL)')
                db.execute('BEGIN IMMEDIATE')
                day=utc_day()
                row=db.execute('SELECT calls FROM daily_calls WHERE day=?',(day,)).fetchone()
                if row and row[0]>=self.limit:
                    raise HTTPException(429,'Đã đạt giới hạn yêu cầu AI trong ngày (UTC). Đã dừng gọi dịch vụ để kiểm soát chi phí.')
                db.execute('INSERT INTO daily_calls(day,calls) VALUES (?,1) ON CONFLICT(day) DO UPDATE SET calls=calls+1',(day,))
        except (sqlite3.Error,OSError):
            raise HTTPException(503,'Chưa kiểm tra được giới hạn chi phí; đã dừng gọi dịch vụ.') from None
