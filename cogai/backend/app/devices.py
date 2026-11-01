"""Registered desk devices (MYHealth/Ricky) and their access tokens.

Usage (from cogai/backend):
    python -m app.devices add <device MAC> <name>   # prints the token once
    python -m app.devices list
    python -m app.devices remove <device MAC>
"""
import hashlib
import hmac
import json
import re
import secrets
import sys
import threading
import time

MAC = re.compile(r'^[0-9a-f]{2}(:[0-9a-f]{2}){5}$')


class Devices:
    """Device MAC -> name and Fernet-encrypted token, in data_dir/devices.json.

    The OTA check hands a registered MAC its token; the WebSocket accepts only that
    token. A MAC is not a secret, so keep the gateway on a trusted network.
    """
    def __init__(self,store,config):
        self.store,self.path=store,config.data_dir/'devices.json'
        self.lock=threading.Lock()
        # Tokens provided by the host's secret store (COGAI_DEVICE_TOKENS) override the file.
        self.fixed={}
        for entry in filter(None,(e.strip() for e in config.device_tokens.split(';'))):
            mac,_,token=entry.partition('=')
            if not token.strip():
                raise ValueError('COGAI_DEVICE_TOKENS cần dạng aa:bb:cc:dd:ee:ff=token;...')
            self.fixed[self.normalize(mac)]=token.strip()

    def _read(self):
        return json.loads(self.path.read_text('utf-8')) if self.path.exists() else {}

    def _write(self,items):
        self.path.parent.mkdir(parents=True,exist_ok=True)
        tmp=self.path.with_suffix('.tmp')
        tmp.write_text(json.dumps(items,ensure_ascii=False,indent=1),'utf-8')
        tmp.replace(self.path)

    @staticmethod
    def normalize(mac):
        mac=(mac or '').strip().lower().replace('-',':')
        if not MAC.match(mac):
            raise ValueError('Địa chỉ MAC không hợp lệ (dạng aa:bb:cc:dd:ee:ff).')
        return mac

    def add(self,mac,name):
        mac,token=self.normalize(mac),secrets.token_urlsafe(32)
        with self.lock:
            items=self._read()
            items[mac]={'name':name[:60],'token':self.store.cipher.encrypt(token.encode()).decode(),
                        'token_hash':hashlib.sha256(token.encode()).hexdigest(),'created':time.time()}
            self._write(items)
        return token

    def remove(self,mac):
        with self.lock:
            items=self._read()
            removed=items.pop(self.normalize(mac),None)
            self._write(items)
        return removed is not None

    def token(self,mac):
        try:
            mac=self.normalize(mac)
        except ValueError:
            return None
        if mac in self.fixed:
            return self.fixed[mac]
        item=self._read().get(mac)
        return self.store.cipher.decrypt(item['token'].encode()).decode() if item else None

    def by_token(self,token):
        if not token:
            return None
        for mac,fixed in self.fixed.items():
            if hmac.compare_digest(fixed.encode(),token.encode()):
                return {'mac':mac,'name':'device'}
        digest=hashlib.sha256(token.encode()).hexdigest()
        for mac,item in self._read().items():
            if hmac.compare_digest(item['token_hash'],digest):
                return {'mac':mac,'name':item['name']}
        return None

    def list(self):
        return [{'mac':mac,'name':item['name'],'created':item['created']} for mac,item in self._read().items()]


def main(argv):
    from .config import Settings
    from .storage import Store
    config=Settings()
    devices=Devices(Store(config),config)
    if argv[:1]==['add'] and len(argv)==3:
        print('Token (chỉ hiện một lần, robot tự nhận qua OTA):',devices.add(argv[1],argv[2]))
    elif argv[:1]==['remove'] and len(argv)==2:
        print('Đã xóa.' if devices.remove(argv[1]) else 'Không có thiết bị này.')
    elif argv==['list']:
        for item in devices.list():
            print(item['mac'],item['name'],time.strftime('%Y-%m-%d %H:%M',time.localtime(item['created'])))
    else:
        print(__doc__)
        return 1
    return 0


if __name__=='__main__':
    sys.exit(main(sys.argv[1:]))
