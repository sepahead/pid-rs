# Symbols and reading conventions

This map applies to [the exposition](EXPOSITION.md) and its [thirteen-target table](SOURCE_CORRESPONDENCE.md).
No symbol in the logical sections denotes an estimated numerical information quantity.

| Symbol or word | Meaning | Domain or caution |
|---|---|---|
| $I$, $i$ | Source index set and one source index | Examples use one-based indices. The generic theorem permits an arbitrary index type; categorical targets require a finite type. |
| $a,b,c$ | Collections: finite sets of source indices | A collection is one AND branch. |
| $\alpha,\beta,\gamma,\lambda,\rho$ | Finite families of collections | A family is an OR of its branches; double braces are meaningful. |
| $a\subseteq b$ | Every member of $a$ belongs to $b$ | Equality is allowed. This is ordinary subset inclusion. |
| $\alpha\preceq\beta$ | For each $b\in\beta$, some $a\in\alpha$ satisfies $a\subseteq b$ | Reverse logical implication; it is not ordinary inclusion between the two families. |
| Antichain | Comparable members of a family must be equal | Requires pairwise inclusion minimality, not disjointness. Collections may overlap. |
| $e$, $e_i$ | Boolean pattern and its value at index $i$ | Values 0/1 correspond to Lean `false`/`true`. |
| $F_\alpha(e)$ | Some collection in $\alpha$ has value 1 at every selected index | A proposition, named `DNF` in Lean. It is not a cumulative numerical PID function. |
| $\mathcal X_i$ | Alphabet of source $i$ | Categorical targets allow a different finite alphabet for each source. |
| $\mathcal T$ | Target alphabet | Separate from every source alphabet. |
| $\Omega$ | Full product of source alphabets and target alphabet | An ambient key space, not automatically the positive-mass support of a law. |
| $x=((x_i),u)$ | A candidate complete key | It has a source tuple and a target value. It is not necessarily an observed row. |
| $z=((s_i),t)$ | Fixed anchor key | Supplies the source values and target value used for comparisons. |
| $e_z(x)_i$ | 1 if $x_i=s_i$, otherwise 0 | Equality flag, not the raw source value or a correctness score. |
| $B_a(z)$ | Keys that match the anchor at every index in collection $a$ | No source outside $a$ is constrained; target is unrestricted. |
| $E_\alpha(z)$ | Union of $B_a(z)$ over $a\in\alpha$ | Full ambient source event before domain restriction. |
| $T_z$ | Keys with target value $t$ | Same event on both sides of C6. |
| $D$ | Specified subset of $\Omega$ | Identify whether it is the full alphabet, known support, or empirical support. |
| $r_i$ in Eq. (8) | Supplied alternate source value with $r_i\ne s_i$ | Alphabet element, not collection $a$. The subscript and Eq. (8) scope distinguish the notation. |
| $p$ | Declared finite probability mass function on $\Omega$ | No particular probability law is assumed by G1–B4. |
| $\widehat p$, $n_x$, $N$ | Empirical mass, observed count at a key, positive total sample count | $\widehat p(x)=n_x/N$. Sample support need not equal population support. |
| $\mathrm{supp}(p)$ | Keys of strictly positive mass under $p$ | This finite-alphabet convention avoids ambiguity about topological support. |
| $i^{\mathrm{sx}}_\cap(t:\alpha)$ | MGW pointwise shared-exclusions information at the anchor, in Eq. (10) | Natural-log version in nats; outside the thirteen formal targets. |
| $\ln$, nats | Natural logarithm and its information unit | Source MGW uses base 2; bits multiplied by $\ln 2$ give nats. Pure event statements are unit-free. |

## Literal examples and Lean's indices

The text names the three sources 1, 2, and 3. The fixed Lean witnesses use `Fin 3`, whose values
are 0, 1, and 2. The translation is reader index $j$ = Lean index $j-1$.

| Text object | Exact contract object |
|---|---|
| $\lambda=\{\{1\}\}$ | `singletonLeft = {{0}}` |
| $\rho=\{\{2\}\}$ | `singletonRight = {{1}}` |
| $\gamma=\{\{1\},\{1,2\}\}$ | `absorbedFamily = {{0}, {0, 1}}` |
| One-value source and target alphabets | `Unit`; its sole element is `()` |
| Binary source anchor 000 | `binaryAnchor` has `false` at each source and `()` at the target |
| Diagonal raw rows 000 and 111 | `binaryDiagonal`: source 0 equals source 1, and source 1 equals source 2 |
| Ambient distinguishing raw row 011 | Source 0 is `false`; sources 1 and 2 are `true` |

When a string follows “raw row,” its digits are categorical source values. When it follows
“pattern” or $e$, its digits are equality flags. At source anchor 000, raw row 011 gives
pattern 100. At source anchor 00, raw row 01 gives pattern 10.

For a zero-source generic index type, there is one Boolean pattern (the empty function). The
empty family and the family containing the empty collection still represent false and true.
The nonempty-collection PID carrier is empty in that zero-source setting. The present note does
not use it as a PID example or assume a nonempty source set where the generic target has none.
