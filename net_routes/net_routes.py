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
import datetime
import logging
import threading
import time
from typing import Callable, Optional

from dateutil.parser import parse
from dateutil.tz import tzlocal
from flask import Flask
from flask_restful import Api, Resource, reqparse
from prometheus_flask_exporter import PrometheusMetrics
from rdflib import Graph, Namespace, RDF, URIRef
import pymongo
import pymongo.collection
import housebot

from rules_iptables import RuleMaker
logging.basicConfig(level=logging.INFO)
log = logging.getLogger()

EV = Namespace("http://bigasterisk.com/event#")


@dataclass(eq=False)
class CalendarSync(threading.Thread):
    """events on this google calendar (read by gcalendarwatch) activate the given device"""
    feed: URIRef
    macToActivate: str
    changeRoute: Callable[[str, str, str], None]

    def __post_init__(self):
        threading.Thread.__init__(self, daemon=True)

    def run(self):
        log.info(f'syncing {self.macToActivate} to calendar feed')
        first = True
        while True:
            try:
                evTitle = self._currentEventTitle()
                if evTitle is not None:
                    changeRoute(self.macToActivate, 'normal', reason=f"calendar event: {evTitle}", say=not first)
                else:
                    changeRoute(self.macToActivate, 'drop', reason="no current calendar event", say=not first)
                time.sleep(60)
            except Exception as e:
                log.warning(f'calendar sync {e!r} - retrying')
                time.sleep(60)
            first = False

    def _currentEventTitle(self) -> Optional[str]:
        g = Graph()
        g.parse('http://gcalendarwatch.default.svc.cluster.local/events', format='n3')
        now = datetime.datetime.now(tzlocal())
        for ev in g.subjects(EV['feed'], self.feed):
            if (ev, RDF.type, EV['Event']) not in g:
                continue
            s = parse(g.value(ev, EV.start).toPython())
            e = parse(g.value(ev, EV.end).toPython())
            log.debug(f'cal event from {s} to {e} title {g.value(ev, EV.title)}')
            if s <= now <= e:
                log.debug('that is happening now')
                return g.value(ev, EV.title).toPython()
        return None


class DbSync(threading.Thread):

    def run(self):
        first = True
        while True:
            syncRoutesFromMongo(say=not first)
            first = False
            time.sleep(5)


if __name__ == '__main__':

    app = Flask(__name__)
    metrics = PrometheusMetrics(app)
    api = Api(app)

    macs_to_send_through_mitmproxy = {}
    last_set_route = {}  # mac : route

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

    def changeRoute(mac, newRoute, reason: str, say=True):
        # this call might not be on the main thread
        last = last_set_route.get(mac, None)
        if last != newRoute:
            log.info(f'request to capture {mac} as {newRoute} because {reason} (say={say})')
            if say:
                housebot.say(f"net-routes changes *{mac}* to *{newRoute}* because {reason}")
            rm.set_routing(mac, newRoute)
            routingChanged()
            last_set_route[mac] = newRoute

    ps4online = URIRef("http://bigasterisk.com/calendar/feed/iem9ppgqdbleh96nkeaj4l6714@group.calendar.google.com")
    ps4mac = '0c:fe:45:db:33:9e'
    syncs = [CalendarSync(feed=ps4online, macToActivate=ps4mac, changeRoute=changeRoute)]
    [s.start() for s in syncs]

    class CaptureRule(Resource):

        def get(self, mac):
            return macs_to_send_through_mitmproxy[mac]

        def put(self, mac):
            cap = macs_to_send_through_mitmproxy[mac]
            args = parser.parse_args()
            log.info(f'put req mac={mac} args={args!r}')
            changeRoute(mac=mac, newRoute=args['route'], reason="web request")
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
        return open('build/index.html').read()

    @app.route('/build/bundle.js')
    def bundle():
        return open('build/bundle.js').read()

    db = pymongo.MongoClient('mongodb.default.svc.cluster.local', tz_aware=True).get_database('timebank')
    hosts = db.get_collection('hosts')
    routes = db.get_collection('routes')

    def syncRoutesFromMongo(say=True):
        for row in routes.find():
            if row['mac'] == ps4mac:
                continue
            ourMode = {'open': 'normal', 'mitmproxy': 'webfilter', 'drop': 'drop'}[row['mode']]
            changeRoute(row['mac'], ourMode, "sync to web form", say=say)

    ds = DbSync()
    ds.start()

    app.run(port=10001, host="0.0.0.0", debug=False)
