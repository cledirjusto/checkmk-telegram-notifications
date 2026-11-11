#!/usr/bin/env python3
# Copyright (C) 2023 Dragosiz ft. Mario Casero mario.casero@dragosiz.es
# Copyright (C) 2026 Cledir Justo
# License: GNU General Public License v2 - see LICENSE
# Este archivo es parte de la integración con Checkmk para notificaciones de Telegram.
#
# 2.2.0: notification parameters via the rulesets API (cmk.rulesets.v1) instead of
#        the legacy GUI plug-in in web/plugins/wato. The bot token uses the standard
#        Checkmk Password field (explicit or password store).

import uuid

from cmk.rulesets.v1 import Help, Message, Title
from cmk.rulesets.v1.form_specs import (
    DictElement,
    Dictionary,
    Password,
    String,
    validators,
)
from cmk.rulesets.v1.rule_specs import NotificationParameters, Topic

_CHAT_ID_REGEX = r"^-?[0-9]+$"


def _migrate_bot_key(value: object) -> tuple[str, str, tuple[str, str]]:
    """Accept every format older versions of this package stored."""
    # 2.1.0: plain token string
    if isinstance(value, str):
        return ("cmk_postprocessed", "explicit_password", (f"uuid{uuid.uuid4()}", value))
    if isinstance(value, tuple):
        # 2.1.1/2.1.2: ("bot_key", token) or ("store", password_id)
        if len(value) == 2 and value[0] == "bot_key":
            return ("cmk_postprocessed", "explicit_password", (f"uuid{uuid.uuid4()}", value[1]))
        if len(value) == 2 and value[0] == "store":
            return ("cmk_postprocessed", "stored_password", (value[1], ""))
        # Already in the Password form spec format
        if len(value) == 3:
            return value  # type: ignore[return-value]
    raise ValueError(f"Invalid bot token format: {value!r}")


def _drop_unknown_keys(value: object) -> dict[str, object]:
    # Parameters migrated from older Telegram packages may still carry
    # bot_token/chat_id next to bot_key/group_id.
    assert isinstance(value, dict)
    return {k: v for k, v in value.items() if k in ("bot_key", "group_id")}


def _parameter_form() -> Dictionary:
    return Dictionary(
        title=Title("Telegram notification parameters"),
        migrate=_drop_unknown_keys,
        elements={
            "bot_key": DictElement(
                required=True,
                parameter_form=Password(
                    title=Title("Bot Token"),
                    help_text=Help(
                        "Telegram bot access token from BotFather. "
                        "Choose the password store to keep the token out of the rule."
                    ),
                    migrate=_migrate_bot_key,
                ),
            ),
            "group_id": DictElement(
                required=True,
                parameter_form=String(
                    title=Title("Chat or group ID"),
                    help_text=Help(
                        "The ID of the Telegram chat or group to which notifications will be "
                        "sent. This ID is obtained by sending a message to the bot and then "
                        "using the Telegram API."
                    ),
                    custom_validate=[
                        validators.LengthInRange(
                            min_value=1,
                            error_msg=Message("The chat or group ID cannot be empty"),
                        ),
                        validators.MatchRegex(
                            _CHAT_ID_REGEX,
                            error_msg=Message("The chat or group ID must be a number."),
                        ),
                    ],
                ),
            ),
        },
    )


rule_spec_telegram = NotificationParameters(
    name="telegram",
    title=Title("Telegram"),
    topic=Topic.NOTIFICATIONS,
    parameter_form=_parameter_form,
)
