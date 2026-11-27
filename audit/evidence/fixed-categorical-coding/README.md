# Fixed physical categories and fitted bins

**Sepehr Mahmoudian · 2026.** Does the direct categorical shared-exclusions function require a fitted equal-width quantizer? The two- and three-source functions take matrices of categorical labels. A label can come from an instrument or from a specified map of measurements to states. The decomposition describes the encoded variables. The categorical construction is due to Makkeh, Gutknecht and Wibral. The fitted equal-width wrapper in pid-rs is a separate composition. Cite the title, year and exact revision of this note. [Defining paper, version 5](https://arxiv.org/abs/2002.03356v5) · [Method catalog](../../../METHODS.md) · [Software citation](../../../CITATION.cff)

The earlier three-source API text required the fitted equal-width quantizer for continuous measurements. The earlier two-source text and two reader guides described only that route. This restricted the documented inputs beyond the type and event definition. The direct function counts rows that have equal states. A rule fixed in advance can assign the three states negative, zero and positive to the trend of a force sensor. Both choices of equality and treatment of a zero trend must be explicit. The published wrist analysis gives the trace length, slope formula, axes, target labels and observed frequencies. [Rust entry points](../../../crates/pid-core/src/sxpid.rs) · [Worked sensor analysis](../../research/robot-wrist-slope-signs/EXPOSITION.md)

When bin edges depend on data, record which rows supplied those edges and how they were applied. In a training and held-out evaluation design, estimate the edges on the training rows and retain them for evaluation. If the same rows supplied and evaluated a map, report that reuse. Inferring performance on new records requires separate evidence. A fixed map also requires a scientific reason for its units, boundaries and target. [Fitted transform assumptions](../../../crates/pid-core/README.md)

## Recompute an eight-record example

Measure a value twice at each of three sensors. Set a sensor's label to one if the second value exceeds the first, and to zero otherwise. All eight possible three-bit rows occur once. One of the assigned zeroes comes from equality of the two readings. Let the target equal the first sensor's label. This example is a designed empirical distribution. Its two target states have probability one half each.

With all three encoded sensors the target is known. Its mutual information with the source tuple is therefore the natural logarithm of two, in nats. If the first source is replaced by a constant, the other two are independent of the target and the mutual information is zero. Giving each state a different integer name within each sensor preserves the events used by the categorical construction. The direct Python function returned 18 atom entries. Their informative, misinformative and signed fields matched under this relabeling. The observed difference was zero in each binary64 field. A raw floating-point source matrix at the same entry point raised a type error.

Run the two commands with the pid-rs Python package and NumPy installed.

```sh
python3 -I -B audit/evidence/fixed-categorical-coding/example.py
python3 -I -B -O audit/evidence/fixed-categorical-coding/example.py
```

The recorded runs used the same native wheel, with SHA-256 `860d42953cc2f58a5d42c6f4eb9bd401ef82bed48af3dba429c52b428eaed3ad`. It was compiled at `927e5138d23e0bd24b70f8df0fd38e610456a244`. The original Cargo manifests, lock file and crate tree matched `89d2051396a5159feaa00569363ca72267c4ae44`. The wheel enabled the experimental Python bindings and the example called the stable direct categorical entry point. The stored result includes the wheel identity. A repeat with a local installation reports the measured fields. These eight rows and the two interpreter modes check one implementation example. The correction follows from the declared input and the definition of equality on its states. [Source example](example.py) · [Native return](native.json)
