import urllib.parse


def always_allowed(url: str):
    netloc = urllib.parse.urlparse(url).netloc
    return ('.' + netloc).endswith((
        '.bigasterisk.com',
        '.bootstrapcdn.com',
        '.cc0textures.com',
        '.struffelproductions.com',
        '.cdn.kastatic.org',
        '.clever.com',
        '.cloudflare.com',
        '.github.com',
        '.gmail.com',
        '.google.com',
        '.googleapis.com',
        '.gravatar.com',
        '.gstatic.com',
        '.khanacademy.org',
        '.polyfill.io',
        '.repl.it',
        '.slack-edge.com',
        '.slack.com',
        '.slack-imgs.com',
        '.studiesweekly.com',
        '.wikimedia.org',
        '.wikipedia.org',
    ))


def too_boring_to_log(url: str):
    if url in {
        'http://www.google.com/gen_204',
        'https://slack.com/beacon/error',
        'https://api.rescuetime.com/collect',
        'https://docs.google.com/document/u/0/preload',
        'https://mail.google.com/domainreliability/upload',
        'https://docs.google.com/offline/offline/manifest',

    }:
        return True
    if url.startswith((
        'https://accounts.google.com/o/oauth2/postmessageRelay',
        'https://app.slack.com/boot/',
        'https://bigasterisk.slack.com/?redir=',
        'https://cello.client-channel.google.com/',
        'https://clients4.google.com/invalidation/lcs/client',
        'https://clients6.google.com/static/proxy.html',
        'https://content.googleapis.com/static/proxy.html',
        'https://docs.google.com/document/backgroundsync',
        'https://docs.google.com/document/offline/',
        'https://docs.google.com/drawings/offline/',
        'https://docs.google.com/offline/common/cacheupdate',
        'https://docs.google.com/offline/extension/frame',
        'https://docs.google.com/offline/fallback',
        'https://docs.google.com/offline/iframeapi',
        'https://docs.google.com/offline/taskiframe',
        'https://docs.google.com/presentation/offline/',
        'https://docs.google.com/spreadsheets/j2clritzapp/static/',
        'https://docs.google.com/spreadsheets/offline/',
        'https://docs.google.com/static/',
        'https://drive.google.com/drive/_/dataservice/backgroundsync',
        'https://drive.google.com/drive/_/dataservice/cacheproxy',
        'https://drive.google.com/drive/offline/coldstart',
        'https://drive.google.com/drive/serviceworker/update',
        'https://lh3.google.com/u/0/d/',
        'https://realtimesupport.clients6.google.com/static/proxy.html',
        'https://signaler-pa.clients6.google.com/',
        'https://www.google.com/_/VisualFrontendUi/gen204/',
        'https://www.youtube.com/api/stats/atr',
        'https://www.youtube.com/api/stats/qoe',
        'https://calendar.google.com/calendar/hello',
        'https://www.youtube.com/yts/',
    )):
        return True
    for substr in [
        '/client_204',
        '/csi_204',
        '/domainreliability/upload-nel',
        '/favicon.ico',
        '/gen_204',
        '/offline/cacheupdate?',
        '/generate_204',
    ]:
        if substr in url:
            return True
    return False
