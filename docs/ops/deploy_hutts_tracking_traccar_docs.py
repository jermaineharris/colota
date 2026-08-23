#!/usr/bin/env python3
"""Deploy Hutts Tracking + Traccar runbook to MCP gateway + Wiki.js + Cursor rule.

Run on utility-hetzner-server-one:
  cd ~/fleet-topic-pipeline-docs-deploy && python3 deploy_hutts_tracking_traccar_docs.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from deploy_mcp_common import (  # noqa: E402
    CURSOR,
    MCP_CURSOR,
    PATHS,
    REFERENCE,
    SCRIPT_DIR,
    install_mcp_markdown,
    load_wiki_key,
    restart_mcp_gateway,
    sudo_cp,
    sudo_write,
    upsert_wiki,
    verify_sync_manifest_paths,
)

WIKI_PATH = "infra/hutts-tracking-traccar"
WIKI_TITLE = "Hutts Tracking + Traccar"
WIKI_DESC = (
    "Private GPS: Hutts Tracking Android app (Colota fork) and Traccar on "
    "hetzner-fleet-garage-one (Tailscale-only OsmAnd)."
)
RULE_DEST = Path("/opt/mcp-gateway/cursor/hutts-tracking-traccar.mdc")

CAPABILITY = '''
        CapabilityEntry(
            key="hutts_tracking_traccar",
            title="Hutts Tracking + Traccar (garage-one)",
            purpose=(
                "Private GPS stack: Hutts Tracking Android app "
                "(com.huttsmedia.huttstracking, Colota fork) posting OsmAnd to "
                "Traccar on hetzner-fleet-garage-one over Tailscale."
            ),
            safety=(
                "Tailscale-only binds; no public WAN ports. Do not put Traccar on "
                "utility-one. Never commit admin password; read "
                "/root/.config/hutts-tracking-traccar.admin.pass on garage-one. "
                "AGPLv3 fork — keep LICENSE/attribution. Prefer Balanced preset "
                "(Instant 0m distance floods jitter points)."
            ),
            best_first_endpoints=[
                "/cursor/runbook/hutts-tracking-traccar",
                "/cursor/rules/hutts-tracking-traccar",
            ],
            recommended_workflow=[
                CapabilityWorkflowStep(
                    step=1,
                    title="Read Hutts Tracking + Traccar runbook",
                    endpoint="/cursor/runbook/hutts-tracking-traccar",
                    why="Hosts, ports, phone settings, ops commands.",
                ),
                CapabilityWorkflowStep(
                    step=2,
                    title="Sync Cursor rule",
                    endpoint="/cursor/rules/hutts-tracking-traccar",
                    why="Save to ~/.cursor/rules/hutts-tracking-traccar.mdc",
                ),
            ],
            mutating_endpoints=[],
            preview_endpoints=[
                "/cursor/runbook/hutts-tracking-traccar",
                "/cursor/rules/hutts-tracking-traccar",
                "/reference/capabilities",
            ],
            cursor_tools=[],
            examples=[
                CapabilityExample(
                    title="Read Hutts Tracking + Traccar runbook",
                    method="GET",
                    path="/cursor/runbook/hutts-tracking-traccar",
                    body=None,
                ),
            ],
        ),
'''


def patch_paths(text: str) -> str:
    if "hutts_tracking_traccar_runbook_path" in text:
        return text
    insert = '''

def hutts_tracking_traccar_runbook_path() -> Path:
    return _env_or_default_path(
        "MCP_GATEWAY_HUTTS_TRACKING_TRACCAR_RUNBOOK_PATH",
        PROJECT_ROOT / "scripts" / "cursor" / "hutts-tracking-traccar-mcp.md",
    )


def hutts_tracking_traccar_rule_path() -> Path:
    return _env_or_default_path(
        "MCP_GATEWAY_HUTTS_TRACKING_TRACCAR_RULE_PATH",
        PROJECT_ROOT / "cursor" / "hutts-tracking-traccar.mdc",
    )

'''
    for anchor in (
        "def fleet_ops_mobile_runbook_path() -> Path:",
        "def fleet_analytics_mobile_runbook_path() -> Path:",
        "def beszel_monitoring_runbook_path() -> Path:",
    ):
        if anchor in text:
            return text.replace(anchor, insert + anchor, 1)
    raise SystemExit("paths.py: no insert anchor for hutts_tracking_traccar")


def patch_cursor_imports(text: str) -> str:
    if "    hutts_tracking_traccar_runbook_path,\n" in text:
        return text
    for old in (
        "    fleet_ops_mobile_runbook_path,\n",
        "    fleet_analytics_mobile_runbook_path,\n",
        "    beszel_monitoring_runbook_path,\n",
    ):
        if old in text:
            return text.replace(
                old,
                old
                + "    hutts_tracking_traccar_runbook_path,\n"
                + "    hutts_tracking_traccar_rule_path,\n",
                1,
            )
    raise SystemExit("cursor.py imports: no anchor")


def patch_cursor_sync_pairs(text: str) -> str:
    if '("/cursor/runbook/hutts-tracking-traccar"' in text:
        return text
    for old in (
        '        ("/cursor/runbook/fleet-ops-mobile", fleet_ops_mobile_runbook_path()),\n',
        '        ("/cursor/runbook/beszel-monitoring", beszel_monitoring_runbook_path()),\n',
    ):
        if old in text:
            return text.replace(
                old,
                old
                + '        ("/cursor/runbook/hutts-tracking-traccar", hutts_tracking_traccar_runbook_path()),\n'
                + '        ("/cursor/rules/hutts-tracking-traccar", hutts_tracking_traccar_rule_path()),\n',
                1,
            )
    raise SystemExit("cursor.py sync pairs: no anchor")


def patch_cursor_routes(text: str) -> str:
    if '@router.get("/cursor/runbook/hutts-tracking-traccar")' in text:
        return text
    block = '''

@router.get("/cursor/runbook/hutts-tracking-traccar")
def get_hutts_tracking_traccar_runbook(_: Annotated[None, Depends(require_gateway_auth)]) -> Response:
    """Hutts Tracking Android GPS + Traccar on garage-one."""
    return _serve_markdown(
        hutts_tracking_traccar_runbook_path(),
        missing_error="hutts_tracking_traccar_runbook_missing",
        missing_hint="Add scripts/cursor/hutts-tracking-traccar-mcp.md.",
        read_error="hutts_tracking_traccar_runbook_read_failed",
    )


@router.get("/cursor/rules/hutts-tracking-traccar")
def get_hutts_tracking_traccar_rule(_: Annotated[None, Depends(require_gateway_auth)]) -> Response:
    """Cursor rule: Hutts Tracking + Traccar."""
    return _serve_markdown(
        hutts_tracking_traccar_rule_path(),
        missing_error="hutts_tracking_traccar_rule_missing",
        missing_hint="Add /opt/mcp-gateway/cursor/hutts-tracking-traccar.mdc.",
        read_error="hutts_tracking_traccar_rule_read_failed",
    )

'''
    for anchor in (
        '@router.get("/cursor/runbook/fleet-ops-mobile")',
        '@router.get("/cursor/runbook/beszel-monitoring")',
    ):
        if anchor in text:
            return text.replace(anchor, block + anchor, 1)
    raise SystemExit("cursor.py routes: no anchor")


def patch_reference(text: str) -> str:
    if 'key="hutts_tracking_traccar"' in text:
        return text
    for anchor in (
        'key="fleet_ops_mobile"',
        'key="beszel_monitoring"',
        'key="fleet_analytics_mobile"',
    ):
        idx = text.find(anchor)
        if idx < 0:
            continue
        entry_start = text.rfind("CapabilityEntry(", 0, idx)
        if entry_start < 0:
            continue
        return text[:entry_start] + CAPABILITY + "\n" + text[entry_start:]
    raise SystemExit("reference.py: no CapabilityEntry anchor")


def main() -> int:
    runbook = SCRIPT_DIR / "hutts-tracking-traccar-mcp.md"
    rule = SCRIPT_DIR / "hutts-tracking-traccar.mdc"
    if not runbook.is_file():
        raise SystemExit(f"Missing {runbook}")
    if not rule.is_file():
        raise SystemExit(f"Missing {rule}")

    install_mcp_markdown(runbook, MCP_CURSOR / "hutts-tracking-traccar-mcp.md")
    sudo_cp(rule, RULE_DEST)

    paths_text = PATHS.read_text(encoding="utf-8")
    sudo_write(PATHS, patch_paths(paths_text))

    cursor_text = CURSOR.read_text(encoding="utf-8")
    cursor_text = patch_cursor_imports(cursor_text)
    cursor_text = patch_cursor_sync_pairs(cursor_text)
    cursor_text = patch_cursor_routes(cursor_text)
    sudo_write(CURSOR, cursor_text)

    ref_text = REFERENCE.read_text(encoding="utf-8")
    sudo_write(REFERENCE, patch_reference(ref_text))

    key = load_wiki_key()
    upsert_wiki(
        key,
        WIKI_PATH,
        WIKI_TITLE,
        WIKI_DESC,
        runbook.read_text(encoding="utf-8"),
    )

    restart_mcp_gateway()
    verify_sync_manifest_paths(
        (
            "/cursor/runbook/hutts-tracking-traccar",
            "/cursor/rules/hutts-tracking-traccar",
        )
    )
    print("OK: hutts-tracking-traccar MCP + wiki + rule")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
