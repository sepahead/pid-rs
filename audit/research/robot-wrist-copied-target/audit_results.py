"""Cross-read the five signed atom products and the full independent finite decomposition."""

from decimal import Decimal, localcontext
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path


SUPPORT_HASH = "739aad4f1e2895973edadf3eae8dc0349a03a6f85329b3a8e064b742c9759050"
LATTICE_HASH = "4b05b519d580f03c4ab7c0ff73523a2e085793b1a0861d9a54f99ebf1edd13ad"
MEMBER_HASH = "f0c901ead751ff3104d7e1aeb23165efb88270b219c1954c43bfff2344a7bb3c"
FIVE = ("04", "05", "06", "05+06", "07")


def require(ok, message):
    if not ok:
        raise ValueError(message)


def checked_samples(count_report, lattice_report):
    full = lattice_report["scientific_result"]
    require(lattice_report["source"] == MEMBER_HASH, "original member identity")
    require(type(count_report["observations"]) is int and count_report["observations"] == 117
            and type(full["N"]) is int and full["N"] == 117, "episode counts")
    cells = count_report["cells"]
    a = [(-1,-1,52,77,75), (-1,1,25,77,42), (1,-1,23,40,75), (1,1,17,40,42)]
    require(len(cells) == len(full["cell_criteria"]) == len(a), "four occupied cells")
    product = Fraction(1)
    for row, other, expected in zip(cells, full["cell_criteria"], a):
        values = tuple(row[name] for name in ("force","torque","count","row","column"))
        require(all(type(number) is int for number in values) and values == expected, "empirical sign table or margins")
        x, w, m, u, v = values
        factor = Fraction(u*v, m*(u+v-m))
        require(row["ratio"] == str(factor) and row["shares_both"] is True and m<u and m<v,
                "occupied row and column support factor")
        corresponding = {"x":x,"w":w,"count":m,"row":u,"column":v,"factor":str(factor)}
        require(json.dumps(other,sort_keys=True) == json.dumps(corresponding,sort_keys=True),
                "independent source or factor")
        product *= factor**m
    require(count_report["count_matrix_negative_zero_positive"] == [[52,0,25],[0,0,0],[23,0,17]],
            "zero slope rows and columns")
    require(count_report["individual_positive_rational"] == str(product) and product > 1, "positive Q")
    require(count_report["occupied"] == 4 and count_report["cells_sharing_row_and_column"] == 4
            and count_report["signed_means_all_zero"] is False and full["set_all_five_to_zero"] is False,
            "support decision")
    expected_products = dict(zip(FIVE,map(str,(1/product,product,1,1,1))))
    require(count_report["five_signed_products"] == full["five_signed_products"] == expected_products,
            "five named products with correct orientations")
    require(full["absolute_product"] == str(product**2) and count_report["five_signed_sum_product"] == "1",
            "sum versus absolute sum")
    require(full["occupied_pairs"]==4 and full["nonstar_cells"] == [[-1,-1],[-1,1],[1,-1],[1,1]],
            "support shape")
    all_values=full["all108"]
    require(len(all_values)==18 and set(FIVE) <= set(all_values), "registry")
    for rule, fields in all_values.items():
        require(set(fields)=={"informative","misinformative","signed"},"component identities")
        for data in fields.values():
            require(set(data)=={"cumulative","atom"} and all(Fraction(s)>0 for s in data.values()), "positive products")
        for role in ("cumulative","atom"):
            require(Fraction(fields["signed"][role]) == Fraction(fields["informative"][role]) /
                    Fraction(fields["misinformative"][role]), "positive component quotient")
        if rule in FIVE:
            require(fields["signed"]["atom"]==expected_products[rule],"five atom positions inside the original 108")
    with localcontext() as context:
        context.prec=65
        magnitude=(Decimal(product.numerator).ln()-Decimal(product.denominator).ln()) / 117
        require(count_report["single_magnitude_nats_rounded"]==format(magnitude,".15f")
                and count_report["sum_of_absolute_means_nats_rounded"]==format(2*magnitude,".15f"),"reported rounded nats")
    return {"episodes":117, "observed_sign_pairs":4, "occupied_cells_with_both_neighbours":4,
            "five_signed_products":expected_products, "per_nonzero_magnitude_nats":format(magnitude,".15f"),
            "sum_absolute_signed_means_nats":format(2*magnitude,".15f"),
            "algebraic_sum_nats":"0", "exact_copy_readouts_correct":117, "conditional_mutual_information_nats":"0"}


def load_checked(support, lattice):
    return checked_bytes(Path(support).read_bytes(), Path(lattice).read_bytes())


def checked_bytes(support, lattice):
    checked = checked_samples(json.loads(support), json.loads(lattice))
    require(sha256(support).hexdigest() == SUPPORT_HASH and sha256(lattice).hexdigest() == LATTICE_HASH,
            "complete original checked records")
    return checked


def recorded_self_test(support, lattice, native, receiver):
    """Exercise role changes and a close but different floating-point word entirely in memory."""
    from copy import deepcopy

    def refuse(action, reason):
        try:
            action()
        except ValueError as exc:
            require(str(exc) == reason, "unexpected refusal: " + str(exc))
        else:
            raise ValueError("accepted alteration: " + reason)

    data = json.loads(support)
    altered = deepcopy(data)
    factors = altered["five_signed_products"]
    factors["04"], factors["05"] = factors["05"], factors["04"]
    refuse(lambda: checked_samples(altered, json.loads(lattice)),
           "five named products with correct orientations")

    changed = json.loads(lattice)
    fields = changed["scientific_result"]["all108"]["01"]
    for channel in ("informative", "misinformative"):
        fields[channel]["atom"] = str(2 * Fraction(fields[channel]["atom"]))
    changed_bytes = json.dumps(changed, sort_keys=True).encode()
    checked_samples(data, changed)
    refuse(lambda: checked_bytes(support, changed_bytes), "complete original checked records")

    words = receiver["strict_load"](native)
    reversed_word = deepcopy(words)
    negative = next(row for row in reversed_word["mgw"]["atoms"] if row["masks"] == [4])
    negative["signed"] = "3fcf466f0b10513e"
    refuse(lambda: receiver["compare"](reversed_word), "wrong native value or mask mgw/04")

    # Changing just the least significant bit at 04 preserves the numerical tolerance.
    # It must still fail the identity check for the originally measured word.
    close = deepcopy(words)
    near = next(row for row in close["mgw"]["atoms"] if row["masks"] == [4])
    near["signed"] = format(int(near["signed"], 16) ^ 1, "016x")
    receiver["compare"](close)
    refuse(lambda: require_native_identity(json.dumps(close, sort_keys=True).encode()), "original native words")
    return [
        "exchange the two signed exact products",
        "change an unplotted atom while preserving all signed quotients",
        "reverse a measured Rust sign",
        "change one accepted binary digit in the original measured word",
    ]


def require_native_identity(blob):
    require(sha256(blob).hexdigest() == "83b84ef9299aef38991ddeb802886f8264cd5fdba558957375d74cf78288f958",
            "original native words")


def main():
    import argparse
    import runpy

    parser = argparse.ArgumentParser(description="Check the original saved calculations without a donor file or network.")
    parser.add_argument("--recorded", action="store_true", required=True, help="read the included scientific records")
    parser.add_argument("--self-test", action="store_true", help="also require four distinct altered inputs to fail")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    outputs = root / "checked"
    for mode in ("ordinary", "optimized"):
        support = (outputs / f"support-{mode}.json").read_bytes()
        lattice = (outputs / f"lattice-{mode}.json").read_bytes()
        summary = checked_bytes(support, lattice)
    rust = root / "rust"
    receiver = runpy.run_path(str(rust / "portable/compare.py"))
    native = (rust / "observed/native-words.json").read_bytes()
    require_native_identity(native)
    ten = receiver["compare"](receiver["strict_load"](native))
    measured = (json.dumps(ten, indent=2, sort_keys=True) + "\n").encode()
    expected = (rust / "observed/ten-results.json").read_bytes()
    require(measured == expected and sha256(expected).hexdigest()
            == "aaaf4420eb433e9706803859696ada6cfbb94488e2b3398f4dca18571495eace",
            "complete original ten bounded results")
    answer = {
        "source": "saved original records",
        "checked_original_modes": ["ordinary", "optimized"],
        "complete_rational_products": 108,
        "bounded_native_means_checked_from_saved_words": len(ten["measurements"]),
        "absolute_mass_nats_per_episode": summary["sum_absolute_signed_means_nats"],
        "rational_record_sha256": LATTICE_HASH,
        "support_record_sha256": SUPPORT_HASH,
        "ten_result_sha256": sha256(measured).hexdigest(),
    }
    if args.self_test:
        answer["refused"] = recorded_self_test(support, lattice, native, receiver)
    print(json.dumps(answer, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
