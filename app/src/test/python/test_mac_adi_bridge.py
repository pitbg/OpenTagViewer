"""Offline regression tests for the opt-in macOS ADI bridge identity."""

import base64
import io
import json

import pytest

import mac_adi_bridge


def test_only_explicit_bridge_path_is_enabled():
    assert mac_adi_bridge.is_bridge_url("https://private.example/v3/get_headers")
    assert not mac_adi_bridge.is_bridge_url("https://ani.example")
    assert not mac_adi_bridge.is_bridge_url("https://private.example/v3/get_headers?x=1")
    assert not mac_adi_bridge.is_bridge_url("file:///v3/get_headers")


def _response(**changes):
    data = {
        "X-MMe-Client-Info": "<MacBookPro13,2> <macOS;13.1;22C65> <com.apple.AuthKit/1 (com.apple.akd/1.0)>",
        "X-Apple-I-MD-LU": base64.b64encode(b"stable-local-user-id").decode(),
        "X-Mme-Device-Id": "00006000-FAKE",
        "X-Apple-I-SRL-NO": "TESTSERIAL00",
    }
    data.update(changes)
    return io.BytesIO(json.dumps(data).encode())


def test_bridge_reuses_provisioned_identity(monkeypatch):
    monkeypatch.setattr(mac_adi_bridge, "urlopen", lambda *_a, **_kw: _response())
    provider, account = mac_adi_bridge.load_profile("https://private.example/v3/get_headers")
    assert provider["identity"].model == "MacBookPro13,2"
    assert provider["identity"].os_build == "22C65"
    assert provider["serial"] == "TESTSERIAL00"
    assert account == {"uid": "stable-local-user-id", "devid": "00006000-FAKE"}


def test_bridge_rejects_an_identity_mismatch(monkeypatch):
    monkeypatch.setattr(
        mac_adi_bridge,
        "urlopen",
        lambda *_a, **_kw: _response(
            **{"X-MMe-Client-Info": "<iPhone15,2> <iPhone OS;17.4;21E219> <com.apple.AuthKit/1 (com.apple.akd/1.0)>"}
        ),
    )
    with pytest.raises(ValueError, match="invalid Mac client info|differs"):
        mac_adi_bridge.load_profile("https://private.example/v3/get_headers")
