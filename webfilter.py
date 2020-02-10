from mitmproxy import http
from rdflib import Namespace, ConjunctiveGraph
import json
import time
import datetime
import urllib.parse
from pymongo import MongoClient
from dateutil import tz
from typing import Dict, Optional, Set
import traceback


class TimebankClient:
    ROOM = Namespace('http://projects.bigasterisk.com/room/')

    def __init__(self):
        self._mac_from_ip: Dict[str, str] = {}
        self._currently_blocked_mac: Set[str] = set()
        self.last_refresh = 0

    def refresh(self):
        graph = self.get_graphs()

        self._mac_from_ip = {}
        self._currently_blocked_mac = set()
        for host, _, status in graph.triples((None, self.ROOM['networking'], None)):
            mac = graph.value(host, self.ROOM['macAddress'], default=None)
            ip = graph.value(host, self.ROOM['ipAddress'], default=None)
            if mac and ip:
                self._mac_from_ip[ip.toPython()] = mac.toPython()

            if status == self.ROOM['blocked']:
                if mac is None:
                    print(f'{host} is blocked but has no listed mac')
                else:
                    self._currently_blocked_mac.add(mac.toPython())

        print(f'currently blocked: {self._currently_blocked_mac}')

    def get_graphs(self):
        graph = ConjunctiveGraph()
        graph.parse('http://bang:10006/graph/timebank', format='trig')
        graph.parse('http://bang:9070/graph', format='trig') # soon to be graph/wifi/
        print(f'fetched {len(graph)} statements from timebank and wifi')
        return graph

    def allowed(self, client_ip, url):
        now = time.time()
        if self.last_refresh < now - 5:
            self.refresh()
            self.last_refresh = now

        if self._mac_from_ip.get(client_ip, 'nomatch') not in self._currently_blocked_mac:
            return True

        netloc = urllib.parse.urlparse(url).netloc
        if ('.' + netloc).endswith((
                '.gmail.com',
                '.google.com',
                '.googleapis.com',
                '.gstatic.com',
                '.slack-edge.com',
                '.slack.com',
                '.bigasterisk.com',
                '.wikimedia.org',
                '.wikipedia.org',
        )):
            return True

        return False

    def mac_from_ip(self, ip):
        return self._mac_from_ip.get(ip, '')

class MongodbLog:
    def __init__(self, mac_from_ip):
        self.mac_from_ip = mac_from_ip
        conn = MongoClient('bang', 27017)
        db = conn.get_database('timebank')
        self.coll = db.get_collection('webproxy')

    def write_event(self, client_ip, doc):
        doc['t'] = datetime.datetime.now(tz.tzlocal())
        doc['ip'] = client_ip
        doc['mac'] = self.mac_from_ip(client_ip)
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

            print(f'request from {client_ip} to {url}')

            if not self.timebank.allowed(client_ip, url):
                flow.kill()

            self.save_interesting_events(flow, url, client_ip)
        except Exception:
            traceback.print_exc()
            raise

    def save_interesting_events(self, flow, url, client_ip):
        host = flow.request.pretty_host
        method = flow.request.method
        path = flow.request.path_components

        if (host == 'bigasterisk.slack.com' and
            method == 'POST' and
            path and path[-1] == 'chat.postMessage'):
            slack_channel = flow.request.multipart_form[b'channel'].decode('ascii')
            message = json.loads(flow.request.multipart_form[b'blocks'])
            self.db.write_event(client_ip, {
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
            self.db.write_event(client_ip, {
                'tag': 'discordChat',
                'channel': discord_channel,
                'message': message,
            })

        if host == 'www.youtube.com' and path and path[0] == 'watch':
            self.db.write_event(client_ip, {
                'tag': 'youtube',
                'watchPage': url,
            })

        if url.startswith('https://www.youtube.com/api/stats/watchtime'):
            d = dict(flow.request.query)
            self.db.write_event(client_ip, {
                'tag': 'youtube',
                'watchtime': {
                    'state': d.get('state'),
                    'pos': d.get('cmt'),
                    'len': d.get('len'),
                    'vid': d.get('docid'),
                },
            })

    def response(self, flow: http.HTTPFlow):
        too_boring = {
            'http://www.google.com/gen_204',
        }
        if flow.response.headers.get('content-type', '').startswith('text/html'):
            client_ip = flow.client_conn.ip_address[0].split(':')[-1]
            url = flow.request.pretty_url
            if url in too_boring:
                return
            self.db.write_event(client_ip, {
                'tag': 'htmlPage',
                'url': url,
            })


addons = [
    Webfilter()
]
