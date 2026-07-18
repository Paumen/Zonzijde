"""Shared outbound-HTTP settings.

requests verifies TLS against this bundle when an agent proxy is in the way;
a normal machine has neither the env var nor the file, so verify stays True.
"""

from __future__ import annotations

import os

CA_BUNDLE = (os.environ.get("REQUESTS_CA_BUNDLE")
             or os.environ.get("CURL_CA_BUNDLE")
             or "/root/.ccr/ca-bundle.crt")
VERIFY = CA_BUNDLE if os.path.exists(CA_BUNDLE) else True
