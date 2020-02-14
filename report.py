"""
serve a live rdf graph of what's happening in the
mongo.timebank.webproxy event log, plus maybe some historical analyses
"""
import datetime
import urllib.parse

from dateutil.tz import tzlocal
from docopt import docopt
from pymongo import MongoClient
from rdflib import Namespace, Literal, URIRef, RDF
from twisted.internet import reactor, task
import cyclone.web
from typing import Set

from standardservice.logsetup import log, verboseLogging
from patchablegraph import PatchableGraph, CycloneGraphEventsHandler, CycloneGraphHandler
from rdfdb.patch import Patch

import url_category

ROOM = Namespace("http://projects.bigasterisk.com/room/")
DCTERMS = Namespace("http://purl.org/dc/terms/")

class Boring(ValueError): pass

def localTimeLiteral(t: datetime.datetime) -> Literal:
    return Literal(t.astimezone(tzlocal()).isoformat(), datatype=ROOM.todo)

def uriFromMongoEvent(docId):
    return URIRef(f'http://bigasterisk.com/webfilter/event/{docId}')

def textFromSlack(message):
    elements = message[0]['elements'][0]['elements']
    return ' '.join(part['text'] for part in elements)

def quadsForEvent(doc):
    ctx = URIRef('http://bigasterisk.com/timebank')
    uri = uriFromMongoEvent(doc['_id'])
    ret = [
        (uri, RDF.type, ROOM['Activity'], ctx),
        (uri, DCTERMS['created'], localTimeLiteral(doc['t']), ctx),
        (uri, DCTERMS['creator'], Literal(doc.get('mac', 'missing-mac')), ctx),
        ]
    tag = doc.get('tag', 'unknown')
    thumbnailUrl = URIRef('other-' + tag)
    if tag == 'youtube':
        ret.extend([
            (uri, RDF.type, ROOM['WebRequest'],  ctx),
        ])
        thumbnailUrl = URIRef('/lib/fontawesome/5.12.1/svgs/brands/youtube.svg')
        if 'watchtime' in doc:
            wt = doc['watchtime']
            ret.extend([
                (uri, ROOM['link'], URIRef(f'https://www.youtube.com/watch?v={wt["vid"]}'), ctx),
                (uri, ROOM['currentTime'], Literal(wt['pos']), ctx),
                (uri, ROOM['videoDuration'], Literal(wt['len']), ctx),
                 ])
        else:
            vid = doc['watchPage'].split('v=')[1].split('&')[0]
            ret.extend([
                (uri, ROOM['viewUrl'], URIRef(doc['watchPage']), ctx),
                (uri, ROOM['videoThumbnailUrl'],
                 URIRef(f'https://img.youtube.com/vi/{vid}/default.jpg'), ctx),
            ])
    elif tag == 'slackChat':
        thumbnailUrl = URIRef('/lib/fontawesome/5.12.1/svgs/brands/slack.svg')
        ret.extend([
            (uri, RDF.type, ROOM['Chat'], ctx),
            (uri, ROOM['desc'], Literal(textFromSlack(doc['message'])), ctx),
        ])
    elif tag == 'htmlPage':
        if url_category.too_boring_to_log(doc['url']):
            raise Boring()
        thumbnailUrl = URIRef('/lib/fontawesome/5.12.1/svgs/brands/chrome.svg')
        query = urllib.parse.splitquery(doc['url'])[1]
        if query:
            d = urllib.parse.parse_qs(query)
            if 'q' in d:
                ret.append((uri, ROOM['searchQuery'], Literal(d['q'][0]), ctx))
        ret.extend([
            (uri, ROOM['link'], URIRef(doc['url']), ctx),
        ])

    ret.extend([
        (uri, ROOM['thumbnailUrl'], thumbnailUrl, ctx),
    ])

    return ret

def update(masterGraph, eventsInGraph, coll):
    eventsInGraph = set()
    recentEvents = set()

    fetched_nonboring_docs = 0
    for doc in coll.find({}, sort=[('t', -1)], limit=1000):
        uri = uriFromMongoEvent(doc['_id'])
        recentEvents.add(uri)
        if uri in eventsInGraph:
            fetched_nonboring_docs += 1
        else:
            try:
                masterGraph.patch(Patch(addQuads=quadsForEvent(doc)))
                eventsInGraph.add(uri)
                fetched_nonboring_docs += 1
            except Boring:
                pass
        if fetched_nonboring_docs > 100:
            break

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
                (r'/graph/webevents',
                 CycloneGraphHandler, {'masterGraph': masterGraph}),
                (r'/graph/webevents/events',
                 CycloneGraphEventsHandler, {'masterGraph': masterGraph}),
            ]
            cyclone.web.Application.__init__(self, handlers,
                                             masterGraph=masterGraph, coll=coll)
    task.LoopingCall(update, masterGraph, eventsInGraph, coll).start(10)
    reactor.listenTCP(9074, Application())
    reactor.run()

if __name__ == '__main__':
    main()
