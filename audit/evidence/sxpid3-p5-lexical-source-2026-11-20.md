# Current and historical sources for the three-source lexical check

Sepehr Mahmoudian · 20 November 2026

The three-source P5 checker follows the named Rust functions that connect 18 antichains to their stored result order. Its source record includes all bytes inside the braces of `discrete_mobius_inversion_3`. A correction to the comment explaining its traversal changed that record. The traversal selects a node with no remaining strict predecessor and breaks ties by input index. The older comment described the choice using the number of sets in a node. [Published reproduction commands](../../SXPID3_SOURCE_MARGINAL_AND_BOUNDED_AUDIT.md#12-reproduction-entry-points) · [Rust source](../../crates/pid-core/src/discrete_pid.rs)

The historical checker and source files at `1be1ec235f2c0ed0e874864e98e8ef4dedaa5bcc` reproduce the August lexical result. Against the corrected Rust source at `0f3122a96e48a099581ad4faf3e3d5d9138367f6`, that checker exited 1 on its manifest digest. The current checker accepts a single revised manifest. Its only changed manifest field is the complete braced function's SHA-256. Replacing the comment in either direction reproduces the corresponding function digest. The historical and current checkers reject one another's source, and a third comment inside the same function was also rejected. [August source receipt](sxpid3-bounded-keyed-scalar-audit-expressions-receipt-v1-2026-08-26.json)

| SHA-256 identity | August source | Current source |
|---|---|---|
| Complete braced function | `72c57cb0372d90aab533b7701e944f0d4bc340ee68826ec6fc2720b9e212ad20` | `e24ae4ec2fd41fde3f3be2c57a28fa7ba66c2b2351edfe71194d4d0721837c11` |
| Lexical manifest | `e0ef5a05bbade1ccbd83767ee0e1e39f05276790bb2b433dd8e5fff7ea83046a` | `cc7243f01137661c674a1b2c9c213851078f0822947d957f2984364582419282` |
| Checker stdout | `a8cdab4307bf3bc46b03ad6487282a5ab4f0768959d1370f008860de978f22d0` | `9bbf6bf401575c51db09ef8c2ee152e0decd7470b4d6a30dce5aa327316b70e3` |

To reproduce a column, use a checkout containing that version of both the checker and its inputs. Run these two commands from the current checkout.

```sh
python3 -I -S -B scripts/check-sxpid3-p5-rust-source-route.py
python3 -I -S -B scripts/check-sxpid3-p5-rust-source-route-self-test.py
```

Repeat both with `-O`. From a separate checkout at the August commit the same commands reproduce the original column. When both checkouts are available, pass `--repo-root` pointing to the other column's checkout to either production checker. The expected exit is 1 with `ROUTE.manifest_sha256`. The hostile suite retains its 54 mutations, Python-flag and source-stability controls. These observations concern source spelling and positional order. The committed receipt retains its original status. The separate Program A reconstruction retains its recorded partial status and zero of five programs closed. [Lexical checker](../../scripts/check-sxpid3-p5-rust-source-route.py) · [Hostile suite](../../scripts/check-sxpid3-p5-rust-source-route-self-test.py)
