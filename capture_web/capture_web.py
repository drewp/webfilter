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
import os
import subprocess
from flask import Flask
from flask_restful import Resource, Api, reqparse
from prometheus_flask_exporter import PrometheusMetrics
from rules_iptables import RuleMaker

if __name__ == '__main__':

    app = Flask(__name__)
    metrics = PrometheusMetrics(app)
    api = Api(app)

    macs_to_send_through_mitmproxy = {
    }

    #mitmdump_ip = os.environ['MITMPROXY_PORT_8443_TCP_ADDR']
    rm = RuleMaker(route_to_localhost_port='8443')

    class Captures(Resource):

        def get(self):
            return macs_to_send_through_mitmproxy

        def post(self):
            pass

    api.add_resource(Captures, '/captures')

    parser = reqparse.RequestParser()
    parser.add_argument('capturing', type=bool)

    def routingChanged():
        pass  # eventsource, tell web page

    class CaptureRule(Resource):

        def get(self, mac):
            return macs_to_send_through_mitmproxy[mac]

        def put(self, mac):
            cap = macs_to_send_through_mitmproxy[mac]

            args = parser.parse_args()
            if cap['capturing'] != args['capturing']:
                if args['capturing']:
                    rm.capture_outgoing_web_traffic(mac)
                    routingChanged()
                else:
                    rm.uncapture(mac)
                    routingChanged()

                cap['capturing'] = args['capturing']
            return cap

        def delete(self, mac):
            rm.uncapture(mac)
            routingChanged()
            del macs_to_send_through_mitmproxy[mac]
            return '', 204

    api.add_resource(CaptureRule, '/captures/<mac>')

    @app.route('/')
    def root():
        return 'root'

    subprocess.check_call(['sh', '-c', 'iptables-save | grep -v capture_web | iptables-restore'])
    rm.capture_outgoing_web_traffic('00:e0:4c:ae:ed:1e')#'dc:ef:ca:ed:58:27')

    app.run(port=10001, host="0.0.0.0", debug=False)
