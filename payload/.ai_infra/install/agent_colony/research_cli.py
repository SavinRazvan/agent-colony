"""
File: research_cli.py
Path: .ai_infra/install/agent_colony/research_cli.py
Role: Procedural CLI for research pack init, fetch (local/GitHub), and INDEX validate.
Used By:
 - .ai_infra/install/agent_colony/cli.py
 - .cursor/agents/researcher.md
Depends On:
 - .ai_infra/templates/research-corpus/
Notes:
 - Writes only under _research_results/; no product tree mutation.
 - GitHub fetch uses shallow clone into cache/<slug>/; unit tests cover path: only.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_FAIL = 1

_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")
_DEFAULT_LENSES = [
    "architecture",
    "cli",
    "agents",
    "skills",
    "tests",
    "decisions",
    "patterns",
]
_DEFAULT_CONSUMERS = ["implementer", "integrator"]


def _fail(cmd: str, code: int, reason: str) -> int:
    print(f"research {cmd}: FAIL — CODE={code} · {reason}", file=sys.stderr)
    return code


def _ok(cmd: str, detail: str) -> int:
    print(f"research {cmd}: PASS — {detail}")
    return EXIT_OK


def research_templates_dir(root: Path) -> Path:
    return root / ".ai_infra" / "templates" / "research-corpus"


def corpus_root(root: Path) -> Path:
    return root / "_research_results"


def pack_dir(root: Path, slug: str) -> Path:
    return corpus_root(root) / "sources" / slug


def cache_dir(root: Path, slug: str) -> Path:
    return corpus_root(root) / "cache" / slug


def validate_slug(slug: str) -> str | None:
    s = (slug or "").strip()
    if not s or not _SLUG_RE.match(s):
        return "slug must match ^[a-z0-9][a-z0-9._-]{0,63}$"
    return None


def _read_template(tpl_dir: Path, name: str) -> str:
    path = tpl_dir / name
    if not path.is_file():
        raise FileNotFoundError(f"missing template {path}")
    return path.read_text(encoding="utf-8")


def _render(template: str, values: dict[str, str]) -> str:
    out = template
    for key, val in values.items():
        out = out.replace("{{" + key + "}}", val)
    # Leave unknown placeholders as-is for agent fill.
    return out.rstrip() + "\n"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


_GITHUB_HTTPS_RE = re.compile(
    r"^https?://(?:www\.)?github\.com/"
    r"(?P<owner>[^/\s]+)/(?P<repo>[^/\s#?]+?)"
    r"(?:\.git)?(?:/(?:tree|blob)/(?P<ref>[^/\s#?]+)(?:/.*)?)?(?:[?#].*)?$",
    re.IGNORECASE,
)


def _parse_github_locator(rest: str) -> tuple[str, str | None]:
    """Parse owner/repo[@ref] → (owner/repo, ref)."""
    text = rest.strip()
    ref = None
    if "@" in text:
        text, ref = text.rsplit("@", 1)
        ref = ref.strip() or None
    parts = text.split("/")
    if len(parts) < 2 or not parts[0] or not parts[1]:
        raise ValueError("github source must be owner/repo[@ref]")
    return f"{parts[0]}/{parts[1]}", ref


def _parse_source(raw: str) -> tuple[str, str, str | None]:
    """Return (kind, locator, ref) where kind is path|github.

    Accepts:
    - path:/abs/or/rel
    - github:owner/repo[@ref]
    - https://github.com/owner/repo[.git][/tree/ref/...]
    - bare local path
    """
    text = (raw or "").strip()
    if not text:
        raise ValueError("empty --source")
    if text.startswith("path:"):
        return "path", text[5:].strip(), None
    if text.startswith("github:"):
        locator, ref = _parse_github_locator(text[7:])
        return "github", locator, ref
    m = _GITHUB_HTTPS_RE.match(text)
    if m:
        repo = m.group("repo")
        if repo.endswith(".git"):
            repo = repo[: -len(".git")]
        locator = f"{m.group('owner')}/{repo}"
        return "github", locator, m.group("ref")
    # Bare path convenience
    return "path", text, None


def _git_sha(repo: Path) -> str | None:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    return (proc.stdout or "").strip() or None


def _write_index_stub(
    pack: Path,
    *,
    slug: str,
    mode: str,
    source: str,
    question: str,
    lenses: list[str],
    status: str,
    commit_sha: str | None = None,
    resolved_path: str | None = None,
    consumers: list[str] | None = None,
    rounds_max: int = 6,
) -> None:
    payload: dict[str, Any] = {
        "schema_version": "1",
        "slug": slug,
        "mode": mode,
        "source": source,
        "question": question,
        "lenses": lenses,
        "rounds_completed": 0,
        "rounds_max": rounds_max if rounds_max > 0 else 6,
        "commit_sha": commit_sha,
        "resolved_path": resolved_path,
        "findings": [],
        "curated_count": 0,
        "consumers": consumers or list(_DEFAULT_CONSUMERS),
        "agent_brief": "AGENT_BRIEF.md",
        "status": status,
    }
    (pack / "INDEX.json").write_text(
        json.dumps(payload, indent=2) + "\n", encoding="utf-8"
    )


def structural_validate_index(data: Any) -> list[str]:
    """Validate INDEX.json against the shipped schema without requiring jsonschema."""
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["INDEX.json root must be an object"]
    required = (
        "schema_version",
        "slug",
        "mode",
        "source",
        "question",
        "lenses",
        "findings",
        "curated_count",
        "status",
    )
    for key in required:
        if key not in data:
            errors.append(f"missing required field: {key}")
    if data.get("schema_version") != "1":
        errors.append("schema_version must be \"1\"")
    slug = data.get("slug")
    if isinstance(slug, str):
        err = validate_slug(slug)
        if err:
            errors.append(err)
    elif "slug" in data:
        errors.append("slug must be a string")
    if data.get("mode") not in ("external", "self"):
        errors.append("mode must be external|self")
    if data.get("status") not in ("init", "fetched", "in_progress", "complete", "blocked"):
        errors.append("status must be init|fetched|in_progress|complete|blocked")
    lenses = data.get("lenses")
    if not isinstance(lenses, list) or not lenses or not all(isinstance(x, str) and x for x in lenses):
        errors.append("lenses must be a non-empty string array")
    findings = data.get("findings")
    if not isinstance(findings, list):
        errors.append("findings must be an array")
    else:
        for i, row in enumerate(findings):
            if not isinstance(row, dict):
                errors.append(f"findings[{i}] must be an object")
                continue
            for k in ("id", "lens", "path", "summary"):
                if not isinstance(row.get(k), str) or not row.get(k):
                    errors.append(f"findings[{i}].{k} must be a non-empty string")
            conf = row.get("confidence")
            if conf is not None and conf not in ("high", "medium", "low"):
                errors.append(f"findings[{i}].confidence must be high|medium|low")
    curated = data.get("curated_count")
    if not isinstance(curated, int) or curated < 0:
        errors.append("curated_count must be a non-negative integer")
    rounds = data.get("rounds_completed")
    if rounds is not None and (not isinstance(rounds, int) or rounds < 0 or rounds > 6):
        errors.append("rounds_completed must be 0..6")
    rounds_max = data.get("rounds_max")
    if rounds_max is not None:
        if not isinstance(rounds_max, int) or rounds_max < 1 or rounds_max > 6:
            errors.append("rounds_max must be 1..6")
        elif isinstance(rounds, int) and rounds > rounds_max:
            errors.append(f"rounds_completed ({rounds}) exceeds rounds_max ({rounds_max})")
    return errors


def cmd_research_init(args: argparse.Namespace) -> int:
    root = Path(args.directory).resolve()
    slug = (args.slug or "").strip()
    err = validate_slug(slug)
    if err:
        return _fail("init", EXIT_USAGE, err)

    tpl_dir = research_templates_dir(root)
    if not tpl_dir.is_dir():
        return _fail("init", EXIT_USAGE, f"missing templates at {tpl_dir}")

    pack = pack_dir(root, slug)
    if pack.exists() and not args.force:
        return _fail("init", EXIT_USAGE, f"pack exists: {pack} (use --force)")

    source = (args.source or "path:(TBD)").strip()
    question = (args.question or "(TBD)").strip()
    mode = (args.mode or "external").strip()
    if mode not in ("external", "self"):
        return _fail("init", EXIT_USAGE, "mode must be external|self")
    lenses = [x.strip() for x in (args.lenses or ",".join(_DEFAULT_LENSES)).split(",") if x.strip()]
    consumers = [
        x.strip()
        for x in (args.consumers or ",".join(_DEFAULT_CONSUMERS)).split(",")
        if x.strip()
    ]
    notes = (args.notes or "").strip()

    if args.brief:
        brief_src = Path(args.brief)
        if not brief_src.is_file():
            return _fail("init", EXIT_USAGE, f"brief not found: {brief_src}")
        brief_body = brief_src.read_text(encoding="utf-8")
    else:
        brief_body = _render(
            _read_template(tpl_dir, "BRIEF.template.md"),
            {
                "source": source,
                "question": question,
                "lenses": json.dumps(lenses),
                "rounds_max": str(args.rounds_max or 6),
                "consumers": json.dumps(consumers),
                "slug": slug,
                "mode": mode,
                "notes": notes or "(none)",
            },
        )

    pack.mkdir(parents=True, exist_ok=True)
    (pack / "findings").mkdir(exist_ok=True)
    (pack / "rounds").mkdir(exist_ok=True)

    corpus = corpus_root(root)
    corpus.mkdir(parents=True, exist_ok=True)
    boundaries = corpus / "RESEARCH_BOUNDARIES.md"
    if not boundaries.is_file():
        shutil.copy2(tpl_dir / "RESEARCH_BOUNDARIES.md", boundaries)

    (pack / "BRIEF.md").write_text(brief_body, encoding="utf-8")
    for name, dest in (
        ("MAP.template.md", "MAP.md"),
        ("CURATED.template.md", "CURATED.md"),
        ("AGENT_BRIEF.template.md", "AGENT_BRIEF.md"),
    ):
        body = _render(
            _read_template(tpl_dir, name),
            {"slug": slug, "question": question},
        )
        (pack / dest).write_text(body, encoding="utf-8")

    lens_tpl = _read_template(tpl_dir / "findings", "_LENS.template.md")
    for lens in lenses:
        (pack / "findings" / f"{lens}.md").write_text(
            _render(lens_tpl, {"lens": lens}),
            encoding="utf-8",
        )

    _write_index_stub(
        pack,
        slug=slug,
        mode=mode,
        source=source,
        question=question,
        lenses=lenses,
        status="init",
        consumers=consumers,
        rounds_max=int(args.rounds_max or 6),
    )
    return _ok("init", f"pack={pack}")


def _clone_github(locator: str, ref: str | None, dest: Path) -> tuple[bool, str]:
    """Shallow-clone owner/repo into dest. Prefer `gh` (private auth), else git HTTPS.

    Returns (ok, detail). Private repos work when `gh auth` / git credentials can
    access the repo the same way a local `gh repo clone` / `git clone` would.
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    git_flags = ["--depth", "1"]
    if ref:
        git_flags.extend(["--branch", ref])

    gh_cmd = ["gh", "repo", "clone", locator, str(dest), "--", *git_flags]
    try:
        proc = subprocess.run(gh_cmd, capture_output=True, text=True, timeout=300, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        proc = None
        gh_err = str(exc)
    else:
        if proc.returncode == 0 and dest.is_dir():
            return True, "gh repo clone"
        gh_err = (proc.stderr or proc.stdout or "").strip()[:400]

    if dest.exists():
        shutil.rmtree(dest, ignore_errors=True)

    url = f"https://github.com/{locator}.git"
    git_cmd = ["git", "clone", *git_flags, url, str(dest)]
    try:
        proc2 = subprocess.run(git_cmd, capture_output=True, text=True, timeout=300, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, f"gh failed ({gh_err}); git clone failed: {exc}"
    if proc2.returncode != 0:
        detail = (proc2.stderr or proc2.stdout or "").strip()[:400]
        return False, f"gh failed ({gh_err}); git clone failed: {detail}"
    return True, "git clone"


def cmd_research_fetch(args: argparse.Namespace) -> int:
    root = Path(args.directory).resolve()
    slug = (args.slug or "").strip()
    err = validate_slug(slug)
    if err:
        return _fail("fetch", EXIT_USAGE, err)

    pack = pack_dir(root, slug)
    if not pack.is_dir():
        return _fail("fetch", EXIT_USAGE, f"pack missing — run research init first: {pack}")

    # Anti-loop: do not re-fetch a pinned pack unless --force
    if (pack / "SOURCE.md").is_file() and not args.force:
        return _fail(
            "fetch",
            EXIT_USAGE,
            f"SOURCE.md already exists for {slug} (use --force to re-fetch)",
        )

    try:
        kind, locator, ref = _parse_source(args.source)
    except ValueError as exc:
        return _fail("fetch", EXIT_USAGE, str(exc))

    tpl_dir = research_templates_dir(root)
    resolved: Path
    commit_sha: str | None = None
    source_label = args.source.strip()

    if kind == "path":
        resolved = Path(locator)
        if not resolved.is_absolute():
            resolved = (root / resolved).resolve()
        else:
            resolved = resolved.resolve()
        if not resolved.exists():
            return _fail("fetch", EXIT_FAIL, f"path not found: {resolved}")
        commit_sha = _git_sha(resolved) if (resolved / ".git").exists() or resolved.is_dir() else None
        if commit_sha is None and resolved.is_dir():
            commit_sha = _git_sha(resolved)
    else:
        cache = cache_dir(root, slug)
        if cache.exists():
            if args.force:
                shutil.rmtree(cache)
            else:
                return _fail("fetch", EXIT_USAGE, f"cache exists: {cache} (use --force)")
        ok, how = _clone_github(locator, ref, cache)
        if not ok:
            return _fail("fetch", EXIT_FAIL, how)
        resolved = cache
        commit_sha = _git_sha(cache)
        source_label = f"github:{locator}" + (f"@{ref}" if ref else "")
        print(f"research fetch: clone via {how}", file=sys.stderr)

    fetched_at = _utc_now()
    source_md = _render(
        _read_template(tpl_dir, "SOURCE.template.md"),
        {
            "source": source_label,
            "resolved_path": str(resolved),
            "ref": ref or "(default)",
            "commit_sha": commit_sha or "(none)",
            "fetched_at": fetched_at,
            "kind": kind,
        },
    )
    (pack / "SOURCE.md").write_text(source_md, encoding="utf-8")

    index_path = pack / "INDEX.json"
    data: dict[str, Any]
    if index_path.is_file():
        try:
            data = json.loads(index_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {}
    else:
        data = {}
    data.update(
        {
            "schema_version": data.get("schema_version") or "1",
            "slug": slug,
            "mode": data.get("mode") or "external",
            "source": source_label,
            "question": data.get("question") or "(TBD)",
            "lenses": data.get("lenses") or list(_DEFAULT_LENSES),
            "rounds_completed": data.get("rounds_completed") or 0,
            "rounds_max": data.get("rounds_max") if isinstance(data.get("rounds_max"), int) else 6,
            "commit_sha": commit_sha,
            "resolved_path": str(resolved),
            "findings": data.get("findings") if isinstance(data.get("findings"), list) else [],
            "curated_count": data.get("curated_count") if isinstance(data.get("curated_count"), int) else 0,
            "consumers": data.get("consumers") or list(_DEFAULT_CONSUMERS),
            "agent_brief": data.get("agent_brief") or "AGENT_BRIEF.md",
            "status": "fetched",
        }
    )
    index_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return _ok("fetch", f"resolved={resolved} sha={commit_sha or 'none'}")


def cmd_research_validate(args: argparse.Namespace) -> int:
    root = Path(args.directory).resolve()
    slug = (args.slug or "").strip()
    err = validate_slug(slug)
    if err:
        return _fail("validate", EXIT_USAGE, err)

    pack = pack_dir(root, slug)
    if not pack.is_dir():
        return _fail("validate", EXIT_FAIL, f"pack missing: {pack}")

    missing = [name for name in ("BRIEF.md", "SOURCE.md", "INDEX.json") if not (pack / name).is_file()]
    if missing:
        return _fail("validate", EXIT_FAIL, f"missing required files: {', '.join(missing)}")

    try:
        data = json.loads((pack / "INDEX.json").read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return _fail("validate", EXIT_FAIL, f"INDEX.json invalid JSON: {exc}")

    errors = structural_validate_index(data)
    schema_path = research_templates_dir(root) / "INDEX.schema.json"
    if schema_path.is_file():
        try:
            import jsonschema  # type: ignore

            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            jsonschema.validate(instance=data, schema=schema)
        except ImportError:
            pass
        except Exception as exc:  # noqa: BLE001 — surface schema errors to user
            errors.append(f"jsonschema: {exc}")

    # Soft completeness for complete status
    status = data.get("status") if isinstance(data, dict) else None
    if status == "complete":
        for name in ("MAP.md", "CURATED.md", "AGENT_BRIEF.md"):
            if not (pack / name).is_file():
                errors.append(f"status=complete requires {name}")

    if errors:
        for e in errors:
            print(f" - {e}", file=sys.stderr)
        return _fail("validate", EXIT_FAIL, f"{len(errors)} error(s)")
    note = ""
    if status == "complete":
        note = " · pack closed (do not deepen further without --force redo)"
    return _ok("validate", f"slug={slug} status={status}{note}")


def register_research_subparser(sub: argparse._SubParsersAction) -> None:
    research = sub.add_parser(
        "research",
        help="Research corpus pack init / fetch / validate",
    )
    research_sub = research.add_subparsers(dest="research_command", required=True)

    init_cmd = research_sub.add_parser("init", help="Scaffold sources/<slug>/ from templates")
    init_cmd.add_argument("--directory", type=Path, default=".")
    init_cmd.add_argument("--slug", required=True)
    init_cmd.add_argument("--source", default="path:(TBD)")
    init_cmd.add_argument("--question", default="(TBD)")
    init_cmd.add_argument("--lenses", default=",".join(_DEFAULT_LENSES))
    init_cmd.add_argument("--consumers", default=",".join(_DEFAULT_CONSUMERS))
    init_cmd.add_argument("--mode", default="external", choices=("external", "self"))
    init_cmd.add_argument("--rounds-max", type=int, default=6)
    init_cmd.add_argument("--notes", default="")
    init_cmd.add_argument("--brief", type=Path, default=None, help="Copy BRIEF.md from path")
    init_cmd.add_argument("--force", action="store_true")
    init_cmd.set_defaults(func=cmd_research_init)

    fetch_cmd = research_sub.add_parser(
        "fetch",
        help="Pin source: local path or shallow GitHub clone into cache/<slug>/",
    )
    fetch_cmd.add_argument("--directory", type=Path, default=".")
    fetch_cmd.add_argument("--slug", required=True)
    fetch_cmd.add_argument(
        "--source",
        required=True,
        help=(
            "path:/abs/or/rel | github:owner/repo[@ref] | "
            "https://github.com/owner/repo[/tree/ref] | bare path"
        ),
    )
    fetch_cmd.add_argument("--force", action="store_true", help="Replace existing cache/")
    fetch_cmd.set_defaults(func=cmd_research_fetch)

    validate_cmd = research_sub.add_parser("validate", help="Validate pack BRIEF/SOURCE/INDEX")
    validate_cmd.add_argument("--directory", type=Path, default=".")
    validate_cmd.add_argument("--slug", required=True)
    validate_cmd.set_defaults(func=cmd_research_validate)
