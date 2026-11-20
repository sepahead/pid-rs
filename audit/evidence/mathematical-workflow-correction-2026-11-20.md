# Corrected printing of the mathematical workflow, 20 November 2026

Sepehr Mahmoudian. *Mathematical Problem-Solving Workflow*. November 2026 corrected printing. A citation identifies the exact repository commit or release. [Workflow PDF](../../output/pdf/mathematical-problem-solving-workflow.pdf) · [Software citation](../../CITATION.cff)

The cover dates the protocol edition “1 September 2026; revised 26 October 2026”. The November printing corrects the subsection “SxPID definition-compatibility firewall” on page 73. The correction specifies when a pair of examples rules out recovery of total mutual information. [Workflow source](../../MATHEMATICAL_PROBLEM_SOLVING_WORKFLOW.md)

## Two systems with different amounts of information

A **source** supplies observations. The **target** is the set of quantities of interest, treated as one ordered list. **Total mutual information** measures how much the sources together reduce uncertainty about the target. The unit here is the bit. A **fair bit** has two equally probable values, 0 and 1.

Lyu, Clark and Raviv give two systems, **hat** and **tilde**. Each target has three bits. The sources together determine all three target bits. In this case, total mutual information equals the target’s **joint entropy**, its uncertainty before the observations. [Primary source, Definition 6 and Lemmas 4–5](https://arxiv.org/html/2604.03869v2#S4)

| System | Equally probable joint source states | Target values | Total mutual information |
|---|---:|---|---:|
| Hat | 64 | Three independent fair bits give eight equally probable target values. | 3 bits |
| Tilde | 32 | The first two bits are independent and fair. The third is 1 exactly when they differ. There are four equally probable target values. | 2 bits |

For example, the tilde targets are 000, 011, 101 and 110. Two fair bits suffice to choose one of these four targets. The hat system needs three fair bits to choose one of its eight targets.

A **minimal recovering set** is a set of sources that determines a given target bit. No smaller subset of that set determines the bit. The authors group target bits that have the same family of minimal recovering sets. Their **descriptor vector** lists the joint entropy of each group. Each system has the same three nonempty groups, with one fair bit in each group. Their descriptor vectors agree, although their total mutual information differs. [Definition 6 and the two systems](https://arxiv.org/html/2604.03869v2#S4)

## When another decomposition can distinguish the systems

A **partial information decomposition** assigns values to information components called atoms. Its **atom vector** lists these values in a fixed order. A **decoder** is a deterministic function that assigns one output to each input atom vector.

Can a decoder return the correct total mutual information for both systems? It can do so exactly when their atom vectors differ. For different vectors, the decoder can return 3 bits for the hat vector and 2 bits for the tilde vector. Equal vectors would require the decoder to return two outputs for one input.

Suppose a single function calculates the atom vector from the descriptor vector for every system. This relation is **factorization through the descriptor vector**. It suffices to make the two atom vectors equal. A common list of atom labels alone does not determine the values. In the finite shared-exclusions calculation, eight of eighteen atom values differ. The sum of all eighteen atom values gives the correct total mutual information for each system. [Foundational study and finite comparison](../../FOUNDATIONAL_SHARED_EXCLUSIONS_PID_AUDIT.md)

A three-input example shows why factorization is unnecessary for equality on a selected pair. Give all three inputs a descriptor value of 0. Give them atom values 0, 0 and 1 and required totals 3, 2 and 2. The first two inputs already rule out a decoder. No function of the single descriptor value can produce both atom values. This example concerns functions on three abstract inputs. [Derivation and scope](../../FOUNDATIONAL_SHARED_EXCLUSIONS_PID_AUDIT.md)

The structural preprint supplies the hat and tilde systems. A separate journal paper by the same authors uses other hypotheses. [Structural preprint, fixed revision](https://arxiv.org/abs/2604.03869v2) · [Distinct journal paper](https://doi.org/10.1103/8rzp-w5z1)

## Publication checks

A local build reached its memory limit. An earlier hosted build moved two named destinations on page 74 and failed the coordinate check. The November printing passed that same check. The hosted process produced identical PDF bytes twice. Its source commit is `6d088576e0fbe88454a32d7e9869e6cb073f9abb`. [Earlier hosted build](https://github.com/sepahead/pid-rs/actions/runs/44700285550) · [Accepted hosted build](https://github.com/sepahead/pid-rs/actions/runs/44718660235)

Both hosted editions have 87 pages. All 91 outline entries, 232 named destinations and 247 link annotations agree, including destination positions and link rectangles. When the same host rebuilt both editions, only page 73 changed at normal size.

The released October images supply a second comparison. Pages 6, 10, 12 and 73 changed in color and grayscale. The November review used the original October records for 166 identical page images. It records fresh observations for the eight changed images and ten high-resolution images. [November visual receipt](mathematical-workflow-visual-receipt-2026-11-20.md)
