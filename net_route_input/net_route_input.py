import datetime
import json
from typing import Set

import cyclone.sse
import cyclone.web
import docopt
import pymongo
import pymongo.collection
from dateutil.tz import tzutc
from prometheus_client import Summary
from prometheus_client.exposition import generate_latest
from prometheus_client.registry import REGISTRY
from standardservice.logsetup import log, verboseLogging
from twisted.internet import reactor


class Metrics(cyclone.web.RequestHandler):

    def get(self):
        self.add_header('content-type', 'text/plain')
        self.write(generate_latest(REGISTRY))


class Hosts(cyclone.web.RequestHandler):

    def get(self):
        hosts = self.settings.hosts  # type: pymongo.collection.Collection
        self.write({'macs': list(hosts.find(projection={'_id': 0}, sort=[('name', 1)]))})


class ModeSettings(cyclone.sse.SSEHandler):

    def bind(self):
        self.settings.poller.requests.add(self)
        msg = self.settings.poller.getModeUpdate()
        self.sendEvent(msg)

    def unbind(self):
        self.settings.poller.requests.remove(self)


class SetMode(cyclone.web.RequestHandler):

    def put(self):
        routes = self.settings.routes  # type: pymongo.collection.Collection
        mac = self.get_argument('mac')
        if not self.settings.hosts.find_one({'mac': mac}):
            raise ValueError(f'mac not found: {mac!r}')
        mode = self.get_argument('mode')
        if mode not in ['open', 'mitmproxy', 'drop']:
            raise ValueError(f'mode {mode}')
        filter = self.get_argument('filter')
        if filter not in ['open', 'filtered', '']:
            raise ValueError(f'filter {filter}')

        routes.update_one(
            {'mac': mac},
            {  #
                '$set': {
                    'mode': mode,
                    'mitmproxyFilter': filter,
                    'lastChange': datetime.datetime.now(tzutc())
                }
            },
            upsert=True)
        self.settings.poller.onChange()
        self.write('ok')


class Poller:

    def __init__(self, routes: pymongo.collection.Collection):
        self.routes = routes
        self.requests = set()  # type: Set[cyclone.sse.SSEHandler]

        # todo: also watch db for stray changes that weren't made by our SetMode

    def getModeUpdate(self):
        updates = []
        for update in self.routes.find(  #
                projection={
                    '_id': 0,
                    'mac': 1,
                    'mode': 1,
                    'mitmproxyFilter': 1,
                    'allowedModes': 1,
                    'lastChange': 1
                }, sort=[('mac', 1)]):
            update['lastChange'] = update['lastChange'].isoformat()
            updates.append(update)
        return {'updates': updates}

    def onChange(self):
        msg = json.dumps(self.getModeUpdate())
        for req in self.requests:
            req.sendEvent(msg)


def fillHosts(hosts: pymongo.collection.Collection):
    # drop old rows first? don't even use mongodb for this data?
    with open('/opt/private_data.json') as initData:
        d = json.load(initData)
        for row in d:
            hosts.update(spec={'mac': row['mac']}, document=row, upsert=True)


def main():
    args = docopt.docopt('''
Usage:
  net_route_input.py [options]

Options:
  -v, --verbose  more logging
''')
    verboseLogging(args['--verbose'])

    db = pymongo.MongoClient('mongodb.default.svc.cluster.local', tz_aware=True).get_database('timebank')
    hosts = db.get_collection('hosts')
    routes = db.get_collection('routes')
    fillHosts(hosts)

    poller = Poller(routes)

    reactor.listenTCP(
        8000,
        cyclone.web.Application(
            [
                (r'/(|bundle\.js|main\.css)', cyclone.web.StaticFileHandler, {
                    'path': 'build',
                    'default_filename': 'index.html'
                }),
                (r'/hosts', Hosts),
                (r'/modeSettings', ModeSettings),
                (r'/modeSet', SetMode),
                (r'/metrics', Metrics),
            ],
            debug=args['--verbose'],
            hosts=hosts,
            routes=routes,
            poller=poller,
        ))
    reactor.run()


if __name__ == '__main__':
    main()
