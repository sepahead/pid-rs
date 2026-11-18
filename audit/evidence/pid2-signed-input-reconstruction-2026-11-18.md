# Signed MI inputs and two-source atom reconstruction

Sepehr Mahmoudian, 2026. Cite this record with the exact repository commit or release. [Software citation](../../CITATION.cff).

Does clipping a negative estimated mutual information before constructing the two-source atoms necessarily break their sum? The position of the edit matters. The component estimates specify the scientific result. The atom equations determine which coordinates that result reconstructs.

## Supplied coordinates and a worked example

Let $r$ denote redundancy, $a$ and $b$ the mutual information estimates for each source with the target, and $j$ the joint-source mutual information estimate. All four inputs are signed real coordinates in nats for this calculation. The two-source equations give the ordered atoms $(r,a-r,b-r,j-a-b+r)$, comprising redundancy, the two unique contributions and synergy. Their sum is $j$ for every supplied tuple. At the population level mutual information is nonnegative. Finite-sample KSG estimates can be negative. The numerical example illustrates the coordinate map and asserts no underlying distribution or estimator realization. [Ehrlich et al., Section II, Eq. (1)](https://arxiv.org/html/2311.06373v3#S2), [version of record](https://doi.org/10.1103/PhysRevE.110.014115).

| Operation | Ordered atoms in nats | Sum in nats |
|---|---|---:|
| Construct from $(r,a,b,j)=(1,-1,2,3)$ | $(1,-2,1,3)$ | 3 |
| Replace $a$ by zero, then construct all atoms | $(1,-1,1,2)$ | 3 |
| Construct from the original inputs, then replace only the negative unique atom by zero | $(1,0,1,3)$ | 5 |

Increasing $a$ by any amount raises its unique contribution and lowers synergy by the same amount. Changing $j$ changes synergy and the total by that amount. Thus clipping a negative $j$ to zero makes the atoms sum to zero relative to the new input. Editing a finished atom without compensating elsewhere changes the original sum by the edit. Co-information $a+b-j$ also changes when a single contributing MI estimate is altered. The experimental Python invariant dictionary computes this alternating sum with compensated summation, so an ordinary binary64 re-evaluation can round differently. These distinctions explain the project policy of preserving the signed estimates for computation and allowing a separately identified scalar presentation transform.

## Existing proof and numerical boundary

The existing Z3 reconstruction obligation tests the negation of the sum identity with four unrestricted reals. It includes tuples obtained by any prior input substitution. A second obligation also checks that redundancy plus each unique atom recovers its corresponding supplied marginal. The repository's represented-coordinate report states the same algebra and documents its binary64 execution separately. [Reconstruction obligation](../../audit/formal/z3/pid2-reconstruction.smt2), [marginal and joint obligation](../../audit/formal/z3/pid2-self-redundancy-mobius.smt2), [numerical assurance, Section 3](../../PID2_REPRESENTED_COORDINATE_ASSURANCE.md).

## Rust implementation and computational cost

Under `experimental-continuous`, the Rust continuous PID2 path forces `NegativeHandling::Allow` when it obtains its KSG inputs. `Pid2Result::from_estimate` subtracts redundancy for each unique atom. It computes synergy by summing the four represented operands exactly and rounding once to binary64. Even correctly rounded atoms can reconstruct different represented coordinates. The constructor checks the two marginal reconstructions and the joint reconstruction against an inclusive 32-position ordered-binary64 guard, and can return a numerical error. After obtaining the four estimates, this fixed-width construction uses constant work and storage. Obtaining the inputs has separate sample-size, dimension and resource requirements. No new timing is reported. The guard is a compatibility policy. An accepted value near zero can still have large relative error. [Rust implementation](../../crates/pid-core/src/pid2.rs), [revision-4 checker](../../scripts/check-pid2-represented-coordinate-v4.py).

At `1479fc5e0ca15e5ef9c5521f8bc7aa36f2a98d20`, contributor guidance, a catalog constraint and several code comments attributed the sum identity to signed input handling. This review corrects that explanation. It retains the estimator policy, function signatures, arithmetic, rejection behavior and existing proof obligations. Reopen if the atom map, treatment of estimated inputs, scalar presentation policy or binary64 reconstruction changes. The source inspection and existing tests establish neither estimator calibration nor independent human review. The inspected arXiv v3 HTML bytes have SHA-256 `8684a3d66ee4846645f1acc85d9c355acbf538c73a07b944f138ff47316a996f`.
