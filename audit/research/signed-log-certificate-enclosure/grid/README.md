# Outward rounding on a signed integer grid

Sepehr Mahmoudian, 2026.

The verifier computes two signed integers before its final division, the lower numerator $l$ and the upper numerator $u$, with $l\leq u$. A positive integer $d$ gives the number of numerator units in one output unit. How wide can the reported interval become when each endpoint rounds outwards? This result describes the last division in an exact finite count verifier. It also applies to negative endpoints.

Let $\lfloor t\rfloor$ denote the greatest integer at most $t$, and $\lceil t\rceil$ the least integer at least $t$. Define $W=\lceil u/d\rceil-\lfloor l/d\rfloor$. Write $s=l-d\lfloor l/d\rfloor$. Then $0\leq s<d$, including when $l$ is negative. Substitution gives $W=\lceil(s+u-l)/d\rceil$. Among all ordered integer numerators with $u-l\leq h$ for an integer $h\geq0$, the largest width is $\lceil(d-1+h)/d\rceil$. Choose $l=d-1$, $u=l+h$ to attain it.

1. A raw gap of at most $d+1$ guarantees $W\leq2$. A gap of $d+2$ can give three. For $d=4$, the interval with numerators $[3,9]$ rounds to $[0,3]$.
2. Let the producer report a separate ordered interval $[a,b]$ with integer endpoints on the output grid. Suppose $[ad,bd]$ intersects the raw interval and $u-l\leq d$. Then $[a-1,b+1]$ contains both rounded endpoints. The gap limit is sharp if the guarantee must hold for every $a\leq b$. Take $[a,b]=[0,0]$ and raw numerators $[-d-1,0]$. With $d=4$, the lower endpoint rounds to $-2$.
3. In the finite categorical verifier let $N\geq1$ be the total count and $d=N2^{24}$. **Assume** $u-l\leq1385(1+80N)$. The stock proof derives $u-l<d$ and $0\leq W\leq2$. The separate count-table argument derives this input inequality under an occupied-support limit of 1,024 and the declared exact integer procedure. The integer proof alone says nothing about an interval for a real logarithm.

The accompanying model uses Lean's integer Euclidean division. The upper endpoint is the negative of the floor of the negative numerator. The nine declarations in the namespace GridProof establish the ceiling comparison, residue identity, attained maximum, two-unit bound, next wider example, padded containment, its sharp threshold, a one-cell implication and the conditional count bound. The named sources give every type and proof. The observer prints the full named terms and their transitive axioms. The underlying kernel terms can refer to compiler-generated auxiliary declarations in the same module. Stock fresh replay checks the safe declarations submitted from the three newly compiled modules. It uses the imported stock libraries. Every named theorem in the successful attempt uses propositional extensionality and the quotient soundness axiom.

With Python 3.14 and the original unpacked official Apple arm64 Lean 4.34.1 release, run the following command from this directory. Supply a new directory for each output.

~~~sh
python3.14 -I -S -B replay.py --toolchain /path/to/lean-4.34.1-darwin_aarch64 --out /path/to/new-output --history
~~~

The replay checks the source, stock files, native exits, output bytes, object identities and per-theorem axioms. Four deliberately false numerical statements must fail at their specified proposition. A separate check compares 4,464 signed integer intervals with the original division code. These comparisons describe finite executions. The universal result follows from the named proof under its assumptions.

Two prior attempts failed under the first criterion, one at proof compilation and one at the observer's type-class search. Under the second criterion the first proof used the prohibited choice axiom. Its replacement first left the goal $0\leq0$ open. The following proof closed it directly. Both ordinary and optimized Python executions checked the selected proof. The original failed predicates, proof payloads, native transcripts and candidate selection are retained. The Python spelling of an unordered set in the old choice diagnostic can vary between runs. The replay checks the exact declaration and the exact three members of that set. All nonempty native streams are compared byte for byte. These results have model-assisted review on shared sources. Human scientific review and a refinement from the original program to the Lean definitions remain open.

Cite Sepehr Mahmoudian, *Outward rounding on a signed integer grid* (2026), and give the exact repository commit or release. The finite categorical partial information decomposition is due to Makkeh, Gutknecht and Wibral. [Defining paper](https://doi.org/10.1103/PhysRevE.103.032149) · [Software citation](https://github.com/sepahead/pid-rs/blob/927e5138d23e0bd24b70f8df0fd38e610456a244/CITATION.cff)
