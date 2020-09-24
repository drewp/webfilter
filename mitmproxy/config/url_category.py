import urllib.parse

allowed_uniques = {
    'https://slackb.com/report-to',
}


def always_allowed(url: str):
    if url in allowed_uniques:
        return True
    if ('.googleusercontent.com' in url and url.endswith('jpg')) or 'googleusercontent.com/fife/' in url or 'googleusercontent.com/ogw/' in url:
        # avatar pics, but not arbitrary games and stuff
        return True
    netloc = urllib.parse.urlparse(url).netloc
    return ('.' + netloc).endswith((
        '.ada.support',
        '.bigasterisk.com',
        '.bootstrapcdn.com',
        '.cc0textures.com',
        '.cdn.kastatic.org',
        '.clever.com',
        '.cloudflare.com',
        '.cloudfront.net',
        '.github.com',
        '.gmail.com',
        '.google.com',
        '.googleapis.com',
        '.googletagmanager.com',
        '.gravatar.com',
        '.gstatic.com',
        '.illuminatehc.com',
        '.khanacademy.org',
        '.ocsp.apple.com'
        '.polyfill.io',
        '.remind.com',
        '.repl.it',
        '.slack-edge.com',
        '.slack-imgs.com',
        '.slack.com',
        '.struffelproductions.com',
        '.studiesweekly.com',
        '.wikimedia.org',
        '.wikipedia.org',
        '.willardmiddleschool.org',
        '.zoom.us',
    ))


def too_boring_to_log(url: str):
    if url in {
        'http://www.google.com/gen_204',
        'https://api.rescuetime.com/collect',
        'https://docs.google.com/document/u/0/preload',
        'https://docs.google.com/offline/offline/manifest',
        'https://mail.google.com/domainreliability/upload',
        'https://self.events.data.microsoft.com/OneCollector/1.0/',
        'https://slack.com/beacon/error',
    }:
        return True
    if url.startswith((
        'http://ocsp.digicert.com/',
        'http://ocsp.pki.goog/',
        'http://updates-http.cdn-apple.com/',
        'https://accounts.google.com/o/oauth2/postmessageRelay',
        'https://app.slack.com/boot/',
        'https://bigasterisk.slack.com/?redir=',
        'https://calendar.google.com/calendar/hello',
        'https://cello.client-channel.google.com/',
        'https://clients4.google.com/invalidation/lcs/client',
        'https://clients6.google.com/static/proxy.html',
        'https://configuration.ls.apple.com/config/defaults',
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
        'https://ocsp.apple.com/',
        'https://realtimesupport.clients6.google.com/static/proxy.html',
        'https://signaler-pa.clients6.google.com/',
        'https://www.google.com/_/VisualFrontendUi/gen204/',
        'https://www.remind.com/fonts/',
        'https://www.youtube.com/api/stats/atr',
        'https://www.youtube.com/api/stats/qoe',
        'https://www.youtube.com/yts/',
    )):
        return True
    for substr in [
        '/client_204',
        '/csi_204',
        '/domainreliability/upload',
        '/favicon.ico',
        '/gen_204',
        '/offline/cacheupdate?',
        '/generate_204',
    ]:
        if substr in url:
            return True
    return False

