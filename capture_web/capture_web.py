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
import logging

from flask import Flask
from flask_restful import Api, Resource, reqparse
from prometheus_flask_exporter import PrometheusMetrics

from rules_iptables import RuleMaker
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger()

if __name__ == '__main__':

    app = Flask(__name__)
    metrics = PrometheusMetrics(app)
    api = Api(app)

    macs_to_send_through_mitmproxy = {
    }

    rm = RuleMaker(route_to_localhost_port='8443', capture_interfaces=['ens5', 'enp1s0'])

    class Captures(Resource):

        def get(self):
            return macs_to_send_through_mitmproxy

        def post(self):
            pass

    api.add_resource(Captures, '/captures')

    parser = reqparse.RequestParser()
    parser.add_argument('capturing', type=bool)

    def routingChanged():
        log.info(' routingChanged')
        pass  # eventsource, tell web page

    class CaptureRule(Resource):

        def get(self, mac):
            return macs_to_send_through_mitmproxy[mac]

        def put(self, mac):
            cap = macs_to_send_through_mitmproxy[mac]

            args = parser.parse_args()
            log.info(f'put req mac={mac} args={args!r}')
            if cap['capturing'] != args['capturing']:
                if args['capturing']:
                    log.info(f'request to capture {mac}')
                    rm.capture_outgoing_web_traffic(mac)
                    routingChanged()
                else:
                    log.info(f'request to uncapture {mac}')
                    rm.uncapture(mac)
                    routingChanged()

                cap['capturing'] = args['capturing']
            return cap

        def delete(self, mac):
            log.info(f'request to forget {mac}')
            rm.uncapture(mac)
            routingChanged()
            del macs_to_send_through_mitmproxy[mac]
            return '', 204

    api.add_resource(CaptureRule, '/captures/<mac>')

    @app.route('/')
    def root():
        return open('index.html').read()

    @app.route('/build/bundle.js')
    def bundle():
        return open('build/bundle.js').read()

    app.run(port=10001, host="0.0.0.0", debug=False)
