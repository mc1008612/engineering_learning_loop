"""Project-first work can use the unmodified Topic/Gate/Evidence/Ability contracts.

All simulated study results live inside disposable Git clones. None are user evidence.
"""
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1]


class ProjectGateFlowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='project_gate_fixture_')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / 'repo'
        # 快照当前工作区（而非 clone HEAD），确保测试验证的是即将提交的内容。
        shutil.copytree(SOURCE, self.root,
                        ignore=shutil.ignore_patterns('.git', '.runtime', '__pycache__'))
        self.run_git('init', '--quiet')
        self.run_git('config', 'user.name', 'Isolated Test Fixture')
        self.run_git('config', 'user.email', 'fixture@local.invalid')
        self.run_git('add', '-A')
        self.run_git('commit', '--quiet', '-m', 'baseline: working-tree snapshot for fixture')
        self.bootstrap()

    def run_git(self, *args):
        p = subprocess.run(['git',*args],cwd=self.root,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        if p.returncode: raise AssertionError(f'git {args}: {p.stderr}')
        return p.stdout

    def run_tool(self, *args, expect=0):
        p=subprocess.run([sys.executable,*args],cwd=self.root,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        if p.returncode != expect:
            raise AssertionError(f'{args}: exit={p.returncode} expected={expect}\nOUT={p.stdout}\nERR={p.stderr}')
        return p.stdout + p.stderr

    def read(self, path):
        return (self.root / path).read_text(encoding='utf-8')

    def write(self, path, text):
        p = self.root / path
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(text,encoding='utf-8')

    def replace_once(self, path, old, new):
        text=self.read(path)
        self.assertEqual(text.count(old),1,f'anchor not unique: {path} {old!r}')
        self.write(path,text.replace(old,new))

    def bootstrap(self):
        slug='PROJECT_DEMO'
        gate=f'{slug}-GATE-G1'
        for name in ('state','gates','evidence','notes'):
            text=self.read(f'03_templates/NEW_TOPIC/{name}.md')
            text=text.replace('<TOPIC>',slug).replace('<GATE_ID>',gate)
            for k,v in {
                'GATE_TITLE':'演示：工程闭环',
                'GATE_OBJECTIVE':'通过可复现的工程测试完成最小闭环。',
                'PREREQUISITE':'软件协议参考实现可运行。',
                'CRITERION_1':'可以独立说明工程输入和输出的契约。',
                'CRITERION_2':'可以提供运行结果、测试与可复现工件。',
                'CRITERION_3':'能够说明测试结果未覆盖的故障边界。',
                'OPTIONAL_STRETCH':'可以扩展一种变式输入。',
                'TOPIC_OBJECTIVE':'最小纵向贯通并证实正确性。',
                'MASTER_REASON':'使用现有 Gate/Evidence 验证项目驱动学习。',
                'CURRENT_OBJECTIVE':'完成闭环工程交付。',
                'CURRENT_GATE_FOCUS':'G1 在进行中，未获取证据。',
                'OPEN_CAPABILITIES':'G1 C1-C3 尚未验证。',
            }.items():
                text=text.replace(f'<{k}>',v)
            self.assertNotIn('<TOPIC>',text)
            self.write(f'01_topics/{slug}/{name}.md',text)
        outline = self.read('00_global/master_outline.md')
        self.old_topic = re.search(r'^current_topic: (.+)$', outline, re.M).group(1)
        old_checkpoint = re.search(r'^master_checkpoint: (.+)$', outline, re.M).group(1)
        self.replace_once('00_global/master_outline.md', f'current_topic: {self.old_topic}', f'current_topic: {slug}')
        self.replace_once('00_global/master_outline.md', f'master_checkpoint: {old_checkpoint}', f'master_checkpoint: {gate}')
        # 暂停原 current topic，但保留其 Gate 状态，形成“新项目推进 + 旧 Gate 未关闭”的场景。
        old_state = f'01_topics/{self.old_topic}/state.md'
        # 每条新 Gate 在 Master Plan 后取得唯一 Mode 路由；fixture 模拟已批准路线。
        self.replace_once('02_specs/TEACHING_MODE_ROUTE.md',
                          'HOST_DEVICE-GATE-G1: PROJECT',
                          'HOST_DEVICE-GATE-G1: PROJECT\nPROJECT_DEMO-GATE-G1: PROJECT')
        for old, new in (('status: ACTIVE', 'status: PAUSED'),
                         ('master_review_required: true', 'master_review_required: false'),
                         ('master_review_reason: OTHER', 'master_review_reason: NONE')):
            if old in self.read(old_state):
                self.replace_once(old_state, old, new)

    def commit_simulation(self):
        self.run_git('add','00_global','01_topics','02_specs/TEACHING_MODE_ROUTE.md')
        self.run_git('commit','-m','TEST FIXTURE ONLY: simulate reviewed learning changes')

    def mark_gate_pass(self,assistance='A1',result='PASS'):
        gates='01_topics/PROJECT_DEMO/gates.md'
        self.replace_once(gates,'Status: `OPEN`','Status: `PASSED`')
        for c in ('C1','C2','C3'):
            self.replace_once(gates,f'- {c}: `NOT_VERIFIED`',f'- {c}: `VERIFIED`')
        self.replace_once(gates,'### Evidence References\n- NONE','### Evidence References\n- PROJECT_DEMO-EXP-001')
        evidence='01_topics/PROJECT_DEMO/evidence.md'
        entry=f'''\n\n### PROJECT_DEMO-EXP-001 — TEST DATA, NOT A USER RESULT

Schema: `evidence_entry`
Type: `ASSESSMENT`
Result: `{result}`
Assistance: `{assistance}`
Gate: `PROJECT_DEMO-GATE-G1`
Lesson: `PROJECT_DEMO-LSN-20990101-000000`

References:
- NONE

Artifacts:
- synthetic-fixture.txt

#### Observation
这是自动化测试构造的合成观察，不是真实用户学习证据。

#### Interpretation
仅用于验证 Gate PASS 规则及 Ability 不自动提升。
'''
        self.write(evidence,self.read(evidence).rstrip()+entry)

    def test_project_topic_routes_to_tutor_while_old_gate_open(self):
        self.assertIn('REPO AUDIT: PASS',self.run_tool('tools/audit.py','--route'))
        self.assertIn('ROUTE:\nTUTOR',self.run_tool('tools/audit.py','--route'))
        self.assertIn('Status: `OPEN`',self.read(f'01_topics/{self.old_topic}/gates.md'))
        self.assertIn('status: PAUSED',self.read(f'01_topics/{self.old_topic}/state.md'))
        self.assertIn('Host–Device Communication | L0',self.read('00_global/ability_profile.md'))

    def test_pending_changes_must_be_reviewed_and_committed_before_tutor(self):
        self.assertIn('CURRENT_STATE: PENDING_LEARNING_CHANGES',self.run_tool('tools/learning.py','status'))
        self.commit_simulation()
        self.assertIn('CURRENT_STATE: READY_FOR_TUTOR',self.run_tool('tools/learning.py','status'))

    def test_unverified_gate_cannot_be_passed(self):
        self.replace_once('01_topics/PROJECT_DEMO/gates.md','Status: `OPEN`','Status: `PASSED`')
        out=self.run_tool('tools/audit.py','--route',expect=1)
        self.assertIn('PASSED but mandatory criteria not all VERIFIED',out)
        self.assertIn('PASSED without Evidence References',out)

    def test_a2_pass_evidence_does_not_qualify(self):
        self.mark_gate_pass(assistance='A2')
        out=self.run_tool('tools/audit.py','--route',expect=1)
        self.assertIn('PASSED without PASS Evidence within Assistance <= A1',out)

    def test_a1_pass_evidence_qualifies_but_ability_does_not_autoupgrade(self):
        ability=self.read('00_global/ability_profile.md')
        self.mark_gate_pass(assistance='A1')
        out=self.run_tool('tools/audit.py','--route')
        self.assertIn('ROUTE:\nMASTER_REVIEW',out)
        self.assertEqual(ability,self.read('00_global/ability_profile.md'))

    def test_partial_evidence_is_allowed_without_forcing_pass(self):
        ev='01_topics/PROJECT_DEMO/evidence.md'
        self.write(ev,self.read(ev).rstrip()+'''\n\n### PROJECT_DEMO-EXP-001 — Synthetic partial check\n
Schema: `evidence_entry`\nType: `DEBUG`\nResult: `PARTIAL`\nAssistance: `A2`\nGate: `PROJECT_DEMO-GATE-G1`\nLesson: `PROJECT_DEMO-LSN-20990101-000000`\n
References:\n- NONE\n
Artifacts:\n- synthetic-fixture.txt\n
#### Observation\n测试 fixture 中出现一条未通过验收的观察。\n
#### Interpretation\n保留进展但不得自动提升 Gate 状态。\n''')
        self.assertIn('REPO AUDIT: PASS',self.run_tool('tools/audit.py','--route'))
        self.assertIn('Status: `OPEN`',self.read('01_topics/PROJECT_DEMO/gates.md'))

    def test_evidence_is_append_only_across_commits(self):
        ev='01_topics/PROJECT_DEMO/evidence.md'
        self.write(ev,self.read(ev).rstrip()+'''\n\n### PROJECT_DEMO-EXP-001 — Fixture\n
Schema: `evidence_entry`\nType: `LEARNING`\nResult: `PARTIAL`\nAssistance: `A2`\nGate: `PROJECT_DEMO-GATE-G1`\nLesson: `PROJECT_DEMO-LSN-20990101-000000`\n
References:\n- NONE\n
Artifacts:\n- NONE\n
#### Observation\n初次证据，测试 fixture。\n
#### Interpretation\n不能修改已有 Evidence。\n''')
        self.commit_simulation()
        self.replace_once(ev,'初次证据，测试 fixture。','删除或篡改原始内容。')
        out=self.run_tool('tools/audit.py','--route',expect=1)
        self.assertIn('was rewritten',out)

    def test_disallowed_current_gate_status_is_rejected(self):
        self.replace_once('01_topics/PROJECT_DEMO/gates.md','Status: `OPEN`','Status: `DRAFT`')
        out=self.run_tool('tools/audit.py','--route',expect=1)
        self.assertIn('current_action=TUTOR cannot use current Gate status=DRAFT',out)

    def test_invalid_ability_level_fails_audit(self):
        self.replace_once('00_global/ability_profile.md','Host–Device Communication | L0','Host–Device Communication | L2.5')
        out=self.run_tool('tools/audit.py','--route',expect=1)
        self.assertIn('invalid level',out)

    def test_full_mock_lesson_handoff_keeps_gate_open_and_adds_evidence(self):
        # Fixture only: runtime transaction + mocked Tutor Handoff, never claimed as human work.
        self.commit_simulation()
        script = r"""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tools'))
from lib.context import build_tutor_context,tutor_prompt_filename
from lib.flow import create_tutor_transaction
from lib.repo import frontmatter,rd,wr,RUNTIME
context=build_tutor_context()
fm=frontmatter(rd(context))
prompt=RUNTIME/'prompts'/tutor_prompt_filename(fm['lesson_id'])
wr(prompt,'This is a synthetic unit-test prompt, not a real lesson.\n')
create_tutor_transaction(lesson_id=fm['lesson_id'],topic=fm['topic'],gate=fm['current_gate'],context_path=context,prompt_path=prompt,handoff_filename=fm['handoff_filename'])
print(json.dumps(fm))
"""
        p = subprocess.run([sys.executable,'-c',script],cwd=self.root,
                           capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr)
        fm=json.loads(p.stdout)
        self.assertIn('CURRENT_STATE: PENDING_LESSON',self.run_tool('tools/learning.py','status'))
        keys=['lesson_id','topic','context_file','context_sha256',
              'fingerprint_state','fingerprint_gates','fingerprint_evidence',
              'fingerprint_notes','fingerprint_master_outline','fingerprint_ability_profile']
        meta={k:fm[k] for k in keys}
        meta.update(schema='tutor_handoff',delta_format='structured_json',
                    lesson_status='COMPLETE',gate='PROJECT_DEMO-GATE-G1',
                    master_review_required='false',master_review_reason='NONE')
        headings='---\n'+''.join(f'{k}: {v}\n' for k,v in meta.items())+'---\n\n'
        handoff = headings + """## Last Lesson

Focus:
合成的测试课，不代表用户成果。

Work:
仅验证协议管线。

Outcome:
模拟部分进度。

Gate Progress:
C1 PARTIAL; Gate OPEN.

Evidence:
PROJECT_DEMO-EXP-001（fixture）。

Suggested Local Next:
下一轮继续，等待真人学习证据。

"""
        def json_section(name,value):
            return f'## {name}\n\n```json\n{json.dumps(value,ensure_ascii=False)}\n```\n\n'
        handoff += json_section('State Delta',{
            'set':{'in_progress':['G1 模拟部分完成。'],
                   'not_yet_verified':['真实项目证据尚不存在。']},
            'add_evidence_anchors':['PROJECT_DEMO-EXP-001']})
        handoff += json_section('Gate Delta',{
            'status':'OPEN','criteria':{'C1':'PARTIAL'},
            'add_evidence_references':['PROJECT_DEMO-EXP-001']})
        handoff += json_section('Evidence To Append',[{
            'id':'PROJECT_DEMO-EXP-001','title':'Synthetic fixture evidence',
            'type':'DEBUG','result':'PARTIAL','assistance':'A2',
            'gate':'PROJECT_DEMO-GATE-G1','lesson_id':fm['lesson_id'],
            'references':[],'artifacts':['synthetic-fixture.txt'],
            'observation':'这是测试程序编造的测试输入，不是真实学习。',
            'interpretation':'用于验证 Handoff->Evidence；不可作为用户能力证据。'}])
        handoff += json_section('Notes Delta',{'append':{'Debug Checklist':['Synthetic test note.']}})
        handoff_rel=Path('.runtime/handoff')/fm['handoff_filename']
        self.write(handoff_rel,handoff)
        self.assertIn('CURRENT_STATE: PENDING_HANDOFF',self.run_tool('tools/learning.py','status'))
        self.assertIn('HANDOFF VALIDATED',self.run_tool('tools/handoff.py','validate',str(handoff_rel)))
        self.replace_once('02_specs/TEACHING_MODE_ROUTE.md',
                          'PROJECT_DEMO-GATE-G1: PROJECT',
                          'PROJECT_DEMO-GATE-G1: CONCEPT')
        self.assertIn('STALE: teaching mode route changed',
                      self.run_tool('tools/handoff.py','validate',str(handoff_rel),expect=3))
        self.replace_once('02_specs/TEACHING_MODE_ROUTE.md',
                          'PROJECT_DEMO-GATE-G1: CONCEPT',
                          'PROJECT_DEMO-GATE-G1: PROJECT')
        self.assertIn('NEXT_ACTION',self.run_tool('tools/handoff.py','preview',str(handoff_rel)))
        out=self.run_tool('tools/handoff.py','apply',str(handoff_rel))
        self.assertIn('APPLY: PASS',out)
        self.assertIn('PROJECT_DEMO-EXP-001',self.read('01_topics/PROJECT_DEMO/evidence.md'))
        self.assertIn('C1: `PARTIAL`',self.read('01_topics/PROJECT_DEMO/gates.md'))
        self.assertIn('Status: `OPEN`',self.read('01_topics/PROJECT_DEMO/gates.md'))
        self.assertIn('Host–Device Communication | L0',self.read('00_global/ability_profile.md'))
        self.assertIn('REPO AUDIT: PASS',self.run_tool('tools/audit.py','--route'))
        self.assertIn('CURRENT_STATE: PENDING_LEARNING_CHANGES',self.run_tool('tools/learning.py','status'))

    def test_ability_master_review_can_happen_before_gate_pass(self):
        # Semantics still require true Human evidence; this only checks routing mechanics.
        self.replace_once('01_topics/PROJECT_DEMO/state.md',
                          'master_review_required: false','master_review_required: true')
        self.replace_once('01_topics/PROJECT_DEMO/state.md',
                          'master_review_reason: NONE','master_review_reason: POSSIBLE_LEVEL_CHANGE')
        before=self.read('00_global/ability_profile.md')
        out=self.run_tool('tools/audit.py','--route')
        self.assertIn('ROUTE:\nMASTER_REVIEW',out)
        self.assertEqual(before,self.read('00_global/ability_profile.md'))
        self.assertIn('Status: `OPEN`',self.read('01_topics/PROJECT_DEMO/gates.md'))
        # A hypothetical Human-approved Master mutation is mechanically possible
        # even while the owning Gate remains OPEN. This is NOT a user level update.
        self.replace_once('00_global/ability_profile.md',
                          'Host–Device Communication | L0',
                          'Host–Device Communication | L1')
        self.replace_once('01_topics/PROJECT_DEMO/state.md',
                          'master_review_required: true','master_review_required: false')
        self.replace_once('01_topics/PROJECT_DEMO/state.md',
                          'master_review_reason: POSSIBLE_LEVEL_CHANGE','master_review_reason: NONE')
        self.assertIn('REPO AUDIT: PASS',self.run_tool('tools/audit.py','--route'))
        self.assertIn('ROUTE:\nTUTOR',self.run_tool('tools/audit.py','--route'))
        self.assertIn('Status: `OPEN`',self.read('01_topics/PROJECT_DEMO/gates.md'))

    def test_no_hidden_second_current_focus(self):
        self.write('00_global/master_outline.md',self.read('00_global/master_outline.md')+'\n## Current Learning Focus\nDuplicate\n')
        out=self.run_tool('tools/audit.py','--route',expect=1)
        self.assertIn('must not duplicate frontmatter routing facts',out)


    def test_every_spec_is_in_required_inventory_and_missing_spec_fails_audit(self):
        specs = sorted(p.name for p in (self.root / '02_specs').glob('*.md'))
        source = (self.root / 'tools/lib/repo.py').read_text(encoding='utf-8')
        unlisted = [s for s in specs if f'02_specs/{s}' not in source]
        self.assertEqual([], unlisted, '每个 02_specs/*.md 都必须登记在 repo.py 的 required 清单中')
        (self.root / '02_specs/PROJECT_GATE_WORKFLOW.md').unlink()
        out = self.run_tool('tools/audit.py', '--route', expect=1)
        self.assertIn('missing 02_specs/PROJECT_GATE_WORKFLOW.md', out)

    def render_fixture_lesson(self):
        script = r"""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tools'))
from lib.context import build_tutor_context
from lib.repo import frontmatter,rd
from lib.render import render_tutor_start_prompt
ctx=build_tutor_context()
fm=frontmatter(rd(ctx))
print(json.dumps({'context':str(ctx.relative_to(Path.cwd())),
                  'prompt':render_tutor_start_prompt(ctx,fm['lesson_id'],fm['handoff_filename']),
                  'metadata':fm},ensure_ascii=False))
"""
        p = subprocess.run([sys.executable,'-c',script], cwd=self.root,
                           capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr)
        result=json.loads(p.stdout)
        result['context_text']=self.read(result['context'])
        return result

    def test_tutor_prompt_includes_shared_and_project_only(self):
        self.commit_simulation()
        result=self.render_fixture_lesson()
        context=result['context_text']
        prompt=result['prompt']
        self.assertEqual('PROJECT',result['metadata']['teaching_mode'])
        self.assertIn(self.read('02_specs/TEACHING_CONTRACT.md').strip(),prompt)
        self.assertIn(self.read('02_specs/TEACHING_PROJECT.md').strip(),prompt)
        self.assertNotIn(self.read('02_specs/TEACHING_CONCEPT.md').strip(),prompt)
        self.assertNotIn('## Teaching Contract',context)
        self.assertIn('<!-- BEGIN:TUTOR_HANDOFF_PROTOCOL -->',context)
        self.assertIn(self.read('02_specs/TUTOR_HANDOFF_PROTOCOL.md').strip(),context)
        self.assertIn('Human 可随时停止',prompt)

    def test_concept_only_uses_concept_strategy(self):
        self.replace_once('02_specs/TEACHING_MODE_ROUTE.md',
                          'PROJECT_DEMO-GATE-G1: PROJECT',
                          'PROJECT_DEMO-GATE-G1: CONCEPT')
        self.commit_simulation()
        result=self.render_fixture_lesson()
        self.assertEqual('CONCEPT',result['metadata']['teaching_mode'])
        self.assertIn(self.read('02_specs/TEACHING_CONCEPT.md').strip(),result['prompt'])
        self.assertNotIn(self.read('02_specs/TEACHING_PROJECT.md').strip(),result['prompt'])
        self.assertNotIn('## Teaching Contract',result['context_text'])

    def test_uncommitted_mode_route_blocks_new_lesson(self):
        self.commit_simulation()
        self.assertIn('CURRENT_STATE: READY_FOR_TUTOR', self.run_tool('tools/learning.py','status'))
        self.replace_once('02_specs/TEACHING_MODE_ROUTE.md',
                          'PROJECT_DEMO-GATE-G1: PROJECT',
                          'PROJECT_DEMO-GATE-G1: CONCEPT')
        status=self.run_tool('tools/learning.py','status')
        self.assertIn('CURRENT_STATE: PENDING_LEARNING_CHANGES',status)
        self.assertIn('02_specs/TEACHING_MODE_ROUTE.md',status)
        self.assertIn('REPO AUDIT: PASS',self.run_tool('tools/audit.py','--route'))
        self.run_git('add','02_specs/TEACHING_MODE_ROUTE.md')
        self.run_git('commit','-m','TEST FIXTURE ONLY: approved mode change')
        self.assertIn('CURRENT_STATE: READY_FOR_TUTOR',self.run_tool('tools/learning.py','status'))

    def test_start_tutor_cli_writes_mode_prompt_and_transaction(self):
        # 真实 CLI 路径，但替换浏览器与剪贴板操作，不访问外部应用。
        self.commit_simulation()
        script = r"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tools'))
import learning
learning.copy_to_system_clipboard=lambda text:(True,'mock clipboard')
learning.open_url=lambda url:(True,'mock browser')
raise SystemExit(learning.start_tutor('https://example.invalid/tutor',None))
"""
        p=subprocess.run([sys.executable,'-c',script],cwd=self.root,
                         capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertIn('TUTOR LESSON READY',p.stdout)
        transaction=json.loads(self.read('.runtime/tutor_transaction.json'))
        prompt=self.read(transaction['prompt_file'])
        context=self.read(transaction['context_file'])
        self.assertIn('# Project Mode',prompt)
        self.assertNotIn('# Concept Mode',prompt)
        self.assertIn('# Teaching Contract',prompt)
        self.assertNotIn('# Teaching Contract',context)
        self.assertIn('teaching_mode: PROJECT',context)
        self.assertIn('CURRENT_STATE: PENDING_LESSON',self.run_tool('tools/learning.py','status'))
        self.run_tool('tools/learning.py','discard-lesson','--confirm',transaction['lesson_id'])
        self.assertIn('CURRENT_STATE: READY_FOR_TUTOR',self.run_tool('tools/learning.py','status'))

    def test_missing_route_for_current_gate_rejects_tutor(self):
        self.replace_once('02_specs/TEACHING_MODE_ROUTE.md',
                          'PROJECT_DEMO-GATE-G1: PROJECT\n','')
        out=self.run_tool('tools/audit.py','--route',expect=1)
        self.assertIn('missing mapping for PROJECT_DEMO-GATE-G1',out)

    def test_duplicate_route_rejected_not_silently_overridden(self):
        self.replace_once('02_specs/TEACHING_MODE_ROUTE.md',
                          'PROJECT_DEMO-GATE-G1: PROJECT',
                          'PROJECT_DEMO-GATE-G1: PROJECT\nPROJECT_DEMO-GATE-G1: CONCEPT')
        out=self.run_tool('tools/audit.py','--route',expect=1)
        self.assertIn('duplicate mapping PROJECT_DEMO-GATE-G1',out)

    def test_illegal_mode_is_rejected(self):
        self.replace_once('02_specs/TEACHING_MODE_ROUTE.md',
                          'PROJECT_DEMO-GATE-G1: PROJECT',
                          'PROJECT_DEMO-GATE-G1: UNKNOWN')
        out=self.run_tool('tools/audit.py','--route',expect=1)
        self.assertIn('invalid mode',out)

    def test_unknown_gate_route_is_rejected(self):
        self.replace_once('02_specs/TEACHING_MODE_ROUTE.md',
                          'PROJECT_DEMO-GATE-G1: PROJECT',
                          'PROJECT_DEMO-GATE-G1: PROJECT\nMISSING-GATE-G1: PROJECT')
        out=self.run_tool('tools/audit.py','--route',expect=1)
        self.assertIn('unknown Gate MISSING-GATE-G1',out)

    def test_missing_mode_spec_is_rejected(self):
        (self.root/'02_specs/TEACHING_PROJECT.md').unlink()
        out=self.run_tool('tools/audit.py','--route',expect=1)
        self.assertIn('missing 02_specs/TEACHING_PROJECT.md',out)

    def test_master_context_includes_current_mode_route(self):
        script = r"""
import sys
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tools'))
from lib.context import build_master_context
print(build_master_context('NONE'))
"""
        p = subprocess.run([sys.executable, '-c', script], cwd=self.root,
                           capture_output=True, text=True)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertIn('PROJECT_DEMO-GATE-G1: PROJECT',self.read(p.stdout.strip()))


if __name__ == '__main__':
    unittest.main()
