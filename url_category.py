import urllib.parse


def always_whitelisted(url: str):
    netloc = urllib.parse.urlparse(url).netloc
    return ('.' + netloc).endswith((
        '.gmail.com',
        '.google.com',
        '.googleapis.com',
        '.gstatic.com',
        '.slack-edge.com',
        '.slack.com',
        '.bigasterisk.com',
        '.wikimedia.org',
        '.wikipedia.org',
        '.repl.it',
        '.gravatar.com',
        '.polyfill.io',
        '.cloudflare.com',
        '.khanacademy.org',
        '.cdn.kastatic.org',
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
        'https://app.slack.com/boot/',
        'https://accounts.google.com/o/oauth2/postmessageRelay',
        'https://bigasterisk.slack.com/?redir=',
        'https://cello.client-channel.google.com/',
        'https://clients4.google.com/invalidation/lcs/client',
        'https://docs.google.com/document/backgroundsync',
        'https://docs.google.com/document/offline/comment',
        'https://docs.google.com/document/offline/edit',
        'https://docs.google.com/document/offline/hs',
        'https://docs.google.com/document/offline/view',
        'https://docs.google.com/document/offline/viewcomments',
        'https://docs.google.com/offline/common/cacheupdate',
        'https://docs.google.com/offline/extension/frame',
        'https://docs.google.com/offline/fallback',
        'https://docs.google.com/offline/iframeapi',
        'https://docs.google.com/offline/taskiframe',
        'https://drive.google.com/drive/_/dataservice/backgroundsync',
        'https://drive.google.com/drive/_/dataservice/cacheproxy',
        'https://drive.google.com/drive/offline/coldstart',
        'https://drive.google.com/drive/serviceworker/update',
        'https://lh3.google.com/u/0/d/',
        'https://realtimesupport.clients6.google.com/static/proxy.html',
        'https://www.youtube.com/api/stats/atr',
        'https://www.youtube.com/yts/',
    )):
        return True
    for substr in [
        '/client_204',
        '/domainreliability/upload-nel',
        '/favicon.ico',
        '/gen_204',
        '/offline/cacheupdate?',
        '/generate_204',
    ]:
        if substr in url:
            return True
    return False
