"""Opt-in identity adapter for a private, emulated macOS Anisette bridge.

The unmodified remote provider substitutes the phone's uid/device ID for the
Anisette machine's. Apple started rejecting this mismatch in October 2026.
Only URLs ending in /v3/get_headers use this experimental adapter. Normal
Anisette servers and local Android Anisette keep their existing behavior.
"""

import base64
import json
import re
from urllib.parse import urlparse
from urllib.request import urlopen


_BRIDGE_PATH = "/v3/get_headers"
_MAC_CLIENT = re.compile(r"^<([^>]+)> <([^;<>]+);([^;<>]+);([^;<>]+)> <")


def is_bridge_url(url: str | None) -> bool:
    if not url:
        return False
    parsed = urlparse(url)
    return parsed.scheme in ("http", "https") and parsed.path == _BRIDGE_PATH and not parsed.query


def load_profile(url: str) -> tuple[dict, dict]:
    """Return (provider kwargs, account kwargs), without logging any headers.

    The Mac identity is fixed by the existing, provisioned emulated machine.
    This is intentionally fail-closed: a malformed response must never make a
    login silently revert to the phone's different machine identity.
    """
    if not is_bridge_url(url):
        raise ValueError("Not an emulated Mac bridge URL")

    from findmy.reports.anisette import DeviceIdentity

    with urlopen(url, timeout=10) as response:
        data = json.load(response)

    client = data["X-MMe-Client-Info"]
    match = _MAC_CLIENT.match(client)
    if not match:
        raise ValueError("Bridge returned invalid Mac client info")
    model, os_name, os_version, os_build = match.groups()
    if (model, os_name, os_version, os_build) != (
        "MacBookPro13,2", "macOS", "13.1", "22C65"
    ):
        raise ValueError("Bridge's platform differs from the provisioned Mac profile")

    # This is the documented macOS 13.1 platform paired with the default
    # CoreADI emulation identity, not the Android phone's platform.
    identity = DeviceIdentity(
        model=model,
        os_name=os_name,
        os_version=os_version,
        os_build=os_build,
        cfnetwork="1404.0.5",
        darwin="22.2.0",
    )
    uid = base64.b64decode(data["X-Apple-I-MD-LU"], validate=True).decode("utf-8")
    devid = data["X-Mme-Device-Id"]
    serial = data["X-Apple-I-SRL-NO"]
    if not uid or not devid or not serial:
        raise ValueError("Bridge identity is incomplete")
    return {"identity": identity, "serial": serial}, {"uid": uid, "devid": devid}
