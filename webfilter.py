from mitmproxy import http
import json

def request(flow: http.HTTPFlow):
    # redirect to different host
    print(f'request {flow.request.pretty_host}')
    r = flow.request
    if r.pretty_host == 'bigasterisk.slack.com' and r.method == 'POST' and r.path_components[-1] == 'chat.postMessage':
        slack_channel = r.multipart_form[b'channel'].decode('ascii')
        message = json.loads(r.multipart_form[b'blocks'])
        print('slack chat', slack_channel, message)

    if r.pretty_host == 'discordapp.com' and r.method == 'POST' and r.path_components[-1] == 'messages':
        if r.path_components[2] != 'channels':
            raise NotImplementedError
        discord_channel = r.path_components[3]
        message = json.loads(r.content)
        print('discord chat', discord_channel, message)

    if r.pretty_host == 'www.youtube.com' and r.path_components[0] == 'watch':
        print('yt watch', r.pretty_url)

    if r.pretty_url.startswith('https://www.youtube.com/api/stats/watchtime'):
        d = dict(r.query)
        print('yt watchtime', d.get('state'), d.get('cmt'), d.get('len'), d.get('docid'))

    if r.pretty_host == "example.com":
        flow.kill()
