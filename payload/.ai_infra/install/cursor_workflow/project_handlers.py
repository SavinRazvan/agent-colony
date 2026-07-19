"""
File: project_handlers.py
Path: .ai_infra/install/cursor_workflow/project_handlers.py
Role: Heavy project CLI command implementations (claim/handoff/PR/doctor/outbox).
Used By:
 - .ai_infra/install/cursor_workflow/project_cli.py (thin cmd_* delegates)
Depends On:
 - .ai_infra/install/cursor_workflow/project_cli.py (late import facade for monkeypatches)
 - .ai_infra/install/cursor_workflow/project_outbox.py (local import inside outbox cmds)
Notes:
 - Call through `pc.*` so tests can monkeypatch the project_cli facade.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

def run_claim(args: argparse.Namespace) -> int:
    """Pattern A: set in_progress + optional assignee + attributed Notes."""
    import project_cli as pc
    root = Path(args.directory).resolve()
    ssot, code = pc._load_enabled_ssot(root, 'claim')
    if ssot is None:
        return code
    item_id, id_code = pc.resolve_item_id_arg(root, args, 'claim')
    if item_id is None:
        return id_code
    agent = (getattr(args, 'agent', None) or '').strip()
    if not agent:
        return pc.fail('claim', pc.EXIT_USAGE, '--agent required')
    try:
        user = pc.resolve_human_github_user(root)
    except Exception as exc:
        return pc.fail('claim', pc.EXIT_USAGE, str(exc))
    if not user:
        return pc.fail('claim', pc.EXIT_USAGE, 'owner.github_user missing')
    conventions = ssot.get('conventions') or {}
    claim_payload: dict[str, Any] = {'to': 'in_progress', 'text': getattr(args, 'text', None) or 'claimed'}
    fields_block = ssot.get('fields') if isinstance(ssot.get('fields'), dict) else {}
    start_cfg = fields_block.get('start_date') if isinstance(fields_block, dict) else None
    if conventions.get('set_start_date_on_claim', True) and isinstance(start_cfg, dict) and start_cfg.get('field_id'):
        claim_payload['start_date'] = pc.utc_today_iso()
    items, err = pc.fetch_project_items(ssot, limit=args.limit)
    if err:
        queued = pc._try_queue_rate_limit(root, ssot, cmd='claim', err_detail=err, op='claim', item_id=item_id, agent=agent, payload=claim_payload)
        if queued is not None:
            return queued
        return pc.fail('claim', pc.EXIT_GH, err)
    item = pc.find_item_by_id(items, item_id)
    if item is None:
        return pc.fail('claim', pc.EXIT_NOT_FOUND, f'item not found: {item_id}')
    before = pc._normalize_status(str(item.get('status') or ''))
    if conventions.get('one_in_progress_per_assignee', True):
        conflicts = pc.in_progress_conflicts_for_user(items, user_handle=user, exclude_id=item_id)
        if conflicts:
            ids = ', '.join((str(c.get('id')) for c in conflicts[:5]))
            return pc.fail('claim', pc.EXIT_VALIDATION, f'one_in_progress_per_assignee: already In progress for {user}: {ids}')
    ok, detail = pc.set_item_status(ssot, item_id, 'in_progress')
    if not ok:
        if 'unknown status' in detail:
            return pc.fail('claim', pc.EXIT_USAGE, detail)
        queued = pc._try_queue_rate_limit(root, ssot, cmd='claim', err_detail=detail, op='claim', item_id=item_id, agent=agent, payload=claim_payload)
        if queued is not None:
            return queued
        return pc.fail('claim', pc.EXIT_GH, detail)
    claim_mode = str(conventions.get('claim') or 'set_assignee')
    if claim_mode == 'set_assignee':
        a_ok, a_detail = pc.set_item_assignee(ssot, item_id, user.lstrip('@'))
        if not a_ok:
            print(f'claim: WARN — assignee skipped: {a_detail}', file=sys.stderr)
        else:
            print(f'claim: assignee=@{a_detail.lstrip('@')}')
    d_ok, d_detail, d_applied = pc.ensure_start_date_if_starting(ssot, item_id, item=item)
    if not d_ok:
        print(f'claim: WARN — start_date skipped: {d_detail}', file=sys.stderr)
    elif d_applied:
        print(f'claim: start_date={d_detail}')
    elif d_detail.startswith('skipped:'):
        if 'field_id missing' in d_detail:
            print(f'claim: WARN — start_date skipped: {d_detail}', file=sys.stderr)
    else:
        # already had a date
        pass
    note = getattr(args, 'text', None) or 'claimed'
    n_ok, n_detail, n_code = pc.append_notes_helper(root, ssot, item_id, agent=agent, text=note, limit=args.limit)
    if not n_ok:
        if n_code == pc.EXIT_GH:
            queued = pc._try_queue_rate_limit(root, ssot, cmd='claim', err_detail=n_detail, op='append-notes', item_id=item_id, agent=agent, payload={'text': note})
            if queued is not None:
                print('claim: status set; Notes QUEUED due to rate-limit', file=sys.stderr)
                return queued
        return pc.fail('claim', n_code, f'status set but Notes failed: {n_detail}')
    pc.save_last_item_id(root, item_id, title=pc._item_title(item), action='claim')
    attr = pc.format_agent_attribution(root, agent)
    print(f'claim: {item_id} → in_progress ({n_detail})')
    print(f'item_id={item_id} · {attr} · Status={before or '?'}→in_progress')
    print(f'next: python3 -m cursor_workflow project handoff --last --agent {agent} --next <agent> --to in_review')
    return pc.EXIT_OK

def run_handoff(args: argparse.Namespace) -> int:
    """Pattern A: attributed Notes with next=@user/agent + optional status."""
    import project_cli as pc
    root = Path(args.directory).resolve()
    ssot, code = pc._load_enabled_ssot(root, 'handoff')
    if ssot is None:
        return code
    item_id, id_code = pc.resolve_item_id_arg(root, args, 'handoff')
    if item_id is None:
        return id_code
    agent = (getattr(args, 'agent', None) or '').strip()
    next_agent = (getattr(args, 'next', None) or '').strip().lstrip('@')
    if not agent:
        return pc.fail('handoff', pc.EXIT_USAGE, '--agent required')
    if not next_agent:
        return pc.fail('handoff', pc.EXIT_USAGE, '--next required (agent name)')
    try:
        next_attr = pc.format_agent_attribution(root, next_agent)
        self_attr = pc.format_agent_attribution(root, agent)
    except ValueError as exc:
        return pc.fail('handoff', pc.EXIT_USAGE, str(exc))
    items, err = pc.fetch_project_items(ssot, limit=args.limit)
    if err:
        queued = pc._try_queue_rate_limit(root, ssot, cmd='handoff', err_detail=err, op='handoff', item_id=item_id, agent=agent, payload={'next': next_agent, 'to': (getattr(args, 'to', None) or '').strip(), 'note': (getattr(args, 'text', None) or '').strip()})
        if queued is not None:
            return queued
        return pc.fail('handoff', pc.EXIT_GH, err)
    item = pc.find_item_by_id(items, item_id)
    if item is None:
        return pc.fail('handoff', pc.EXIT_NOT_FOUND, f'item not found: {item_id}')
    before = pc._normalize_status(str(item.get('status') or ''))
    extra = (getattr(args, 'text', None) or '').strip()
    note_core = f'next={next_attr}'
    if extra:
        note_core = f'{extra} · {note_core}'
    status_to = (getattr(args, 'to', None) or '').strip()
    if status_to:
        ok, detail = pc.set_item_status(ssot, item_id, status_to)
        if not ok:
            if 'unknown' in detail.lower():
                return pc.fail('handoff', pc.EXIT_USAGE, detail)
            queued = pc._try_queue_rate_limit(root, ssot, cmd='handoff', err_detail=detail, op='handoff', item_id=item_id, agent=agent, payload={'next': next_agent, 'to': status_to, 'note': extra})
            if queued is not None:
                return queued
            return pc.fail('handoff', pc.EXIT_GH, detail)
        if pc._normalize_status(status_to) == 'in_progress':
            d_ok, d_detail, d_applied = pc.ensure_start_date_if_starting(ssot, item_id, item=item)
            if not d_ok:
                print(f'handoff: WARN — start_date skipped: {d_detail}', file=sys.stderr)
            elif d_applied:
                print(f'handoff: start_date={d_detail}')
            elif 'field_id missing' in d_detail:
                print(f'handoff: WARN — start_date skipped: {d_detail}', file=sys.stderr)
    n_ok, n_detail, n_code = pc.append_notes_helper(root, ssot, item_id, agent=agent, text=note_core, limit=args.limit)
    if not n_ok:
        if n_code == pc.EXIT_GH:
            queued = pc._try_queue_rate_limit(root, ssot, cmd='handoff', err_detail=n_detail, op='handoff', item_id=item_id, agent=agent, payload={'next': next_agent, 'to': status_to, 'note': extra})
            if queued is not None:
                return queued
        return pc.fail('handoff', n_code, n_detail)
    pc.save_last_item_id(root, item_id, title=pc._item_title(item), action='handoff')
    after = status_to or before or '?'
    print(f'handoff: {item_id} — {n_detail}')
    print(f'item_id={item_id} · {self_attr} · Status={before or '?'}→{after} · next={next_attr}')
    return pc.EXIT_OK

def run_mention_pr(args: argparse.Namespace) -> int:
    """
    Append Notes with canonical PR URL + print find-by-pr candidates.
    When Draft + promote_to_issue_on_pr: promote first (FAIL on promote error).
    Does not write LINKED_PULL_REQUESTS (derived on GitHub for Issue↔PR links).
    """
    import project_cli as pc
    root = Path(args.directory).resolve()
    ssot, code = pc._load_enabled_ssot(root, 'mention-pr')
    if ssot is None:
        return code
    item_id, id_code = pc.resolve_item_id_arg(root, args, 'mention-pr')
    if item_id is None:
        return id_code
    agent = (getattr(args, 'agent', None) or '').strip()
    if not agent:
        return pc.fail('mention-pr', pc.EXIT_USAGE, '--agent required')
    pr_ref = (getattr(args, 'pr', None) or '').strip()
    if not pr_ref:
        return pc.fail('mention-pr', pc.EXIT_USAGE, '--pr required')
    repo = str(ssot.get('default_repo') or '').strip()
    view_args = ['pr', 'view', pr_ref, '--json', 'url,number,title']
    if repo:
        view_args.extend(['--repo', repo])
    proc = pc.run_gh(view_args)
    if proc.returncode != 0:
        return pc.fail('mention-pr', pc.EXIT_GH, (proc.stderr or proc.stdout or 'gh pr view failed').strip())
    try:
        pdata = json.loads(proc.stdout or '{}')
    except json.JSONDecodeError:
        return pc.fail('mention-pr', pc.EXIT_GH, 'invalid gh pr view JSON')
    pr_url = str(pdata.get('url') or '').strip()
    pr_num = pdata.get('number')
    if not pr_url:
        return pc.fail('mention-pr', pc.EXIT_GH, 'pr view missing url')
    kind, _cid, _meta, kerr = pc.resolve_item_content(ssot, item_id)
    conventions = ssot.get('conventions') or {}
    promote_on = conventions.get('promote_to_issue_on_pr', True)
    if kind == 'draft' or (kerr and 'Draft' in str(kerr)):
        if promote_on:
            p_ok, p_detail, p_meta = pc.promote_draft_item_to_issue(ssot, item_id, repo=repo)
            if not p_ok:
                queued = pc._try_queue_rate_limit(root, ssot, cmd='mention-pr', err_detail=p_detail, op='promote-to-issue', item_id=item_id, agent=agent, payload={'repo': repo, 'text': f'PR {pr_num}: {pr_url}'})
                if queued is not None:
                    return queued
                return pc.fail('mention-pr', pc.EXIT_GH, f'promote_to_issue_on_pr failed: {p_detail}')
            print(f'mention-pr: promoted {item_id} → Issue #{p_meta.get('issue_number')}', file=sys.stderr)
        else:
            print(f'mention-pr: WARN — card looks DraftIssue; GitHub Linked pull requests fills for Issue-backed items. Run: project promote-to-issue --last (promote_to_issue_on_pr={promote_on}).', file=sys.stderr)
    note = f'PR {pr_num}: {pr_url}'
    ok, detail, err_code = pc.append_notes_helper(root, ssot, item_id, agent=agent, text=note, limit=args.limit)
    if not ok:
        if err_code == pc.EXIT_GH:
            queued = pc._try_queue_rate_limit(root, ssot, cmd='mention-pr', err_detail=detail, op='append-notes', item_id=item_id, agent=agent, payload={'text': note})
            if queued is not None:
                return queued
        return pc.fail('mention-pr', err_code, detail)
    print(f'mention-pr: {item_id} — Notes {note}')
    items, err = pc.fetch_project_items(ssot, limit=args.limit)
    if not err:
        matches = pc.find_items_mentioning_pr(items, pr_number=str(pr_num or ''), pr_url=pr_url)
        if matches:
            print('mention-pr: find-by-pr candidates: ' + ', '.join((str(m.get('id')) for m in matches[:5])))
        else:
            print('mention-pr: find-by-pr — no other matches yet (Notes just written)')
    return pc.EXIT_OK

def run_promote_to_issue(args: argparse.Namespace) -> int:
    """Convert DraftIssue project item to Issue (same PVTI_); Notes + optional assignee."""
    import project_cli as pc
    root = Path(args.directory).resolve()
    ssot, code = pc._load_enabled_ssot(root, 'promote-to-issue')
    if ssot is None:
        return code
    item_id, id_code = pc.resolve_item_id_arg(root, args, 'promote-to-issue')
    if item_id is None:
        return id_code
    agent = (getattr(args, 'agent', None) or '').strip()
    if not agent:
        return pc.fail('promote-to-issue', pc.EXIT_USAGE, '--agent required')
    repo = (getattr(args, 'repo', None) or '').strip() or str(ssot.get('default_repo') or '').strip()
    ok, detail, meta = pc.promote_draft_item_to_issue(ssot, item_id, repo=repo)
    if not ok:
        queued = pc._try_queue_rate_limit(root, ssot, cmd='promote-to-issue', err_detail=detail, op='promote-to-issue', item_id=item_id, agent=agent, payload={'repo': repo})
        if queued is not None:
            return queued
        return pc.fail('promote-to-issue', pc.EXIT_GH, detail)
    issue_n = meta.get('issue_number')
    url = str(meta.get('url') or '')
    out_id = str(meta.get('item_id') or item_id)
    if meta.get('noop'):
        print(f'promote-to-issue: {out_id} already Issue #{issue_n}')
    else:
        print(f'promote-to-issue: {out_id} → Issue #{issue_n} ({url})')
    try:
        user = pc.resolve_human_github_user(root)
    except Exception:
        user = ''
    if user:
        a_ok, a_detail = pc.set_item_assignee(ssot, out_id, user.lstrip('@'))
        if not a_ok:
            print(f'promote-to-issue: WARN — assignee skipped: {a_detail}', file=sys.stderr)
        else:
            print(f'promote-to-issue: assignee=@{a_detail.lstrip('@')}')
    note = f'promoted to Issue #{issue_n}: {url}' if url else f'promoted to Issue #{issue_n}'
    n_ok, n_detail, n_code = pc.append_notes_helper(root, ssot, out_id, agent=agent, text=note, limit=args.limit)
    if not n_ok:
        if n_code == pc.EXIT_GH:
            queued = pc._try_queue_rate_limit(root, ssot, cmd='promote-to-issue', err_detail=n_detail, op='append-notes', item_id=out_id, agent=agent, payload={'text': note})
            if queued is not None:
                print('promote-to-issue: Issue converted; Notes QUEUED due to rate-limit', file=sys.stderr)
                return queued
        return pc.fail('promote-to-issue', n_code, f'promoted but Notes failed: {n_detail}')
    pc.save_last_item_id(root, out_id, title='', action='promote-to-issue')
    attr = pc.format_agent_attribution(root, agent)
    print(f'promote-to-issue: Notes {n_detail}')
    print(f'item_id={out_id} · {attr} · Issue=#{issue_n}')
    print(f'next: python3 -m cursor_workflow project mention-pr --pr <n> --last --agent {agent}')
    return pc.EXIT_OK

def run_doctor(args: argparse.Namespace) -> int:
    import project_cli as pc
    root = Path(args.directory).resolve()
    ssot, errs = pc.load_project_ssot(root)
    if errs or ssot is None:
        return pc.fail('doctor', pc.EXIT_USAGE, errs[0] if errs else 'project_ssot missing')
    enabled_errs = pc.require_enabled(ssot)
    if enabled_errs:
        return pc.fail('doctor', pc.EXIT_USAGE, enabled_errs[0])
    try:
        pc.status_field_id(ssot)
        pc.resolve_status_option_id(ssot, 'ready')
    except KeyError as exc:
        return pc.fail('doctor', pc.EXIT_USAGE, str(exc))
    user = pc.resolve_human_github_user(root)
    if not user:
        return pc.fail('doctor', pc.EXIT_USAGE, 'owner.github_user missing')
    tpl_dir = pc.project_templates_dir(root)
    for name in pc._TEMPLATE_NAMES:
        path = tpl_dir / f'card-body-{name}.md'
        if not path.is_file():
            return pc.fail('doctor', pc.EXIT_USAGE, f'missing template {path}')
    import project_outbox as _outbox
    cfg_pre = _outbox.load_outbox_config(ssot)
    rl_pre = _outbox.graphql_rate_limit()
    skip_live = False
    if not rl_pre.get('error'):
        try:
            rem_pre = int(rl_pre.get('remaining')) if rl_pre.get('remaining') is not None else 9999
        except (TypeError, ValueError):
            rem_pre = 9999
        if rem_pre < int(cfg_pre['min_graphql_remaining']):
            skip_live = True
            print('doctor: WARN — skipping live gh project item-list (low GraphQL quota)', file=sys.stderr)
    if not skip_live:
        proc = pc.run_gh(['project', 'item-list', str(ssot['number']), '--owner', str(ssot['owner']), '--format', 'json', '--limit', '1'])
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout or 'gh project not readable').strip()
            if _outbox.is_rate_limit_error(detail):
                print('doctor: WARN — gh project item-list rate-limited; config still ok', file=sys.stderr)
            else:
                return pc.fail('doctor', pc.EXIT_GH, detail)
    print('doctor: ok')
    print(f'project: {ssot.get('name')} ({ssot.get('url')})')
    print(f'human: {user}')
    print(f'templates: {tpl_dir}')
    fields = ssot.get('fields') if isinstance(ssot.get('fields'), dict) else {}
    for key in ('start_date', 'estimate', 'size'):
        block = fields.get(key) if isinstance(fields, dict) else None
        if isinstance(block, dict) and block.get('field_id'):
            print(f'tier1.{key}: {block['field_id']}')
        else:
            print(f'doctor: WARN — fields.{key}.field_id missing (Tier-1)', file=sys.stderr)
    conventions = ssot.get('conventions') if isinstance(ssot.get('conventions'), dict) else {}
    print(f"set_start_date_on_claim: {conventions.get('set_start_date_on_claim', True)}")
    print('doctor: note — Size/Estimate use points table in project-board-ssot skill (not hours)')
    print(f"item_kind_default: {conventions.get('item_kind_default', 'issue')}")
    print(f'promote_to_issue_on_pr: {conventions.get('promote_to_issue_on_pr', True)}')
    default_repo = str(ssot.get('default_repo') or '').strip()
    if default_repo:
        print(f'default_repo: {default_repo}')
    else:
        print('doctor: WARN — project_ssot.default_repo missing (required for promote-to-issue / item_kind_default=issue)', file=sys.stderr)
    print('doctor: note — convertProjectV2DraftIssueItemToIssue may fail on fine-grained PATs; use classic PAT with project+repo scopes if promote fails')
    cfg = cfg_pre
    path = _outbox.outbox_path(root, cfg)
    counts = _outbox.count_outbox(path)
    rl = rl_pre
    print(f'outbox: enabled={cfg['enabled']} pending={counts['pending']} path={path}')
    if rl.get('error'):
        print(f'doctor: WARN — graphql rate_limit: {rl['error']}', file=sys.stderr)
    else:
        rem = rl.get('remaining')
        try:
            rem_i = int(rem) if rem is not None else -1
        except (TypeError, ValueError):
            rem_i = -1
        reset = _outbox.format_reset_iso(rl.get('reset_epoch'))
        print(f'graphql: remaining={rem}/{rl.get('limit')} reset={reset}')
        if rem_i >= 0 and rem_i < int(cfg['min_graphql_remaining']):
            print(f'doctor: WARN — GraphQL remaining {rem_i} < min_graphql_remaining {cfg['min_graphql_remaining']}; prefer outbox queue; flush after {reset}', file=sys.stderr)
    if counts['pending'] > 0:
        print(f'doctor: WARN — {counts['pending']} pending outbox ops; run: python3 -m cursor_workflow project outbox flush', file=sys.stderr)
    return pc.EXIT_OK

def run_queue(args: argparse.Namespace) -> int:
    """Explicit enqueue (no live board write)."""
    import project_cli as pc
    import project_outbox as _outbox
    root = Path(args.directory).resolve()
    ssot, code = pc._load_enabled_ssot(root, 'queue')
    if ssot is None:
        return code
    item_id, id_code = pc.resolve_item_id_arg(root, args, 'queue')
    if item_id is None:
        return id_code
    agent = (getattr(args, 'agent', None) or '').strip()
    if not agent:
        return pc.fail('queue', pc.EXIT_USAGE, '--agent required')
    op = (getattr(args, 'op', None) or '').strip()
    payload: dict[str, Any] = {}
    if op == 'append-notes':
        text = (getattr(args, 'text', None) or '').strip()
        if not text:
            return pc.fail('queue', pc.EXIT_USAGE, '--text required for append-notes')
        payload = {'text': text}
    elif op == 'set-status':
        to = (getattr(args, 'to', None) or '').strip()
        if not to:
            return pc.fail('queue', pc.EXIT_USAGE, '--to required for set-status')
        payload = {'to': to}
    elif op == 'handoff':
        nxt = (getattr(args, 'next', None) or '').strip()
        if not nxt:
            return pc.fail('queue', pc.EXIT_USAGE, '--next required for handoff')
        payload = {'next': nxt, 'to': (getattr(args, 'to', None) or '').strip(), 'note': (getattr(args, 'text', None) or '').strip()}
    elif op == 'claim':
        payload = {'to': (getattr(args, 'to', None) or 'in_progress').strip() or 'in_progress', 'text': (getattr(args, 'text', None) or 'claimed').strip()}
    elif op == 'set-assignee':
        login = (getattr(args, 'login', None) or '').strip()
        if not login:
            try:
                login = pc.resolve_human_github_user(root)
            except Exception as exc:
                return pc.fail('queue', pc.EXIT_USAGE, str(exc))
        payload = {'login': login.lstrip('@')}
    else:
        return pc.fail('queue', pc.EXIT_USAGE, 'op must be append-notes|set-status|handoff|claim|set-assignee')
    entry, err = _outbox.enqueue_op(root, ssot, op=op, item_id=item_id, agent=agent, payload=payload)
    if entry is None:
        return pc.fail('queue', pc.EXIT_VALIDATION, err)
    print(_outbox.queued_message('queue', entry))
    return pc.EXIT_QUEUED

def run_outbox_status(args: argparse.Namespace) -> int:
    import project_cli as pc
    import project_outbox as _outbox
    root = Path(args.directory).resolve()
    ssot, code = pc._load_enabled_ssot(root, 'outbox')
    if ssot is None:
        return code
    cfg = _outbox.load_outbox_config(ssot)
    path = _outbox.outbox_path(root, cfg)
    counts = _outbox.count_outbox(path)
    rl = _outbox.graphql_rate_limit()
    print(f'outbox.enabled: {cfg['enabled']}')
    print(f'outbox.path: {path}')
    print(f'counts: pending={counts['pending']} failed={counts['failed']} done={counts['done']} total={counts['total']}')
    if rl.get('error'):
        print(f'graphql: error — {rl['error']}')
    else:
        reset = _outbox.format_reset_iso(rl.get('reset_epoch'))
        print(f'graphql: remaining={rl.get('remaining')}/{rl.get('limit')} reset={reset} min_flush={cfg['min_graphql_remaining']}')
    return pc.EXIT_OK

def run_outbox_flush(args: argparse.Namespace) -> int:
    import project_cli as pc
    import project_outbox as _outbox
    root = Path(args.directory).resolve()
    ssot, code = pc._load_enabled_ssot(root, 'outbox')
    if ssot is None:
        return code
    max_ops = getattr(args, 'max', None)
    code_out, summary = _outbox.flush_outbox(root, ssot, max_ops=max_ops, limit=getattr(args, 'limit', 100) or 100)
    if code_out != pc.EXIT_OK:
        return pc.fail('outbox flush', code_out, summary)
    print(f'outbox flush: {summary}')
    return pc.EXIT_OK
