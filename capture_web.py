import sys
sys.path.append('/usr/lib/python3/dist-packages/')
import nftables
nft = nftables.Nftables(sofile='/usr/lib/x86_64-linux-gnu/libnftables.so.1')
nft.set_echo_output(True)
print(nft.json_cmd({'nftables':[
    {'add':
     {'table':
      {'name': 'nat'}}},
    {'add':
     {'chain':
      {'table': 'nat',
       'name': 'postrouting',
       'type': 'nat',
       'hook': 'postrouting',
       'priority': '-100'
       }
      }
     },
    {'add':
     {'rule':
      {'table': 'nat',
       'chain': 'postrouting',
       'expr': [
           {"snat":
            {"addr": '10.2.0.99',
             "port": 8443,
            }
           }
       ]
      }
     }
    }]}))
#ctx.run(r'sudo nft --echo add chain ip nat OUTPUT \{ type nat hook output priority -100\; policy accept; \}', pty=True)

#ctx.run(rf'sudo nft --echo add rule  ip nat OUTPUT skuid \!= 0 tcp dport {port} counter redirect to :8443')
