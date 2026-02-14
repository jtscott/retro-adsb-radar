import threading
import requests
import time
import logging
import config

class Aircraft:
    def __init__(self, data):
        self.hex = data.get('hex', '000000')
        self.callsign = str(data.get('flight', '???')).strip().upper()
        
        # NEW: Extract Squawk
        self.squawk = str(data.get('squawk', '????')).strip()
        
        op_full = str(data.get('ownOp', '')).strip()
        self.own_op = op_full.split(' ')[0].upper()[:7] if op_full else ""
        
        self.type = str(data.get('t', '???')).strip().upper()
        self.altitude = data.get('alt_baro', data.get('alt_geom', 0)) or 0
        self.speed = data.get('gs', 0) or 0
        self.track = data.get('track', 0) or 0
        self.lat = data.get('lat', None)
        self.lon = data.get('lon', None)
        self.distance = data.get('r_dst', 999.0)
        self.is_military = self._check_military(self.hex)

    def _check_military(self, hex_id):
        try:
            mil_list = getattr(config, 'MIL_PREFIX_LIST', '')
            if not mil_list: return False
            prefixes = [p.strip().upper() for p in str(mil_list).split(',')]
            return any(str(hex_id).upper().startswith(p) for p in prefixes if p)
        except: return False

class AircraftTracker:
    def __init__(self):
        self.aircraft = []
        self.status = "OFFLINE"
        self.last_update = 0
        self.running = False

    def fetch(self):
        try:
            r = requests.get(config.TAR1090_URL, timeout=2)
            if r.status_code == 200:
                data = r.json()
                new_list = []
                for a_data in data.get('aircraft', []):
                    a = Aircraft(a_data)
                    if a.lat is not None and a.lon is not None:
                        new_list.append(a)
                self.aircraft = new_list
                self.status = "SYNC"
                self.last_update = time.time()
            else:
                self.status = f"ERR {r.status_code}"
        except:
            self.status = "ERR"

    def run(self):
        while self.running:
            self.fetch()
            time.sleep(getattr(config, 'FETCH_INTERVAL', 5))

    def start(self):
        self.running = True
        threading.Thread(target=self.run, daemon=True).start()