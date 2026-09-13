---
title: "What the finite-horizon bias bounds tell you"
subtitle: "Categorical MGW shared exclusions · five exact formal families"
author: "pid-rs contributors"
date: "8 September 2026"
lang: en
---

For a **fixed categorical MGW atom**, a **fixed raw horizon** $h$ and **iid complete source-and-target rows**, five accepted Lean statements bound the difference between the population atom and the expectation of a specified prefix statistic. Sources and target may depend within each row. One block uses a fresh anchor and $h$ further rows. All information quantities are in nats.

Let $\theta$ be the atom, let $B_h$ be the native block statistic, and define $e_h=\theta-\mathbb E[B_h]$. Conventional statistical bias has the opposite sign. For supported anchor $z$, put $a_z=P(\text{source query})$, $v_z=P(\text{target match})$ and $q_z=P(\text{query and target match})$. The query has an OR between source collections and an AND within each collection.

The supported population moments $K_a=\mathbb E[1/a]$, $K_q=\mathbb E[1/q]$ and $K_T=\mathbb E[1/v]$ give

$$
-\frac{K_q-K_T}{h+1}\le e_h\le\frac{K_a-1}{h+1},
\qquad
|e_h|\le\frac{K_q-1}{h+1}.
$$

For **any member collection** $C$ of the chosen node, let $K_C$ and $K_{CT}$ be the positive population support counts of its source projection and source-target projection. Then

$$
-\frac{K_{CT}-K_T}{h+1}\le e_h\le\frac{K_C-1}{h+1},
\qquad
|e_h|\le\frac{K_{CT}-1}{h+1}.
$$

A justified population floor $q_z\ge\eta$ with $0<\eta\le1$ gives the potentially faster bound

$$
|e_h|\le\frac{(1-\eta)^{h+1}}{(h+1)\eta}.
$$

These are useful **sufficient fixed-horizon planning bounds** when their population inputs are known. A small source-target projection can give a better support bound than the full multivariate alphabet. An observed category count or smallest observed frequency cannot replace a population count or floor without additional evidence.

The bounds may be conservative. Constant sources have zero signed error even when $K_q$ is large. Overlapping queries can have a noninteger moment such as $K_q=4/3$; they are not projection fibers. For one fair source independent of a fair target, $\mathbb E[B_1]=1/4$ although $\theta=0$. A positive short-prefix mean is not evidence of nonzero population information by itself.

The result controls **mean truncation error**, not sampling variation, confidence coverage, stopping, implementation accuracy or downstream utility. Binning changes the estimand to the resulting categorical law. Same-sample fitting, serially dependent rows and continuous or hyperbolic PID require separate arguments. For a prediction task or a one-source relation, direct task loss or MI may be the better starting point.

See the [complete derivation and four worked examples](EXPOSITION.md), the [exact theorem map](THEOREM_MAP.md), and the defining [MGW v5 paper](https://arxiv.org/abs/2002.03356v5). Formal acceptance is local; public production and hosted replay remain separate. No novelty or superiority claim follows.
