from invoke import task, Collection

import sys
sys.path.append('/my/proj/release')
from serv_tasks import serv_tasks

ns = Collection()

c = Collection('webfilter')
ns.add_collection(c)
serv_tasks(c, 'serv.n3', 'webfilter')
c = Collection('report')
ns.add_collection(c)
serv_tasks(c, 'serv.n3', 'webfilter_report')
