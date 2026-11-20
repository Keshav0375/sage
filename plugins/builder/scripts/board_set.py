"""Set one ticket's Status on the project's GitHub Project board. Deterministic, rerun-safe, no LLM.

  python3 -I board_set.py --project-dir projects/<p> --ticket E0-T4 --status review

Status keys follow the ticket frontmatter: todo, in_progress, review, done, blocked
(board options: Backlog, In progress, In review, Done, Backlog).
The board is epic/README.md github.project_id; the item is found through the ticket's issue.
Prints one line: `board: <ticket> -> <option>` or `board: skipped (<reason>)`. Exit 0 unless a
GraphQL call fails after retries (exit 1), so a board outage never stops a build.
"""
import argparse, glob, json, os, re, subprocess, sys, time

STATUS = {'todo': 'Backlog', 'in_progress': 'In progress', 'review': 'In review', 'done': 'Done', 'blocked': 'Backlog'}


def gql(query, **vars):
    args = ['gh', 'api', 'graphql', '-f', f'query={query}']
    for k, v in vars.items():
        args += ['-F' if isinstance(v, int) else '-f', f'{k}={v}']
    msg = ''
    for attempt in range(5):
        r = subprocess.run(args, capture_output=True, text=True)
        if r.returncode == 0:
            out = json.loads(r.stdout)
            if not out.get('errors'):
                return out['data']
            msg = json.dumps(out['errors'])[:300]
        else:
            msg = (r.stderr or r.stdout)[:300]
        if any(x in msg.lower() for x in ('rate limit', 'secondary', 'timeout', 'something went wrong', '502', '503')):
            time.sleep(15 * (attempt + 1))
            continue
        break
    print(f'board: error ({msg})')
    sys.exit(1)


def frontmatter(path):
    lines = open(path).read().split('\n')
    end = lines.index('---', 1)
    f = {}
    for l in lines[1:end]:
        m = re.match(r'^([A-Za-z_][\w-]*):\s?(.*)$', l)
        if m:
            try:
                f[m.group(1)] = json.loads(m.group(2)) if m.group(2).strip() else None
            except Exception:
                f[m.group(1)] = m.group(2)
    return f


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--project-dir', required=True)
    ap.add_argument('--ticket', required=True)
    ap.add_argument('--status', required=True, choices=sorted(STATUS))
    a = ap.parse_args()

    github = frontmatter(os.path.join(a.project_dir, 'epic', 'README.md')).get('github') or {}
    pid = github.get('project_id')
    if not pid:
        print('board: skipped (no github.project_id in epic/README.md)')
        return
    files = glob.glob(os.path.join(a.project_dir, 'epic', '*', 'tickets', f'{a.ticket}-*.md'))
    if not files:
        print(f'board: skipped (no ticket file for {a.ticket})')
        return
    issue = frontmatter(files[0]).get('issue') or {}
    if not isinstance(issue, dict) or not issue.get('repo') or not issue.get('number'):
        print(f'board: skipped ({a.ticket} has no published issue)')
        return
    owner, name = issue['repo'].split('/', 1)

    items = gql('query($o:String!,$n:String!,$i:Int!){repository(owner:$o,name:$n){issue(number:$i){projectItems(first:20){nodes{id project{id}}}}}}',
                o=owner, n=name, i=int(issue['number']))['repository']['issue']['projectItems']['nodes']
    item = next((x['id'] for x in items if x['project']['id'] == pid), None)
    if not item:
        item = gql('mutation($p:ID!,$c:ID!){addProjectV2ItemById(input:{projectId:$p,contentId:$c}){item{id}}}', p=pid,
                   c=gql('query($o:String!,$n:String!,$i:Int!){repository(owner:$o,name:$n){issue(number:$i){id}}}',
                         o=owner, n=name, i=int(issue['number']))['repository']['issue']['id'])['addProjectV2ItemById']['item']['id']

    fields = gql('query($id:ID!){node(id:$id){... on ProjectV2{field(name:"Status"){... on ProjectV2SingleSelectField{id options{id name}}}}}}', id=pid)['node']['field']
    want = STATUS[a.status]
    opt = next((o['id'] for o in fields['options'] if o['name'].lower() == want.lower()), None)
    if not opt:
        print(f'board: skipped (no Status option "{want}")')
        return
    gql('mutation($p:ID!,$i:ID!,$f:ID!,$o:String!){updateProjectV2ItemFieldValue(input:{projectId:$p,itemId:$i,fieldId:$f,value:{singleSelectOptionId:$o}}){projectV2Item{id}}}',
        p=pid, i=item, f=fields['id'], o=opt)
    print(f'board: {a.ticket} -> {want}')


if __name__ == '__main__':
    main()
