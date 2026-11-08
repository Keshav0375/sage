"""Set up a project's GitHub Project board like the sage template (views, workflows, fields) and fill
it from the epic and ticket files. Deterministic and rerun-safe; no LLM.

  python3 -I project_board.py --project-dir projects/<p> --owner <login> --template <number>
          [--title <title>] [--close-old] [--dry-run]

1. Board: reuse epic/README.md github.board_number when it is set and open; else copy the template
   project (views with grouping, workflows, fields come with the copy) and save the new number.
2. Fields: Phase options = the plan's phases; Category is renamed Epic with one option per epic;
   Level, Priority, Size, Status keep the template options.
3. Views: one table view per phase ("Phase <n> <name>", filter phase + level:Task) when missing.
4. Items: every epic and ticket issue is added; Status, Priority, Size, Estimate, Level, Phase,
   Epic and Task ID are set from the files (batched GraphQL mutations).
5. The repos are linked; with --close-old the previous board is closed (not deleted).
"""
import argparse, glob, json, os, re, subprocess, sys, time

STATUS = {'todo': 'Backlog', 'in_progress': 'In progress', 'review': 'In review', 'done': 'Done', 'blocked': 'Backlog'}
ESTIMATE = {'XS': 1, 'S': 2, 'M': 3, 'L': 5, 'XL': 8}
COLORS = ['GRAY', 'BLUE', 'GREEN', 'YELLOW', 'ORANGE', 'RED', 'PINK', 'PURPLE']


def gql(query, **vars):
    args = ['gh', 'api', 'graphql', '-f', f'query={query}']
    for k, v in vars.items():
        args += ['-F' if isinstance(v, (int, bool)) else '-f', f'{k}={json.dumps(v) if isinstance(v, bool) else v}']
    for attempt in range(6):
        r = subprocess.run(args, capture_output=True, text=True)
        if r.returncode == 0:
            out = json.loads(r.stdout)
            if not out.get('errors'):
                return out['data']
            msg = json.dumps(out['errors'])[:400]
        else:
            msg = (r.stderr or r.stdout)[:400]
        if any(x in msg.lower() for x in ('rate limit', 'secondary', 'timeout', 'something went wrong', '502', '503', 'abuse')):
            time.sleep(30 * (attempt + 1)); continue
        raise SystemExit(f'GraphQL error: {msg}')
    raise SystemExit('GraphQL: retries exhausted')


def fm(path):
    text = open(path).read()
    lines = text.split('\n')
    end = lines.index('---', 1)
    f = {}
    for l in lines[1:end]:
        m = re.match(r'^([A-Za-z_][\w-]*):\s?(.*)$', l)
        if m:
            try:
                f[m.group(1)] = json.loads(m.group(2)) if m.group(2).strip() else None
            except Exception:
                f[m.group(1)] = m.group(2)
    return f, lines, end


def set_readme_github(path, github):
    f, lines, end = fm(path)
    out, done = [], False
    for l in lines[1:end]:
        if l.startswith('github:'):
            out.append('github: ' + json.dumps(github)); done = True
        else:
            out.append(l)
    if not done:
        out.insert(0, 'github: ' + json.dumps(github))
    open(path, 'w').write('\n'.join(['---'] + out + lines[end:]))


def priority(phase, is_spike):
    p = 0 if phase is not None and phase <= 0 else 1 if phase is not None and phase <= 2 else 2
    return f'P{max(0, p - 1) if is_spike else p}'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--project-dir', required=True)
    ap.add_argument('--owner', required=True)
    ap.add_argument('--template', type=int, required=True)
    ap.add_argument('--title')
    ap.add_argument('--close-old', action='store_true')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()
    E = os.path.join(a.project_dir, 'epic')
    readme = os.path.join(E, 'README.md')
    gh, _, _ = fm(readme)
    github = gh.get('github') or {}
    title = a.title or os.path.basename(os.path.abspath(a.project_dir)).capitalize()

    # plan from files
    epics, tickets = [], []
    for ed in sorted(os.listdir(E)):
        if not re.match(r'E\d+', ed) or not os.path.isdir(os.path.join(E, ed)):
            continue
        ef, _, _ = fm(os.path.join(E, ed, 'epic.md'))
        epics.append(ef)
        for t in sorted(glob.glob(os.path.join(E, ed, 'tickets', '*.md'))):
            tf, _, _ = fm(t)
            tf['_phase'], tf['_phase_name'], tf['_epic_title'] = ef.get('phase'), ef.get('phase_name'), ef.get('title')
            tickets.append(tf)
    epics.sort(key=lambda e: int(str(e['key'])[1:]))
    phases = sorted({(e.get('phase'), e.get('phase_name')) for e in epics if e.get('phase') is not None})
    phase_label = lambda n, name: f'Phase {n} {name}' if name else f'Phase {n}'
    print(f'plan: {len(epics)} epics, {len(tickets)} tickets, phases {[phase_label(*p) for p in phases]}')
    if a.dry_run:
        return

    owner = gql('query($l:String!){user(login:$l){id}}', l=a.owner)['user']['id']

    # 1. board
    board = None
    if github.get('board_number'):
        b = gql('query($l:String!,$n:Int!){user(login:$l){projectV2(number:$n){id number url closed}}}', l=a.owner, n=github['board_number'])['user']['projectV2']
        if b and not b['closed']:
            board = b
    if not board:
        tpl = gql('query($l:String!,$n:Int!){user(login:$l){projectV2(number:$n){id}}}', l=a.owner, n=a.template)['user']['projectV2']
        board = gql('mutation($p:ID!,$o:ID!,$t:String!){copyProjectV2(input:{projectId:$p,ownerId:$o,title:$t,includeDraftIssues:false}){projectV2{id number url closed}}}',
                    p=tpl['id'], o=owner, t=title)['copyProjectV2']['projectV2']
        print('copied template to', board['url'])
        old = github.get('project_number')
        github.update({'previous_project_number': old} if old and old != board['number'] else {})
        github.update({'board_number': board['number'], 'project_number': board['number'], 'project_url': board['url'], 'project_id': board['id']})
        set_readme_github(readme, github)

    pid = board['id']

    # 2. fields
    def fields():
        q = gql('query($id:ID!){node(id:$id){... on ProjectV2{fields(first:50){nodes{... on ProjectV2FieldCommon{id name dataType} ... on ProjectV2SingleSelectField{options{id name}}}}}}}', id=pid)
        return {f['name']: f for f in q['node']['fields']['nodes'] if f}
    F = fields()

    def set_options(field_name, names, rename=None):
        f = F[field_name]
        have = [o['name'] for o in f.get('options', [])]
        if have == names and not rename:
            return
        opts = [{'name': n, 'color': COLORS[i % len(COLORS)], 'description': ''} for i, n in enumerate(names)]
        q = 'mutation($f:ID!,$o:[ProjectV2SingleSelectFieldOptionInput!]' + (',$n:String' if rename else '') + '){updateProjectV2Field(input:{fieldId:$f,singleSelectOptions:$o' + (',name:$n' if rename else '') + '}){projectV2Field{... on ProjectV2SingleSelectField{id}}}}'
        args = ['gh', 'api', 'graphql', '-f', f'query={q}', '-f', f'f={f["id"]}']
        body = {'query': q, 'variables': {'f': f['id'], 'o': opts, **({'n': rename} if rename else {})}}
        r = subprocess.run(['gh', 'api', 'graphql', '--input', '-'], input=json.dumps(body), capture_output=True, text=True)
        if r.returncode != 0 or '"errors"' in r.stdout:
            raise SystemExit(f'field {field_name}: {(r.stderr or r.stdout)[:300]}')

    set_options('Phase', [phase_label(*p) for p in phases])
    epic_names = [f"{e['key']} {e['title']}" for e in epics]
    if 'Epic' in F:
        set_options('Epic', epic_names)
    elif 'Category' in F:
        set_options('Category', epic_names, rename='Epic')
    F = fields()
    opt = lambda field, name: next((o['id'] for o in F[field].get('options', []) if o['name'] == name), None)

    # 3. per-phase views
    vq = gql('query($id:ID!){node(id:$id){... on ProjectV2{views(first:50){nodes{id name}}}}}', id=pid)
    have_views = {v['name'] for v in vq['node']['views']['nodes']}
    for n, name in phases:
        vname = phase_label(n, name)
        if vname in have_views:
            continue
        v = gql('mutation($p:ID!,$n:String!){createProjectV2View(input:{projectId:$p,name:$n,layout:TABLE_LAYOUT}){projectV2View{id}}}', p=pid, n=vname)
        vid = v['createProjectV2View']['projectV2View']['id']
        gql('mutation($v:ID!,$f:String!){updateProjectV2View(input:{viewId:$v,filter:$f}){projectV2View{id}}}', v=vid, f=f'phase:"{vname}" level:Task')
        print('view', vname)

    # 4. items
    rows = [(e, True) for e in epics] + [(t, False) for t in tickets]
    rows = [(r, is_epic) for r, is_epic in rows if (r.get('issue') or {}).get('url')]
    node_ids = {}
    for i in range(0, len(rows), 20):
        chunk = rows[i:i + 20]
        q = 'query{' + ' '.join(f'r{j}:resource(url:"{r["issue"]["url"]}"){{... on Issue{{id}}}}' for j, (r, _) in enumerate(chunk)) + '}'
        d = gql(q)
        for j, (r, _) in enumerate(chunk):
            node_ids[r['key']] = (d.get(f'r{j}') or {}).get('id')
    item_ids = {}
    keys = [r['key'] for r, _ in rows if node_ids.get(r['key'])]
    for i in range(0, len(keys), 10):
        chunk = keys[i:i + 10]
        q = 'mutation{' + ' '.join(f'a{j}:addProjectV2ItemById(input:{{projectId:"{pid}",contentId:"{node_ids[k]}"}}){{item{{id}}}}' for j, k in enumerate(chunk)) + '}'
        d = gql(q)
        for j, k in enumerate(chunk):
            item_ids[k] = d[f'a{j}']['item']['id']
        time.sleep(1)
    print('items added or found:', len(item_ids))

    # 5. field values
    sets = []
    for r, is_epic in rows:
        k = r['key']
        if k not in item_ids:
            continue
        phase_n = r.get('phase') if is_epic else r.get('_phase')
        phase_name = r.get('phase_name') if is_epic else r.get('_phase_name')
        epic_key = k if is_epic else r.get('epic')
        epic_title = r.get('title') if is_epic else r.get('_epic_title')
        is_spike = (not is_epic) and str(r.get('title', '')).lower().startswith('spike')
        vals = {
            'Status': ('single', opt('Status', STATUS.get(r.get('status'), 'Backlog'))),
            'Priority': ('single', opt('Priority', priority(phase_n, is_spike))),
            'Level': ('single', opt('Level', 'Epic' if is_epic else 'Task')),
            'Phase': ('single', opt('Phase', phase_label(phase_n, phase_name)) if phase_n is not None else None),
            'Epic': ('single', opt('Epic', f'{epic_key} {epic_title}')),
            'Task ID': ('text', k),
        }
        if not is_epic and r.get('size') in ESTIMATE:
            vals['Size'] = ('single', opt('Size', r['size']))
            vals['Estimate'] = ('number', ESTIMATE[r['size']])
        for field, (kind, v) in vals.items():
            if field in F and v is not None:
                sets.append((item_ids[k], F[field]['id'], kind, v))
    for i in range(0, len(sets), 15):
        chunk = sets[i:i + 15]
        parts = []
        for j, (item, field, kind, v) in enumerate(chunk):
            value = {'single': f'singleSelectOptionId:"{v}"', 'text': f'text:{json.dumps(v)}', 'number': f'number:{v}'}[kind]
            parts.append(f'u{j}:updateProjectV2ItemFieldValue(input:{{projectId:"{pid}",itemId:"{item}",fieldId:"{field}",value:{{{value}}}}}){{projectV2Item{{id}}}}')
        gql('mutation{' + ' '.join(parts) + '}')
        time.sleep(1)
    print('field values set:', len(sets))

    # 6. repos and the old board
    repos = {(r.get('issue') or {}).get('repo') for r, _ in rows}
    for repo in sorted(x for x in repos if x):
        o, n = repo.split('/')
        rid = gql('query($o:String!,$n:String!){repository(owner:$o,name:$n){id}}', o=o, n=n)['repository']['id']
        try:
            gql('mutation($p:ID!,$r:ID!){linkProjectV2ToRepository(input:{projectId:$p,repositoryId:$r}){repository{id}}}', p=pid, r=rid)
        except SystemExit as e:
            print('link', repo, 'skipped:', str(e)[:120])
    if a.close_old and github.get('previous_project_number'):
        old = gql('query($l:String!,$n:Int!){user(login:$l){projectV2(number:$n){id closed}}}', l=a.owner, n=github['previous_project_number'])['user']['projectV2']
        if old and not old['closed']:
            gql('mutation($p:ID!){updateProjectV2(input:{projectId:$p,closed:true}){projectV2{id}}}', p=old['id'])
            print('closed old board', github['previous_project_number'])
    print('board:', board['url'])


if __name__ == '__main__':
    main()
