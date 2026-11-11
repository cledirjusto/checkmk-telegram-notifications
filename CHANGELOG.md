# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[semantic versioning](https://semver.org/).

## [Unreleased]

## [2.2.0] - 2026-11-11

First release of this fork of Telegram_Notifications 2.1.0 by Mario Casero.

### Changed

- The *Bot Token* is a standard Checkmk password field. The GUI masks it, and it
  can be taken from the password store, where it is stored encrypted. In 2.1.0
  it was a plain text field shown to everyone who could open the parameter.
- The notification parameters are registered with the rulesets API
  (`NotificationParameters` from `cmk.rulesets.v1`) instead of the legacy GUI
  plug-in `web/plugins/wato/telegram.py`. On Checkmk 2.5 *Analyze configuration*
  reported that file as CRIT ("Legacy GUI extension in 'wato' uses an API
  (legacy) which was marked as deprecated in Checkmk 2.4.0 and is removed in
  Checkmk 2.5.0").
- Requires Checkmk 2.5.0. 2.1.0 also loaded on 2.4.

### Fixed

- Parameters migrated from older Telegram packages carried `bot_token` and
  `chat_id` next to `bot_key` and `group_id`. The extra keys are dropped when the
  parameter is saved.

### Compatibility

- Parameters saved by 2.1.0 work without changes. The script reads the old
  plain-text token and the GUI converts it to the new format on save.
- The package keeps the name `Telegram_Notifications`, so it upgrades the
  upstream 2.1.0 in place.

## [2.1.0] - upstream

Telegram_Notifications 2.1.0 by Mario Casero, packaged on Checkmk 2.5.0p17.
