#!/usr/bin/python3
"""
To see a dump in nft-language:
  nft list ruleset


See
https://github.com/firewalld/firewalld/blob/master/src/firewall/core/nftables.py
for one of the few other published users of the nft json API.

dot# cd /usr/share/ca-certificates
dot# mkdir extra
dot# cat > extra/mitmproxy.crt
(paste mitmproxy/mitmproxy-ca-cert.cer)
dot# sudo dpkg-reconfigure ca-certificates


"""
from dataclasses import dataclass
import logging
import threading
import time
from typing import Callable

from flask import Flask

from flask_restful import Api, Resource, reqparse
from prometheus_flask_exporter import PrometheusMetrics
from rdflib import Graph, Namespace, RDF, URIRef
from rules_iptables import RuleMaker
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger()

EV = Namespace("http://bigasterisk.com/event#")


@dataclass(eq=False)
class CalendarSync(threading.Thread):
    """events on this google calendar (read by gcalendarwatch) activate the given device"""
    feed: URIRef
    macToActivate: str
    changeRoute: Callable[[str, str], None]

    def __post_init__(self):
        threading.Thread.__init__(self, daemon=True)

    def run(self):
        while True:
            if self._inAnyEvents():
                changeRoute(self.macToActivate, 'normal')
            else:
                changeRoute(self.macToActivate, 'drop')
            time.sleep(60)

    def _inAnyEvents(self):
        g = Graph()
        g.parse('http://gcalendarwatch.default.svc.cluster.local/events', format='n3')
        for ev in g.subjects(EV['feed'], self.feed):
            if (ev, RDF.type, EV['Event']) not in g:
                continue
            s = g.value(ev, EV.start).toPython()
            e = g.value(ev, EV.end).toPython()
            log.debug(f'cal event from {s} to {e} title {g.value(ev, EV.title)}')


if __name__ == '__main__':

    app = Flask(__name__)
    metrics = PrometheusMetrics(app)
    api = Api(app)

    macs_to_send_through_mitmproxy = {
    }

    rm = RuleMaker(webfilter_port='8443', capture_interfaces=['ens5', 'enp1s0'])

    class Captures(Resource):

        def get(self):
            return macs_to_send_through_mitmproxy

        def post(self):
            pass

    api.add_resource(Captures, '/routes')

    parser = reqparse.RequestParser()
    parser.add_argument('route', type=str)  # 'normal', 'drop', 'webfilter'

    def routingChanged():
        log.info(' routingChanged')
        pass  # eventsource, tell web page

    def changeRoute(mac, newRoute):
        cap = macs_to_send_through_mitmproxy[mac]
        if cap['route'] != newRoute:
            log.info(f'request to capture {mac} as {newRoute}')
            rm.set_routing(mac, newRoute)
            routingChanged()
            cap['route'] = newRoute

    syncs = [CalendarSync(feed=ps4online, macToActivate=ps4mac, changeRoute=changeRoute)]
    [s.start() for s in syncs]

    class CaptureRule(Resource):

        def get(self, mac):
            return macs_to_send_through_mitmproxy[mac]

        def put(self, mac):
            cap = macs_to_send_through_mitmproxy[mac]
            args = parser.parse_args()
            log.info(f'put req mac={mac} args={args!r}')
            changeRoute(mac=mac, newRoute=args['route'])
            return cap

        def delete(self, mac):
            log.info(f'request to forget {mac}')
            rm.set_routing(mac, 'normal')
            routingChanged()
            del macs_to_send_through_mitmproxy[mac]
            return '', 204

    api.add_resource(CaptureRule, '/routes/<mac>')

    @app.route('/')
    def root():
        return open('index.html').read()

    @app.route('/build/bundle.js')
    def bundle():
        return open('build/bundle.js').read()

    app.run(port=10001, host="0.0.0.0", debug=False)
