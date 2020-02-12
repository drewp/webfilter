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
DCTERMS = Namespace("http://purl.org/dc/terms/")

def localTimeLiteral(t: datetime.datetime) -> Literal:
    return Literal(t.astimezone(tzlocal()).isoformat(), datatype=ROOM.todo)

def uriFromMongoEvent(docId):
    return URIRef(f'http://bigasterisk.com/webfilter/event/{docId}')

def textFromSlack(message):
    print(repr(message))
    elements = message[0]['elements'][0]['elements']
    return ' '.join(part['text'] for part in elements)

def quadsForEvent(doc):
    ctx = URIRef('http://bigasterisk.com/timebank')
    uri = uriFromMongoEvent(doc['_id'])
    ret = [
        (uri, RDF.type, ROOM['Activity'], ctx),
        (uri, DCTERMS['created'], localTimeLiteral(doc['t']), ctx),
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
    elif doc.get('tag', '') == 'slackChat':
        ret.extend([
            (uri, RDF.type, ROOM['Chat'], ctx),
            (uri, ROOM['thumbnailUri'], URIRef('slackthumb'), ctx),
            (uri, ROOM['desc'], Literal(textFromSlack(doc['message'])), ctx),
        ])

    return ret

def update(masterGraph, eventsInGraph, coll):
    eventsInGraph = set()
    recentEvents = set()

    for doc in coll.find({}, sort=[('t', -1)], limit=30):
        uri = uriFromMongoEvent(doc['_id'])
        recentEvents.add(uri)
        if uri not in eventsInGraph:
            masterGraph.patch(Patch(addQuads=quadsForEvent(doc)))
            eventsInGraph.add(uri)

    for uri in eventsInGraph.difference(recentEvents):
        oldStatements = list(masterGraph.quads((uri, None, None, None)))
        masterGraph.patch(Patch(delQuads=oldStatements))
        eventsInGraph.remove(uri)

def main():
    arg = docopt("""
    Usage: report.py [options]

    -v                    Verbose
    """)
    verboseLogging(arg['-v'])

    masterGraph = PatchableGraph()
    eventsInGraph: Set[URIRef] = set()
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
    task.LoopingCall(update, masterGraph, eventsInGraph, coll).start(5)
    reactor.listenTCP(9074, Application())
    reactor.run()

if __name__ == '__main__':
    main()
