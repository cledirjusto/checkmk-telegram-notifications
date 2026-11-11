#!/usr/bin/env python3
# Telegram notifications for Checkmk
# License: GNU General Public License v2 - see LICENSE
"""Minimal stand-ins for the Checkmk modules the plug-ins import.

The ruleset and the notification script can only be imported inside a Checkmk
site. These stubs reproduce the behaviour the plug-ins rely on, copied from
Checkmk 2.5.0p18:

* ``add_to_event_context`` from ``cmk/base/events.py``, which turns notification
  parameters into the ``NOTIFY_PARAMETER_*`` variables a script receives.
* ``retrieve_from_passwordstore`` and ``get_password_from_env_or_context`` from
  ``cmk/notification_plugins/utils.py``.

The form spec classes only record their arguments.
"""

from __future__ import annotations

import sys
import types
from typing import Any

# The password store of the fake site: id -> secret
PASSWORD_STORE: dict[str, str] = {}


def add_to_event_context(context: dict[str, str], prefix: str, param: object) -> None:
    if isinstance(param, list | tuple):
        if all(isinstance(p, str) for p in param):
            suffix, separator = ("S", " ") if isinstance(param, list) else ("", "\t")
            add_to_event_context(context, prefix + suffix, separator.join(param))
        for nr, value in enumerate(param, start=1):
            add_to_event_context(context, f"{prefix}_{nr}", value)
    elif isinstance(param, dict):
        for key, value in param.items():
            add_to_event_context(context, f"{prefix}_{key.upper()}", value)
    elif isinstance(param, str | int | float):
        context[prefix] = str(param)
    elif param is None:
        context[prefix] = ""
    else:
        context[prefix] = repr(param)


def _extract(password_id: str) -> str | None:
    return PASSWORD_STORE.get(password_id)


def retrieve_from_passwordstore(parameter: str | list[str]) -> str:
    if isinstance(parameter, list):
        if "explicit_password" in parameter:
            value: str | None = parameter[-1]
        else:
            value = _extract(parameter[-2])
            if value is None:
                sys.exit(2)
    else:
        values = parameter.split()
        if len(values) != 2:
            raise ValueError(f"unexpected parameter {parameter!r}")
        if values[0] == "store":
            value = _extract(values[1])
            if value is None:
                sys.exit(2)
        else:
            value = values[1]
    assert value is not None
    return value


def get_password_from_env_or_context(key: str, context: dict[str, str]) -> str:
    return retrieve_from_passwordstore([context[k] for k in context if k.startswith(key)])


class _Recorder:
    """Stores constructor arguments, like the frozen dataclasses of the API."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.args = args
        self.kwargs = kwargs
        for name, value in kwargs.items():
            setattr(self, name, value)


class _Text(str):
    def __mod__(self, other: object) -> _Text:
        return _Text(str.__mod__(self, other))


def install() -> None:
    """Register the stub modules in sys.modules."""
    cmk = types.ModuleType("cmk")
    rulesets = types.ModuleType("cmk.rulesets")
    v1 = types.ModuleType("cmk.rulesets.v1")
    form_specs = types.ModuleType("cmk.rulesets.v1.form_specs")
    rule_specs = types.ModuleType("cmk.rulesets.v1.rule_specs")
    validators = types.ModuleType("cmk.rulesets.v1.form_specs.validators")

    v1.Help = v1.Message = v1.Title = _Text
    for name in ("DictElement", "Dictionary", "Password", "String"):
        setattr(form_specs, name, type(name, (_Recorder,), {}))
    for name in ("LengthInRange", "MatchRegex"):
        setattr(validators, name, type(name, (_Recorder,), {}))
    form_specs.validators = validators
    rule_specs.NotificationParameters = type("NotificationParameters", (_Recorder,), {})
    rule_specs.Topic = types.SimpleNamespace(NOTIFICATIONS="notifications")

    notification_plugins = types.ModuleType("cmk.notification_plugins")
    utils = types.ModuleType("cmk.notification_plugins.utils")
    utils.retrieve_from_passwordstore = retrieve_from_passwordstore
    utils.get_password_from_env_or_context = get_password_from_env_or_context
    notification_plugins.utils = utils

    requests = types.ModuleType("requests")
    requests.exceptions = types.SimpleNamespace(RequestException=Exception)

    cmk.rulesets = rulesets
    cmk.notification_plugins = notification_plugins
    rulesets.v1 = v1
    v1.form_specs = form_specs
    v1.rule_specs = rule_specs
    sys.modules.update(
        {
            "cmk": cmk,
            "cmk.rulesets": rulesets,
            "cmk.rulesets.v1": v1,
            "cmk.rulesets.v1.form_specs": form_specs,
            "cmk.rulesets.v1.form_specs.validators": validators,
            "cmk.rulesets.v1.rule_specs": rule_specs,
            "cmk.notification_plugins": notification_plugins,
            "cmk.notification_plugins.utils": utils,
            "requests": requests,
        }
    )
