"""
To see a dump in nft-language:
  nft list ruleset


See
https://github.com/firewalld/firewalld/blob/master/src/firewall/core/nftables.py
for one of the few other published users of the nft json API.
"""
from pprint import pprint
import nftables


def match_saddr(ip):
    return {"match": {
        "left": {"payload": {"protocol": "ip", "field": "saddr"}},
        "op": "==",
        "right":  {"prefix": {"addr": ip, "len": 32}}
    }}


def match_source_mac(mac):
    return {"match": {
        "left": {"payload": {"protocol": "ether", "field": "saddr"}},
        "op": "==",
        "right": mac
    }}


def match_dport(protocol, port):
    return {"match": {
        "left": {"payload": {"protocol": protocol, "field": "dport"}},
        "op": "==",
        "right": port
    }}


def redirect_rule(table, chain, source_match, protocol, attempt_dport, redirect_port):
    return {'rule': {
        'family': 'inet',
        'table': table,
        'chain': chain,
        'expr': [
            source_match,
            match_dport(protocol, attempt_dport),
            {"redirect": {"port": redirect_port}},
        ]
    }}


class RuleMaker:
    """
    Build nft rules for redirecting internal hosts' web traffic to mitmproxy.
    """

    def __init__(self):
        self.nft = nftables.Nftables(
            sofile='/usr/lib/x86_64-linux-gnu/libnftables.so.1')
        self.nft.set_echo_output(True)
        self.nft.set_handle_output(True)
        self.mitm_proxy_local_port = 8443

    def nft_run(self, tasks, show_result=True):
        rc, out, err = self.nft.json_cmd({'nftables': tasks})
        if rc != 0:
            raise ValueError(f'err={err!r} rc={rc}')
        if show_result:
            print('result:')
            pprint(out)

    def flush(self):
        self.nft_run([
            {'flush':  {'ruleset': None}},
        ], show_result=False)

    def capture_outgoing_web_traffic(self, mac):
        nat_table = 'mitm_capture'
        chain = 'prerouting'
        match = match_source_mac(mac)

        blocks = []
        for port in [80, 443]:
            for protocol in ['tcp', 'udp']:
                blocks.append({'add': redirect_rule(nat_table,
                                  chain,
                                  match,
                                  protocol=protocol,
                                  attempt_dport=port,
                                  redirect_port=self.mitm_proxy_local_port)})

        self.nft_run([
            {'add': {'table': {
                'family': 'inet',
                'name': nat_table,
            }}},
            {'add': {'chain': {
                'family': 'inet',
                'table': nat_table,
                'name': chain,
                'type': 'nat',
                'hook': 'prerouting',
                'prio': -100,
            }}}] + blocks)


macs_to_send_through_mitmproxy = [
    # 'dc:ef:ca:ed:58:27', # drewnote
    '7c:b0:c2:83:31:0f',  # arilaptop
    'c8:1f:66:13:9b:6d',  # dot
    '1c:c1:de:56:e6:70',  # music
    #'0c:fe:45:db:33:9e',  # ps4
]

if __name__ == '__main__':
    rm = RuleMaker()
    rm.flush()
    for mac in macs_to_send_through_mitmproxy:
        rm.capture_outgoing_web_traffic(mac)
    # possibly need a mitmproxy restart after this for very-long-lived
    # connections or tables
