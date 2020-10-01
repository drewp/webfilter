import logging
import subprocess
import threading

import iptc
iptables_lock = threading.Lock()

log = logging.getLogger()


class RuleMaker:
    """
    Build iptables rules for redirecting internal hosts' web traffic to mitmproxy.
    """

    def __init__(self, webfilter_port='8443', capture_interfaces=['ens5']):
        self.webfilter_port = webfilter_port
        self.capture_interfaces = capture_interfaces

        # todo: pick up existing state
        with iptables_lock:
            subprocess.check_call(['sh', '-c', 'iptables-save | grep -v net_routes | iptables-restore'])

    def _webfilter_rules(self, mac):
        for port in [80, 443]:
            for protocol in ['tcp', 'udp']:
                for iface in self.capture_interfaces:
                    rule = iptc.Rule()
                    rule.in_interface = iface
                    rule.protocol = protocol
                    rule.create_match(protocol).dport = str(port)
                    rule.create_match('mac').mac_source = mac
                    rule.create_match('comment').comment = "net_routes"
                    rule.target = iptc.Target(rule, 'REDIRECT')
                    rule.target.to_ports = self.webfilter_port
                    yield rule

    def _drop_rules(self, mac):
        rule = iptc.Rule()
        rule.create_match('mac').mac_source = mac
        rule.create_match('comment').comment = "net_routes"
        rule.target = iptc.Target(rule, 'DROP')
        yield rule

    def set_routing(self, mac, mode):
        self.uncapture(mac)
        if mode == 'normal':
            pass
        elif mode == 'drop':
            with iptables_lock:
                table = iptc.Table(iptc.Table.RAW)
                chain = iptc.Chain(table, 'PREROUTING')
                for rule in self._drop_rules(mac):
                    log.info('adding drop rule for %r', mac)
                    chain.insert_rule(rule)

        elif mode == 'webfilter':
            with iptables_lock:
                table = iptc.Table(iptc.Table.NAT)
                chain = iptc.Chain(table, 'PREROUTING')
                for rule in self._webfilter_rules(mac):
                    log.info('adding mitmproxy route for %r', mac)
                    chain.insert_rule(rule)
        else:
            raise NotImplementedError(mode)

    def uncapture(self, mac):
        log.info('clearing routing rules for %r', mac)
        with iptables_lock:
            for table, rules in [
                (iptc.Table(iptc.Table.NAT), self._webfilter_rules(mac)),
                (iptc.Table(iptc.Table.RAW), self._drop_rules(mac)),
            ]:
                chain = iptc.Chain(table, 'PREROUTING')
                for rule in rules:
                    # log.info('deleting %r', rule)
                    try:
                        chain.delete_rule(rule)
                    except iptc.IPTCError as e:
                        log.debug(f"  delete failed {e!r}- ignore")
