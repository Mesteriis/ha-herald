"""Regression coverage for rewriting defaults at the service boundary."""

from __future__ import annotations

import pytest

from custom_components.herald.request import HeraldRequest
from custom_components.herald.services import NOTIFY_SCHEMA


@pytest.mark.parametrize(
    "options,expected",
    [
        ({}, True),
        ({"rewrite": False}, False),
        ({"already_humanized": True}, False),
        ({"already_humanized": False}, True),
        ({"already_humanized": True, "rewrite": True}, True),
        ({"already_humanized": False, "rewrite": False}, False),
    ],
)
def test_rewrite_default_preserves_explicit_and_legacy_opt_out(options, expected):
    data = NOTIFY_SCHEMA({"message": "CO2: 1200 ppm.", "channels": ["persistent_default"], **options})
    request = HeraldRequest.from_service_data(data)

    assert request.rewrite is expected
    assert request.message == "CO2: 1200 ppm."
    assert request.legacy_channels == ["persistent_default"]
