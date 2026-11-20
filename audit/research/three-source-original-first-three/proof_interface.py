"""Validate a small, explicit ordinary tactic language, insert only the named proof lines."""

import re

PLAIN = {"rfl", "decide", "decide +kernel", "assumption", "constructor", "trivial", "congr 1",
         "simp", "simp_all", "left", "right"}
LEADING = {"intro","rintro","exact","apply","refine","rw","simp","simp_all","unfold","change","show",
           "have","rcases","cases","by_cases","subst","revert","obtain","use","specialize",
           "rename_i","generalize"}
OPTIONS = re.compile(r"[A-Za-z0-9_'. ,()\[\]{}:<>!?=+*/%|&⟨⟩←→↔∧∨¬∃∀≤≥≠·ρλ⊢-]+\Z")
FORBIDDEN = {"axiom","theorem","lemma","def","instance","opaque","example","unsafe","partial",
             "sorry","sorryAx","admit","native_decide","implemented_by","extern","run_tac","run_cmd",
             "elab","elab_rules","syntax","macro","macro_rules","tactic","eval","set_option","import",
             "namespace","section","end","initialize","attribute","termination_by","decreasing_by","where",
             "classical","ofReduceBool","ofReduceNat","trustCompiler","IO","Lean","System","run","do",
             "include","omit","open","mutual","scoped","attribute","axioms","exact?","by_contra!"}

def require(ok, why):
    if not ok: raise ValueError(why)

def script(lines):
    require(type(lines) is list and 1<=len(lines)<=384,"empty or excessive tactic body")
    out=[]
    for raw in lines:
        require(type(raw) is str and raw and len(raw)<=2048 and raw.rstrip()==raw and
                "\n" not in raw and "\r" not in raw and "\t" not in raw,"tactic line format")
        n=len(raw)-len(raw.lstrip(" "))
        require(n<=12 and n%2==0,"proof indentation")
        s=raw.strip()
        require(OPTIONS.fullmatch(s) and "/-" not in s and "-/" not in s and "--" not in s and
                ".." not in s and "?" not in s.replace("?_","") and not s.startswith(".") and ":=" not in s[:3],
                "ordinary proof alphabet")
        # Nested proof terms, where needed, are solely one of these kernel tactics.
        words=re.findall(r"[A-Za-z_][A-Za-z0-9_']*",re.sub(r"\(by (?:decide(?: \+kernel)?|rfl)\)","_",s))
        require(not (set(words)&(FORBIDDEN|{"by"})),"unregistered proof language")
        lead=s.split(" ",1)[0]
        require(s in PLAIN or (lead in LEADING and len(s)>len(lead)+1),"unregistered tactic "+lead)
        out.append("  "+raw)
    require(sum(map(len,out))<=49152,"proof body bytes")
    return "\n".join(out)

def fill(templates, payload, slots):
    require(type(payload) is dict and set(payload)==set(slots),"exact roster of proof fields")
    proofs={k:script(payload[k]) for k in slots}
    output={}
    used=[]
    for name,source in templates.items():
        def insert(m):
            key=m[1]; require(key in proofs and key not in used,"missing or duplicate slot");used.append(key)
            return proofs[key]
        built=re.sub(r"^@@PROOF ([A-Za-z0-9_.]+)@@$",insert,source,flags=re.M)
        require("@@" not in built,"unresolved proof sentinel")
        output[name]=built
    require(used==slots,"proof slot order or membership")
    return output

