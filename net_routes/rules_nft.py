"""maybe conflicts (or can't work next) to k8s rules, which use iptables"""

import pprint
import nftables


def match_saddr(ip):
    return {
        "match": {
            "left": {
                "payload": {
                    "protocol": "ip",
                    "field": "saddr"
                }
            },
            "op": "==",
            "right": {
                "prefix": {
                    "addr": ip,
                    "len": 32
                }
            }
        }
    }


def match_source_mac(mac):
    return {"match": {"left": {"payload": {"protocol": "ether", "field": "saddr"}}, "op": "==", "right": mac}}


def match_dport(protocol, port):
    return {"match": {"left": {"payload": {"protocol": protocol, "field": "dport"}}, "op": "==", "right": port}}


def redirect_rule(table, chain, source_match, protocol, attempt_dport, redirect_port):
    return {
        'rule': {
            'family': 'inet',
            'table': table,
            'chain': chain,
            'expr': [
                source_match,
                match_dport(protocol, attempt_dport),
                {
                    "redirect": {
                        "port": redirect_port
                    }
                },
            ],
            'comment': 'net_routes',
        }
    }


class RuleMaker:
    """
    Build nft rules for redirecting internal hosts' web traffic to mitmproxy.
    """

    def __init__(self):
        self.nft = nftables.Nftables(sofile='/usr/lib/x86_64-linux-gnu/libnftables.so.1')
        self.nft.set_echo_output(True)
        self.nft.set_handle_output(True)
        self.mitm_proxy_local_port = 8443

        self.nat_table = 'mitm_capture'
        self.chain = 'prerouting'

    def nft_run(self, tasks, show_result=True):
        rc, out, err = self.nft.json_cmd({'nftables': tasks})
        if rc != 0:
            raise ValueError(f'err={err!r} rc={rc}')
        if show_result:
            print('result:')
            pprint.pprint(out)

    def flush(self):
        self.nft_run([
            {
                'flush': {
                    'ruleset': None
                }
            },
        ], show_result=False)

    def _capture_rules(self, mac):
        rules = []
        match = match_source_mac(mac)
        for port in [80, 443]:
            for protocol in ['tcp', 'udp']:
                rules.append(
                    redirect_rule(self.nat_table,
                                  self.chain,
                                  match,
                                  protocol=protocol,
                                  attempt_dport=port,
                                  redirect_port=self.mitm_proxy_local_port))
        return rules

    def capture_outgoing_web_traffic(self, mac):
        tasks = [{
            'add': {
                'table': {
                    'family': 'inet',
                    'name': self.nat_table,
                }
            }
        }, {
            'add': {
                'chain': {
                    'family': 'inet',
                    'table': self.nat_table,
                    'name': self.chain,
                    'type': 'nat',
                    'hook': 'prerouting',
                    'prio': -100,
                }
            }
        }]
        tasks += [{'add': rule} for rule in self._capture_rules(mac)]
        self.nft_run(tasks)

    def uncapture(self, mac):
        self.nft_run([{'delete': rule} for rule in self._capture_rules(mac)])
