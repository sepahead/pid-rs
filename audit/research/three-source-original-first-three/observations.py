"""Read the entire stock output for every named target, without invoking Lean."""

import hashlib

def read_records(terms, axes, row, qualified, allowed):
    roster=row["targets"]; uses=row["consumer_uses"]
    require=qualified.require
    printed=qualified.verify_axioms(axes,roster,set(allowed))
    observed={}; trusts=set()
    direct={"direct_type_axioms":"type_constants","direct_value_axioms":"value_constants"}
    with terms.open(encoding="utf-8") as out:
        for text in out:
            require(text.startswith(qualified.PREFIX),"unrecognised compiler output")
            entry=qualified.json.loads(text[len(qualified.PREFIX):],object_pairs_hook=qualified.pairs)
            require(set(entry)==set(qualified.FIELDS)|set(direct),"exact term record fields")
            name=entry["name"]
            require(name not in observed and roster.get(name)==entry["owner"] and entry["kind"]=="theorem",
                    "theorem identity, membership or owner")
            require(entry["universe_parameters"]==[] and entry["axioms"]==printed[name],"theorem universe or axioms")
            trust=entry["ordinary_import_trust"];require(type(trust) is int and trust>=0,"import trust");trusts.add(trust)
            ids={}
            for key in ("type_constructor_representation","value_constructor_representation"):
                v=entry[key]
                require(type(v) is str and "Lean.Expr." in v and not any(s in v for s in
                        ("<unknown>","<opaque>","...","…","Lean.Expr.fvar","Lean.Expr.mvar","Lean.Level.mvar")),
                        "incomplete/open kernel expression")
                ids[key]=hashlib.sha256(v.encode()).hexdigest()
            for fld,constants in direct.items():
                xs=entry[constants]
                require(isinstance(xs,list) and all(isinstance(x,str) and x for x in xs)
                        and xs==sorted(set(xs)) and "sorryAx" not in xs,"constant inventory")
                ds=entry[fld]
                require(ds==sorted(set(ds)) and set(ds)<=set(xs) and set(ds)<=set(printed[name]),
                        "direct axiom readback")
            if name in uses:
                require(uses[name] in entry["value_constants"],"consumer must directly use its exact theorem")
            observed[name]={"owner":entry["owner"],"expressions":ids,"axioms":printed[name],
                **{k:entry[k] for k in direct}}
    require(list(roster)==list(observed) and len(trusts)==1,"theorem order, coverage or trust")
    return {"checked":len(observed),"ordinary_import_trust":trusts.pop(),"declarations":observed,
            "raw_terms_sha256":qualified.digest(terms),"axiom_listing_sha256":qualified.digest(axes)}

