"""Project-first work can use the unmodified Topic/Gate/Evidence/Ability contracts.

All simulated study results live inside disposable Git clones. None are user evidence.
"""
import json
from pathlib import Path
import re
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
        subprocess.run(['git','clone','--quiet','--no-local',str(SOURCE),str(self.root)], check=True)
        self.run_git('config','user.name','Isolated Test Fixture')
        self.run_git('config','user.email','fixture@local.invalid')
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
        self.replace_once('00_global/master_outline.md','current_topic: CLOCK_RESET','current_topic: PROJECT_DEMO')
        self.replace_once('00_global/master_outline.md','master_checkpoint: CLOCK_RESET-GATE-G2','master_checkpoint: PROJECT_DEMO-GATE-G1')
        self.replace_once('01_topics/CLOCK_RESET/state.md','status: ACTIVE','status: PAUSED')
        self.replace_once('01_topics/CLOCK_RESET/state.md','master_review_required: true','master_review_required: false')
        self.replace_once('01_topics/CLOCK_RESET/state.md','master_review_reason: OTHER','master_review_reason: NONE')

    def commit_simulation(self):
        self.run_git('add','00_global','01_topics')
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
        self.assertIn('Status: `OPEN`',self.read('01_topics/CLOCK_RESET/gates.md'))
        self.assertIn('status: PAUSED',self.read('01_topics/CLOCK_RESET/state.md'))
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


if __name__ == '__main__':
    unittest.main()
