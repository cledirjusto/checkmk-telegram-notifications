#!/usr/bin/env python3
# Telegram notifications for Checkmk
# License: GNU General Public License v2 - see LICENSE
"""Shared test helpers."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import sys
import types
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RULESET = REPO_ROOT / "local/lib/python3/cmk_addons/plugins/telegram/rulesets/telegram.py"
SCRIPT = REPO_ROOT / "local/share/check_mk/notifications/telegram"


def _load(name: str, path: Path) -> types.ModuleType:
    import cmk_stub

    cmk_stub.install()
    # the notification script has no .py suffix, so name the loader explicitly
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    loader.exec_module(module)
    return module


def load_ruleset() -> types.ModuleType:
    return _load("telegram_ruleset", RULESET)


def load_script() -> types.ModuleType:
    return _load("telegram_script", SCRIPT)
