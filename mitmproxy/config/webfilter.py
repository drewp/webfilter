"""plugin script for mitmdump that rejects some web requests"""
import datetime
import importlib
import inspect
import json
import os
import sys
import time
import traceback
from typing import Dict, Set

from dateutil import tz
import mitmproxy.flow
import mitmproxy.http
import mitmproxy.proxy.protocol
import prometheus_client
from prometheus_client import Summary, Counter
from pymongo import MongoClient
from rdflib import ConjunctiveGraph, Namespace

import url_category


def plog(msg):
    caller = inspect.currentframe().f_back
    fn = os.path.basename(caller.f_code.co_filename)
    print(f'{fn}:{caller.f_lineno}--> {msg}', file=sys.stdout, flush=True)


_ntc = prometheus_client.REGISTRY._names_to_collectors


def _reuseOrMake(mtype, name, *args):
    searchName = name
    if issubclass(mtype, Counter):
        searchName = name + '_total'
    if searchName in _ntc:
        return _ntc[searchName]
    return mtype(name, *args)


REFRESH = _reuseOrMake(Summary, 'refresh_calls', 'time in TimebankClient.refresh')
REQUEST_KILLS = _reuseOrMake(Counter, 'request_kills', 'requests killed')
REQUEST_ERRORS = _reuseOrMake(Counter, 'request_errors', 'requests that could not be understood')
RESPONSES = _reuseOrMake(Counter, 'responses', 'responses seen', ['contentType'])
REQUEST_HANDLER = _reuseOrMake(Summary, 'request_handler', 'time in Webfilter.request')
RESPONSE_HANDLER = _reuseOrMake(Summary, 'response_handler', 'time in Webfilter.response')

plog('init metrics %r' % sorted(_ntc.keys()))


def trunc_url(url):
    if len(url) > 103:
        url = url[:100] + '...'
    return url


class TimebankClient:
    ROOM = Namespace('http://projects.bigasterisk.com/room/')

    def __init__(self):
        self._mac_from_ip: Dict[str, str] = {}
        self._currently_blocked_mac: Set[str] = set()
        self._last_refresh = 0

    @REFRESH.time()
    def refresh(self):
        plog('refresh now')
        t1 = time.time()
        importlib.reload(url_category)
        graph = self._get_graphs()

        self._mac_from_ip = {}
        self._currently_blocked_mac = set()
        for host, _, status in graph.triples((None, self.ROOM['networking'], None)):
        for host in graph.subjects(RDF.type, self.ROOM['NetworkedDevice']):
            mac = graph.value(host, self.ROOM['macAddress'], default=None)
            ip = graph.value(host, self.ROOM['ipAddress'], default=None)
            if mac and ip:
                self._mac_from_ip[ip.toPython()] = mac.toPython()

            if status == self.ROOM['blocked']:
                if mac is None:
                    plog(f'{host} is blocked but has no listed mac')
                else:
                    self._currently_blocked_mac.add(mac.toPython())

        # turn these to metrics
        plog(f'{len(self._mac_from_ip)} macs with ips')
        plog(f'currently blocked: {self._currently_blocked_mac}')
        plog(f'refresh took {(time.time()-t1)*1000:.1f} ms')

    def _get_graphs(self):
        graph = ConjunctiveGraph()
        try:
            graph.parse(f'http://{os.environ["WIFI_PORT_80_TCP_ADDR"]}/graph/wifi', format='trig')
            # graph.parse('http://bang:10006/graph/timebank', format='trig')
        except Exception as e:
            plog(f"failed to fetch graph(s): {e!r}")

        plog(f'fetched {len(graph)} statements from timebank and wifi')
        return graph

    def allowed(self, client_ip, url):
        now = time.time()
        if self._last_refresh < now - 5:
            self.refresh()
            self._last_refresh = now

        # try:
        #     mac = self._mac_from_ip[client_ip]
        #     plog(f'request from {mac} {client_ip}')
        # except KeyError:
        #     return False

        # if mac not in self._currently_blocked_mac:
        #     plog('known and not blocked')
        #     return True

        if url_category.always_allowed(url):
            plog(f'allowed: {trunc_url(url)}')
            return True
        else:
            plog(f'not in always_allowed: {trunc_url(url)}')

        return False

    def mac_from_ip(self, ip):
        return self._mac_from_ip.get(ip, '')


class MongodbLog:

    def __init__(self, mac_from_ip):
        try:
            self.mac_from_ip = mac_from_ip
            conn = MongoClient(os.environ['MONGODB_SERVICE_HOST'], tz_aware=True)
            db = conn.get_database('timebank')
            self.coll = db.get_collection('webproxy')
        except Exception:
            traceback.print_exc(file=sys.stderr)
            raise

    def write_event(self, client_ip, killed, doc):
        doc['t'] = datetime.datetime.now(tz.tzlocal())
        doc['ip'] = client_ip
        doc['mac'] = self.mac_from_ip(client_ip)
        doc['killed'] = killed
        self.coll.insert_one(doc)


class PluginCrash(ValueError):
    """for testing; make this mitmproxy error so it gets dropped,
    and we can observe mitmproxy running without it (which needs to be caught and fixed)
    """


class Webfilter:

    def __init__(self):
        plog("Webfilter init")
        self.timebank = TimebankClient()
        self.timebank.refresh()

        self.db = MongodbLog(self.timebank.mac_from_ip)

    # def clientconnect(self, layer: mitmproxy.proxy.protocol.Layer):
    #     plog(f'connect {layer}')

    def _internal_url(self, url, flow):
        if url == "http://10.5.0.1:8443/metrics":
            flow.response = mitmproxy.http.HTTPResponse.make(
                200,
                prometheus_client.generate_latest(),
            )
            return

        flow.kill()

    @REQUEST_HANDLER.time()
    def request(self, flow: mitmproxy.http.HTTPFlow):
        try:
            client_ip = flow.client_conn.ip_address[0].split(':')[-1]
            url = flow.request.pretty_url

            plog(f'request from {client_ip} to {trunc_url(url)}')
            if '10.5.0.1' in url:
                # don't try to fulfill this- it will infinitely route back to mitmdump!
                self._internal_url(url, flow)
                return

            if 'example.com/die' in url:
                # special for testing
                raise PluginCrash()

            killed = False
            if not self.timebank.allowed(client_ip, url):
                flow.kill()
                REQUEST_KILLS.inc()
                killed = True

            self.save_interesting_events(flow, url, client_ip, killed)
        except PluginCrash:
            raise
        except Exception:
            traceback.print_exc(file=sys.stdout)
            flow.kill()
            REQUEST_ERRORS.inc()
            # but don't raise or crash, or webfilter.py just won't be loaded and all reqs go through!

    def save_interesting_events(self, flow, url, client_ip, killed):
        host = flow.request.pretty_host
        method = flow.request.method
        path = flow.request.path_components

        if (host == 'bigasterisk.slack.com' and method == 'POST' and path and path[-1] == 'chat.postMessage'):
            slack_channel = flow.request.multipart_form[b'channel'].decode('ascii')
            message = json.loads(flow.request.multipart_form[b'blocks'])
            self.db.write_event(client_ip, killed, {
                'tag': 'slackChat',
                'channel': slack_channel,
                'message': message,
            })

        if (host == 'discordapp.com' and method == 'POST' and path and path[-1] == 'messages'):
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
            self.db.write_event(
                client_ip, killed, {
                    'tag': 'youtube',
                    'watchtime': {
                        'state': d.get('state'),
                        'pos': d.get('cmt'),
                        'len': d.get('len'),
                        'vid': d.get('docid'),
                        'referrer': d.get('referrer'),
                    },
                })

        if killed:
            self.db.write_event(client_ip, killed, {
                'tag': 'htmlPage',
                'url': url,
            })

    @RESPONSE_HANDLER.time()
    def response(self, flow: mitmproxy.http.HTTPFlow):
        first_ct = flow.response.headers.get('content-type', '').split(';')[0]
        RESPONSES.labels(contentType=first_ct).inc()
        if first_ct == 'text/html':
            client_ip = flow.client_conn.ip_address[0].split(':')[-1]
            url = flow.request.pretty_url
            if url_category.too_boring_to_log(url):
                return
            self.db.write_event(client_ip, killed=False, doc={
                'tag': 'htmlPage',
                'url': url,
            })


plog('registering webfilter')
addons = [Webfilter()]
