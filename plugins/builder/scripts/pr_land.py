"""Land one ticket's PR in the background: wait for its CI, merge on green, move the board card.
Deterministic, no LLM. The build loop starts it with run_in_background and goes on to the next
ticket; the exit wakes the loop.

  python3 -I pr_land.py --pr <url> --project-dir projects/<p> --ticket E0-T4 \
          --out projects/.runtime/builder/<p>/<ticket>/land.md [--timeout-min 45]

1. Waits until checks are reported (up to 5 min), then `gh pr checks --watch` until all finish.
2. All green (or skipped): `gh pr merge --merge` (merge commit, so stacked branches stay clean),
   then board_set.py --status done. Writes `status: MERGED` and the merge sha. Exit 0.
3. Any failed check: writes `status: CI_FAILED` and, per failed job, the tail of
   `gh run view --log-failed`. The card stays In review. Exit 1. Nothing is merged.
4. Not mergeable (conflict) or timeout: `status: CONFLICT` / `status: CI_TIMEOUT`. Exit 2.
The out file starts with `sha:` (the PR head) and `status:` like every builder report.
"""
import argparse, json, os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))


def sh(*args, check=False):
    r = subprocess.run(list(args), capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f'{" ".join(args)}: {(r.stderr or r.stdout)[:400]}')
    return r


def pr_json(url, fields):
    return json.loads(sh('gh', 'pr', 'view', url, '--json', fields, check=True).stdout)


def write(out, sha, status, body):
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, 'w') as f:
        f.write(f'sha: {sha}\nstatus: {status}\n\n{body.rstrip()}\n')
    print(f'land: {status} ({out})')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--pr', required=True)
    ap.add_argument('--project-dir', required=True)
    ap.add_argument('--ticket', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--timeout-min', type=int, default=45)
    a = ap.parse_args()

    info = pr_json(a.pr, 'headRefOid,state,mergeable')
    sha = info['headRefOid']
    if info['state'] == 'MERGED':
        write(a.out, sha, 'MERGED', f'PR {a.pr} was already merged.')
        sh('python3', '-I', os.path.join(HERE, 'board_set.py'), '--project-dir', a.project_dir, '--ticket', a.ticket, '--status', 'done')
        return 0

    deadline = time.time() + a.timeout_min * 60
    # 1. wait for checks to be reported
    while True:
        r = sh('gh', 'pr', 'checks', a.pr, '--json', 'name,state,bucket,link')
        checks = json.loads(r.stdout) if r.returncode in (0, 1, 8) and r.stdout.strip().startswith('[') else []
        if checks or time.time() > deadline - (a.timeout_min - 5) * 60:
            break
        time.sleep(20)
    # 2. wait for them to finish
    while time.time() < deadline:
        checks = json.loads(sh('gh', 'pr', 'checks', a.pr, '--json', 'name,state,bucket,link').stdout or '[]')
        if checks and all(c['bucket'] != 'pending' for c in checks):
            break
        time.sleep(30)
    else:
        write(a.out, sha, 'CI_TIMEOUT', f'Checks still pending after {a.timeout_min} min:\n' +
              '\n'.join(f'- {c["name"]}: {c["state"]}' for c in checks))
        return 2

    failed = [c for c in checks if c['bucket'] in ('fail', 'cancel')]
    summary = '\n'.join(f'- {c["name"]}: {c["state"]}' for c in checks) or '- (no checks reported)'
    if failed:
        logs = []
        for c in failed:
            run_id = next((p for p in c.get('link', '').split('/') if p.isdigit()), None)
            tail = ''
            if run_id:
                tail = '\n'.join(sh('gh', 'run', 'view', run_id, '--log-failed').stdout.splitlines()[-60:])
            logs.append(f'### {c["name"]} ({c["state"]})\n{c.get("link", "")}\n```\n{tail}\n```')
        write(a.out, sha, 'CI_FAILED', f'PR {a.pr}\n\n## Checks\n{summary}\n\n## Failed job logs (tail)\n' + '\n\n'.join(logs))
        return 1

    # 3. merge
    info = pr_json(a.pr, 'headRefOid,mergeable')
    if info['headRefOid'] != sha:
        write(a.out, info['headRefOid'], 'CI_TIMEOUT', 'The PR head moved while CI ran; start pr_land again for the new head.')
        return 2
    if info['mergeable'] == 'CONFLICTING':
        write(a.out, sha, 'CONFLICT', f'PR {a.pr} has merge conflicts with its base. CI:\n{summary}')
        return 2
    m = sh('gh', 'pr', 'merge', a.pr, '--merge')
    if m.returncode != 0:
        write(a.out, sha, 'CONFLICT', f'gh pr merge failed: {(m.stderr or m.stdout)[:400]}\nCI:\n{summary}')
        return 2
    merge_sha = (pr_json(a.pr, 'mergeCommit').get('mergeCommit') or {}).get('oid', '?')
    board = sh('python3', '-I', os.path.join(HERE, 'board_set.py'), '--project-dir', a.project_dir, '--ticket', a.ticket, '--status', 'done').stdout.strip()
    write(a.out, sha, 'MERGED', f'PR {a.pr} merged as {merge_sha}.\n{board}\n\n## Checks\n{summary}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
