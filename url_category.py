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
        'https://api.rescuetime.com/collect',
        "https://docs.google.com/document/u/0/preload",
        "https://mail.google.com/domainreliability/upload",
    }:
        return True
    if url.startswith((
        "https://app.slack.com/boot/",
        'https://cello.client-channel.google.com/',
        'https://clients4.google.com/invalidation/lcs/client',
        'https://lh3.google.com/u/0/d/',
        'https://www.youtube.com/api/stats/atr',
        'https://www.youtube.com/yts/',
    )):
        return True
    for substr in [
        '/generate_204',
        '/favicon.ico',
        '/domainreliability/upload-nel'
    ]:
        if substr in url:
            return True
    return False
