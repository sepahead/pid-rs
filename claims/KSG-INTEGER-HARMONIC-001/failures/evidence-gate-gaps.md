# Retained failures: custody, shadowing, and serial/parallel evidence gates

## Fixture-generator relationship is not locally bound

The fixture currently embeds the live generator SHA-256 and a separate no-write generator replay
passes. The standalone claim checker nevertheless reads only fixture bytes, their sidecar, and
selected counts. The Rust KSG fixture type omits the generator field. Thus the relationship is
enforced by a separate CI step, not by either local consumer that claims the fixture as evidence.

The correction is to hash live generator bytes in both consumers and add generator-drift and
resealed-metadata mutations. This strengthens custody but does not make the generator
mathematically independent of the shared harmonic identity.

## Live code can preserve markers and change semantics

The source checker masks comments and strings, so its named decoy mutations are useful. It then
checks marker presence rather than Rust def-use. For example, the following retains the required
`upper` marker but changes the value used later:

```rust
let upper = x.max(y);
let _ = upper;
let upper = x;
```

Likewise, this retains the required compensated output marker but replaces the final table value:

```rust
out[argument] = sum + correction;
let _ = out[argument];
out[argument] = sum;
```

Add both as baseline-first source-only mutations, reject duplicate audited bindings/writes, and
retain compiled corpus/tiny witnesses as the semantic backstop. Even after that correction, label
the checker textual rather than a compiler refinement proof.

## The frozen-reference file is not literally dual-mode

The file-level gate requires both `experimental-pipelines` and `parallel`, while its prose says the
same test runs in serial and parallel configurations. A `parallel`-enabled deterministic result is
not a separately captured serial oracle. Make the file available with `experimental-pipelines`
alone, retain test enumeration/output from that build, and then replay the identical constants
with `parallel`.

This closes one-target serial/parallel evidence only. It does not establish non-IEEE, x87
double-rounding, cross-architecture, or cross-platform bit identity.
