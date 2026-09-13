---
title: "What the finite-horizon bias bounds tell you"
subtitle: "Categorical MGW shared exclusions · five exact formal families"
author: "pid-rs contributors"
date: "8 September 2026"
lang: en
---

For a **fixed finite categorical MGW atom**, a **fixed raw horizon** $h$ and **iid complete source-and-target rows**, five locally accepted Lean statements bound mean truncation error. Within-row dependence is allowed. Each block uses a fresh anchor and $h$ further rows from the same law. Information is in nats.

Let $p(z)$ be the complete-row population PMF, $\theta$ the atom and $B_h$ the [Section 3 prefix statistic](EXPOSITION.md). Define $e_h=\theta-\mathbb E[B_h]$, opposite in sign to conventional bias. At each anchor with $p(z)>0$, let $a_z=P(\text{source query})$, $v_z=P(\text{target match})$ and $q_z=P(\text{query and target match})$. The query ORs source collections and ANDs matches within each collection.

The supported population moments $K_a=\sum_{z:p(z)>0}p(z)/a_z$, $K_q=\sum_{z:p(z)>0}p(z)/q_z$ and $K_T=\sum_{z:p(z)>0}p(z)/v_z$ give

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

A justified population floor $q_z\ge\eta$ for **every** anchor with $p(z)>0$, with $0<\eta\le1$, gives the potentially faster bound

$$
|e_h|\le\frac{(1-\eta)^{h+1}}{(h+1)\eta}.
$$

These are **sufficient fixed-horizon planning bounds** for known population inputs. Small source-target projections may improve the support bound. Observed category counts or minimum observed frequencies cannot replace population support counts or floors without further evidence.

The bounds can be conservative: constant sources have zero signed error even with large $K_q$. Overlapping queries need not be projection fibers: $K_q=4/3$ is possible. For one fair source independent of a fair target, $\mathbb E[B_1]=1/4$ while $\theta=0$. A positive short-prefix mean alone does not show population information.

The bounds control **mean truncation error**. Sampling variation, confidence coverage, stopping, implementation accuracy and utility remain open. Binning changes the estimand to the resulting categorical law. Same-sample fitting, serial dependence, continuous PID and hyperbolic PID need separate arguments. For prediction or a one-source relation, consider direct task loss or MI.

See the [derivation and four worked examples](EXPOSITION.md), [theorem map](THEOREM_MAP.md), and defining [MGW v5 paper](https://arxiv.org/abs/2002.03356v5). Local formal acceptance is separate from public integration and hosted replay. No novelty or superiority is claimed.
