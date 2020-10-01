import requests


def say(msg):
    for user in [
            'http://bigasterisk.com/foaf.rdf#drewp',
            'http://bigasterisk.com/kelsi/foaf.rdf#kelsi',
    ]:
        try:
            requests.post('http://c3po.default.svc.cluster.local:9040/', data={'user': str(user), 'msg': msg, 'mode': 'slack'}, timeout=2)
        except requests.exceptions.ReadTimeout:
            pass  # prob worked. Not sure why this breaks.
        except Exception:
            import traceback
            traceback.print_exc()
            raise
