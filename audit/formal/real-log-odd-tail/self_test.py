"""Check the restricted input grammar, axiom inventory and receipt consistency."""
from pathlib import Path
import runpy

here = Path(__file__).resolve().parent
judge = runpy.run_path(str(here/"judge.py"))
allowed = set((here/"allowed-identifiers.txt").read_text().split())


def refused(fn, *args):
    try:
        fn(*args)
    except ValueError:
        return
    raise ValueError("invalid object passed its fixed preflight")


def main():
    lex = judge["source_payload"]
    if lex("  exact h₀\n", allowed) != "  exact h₀\n".encode():
        raise ValueError("valid limited syntax lost")
    if lex("  have h_value := h₀\n  exact h_value\n",allowed).count(b"\n") != 2:
        raise ValueError("local binding")
    examples = ["", "  exact h₀", "exact h₀\n", "  sorry\n", "  exact sorryAx\n",
                "  native_decide\n", "  run_tac skip\n", "  #check h₀\n",
                "  exact IO.println\n","  exact Lean.ofReduceBool\n","  unsafe\n",
                "  partial\n", "  set_option autoImplicit false\n","  axiom foo\n",
                "  exact h₀ -- do something else\n","  /- comment -/\n",
                "  exact \x00\n","  exact h₀\n\nimport Proof\n",
                "  exact h₀\u200d\n","  exact h₀\t\n","  exact \x60h₀\n",
                "  exact "+("x"*41000)+"\n"]
    for text in examples:
        refused(lex,text,allowed)
    ax=judge["axioms"]
    valid="'PIDRealTail.sharp' depends on axioms: [propext, Classical.choice, Quot.sound]\n"
    if ax(valid,["sharp"])["sharp"] != ["Classical.choice","Quot.sound","propext"]:
        raise ValueError("axiom inventory")
    for text in [valid.replace("propext","sorryAx"),valid.replace("sharp","irrelevant"),valid+valid,""]:
        refused(ax,text,["sharp"])
    print(f"{len(examples)} prohibited proof payloads and four false axiom records were rejected")


if __name__ == "__main__":
    main()

