from __future__ import annotations

import atexit
import os
import tempfile

# The egress proxy inspects some hosts (chain rooted in the Anthropic proxy CA
# bundle) and passes others through with their real public chain. Trusting only
# one root set makes the other class of host fail TLS, so verification must union
# the public roots (certifi) with the proxy CA bundle — do not collapse this back
# to a single bundle.
CA_BUNDLE = (os.environ.get("REQUESTS_CA_BUNDLE")
             or os.environ.get("CURL_CA_BUNDLE")
             or "/root/.ccr/ca-bundle.crt")


def _build_verify() -> str | bool:
    try:
        import certifi
        public = certifi.where()
    except Exception:
        public = None
    have_proxy = os.path.exists(CA_BUNDLE)
    if public and have_proxy:
        fd, path = tempfile.mkstemp(prefix="zonzijde-ca-", suffix=".pem")
        try:
            with os.fdopen(fd, "wb") as out, \
                    open(public, "rb") as pub, open(CA_BUNDLE, "rb") as proxy:
                out.write(pub.read())
                out.write(b"\n")
                out.write(proxy.read())
        except Exception:
            os.unlink(path)
            raise
        atexit.register(lambda: os.unlink(path) if os.path.exists(path) else None)
        return path
    if have_proxy:
        return CA_BUNDLE
    return public or True


VERIFY = _build_verify()
