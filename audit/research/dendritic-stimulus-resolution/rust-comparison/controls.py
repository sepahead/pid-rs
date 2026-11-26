"""Alter real returned records or the real constructed rows and require a scoped refusal."""
from copy import deepcopy


def rejected(function, message):
    try:
        function()
    except (ValueError, KeyError, TypeError) as exc:
        return str(exc)
    raise ValueError("control accepted: " + message)


def exercise(c, proposed, expected, actual, targets):
    result = {}
    def row_fault(name, change):
        altered = deepcopy(proposed)
        change(altered)
        result[name] = rejected(lambda: c["validate_rows"](altered, expected), name)

    def wrong_axes(table):
        for row in table["100"]:
            row[0], row[1] = row[1], row[0]

    def late_flag(table):
        for row in table["50"]:
            row[2] = int(row[0] > row[1])

    row_fault("exchange basal and tuft after grouping", wrong_axes)
    row_fault("compute flag after grouping", late_flag)
    row_fault("assign one to an equal-input tie", lambda d: d["100"][0].__setitem__(2, 1))
    row_fault("change zero-spike class", lambda d: d["50"][0].__setitem__(3, 1))
    row_fault("boolean source label", lambda d: d["10"][0].__setitem__(2, False))
    row_fault("drop an input row", lambda d: d["10"].pop())
    row_fault("replace counts by occupied support", lambda d: d.__setitem__("100", list(
        map(list, dict.fromkeys(tuple(x) for x in d["100"])))))
    result["repeated JSON key"] = rejected(lambda:c["load_json"](b'{"10":[],"10":[]}'), "duplicate input")

    def native_fault(name, change):
        altered = deepcopy(actual)
        change(altered)
        result[name] = rejected(lambda:c["check"](altered, expected, targets), name)

    def record(d, route, node):
        return next(row for row in d["100"][route]["atoms"] if c["key_of"](row["masks"]) == node)

    def put(d, field, value):
        record(d, "mgw", "04")[field] = value

    def curve(d):
        info = record(d, "mgw", "04")
        info["informative"], info["misinformative"] = info["misinformative"], info["informative"]

    native_fault("exchange informative and misinformative", curve)
    native_fault("reverse signed coordinate", lambda d:put(d,"signed",c["write_bits"](
        -float(c["binary64"](record(d, "mgw", "04")["signed"])))))
    native_fault("use bits instead of nats", lambda d:put(d,"signed",c["write_bits"](
        float(c["binary64"](record(d, "mgw", "04")["signed"]))/0.6931471805599453)))
    native_fault("omit normalization by observation count", lambda d:put(d,"signed",c["write_bits"](
        651 * float(c["binary64"](record(d, "mgw", "04")["signed"])))))
    native_fault("use Williams-Beer in the signed shared-exclusions slot", lambda d:put(
        d,"signed",record(d,"imin","04")["imin"]))
    native_fault("source-key substitution at a nonzero atom", lambda d:record(d,"mgw","04").__setitem__(
        "masks", [1]))
    native_fault("drop I_min atom", lambda d:d["10"]["imin"]["atoms"].pop())
    native_fault("NaN", lambda d:put(d,"informative","7ff8000000000000"))
    native_fault("positive infinity", lambda d:put(d,"signed","7ff0000000000000"))
    native_fault("typed count", lambda d:d["100"]["mgw"].__setitem__("sample_count", True))
    native_fault("false pointwise inclusion", lambda d:d["100"]["mgw"].__setitem__("pointwise_included", 1))
    native_fault("finite overshoot at an exact zero", lambda d:next(
        row for row in d["10"]["mgw"]["atoms"] if row["masks"] == [4]
    ).__setitem__("signed", c["write_bits"](1e-11)))
    enough = deepcopy(actual)
    for width in c["WIDTHS"]:
        for route in ("mgw","imin"):
            enough[width][route]["atoms"].reverse()
            for row in enough[width][route]["atoms"]:
                row["masks"].reverse()
    c["check"](enough, expected, targets)
    return {"rejections": result, "positive_control": "all record and mask lists reversed, with labels retained"}
