from invoke import task, Collection

import sys
sys.path.append('/my/proj/release')
from serv_tasks import serv_tasks

ns = Collection()
serv_tasks(ns, 'serv.n3', 'webfilter')

@ns.add_task
@task
def proxy_start(ctx):
    for proto in ['', '6']:
        for port in [80, 443]:
            ctx.run(f'sudo ip{proto}tables '
                    f'-t nat '
                    f'-A OUTPUT '
                    f'-p tcp '
                    f'-m owner ! --uid-owner root '
                    f'--dport {port} '
                    f'-j REDIRECT '
                    f'--to-port 8443', pty=True)

@ns.add_task
@task
def proxy_stop(ctx):
    ctx.run(f'sudo iptables-save | grep -v 8443 | sudo iptables-restore', pty=True)
