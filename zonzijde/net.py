from __future__ import annotations

import os

CA_BUNDLE = (os.environ.get("REQUESTS_CA_BUNDLE")
             or os.environ.get("CURL_CA_BUNDLE")
             or "/root/.ccr/ca-bundle.crt")
VERIFY = CA_BUNDLE if os.path.exists(CA_BUNDLE) else True
