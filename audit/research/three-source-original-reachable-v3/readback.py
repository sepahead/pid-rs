"""Independent checks of inter-stage bytes, registered term edges and finite output traces."""

def require(ok, why):
    if not ok:
        raise ValueError(why)


def inputs(assembly, directory, mod, available, accepted_sources, kind, extra=None):
    source=directory/(mod+".lean")
    actual=assembly.digest(source)
    require(accepted_sources.get(source.name)==actual, "source changed between stages "+mod)
    imports = [line.split()[1:] for line in source.read_text().splitlines() if line.startswith("import ")]
    locals_ = {}
    for names in imports:
        for name in names:
            if (directory/(name+".lean")).is_file():
                require(name+".olean" in available, "missing local import "+name)
                locals_[name+".olean"] = available[name+".olean"]
    return {"module":mod,"action":kind,"source":actual,"direct_local_imports":locals_,
            "case_objects_before":dict(available),"stock_anchors":extra or {}}


def dependency_rows(stream, row, common, existing):
    required=row["required_uses"]
    edges={}
    for line in stream.read_text().splitlines():
        require(line.startswith(common.PREFIX),"unexpected proof stream marker")
        raw=common.json.loads(line[len(common.PREFIX):],object_pairs_hook=common.pairs)
        name=raw["name"]
        if name in required:
            need=required[name]
            require(set(need)<=set(raw["value_constants"]), "missing direct proof dependency at "+name)
            edges[name]={"required":need,"observed_direct_value_constants":raw["value_constants"]}
    require(set(edges)==set(required) and existing["checked"]==len(row["targets"]),"all source and term edges")
    return edges


def checkpoints_against_final(early, final):
    for module, entries in early.items():
        for name, listed in entries.items():
            require(listed==final["declarations"][name]["axioms"],
                    "module/final independent axiom disagreement "+module+"/"+name)


def finite_rows(case, trace):
    """A reference from the source's finite set and bit definitions, independent of the Lean printer."""
    canonical={1,2,4,8,16,32,64,3,9,33,10,18,12,20,36,48,11,52}
    def subset(u,v):
        return (u & v)==u
    if case in {"W01","W03"}:
        coordinates=[[i] for i in range(128)]
    elif case=="W15":
        coordinates=[[k,r] for k in range(16) for r in range(16)]
    else:
        raise ValueError("unregistered original finite trace")
    require(len(trace["rows"])==len(coordinates),"one native record per coordinate")
    for point,record in zip(coordinates,trace["rows"]):
        require(list(record["projected"])==point and type(record["assertions"]) is list and
                len(record["assertions"])==2 and all(type(x) is bool for x in record["assertions"]),
                "ordered coordinates and successful Boolean pair")
        if case in {"W01","W03"}:
            a=point[0]
            family=[u for u in range(1,8) if a & (1 << (u-1))]
            valid=bool(family) and all(not subset(u,v) and not subset(v,u)
                                       for i,u in enumerate(family) for v in family[i+1:])
            if case=="W01":
                expected=[True, valid!=(a in canonical)]
            else:
                order=all(any(subset(u,v) for u in family) for v in family)
                expected=[valid,not order]
        else:
            k,r=point
            def bit(x,i):
                return (x>>i)&1
            # The seven subsets have membership selector 64. Bit 0 in a subset denotes
            # the first source, whose cell position is bit 3. Cell bit 0 is the target.
            left=any(bool(64 & (1 << (u-1))) and all(not bit(u,s) or bit(k,3-s)==bit(r,3-s)
                                                   for s in range(3)) for u in range(1,8))
            right=all(bit(k,i)==bit(r,i) for i in (3,2,1))
            expected=[True,left!=right]
        require(record["assertions"]==expected and not all(expected),"both actual ordered assertions")
