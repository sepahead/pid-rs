# Retained source-mask and array-order failure

## Exact witness

Use binary cell order $8s_1+4s_2+2s_3+t$ and

```text
c[0] = 1, c[2] = 1, all other counts = 0.
```

The supported states are $(0,0,0,0)$ and $(0,0,1,0)$. They agree on $S_1,S_2$ and differ on
$S_3$.

At certificate key `03`, mask $3=\{S_1,S_2\}$, both rows lie in the keyed event:

$$
Q^+_{03}=Q^-_{03}=1.
$$

At certificate key `04`, mask $4=\{S_3\}$, only the keyed row lies in the event:

$$
Q^+_{04}=Q^-_{04}=4.
$$

Thus swapping mask bits 3 and 4, or comparing the current specialized Rust array positionally with
the certificate registry, changes an exact product from one to four.

## Why this is a live boundary

The certificate order is

```text
(1), (2), (3), (4), ...
```

The current specialized Rust order is

```text
(1), (2), (4), (3), ...
```

and the general $n$-source enumeration has a third positional order. These can all represent the
same lattice when keyed by their sorted mask sets. Positional equality is nevertheless false.

## Regression requirement

Every comparison must:

1. remove no nonzero mask and admit no padded zero as a semantic member;
2. sort masks within the antichain;
3. construct the stable key from the sorted set;
4. reject duplicate or missing keys; and
5. compare products, intervals, and atoms by key.

A test that first reorders both arrays with the same potentially wrong lookup table remains
correlated. At least one route must derive the key directly from source-mask membership.
