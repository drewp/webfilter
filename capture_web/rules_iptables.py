import subprocess
import threading

import iptc
iptables_lock = threading.Lock()


class RuleMaker:
    """
    Build iptables rules for redirecting internal hosts' web traffic to mitmproxy.
    """

    def __init__(self, route_to_localhost_port='8443', capture_interfaces=['ens5']):
        self.route_to_localhost_port = route_to_localhost_port
        self.capture_interfaces = capture_interfaces

        # todo: pick up existing state
        with iptables_lock:
            subprocess.check_call(['sh', '-c', 'iptables-save | grep -v capture_web | iptables-restore'])

    def _rule(self, mac):
        for port in [80, 443]:
            for protocol in ['tcp', 'udp']:
                for iface in self.capture_interfaces:
                    rule = iptc.Rule()
                    rule.in_interface = iface
                    rule.protocol = protocol
                    rule.create_match(protocol).dport = str(port)
                    rule.create_match('mac').mac_source = mac
                    rule.create_match('comment').comment = "capture_web"
                    rule.target = iptc.Target(rule, 'REDIRECT')
                    rule.target.to_ports = self.route_to_localhost_port
                    yield rule

    def capture_outgoing_web_traffic(self, mac):
        with iptables_lock:
            table = iptc.Table(iptc.Table.NAT)
            chain = iptc.Chain(table, 'PREROUTING')
            for rule in self._rule(mac):
                print('adding', rule)
                chain.insert_rule(rule)

    def uncapture(self, mac):
        with iptables_lock:
            table = iptc.Table(iptc.Table.NAT)
            chain = iptc.Chain(table, 'PREROUTING')
            for rule in self._rule(mac):
                print('deleting', rule)
                try:
                    chain.delete_rule(rule)
                except iptc.IPTCError:
                    print("  delete failed- ignore")
