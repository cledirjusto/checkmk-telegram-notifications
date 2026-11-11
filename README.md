# Telegram notifications – Checkmk extension

[![License: GPL v2](https://img.shields.io/badge/License-GPL_v2-blue.svg)](LICENSE)
![Checkmk 2.5+](https://img.shields.io/badge/Checkmk-2.5%2B-green)

Send Checkmk host and service notifications to a Telegram chat or group.

This is a fork of **Telegram_Notifications 2.1.0 by Mario Casero**, itself based
on [telegram-notify](https://exchange.checkmk.com/p/telegram-notify) from the
Checkmk Exchange. The message format and the notification script are his. This
fork changes how the bot token is configured and moves the GUI part to the
Checkmk 2.5 plug-in API:

| | 2.1.0 (upstream) | 2.2.0 (this fork) |
| --- | --- | --- |
| Bot token in the GUI | plain text field, visible to everyone who can open the rule | standard Checkmk password field, masked |
| Password store | not supported | the token can be picked from *Setup → General → Passwords* |
| Notification parameters | legacy GUI plug-in in `web/plugins/wato` | rulesets API (`cmk.rulesets.v1`), `cmk_addons/plugins/telegram/rulesets` |
| *Analyze configuration* on 2.5 | CRIT: "Legacy GUI extension in 'wato' uses an API (legacy) which was marked as deprecated in Checkmk 2.4.0 and is removed in Checkmk 2.5.0" | OK |

Parameters saved with 2.1.0 keep working after the upgrade. Nothing has to be
re-entered.

Verified on a **Checkmk 2.5.0p18 Pro** site: the parameter pages open with
values saved by 2.1.0 and by this version, the script reads the token in every
stored format, and *Analyze configuration* reports no legacy GUI extension.

## Requirements

* Checkmk 2.5.0 or newer.
* A Telegram bot token from [@BotFather](https://t.me/BotFather).
* The ID of the chat or group, with the bot added to the group.
* Outbound HTTPS from the site to `api.telegram.org`.

## Installation

1. Download the latest `Telegram_Notifications-<version>.mkp` from the
   [releases page](../../releases), or build it yourself (see below).
2. Install it on the central site:

   ```
   OMD[mysite]:~$ mkp add Telegram_Notifications-2.2.0.mkp
   OMD[mysite]:~$ mkp enable Telegram_Notifications 2.2.0
   OMD[mysite]:~$ omd restart apache
   ```

   or use *Setup → Maintenance → Extension packages*.

3. In a distributed setup, activate changes with *Replicate extensions* enabled
   for the remote sites, or install the package on each site.

### Upgrading from Mario Casero's 2.1.0

The package keeps the name `Telegram_Notifications`, so it installs as a newer
version of the same package. After enabling 2.2.0 the old version stays
installed as *Enabled (inactive)*. Once a test notification works, remove it:

```
OMD[mysite]:~$ mkp remove Telegram_Notifications 2.1.0
```

Until then, `mkp enable Telegram_Notifications 2.1.0` rolls back.

## Configuration

1. Store the bot token in *Setup → General → Passwords*, for example with the
   ID `telegram_bot`.
2. Open *Setup → Notifications → Parameters for notification methods →
   Telegram* and create a parameter. Under *Bot Token* choose the password
   store entry, and enter the chat or group ID.
3. Use the parameter in a notification rule, then send a *Test notification*.
   `~/var/log/notify.log` shows `200: OK` when Telegram accepted the message.

A token typed in directly (*Explicit*) is also accepted. It is masked in the
GUI but stored in clear text in `notification_parameter.mk`. The password store
keeps it encrypted.

### Finding the chat or group ID

Add the bot to the group, send a message there (in groups the bot only sees
commands and mentions, e.g. `/start@your_bot`), then ask the Bot API:

```
curl -s "https://api.telegram.org/bot<TOKEN>/getUpdates" | python3 -m json.tool | grep -A3 '"chat"'
```

The `"id"` inside `"chat"` is the value to use. Group IDs are negative,
supergroup IDs start with `-100`.

## How the token is read

The notification script receives the parameter as `NOTIFY_PARAMETER_BOT_KEY*`
variables and accepts every format a version of this package stored:

| Stored by | Format | Read as |
| --- | --- | --- |
| 2.1.0 | `"<token>"` | the token |
| 2.2.0 | `("cmk_postprocessed", "explicit_password", (<id>, "<token>"))` | the token |
| 2.2.0 | `("cmk_postprocessed", "stored_password", ("<password id>", ""))` | looked up in the password store |

Opening and saving a parameter in the GUI converts older formats to the 2.2.0
one. Keys left behind by other Telegram packages (`bot_token`, `chat_id`) are
dropped on save.

## Development

Nothing in this section ships to a site: the `.mkp` contains only the files
under `local/`.

```
python3 -m venv .venv && .venv/bin/pip install pytest ruff
.venv/bin/python -m pytest -q
.venv/bin/ruff check . && .venv/bin/ruff format --check .
python3 scripts/build_mkp.py --update-manifest   # -> dist/Telegram_Notifications-<version>.mkp
```

The tests import the ruleset and the notification script against
`tests/cmk_stub.py`, which copies from Checkmk 2.5.0p18 the functions that turn
parameters into environment variables and read the password store.

To release, bump `version` in `package.manifest` and `pyproject.toml`, update
`CHANGELOG.md` and tag `v<version>`. The GitHub workflow builds the `.mkp` and
attaches it to the release.

## License and credits

GNU General Public License v2 (GPL-2.0-or-later), see [LICENSE](LICENSE).

* Original package: Mario Casero (Dragosiz), Telegram_Notifications 2.1.0.
* Based on [telegram-notify](https://exchange.checkmk.com/p/telegram-notify) from the Checkmk Exchange.

Telegram is a trademark of Telegram FZ-LLC. This project is not affiliated with
or endorsed by Telegram or Checkmk GmbH.
