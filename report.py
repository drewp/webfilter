"""
serve a live rdf graph of what's happening in the
mongo.timebank.webproxy event log, plus maybe some historical analyses
"""
import sys, datetime, logging

from dateutil.tz import tzlocal
from docopt import docopt
from pymongo import MongoClient
from rdflib import Namespace, Literal, URIRef, RDF
from twisted.internet import reactor, task, defer
import cyclone.web

from standardservice.logsetup import log, verboseLogging
from patchablegraph import PatchableGraph, CycloneGraphEventsHandler, CycloneGraphHandler
from rdfdb.patch import Patch

ROOM = Namespace("http://projects.bigasterisk.com/room/")


def uriFromMongoEvent(docId):
    return URIRef(f'http://bigasterisk.com/webfilter/event/{docId}')

def quadsForEvent(doc):
    ctx = URIRef('http://bigasterisk.com/timebank')
    uri = uriFromMongoEvent(doc['_id'])
    ret = [
        (uri, RDF.type, ROOM['Activity'], ctx),
        ]
    if doc.get('tag', '') == 'youtube':
        ret.extend([
            (uri, RDF.type, ROOM['WebRequest'],  ctx),
        ])
        if 'watchtime' in doc:
            wt = doc['watchtime']
            ret.extend([
                (uri, ROOM['thumbnailUrl'], URIRef('http://...'), ctx),
                (uri, ROOM['link'], URIRef(f'https://www.youtube.com/watch?v={wt["vid"]}'), ctx),
                (uri, ROOM['currentTime'], Literal(wt['pos']), ctx),
                (uri, ROOM['videoDuration'], Literal(wt['len']), ctx),
                 ])
        else:
            ret.extend([
                (uri, ROOM['viewUrl'], URIRef(doc['watchPage']), ctx),
            ])
    return ret

def update(masterGraph, coll):
    eventsInGraph = set()
    recentEvents = set()

    for doc in coll.find({}, sort=[('t', -1)], limit=100):
        uri = uriFromMongoEvent(doc['_id'])
        recentEvents.add(uri)
        if not masterGraph.contains(uri):
            masterGraph.patch(Patch(addQuads=quadsForEvent(doc)))

    for uri in eventsInGraph.difference(recentEvents):
        oldStatements = list(masterGraph.quads((uri, None, None, None)))
        masterGraph.patch(Patch(delQuads=oldStatements))

def main():
    arg = docopt("""
    Usage: report.py [options]

    -v                    Verbose
    """)
    verboseLogging(arg['-v'])

    masterGraph = PatchableGraph()
    coll = MongoClient('bang5', tz_aware=True).get_database('timebank').get_collection('webproxy')

    class Application(cyclone.web.Application):
        def __init__(self):
            handlers = [
                (r"/()",
                 cyclone.web.StaticFileHandler,
                 {"path": ".", "default_filename": "index.html"}),
                (r'/build/(bundle\.js)', cyclone.web.StaticFileHandler,
                {"path":"build"}),
                (r'/webevents',
                 CycloneGraphHandler, {'masterGraph': masterGraph}),
                (r'/webevents/events',
                 CycloneGraphEventsHandler, {'masterGraph': masterGraph}),
            ]
            cyclone.web.Application.__init__(self, handlers,
                                             masterGraph=masterGraph, coll=coll)
    task.LoopingCall(update, masterGraph, coll).start(5)
    reactor.listenTCP(9074, Application())
    reactor.run()

if __name__ == '__main__':
    main()
