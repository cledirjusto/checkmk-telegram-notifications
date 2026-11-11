#!/usr/bin/env python3
# Telegram notifications for Checkmk
# License: GNU General Public License v2 - see LICENSE
"""Tests for the repository layout, the manifest and the .mkp builder."""

from __future__ import annotations

import ast
import json
import sys
import tarfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import build_mkp  # noqa: E402

SCRIPT = REPO_ROOT / "local/share/check_mk/notifications/telegram"


@pytest.fixture(scope="module")
def manifest() -> dict:
    return build_mkp.load_manifest(REPO_ROOT / "package.manifest")


def test_manifest_matches_the_local_tree(manifest):
    problems = build_mkp.check_manifest(manifest, build_mkp.scan_parts(REPO_ROOT))
    assert problems == [], "run 'python3 scripts/build_mkp.py --update-manifest'"


def test_versions_agree(manifest):
    assert build_mkp.check_versions(REPO_ROOT, manifest) == []


def test_manifest_has_the_fields_checkmk_requires(manifest):
    for key in (
        "name",
        "title",
        "version",
        "version.min_required",
        "version.packaged",
        "version.usable_until",
        "author",
        "description",
        "download_url",
        "files",
    ):
        assert key in manifest, key
    # same name as the upstream package, so installing this one replaces it
    assert manifest["name"] == "Telegram_Notifications"


def test_no_legacy_gui_extension_is_packaged(manifest):
    """Files below web/ are what Analyze configuration reports as legacy in 2.5."""
    assert "web" not in manifest["files"]


@pytest.mark.parametrize(
    "path",
    sorted(
        p.relative_to(REPO_ROOT)
        for p in [*(REPO_ROOT / "local").rglob("*.py"), SCRIPT]
        if "__pycache__" not in p.parts
    ),
    ids=str,
)
def test_plugin_files_are_valid_python(path):
    """Syntax check without importing - the cmk modules only exist in a site."""
    ast.parse((REPO_ROOT / path).read_text(encoding="utf-8"), filename=str(path))


@pytest.mark.parametrize(
    "path", sorted((REPO_ROOT / "local/lib/python3/cmk/gui/plugins/views").iterdir()), ids=str
)
def test_views_are_python_literals(path):
    ast.literal_eval(path.read_text(encoding="utf-8"))


def test_the_notification_script_is_executable():
    assert SCRIPT.stat().st_mode & 0o100


def test_build_produces_an_installable_mkp(tmp_path, manifest):
    target = build_mkp.build_mkp(REPO_ROOT, manifest, tmp_path)
    assert target.is_file()

    with tarfile.open(target, "r:gz") as tar:
        names = tar.getnames()
        assert {"info", "info.json"} <= set(names)
        packaged = json.loads(tar.extractfile("info.json").read())
        assert packaged == manifest

        members = {}
        for part in manifest["files"]:
            assert f"{part}.tar" in names
            with tarfile.open(fileobj=tar.extractfile(f"{part}.tar"), mode="r:") as inner:
                members[part] = {m.name: m for m in inner.getmembers()}
            assert set(members[part]) == set(manifest["files"][part])

    assert members["notifications"]["telegram"].mode == 0o755
    # tar entries are owned by root so unpacking in a site is predictable
    for part_members in members.values():
        assert all(m.uid == 0 and m.gid == 0 for m in part_members.values())


def test_the_info_member_is_readable_by_checkmk(tmp_path, manifest):
    """Checkmk reads the 'info' member as a Python literal."""
    target = build_mkp.build_mkp(REPO_ROOT, manifest, tmp_path)
    with tarfile.open(target, "r:gz") as tar:
        info = ast.literal_eval(tar.extractfile("info").read().decode("utf-8"))
    assert info == manifest
