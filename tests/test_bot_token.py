#!/usr/bin/env python3
# Telegram notifications for Checkmk
# License: GNU General Public License v2 - see LICENSE
"""The bot token must survive every format a version of this package stored.

Each case goes through the same path as a real notification: the stored
parameter is flattened into NOTIFY_PARAMETER_* variables and the script reads
the token back.
"""

from __future__ import annotations

import cmk_stub
import pytest
from conftest import load_ruleset, load_script

EXPLICIT = "1234567890:AAEXPLICITEXPLICITEXPLICITEXPLICITE"
STORED = "1234567890:AASTORESTORESTORESTORESTORESTORESTO"

# what each version wrote to notification_parameter.mk for the bot token
STORED_FORMATS = {
    "2.1.0 plain string": EXPLICIT,
    "2.1.x explicit": ("bot_key", EXPLICIT),
    "2.1.x password store": ("store", "telegram_bot"),
    "2.2.0 explicit": ("cmk_postprocessed", "explicit_password", ("uuid1234", EXPLICIT)),
    "2.2.0 password store": ("cmk_postprocessed", "stored_password", ("telegram_bot", "")),
}
EXPECTED = {
    "2.1.0 plain string": EXPLICIT,
    "2.1.x explicit": EXPLICIT,
    "2.1.x password store": STORED,
    "2.2.0 explicit": EXPLICIT,
    "2.2.0 password store": STORED,
}


@pytest.fixture(autouse=True)
def password_store():
    cmk_stub.PASSWORD_STORE.clear()
    cmk_stub.PASSWORD_STORE["telegram_bot"] = STORED


def _context(params: dict) -> dict[str, str]:
    context: dict[str, str] = {}
    cmk_stub.add_to_event_context(context, "PARAMETER", params)
    return context


@pytest.mark.parametrize("label", sorted(STORED_FORMATS))
def test_script_reads_the_token_as_stored(label):
    script = load_script()
    context = _context({"bot_key": STORED_FORMATS[label], "group_id": "-100"})
    assert script.get_bot_token(context) == EXPECTED[label]


@pytest.mark.parametrize("label", sorted(STORED_FORMATS))
def test_script_reads_the_token_after_the_gui_migrated_it(label):
    """Saving the parameter in the GUI rewrites it through the form spec migration."""
    script = load_script()
    migrated = load_ruleset()._migrate_bot_key(STORED_FORMATS[label])
    assert migrated[0] == "cmk_postprocessed"
    context = _context({"bot_key": migrated, "group_id": "-100"})
    assert script.get_bot_token(context) == EXPECTED[label]


def test_migration_rejects_unknown_formats():
    with pytest.raises(ValueError):
        load_ruleset()._migrate_bot_key(("something", "else"))


def test_keys_from_older_telegram_packages_are_dropped():
    ruleset = load_ruleset()
    value = {"bot_key": EXPLICIT, "group_id": "-1", "bot_token": EXPLICIT, "chat_id": "-1"}
    assert ruleset._drop_unknown_keys(value) == {"bot_key": EXPLICIT, "group_id": "-1"}


def test_rule_spec_matches_the_notification_script_name():
    """Checkmk links parameters and script by this name."""
    spec = load_ruleset().rule_spec_telegram
    assert spec.name == "telegram"
    assert spec.topic == "notifications"
