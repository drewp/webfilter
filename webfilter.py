import datetime
import inspect
import json
import sys
import time
import traceback
from typing import Dict, Set

from dateutil import tz

from mitmproxy import http
from pymongo import MongoClient
from rdflib import ConjunctiveGraph, Namespace
import url_category

def plog(msg):
    caller = inspect.currentframe().f_back
    print(f'{caller.f_code.co_filename}:{caller.f_lineno}-->', msg, file=sys.stderr)

class TimebankClient:
    ROOM = Namespace('http://projects.bigasterisk.com/room/')

    def __init__(self):
        self._mac_from_ip: Dict[str, str] = {}
        self._currently_blocked_mac: Set[str] = set()
        self._last_refresh = 0

    def refresh(self):
        plog('refresh now')
        graph = self._get_graphs()

        self._mac_from_ip = {}
        self._currently_blocked_mac = set()
        for host, _, status in graph.triples((None, self.ROOM['networking'], None)):
            mac = graph.value(host, self.ROOM['macAddress'], default=None)
            ip = graph.value(host, self.ROOM['ipAddress'], default=None)
            if mac and ip:
                self._mac_from_ip[ip.toPython()] = mac.toPython()

            if status == self.ROOM['blocked']:
                if mac is None:
                    plog(f'{host} is blocked but has no listed mac')
                else:
                    self._currently_blocked_mac.add(mac.toPython())

        plog(f'currently blocked: {self._currently_blocked_mac}')

    def _get_graphs(self):
        graph = ConjunctiveGraph()
        graph.parse('http://bang:10006/graph/timebank', format='trig')
        graph.parse('http://bang:9070/graph/wifi', format='trig')
        plog(f'fetched {len(graph)} statements from timebank and wifi')
        return graph

    def allowed(self, client_ip, url):
        now = time.time()
        if self._last_refresh < now - 5:
            self.refresh()
            self._last_refresh = now


        try:
            mac = self._mac_from_ip[client_ip]
            plog(f'request from {mac} {client_ip}')
        except KeyError:
            return False

        if mac not in self._currently_blocked_mac:
            plog(f'known and not blocked')
            return True

        if url_category.always_allowed(url):
            plog(f'allowed: {url}')
            return True

        return False

    def mac_from_ip(self, ip):
        return self._mac_from_ip.get(ip, '')

class MongodbLog:
    def __init__(self, mac_from_ip):
        self.mac_from_ip = mac_from_ip
        conn = MongoClient('bang', tz_aware=True)
        db = conn.get_database('timebank')
        self.coll = db.get_collection('webproxy')

    def write_event(self, client_ip, killed, doc):
        doc['t'] = datetime.datetime.now(tz.tzlocal())
        doc['ip'] = client_ip
        doc['mac'] = self.mac_from_ip(client_ip)
        doc['killed'] = killed
        self.coll.insert_one(doc)

class Webfilter:
    def __init__(self):
        self.timebank = TimebankClient()
        self.timebank.refresh()

        self.db = MongodbLog(self.timebank.mac_from_ip)

    def request(self, flow: http.HTTPFlow):
        try:
            client_ip = flow.client_conn.ip_address[0].split(':')[-1]

            url = flow.request.pretty_url

            plog(f'request from {client_ip} to {url}')

            killed = False
            if not self.timebank.allowed(client_ip, url):
                flow.kill()
                killed = True

            self.save_interesting_events(flow, url, client_ip, killed)
        except Exception:
            traceback.print_exc()
            raise

    def save_interesting_events(self, flow, url, client_ip, killed):
        host = flow.request.pretty_host
        method = flow.request.method
        path = flow.request.path_components

        if (host == 'bigasterisk.slack.com' and
            method == 'POST' and
            path and path[-1] == 'chat.postMessage'):
            slack_channel = flow.request.multipart_form[b'channel'].decode('ascii')
            message = json.loads(flow.request.multipart_form[b'blocks'])
            self.db.write_event(client_ip, killed, {
                'tag': 'slackChat',
                'channel': slack_channel,
                'message': message,
            })

        if (host == 'discordapp.com' and
            method == 'POST' and
            path and path[-1] == 'messages'):
            if path[2] != 'channels':
                raise NotImplementedError
            discord_channel = path[3]
            message = json.loads(flow.request.content)
            self.db.write_event(client_ip, killed, {
                'tag': 'discordChat',
                'channel': discord_channel,
                'message': message,
            })

        if host == 'www.youtube.com' and path and path[0] == 'watch':
            self.db.write_event(client_ip, killed, {
                'tag': 'youtube',
                'watchPage': url,
            })

        if url.startswith((
                'https://www.youtube.com/api/stats/watchtime',
                'https://www.youtube.com/api/stats/playback',
        )):
            d = dict(flow.request.query)
            self.db.write_event(client_ip, killed, {
                'tag': 'youtube',
                'watchtime': {
                    'state': d.get('state'),
                    'pos': d.get('cmt'),
                    'len': d.get('len'),
                    'vid': d.get('docid'),
                    'referrer': d.get('referrer'),
                },
            })

    def response(self, flow: http.HTTPFlow):
        if flow.response.headers.get('content-type', '').startswith('text/html'):
            client_ip = flow.client_conn.ip_address[0].split(':')[-1]
            url = flow.request.pretty_url
            if url_category.too_boring_to_log(url):
                return
            self.db.write_event(client_ip, False, {
                'tag': 'htmlPage',
                'url': url,
            })


addons = [
    Webfilter()
]
