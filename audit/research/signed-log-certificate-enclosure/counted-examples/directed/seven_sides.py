"""Compare the true p-grid cell with seven fixed, admitted four-row certificates."""
from fractions import Fraction
from hashlib import sha256
from pathlib import Path
import json
import runpy
import sys


def verify(test, reason):
    if not test:
        raise ValueError(reason)


def main(case_json, raw):
    verify(sha256(case_json.read_bytes()).hexdigest() ==
           "e4064d202075824beb40756cc516523217d26804cf254375e45fe0bcc7c93e04", "frozen seven tables")
    verify(sha256(raw.read_bytes()).hexdigest() ==
           "b8e01525e86297b370b845c0d63be5a21b1bcccc702c9d172a9af3664cc9f6e2", "original arithmetic")
    helpers = runpy.run_path(str(Path(__file__).with_name("true_cell.py")))
    lf, uf = helpers["log_ratio"](5)
    ls, us = helpers["log_ratio"](7)
    fun = runpy.run_path(str(raw))["log_interval"]
    answers = []
    for row in json.loads(case_json.read_text())["records"]:
        p = row["p"]
        m,n = row["witness"]["m"],row["witness"]["n"]
        scale = 1 << p
        values = [Fraction(scale*m,n)*x for x in (lf+ls,uf+us)]
        a = helpers["floor"](values[0])
        verify(a < values[0] < values[1] < a+1,"strict single verified cell")
        lo,hi = fun(Fraction(1 << m),n,p)
        pair = [int(lo*scale),int(hi*scale)]
        verify(pair in ([a-1,a+1],[a,a+2]), "one extra grid line")
        answers.append({"precision":p,"m":m,"N":n,"cell_lower":str(a),
                        "side_with_one_required_extra_unit":"lower" if pair[0]<a else "upper",
                        "verifier_outer_endpoint_differences":[pair[0]-a,pair[1]-(a+1)]})
    print(json.dumps(answers,indent=2,sort_keys=True))


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
