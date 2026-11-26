"""Accept only ordinary proof lines in the six fixed source holes."""
import re

SLOTS = ('branchReaches','suffix','branchMatches','nodeMatches','extensional','cumulative')
PLAIN = {'rfl', 'assumption', 'constructor', 'trivial', 'omega', 'simp', 'simp_all', 'rintro', 'contradiction', 'decide', 'split'}
START = {'intro','rintro','exact','apply','refine','rw','simp','simpa','simp_all','unfold','change','show',
         'have','rcases','cases','by_cases','subst','revert','obtain','specialize','rename_i',
         'generalize','induction','funext','use','all_goals','case','next','split','injection','replace','left','right'}
ALPHABET = re.compile(r"[A-Za-z0-9_'. ,()\[\]{}:<>!?=+*/%|&⟨⟩←→↔∧∨¬∃∀≤≥≠·⊢α∈;-]+\Z")
FORBIDDEN = set("""
axiom theorem lemma def instance opaque example unsafe partial sorry sorryAx admit native_decide
implemented_by extern run_tac run_cmd elab elab_rules syntax macro macro_rules tactic eval set_option
import namespace section end initialize attribute termination_by decreasing_by where classical
ofReduceBool ofReduceNat trustCompiler IO Lean System run do include omit open mutual scoped
axioms exact? by_contra! simp_arith native compiler irreducible axiomInfo
""".split())

def require(ok, label):
    if not ok:
        raise ValueError(label)

def build(template, payload):
    require(type(payload) is dict and len(payload) == len(SLOTS) and set(payload)==set(SLOTS), 'proof field roster')
    for name in SLOTS:
        lines = payload[name]
        require(type(lines) is list and 1 <= len(lines) <= 160, 'line count')
        accepted = []
        for raw in lines:
            require(type(raw) is str and 0 < len(raw) <= 1024 and raw.rstrip()==raw, 'line size')
            require(';' not in raw.replace('<;>','') and ALPHABET.fullmatch(raw) and not any(z in raw for z in ('/-','-/','--','..','?')), 'proof alphabet')
            blank = len(raw)-len(raw.lstrip(' '))
            require(blank <= 16 and blank % 2 == 0, 'indent')
            line = raw.strip()
            if line.startswith('· '):
                line = line[2:]
            words = re.findall("[A-Za-z_][A-Za-z0-9_']*", re.sub(r'\(by (?:decide|rfl|omega)\)', '_', line))
            require(not (set(words) & (FORBIDDEN|{'by'})), 'forbidden proof word')
            require(line in PLAIN or line.split(' ',1)[0] in START, 'tactic start')
            accepted.append('  '+raw)
        marker = '@@PROOF '+name+'@@'
        require(template.count(marker)==1, 'missing or duplicate fixed hole')
        template = template.replace(marker,'\n'.join(accepted))
    require('@@' not in template, 'unfilled proof')
    return template
