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
            "https://docs.google.com/document/u/0/preload",
        "https://app.slack.com/boot/block-kit-builder.html",
        "https://app.slack.com/boot/client.html",
        "https://app.slack.com/boot/docs.html",
        "https://app.slack.com/boot/workflow-builder.html",
        "https://beacons.gvt2.com/domainreliability/upload-nel",
        "https://beacons2.gvt2.com/domainreliability/upload-nel",
        "https://beacons4.gvt2.com/domainreliability/upload-nel",
        "https://mail.google.com/domainreliability/upload",
        'http://www.google.com/gen_204',
        'https://api.rescuetime.com/collect',
    }:
        return True
    if url.startswith((
        'https://clients4.google.com/invalidation/lcs/client',
        'https://lh3.google.com/u/0/d/',
        'https://www.youtube.com/api/stats/atr',
        'https://www.youtube.com/yts/',

    )):
        return True
    for substr in ['/generate_204', '/favicon.ico']:
        if substr in url:
            return True
    return False
