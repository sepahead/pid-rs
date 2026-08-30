# Third-party notices

This repository's project-authored material is licensed as stated in
[`README.md`](README.md), except where a file carries a more specific notice. The mathematical
results guide uses the Pandoc template projections described below. It and the separate SxPID3
source-marginal audit use the embedded font subsets described below. The complete input font files
are not stored in this repository.

## Pandoc 3.1.3 and 3.10.2 LaTeX projections

`scripts/normalize-mathematical-results-guide-pandoc-tex.py` is distributed under the BSD
3-Clause license. Its project-authored validation and custody logic embeds exact fragments of the
Pandoc 3.1.3 and 3.10.2 LaTeX template projections. The repository retains the exact BSD notice
that is byte-identical at both upstream tags in
[`pandoc-templates-bsd-3-clause-3.1.3-and-3.10.2.txt`](audit/formal/latex/mathematical-results-guide/pandoc-templates-bsd-3-clause-3.1.3-and-3.10.2.txt).
That retained file has SHA-256
`cf5b70694cf50403b51f3315f98d010de6435022ff984911819219034a088180`.

The upstream `pandoc-templates` tag locators are
[`3.1.3` (`c8798e9…`)](https://github.com/jgm/pandoc-templates/tree/3.1.3) and
[`3.10.2` (`5f26b7a…`)](https://github.com/jgm/pandoc-templates/tree/3.10.2).
Pandoc's heading-writer change is anchored by
[issue #8744](https://github.com/jgm/pandoc/issues/8744) and
[commit `70329ed…`](https://github.com/jgm/pandoc/commit/70329edcd7afb7b3f8f015b13ab2e734c9e31d05).
The unnumbered-longtable change started in
[commit `e13aa5c…`](https://github.com/jgm/pandoc/commit/e13aa5c0157744de262ac512cc95a76a4562e37b).
[Commit `d835461…`](https://github.com/jgm/pandoc/commit/d8354618c43ceb7ec917608229bdbf673c2469ad)
then added the exact `none` counter and `LTcaptype` form used here and closed
[issue #11201](https://github.com/jgm/pandoc/issues/11201).

These locators and retained bytes establish bounded source provenance. They do not authenticate
an installed Pandoc executable, establish general equivalence between Pandoc releases, or prove
PDF accessibility. In particular, the normalized TeX image option does not establish a PDF
`/Alt` entry, an accessible figure, or PDF/UA conformance.

## Source Sans Pro 3.006

The accepted OpenType font programs report this font-program metadata: Copyright © 2010–2019
Adobe Systems Incorporated, with Reserved Font Name “Source”. Source Sans Pro is licensed under
the SIL Open Font License 1.1. This repository retains an exact local copy of the installed TeX
Live package's [OFL 1.1 license file](audit/formal/latex/mathematical-results-guide/font-licenses/source-sans-pro-ofl-1.1-tex-live-2024.txt);
the general license is also available from the [SIL Open Font License
site](https://openfontlicense.org/). The upstream project is
[adobe-fonts/source-sans](https://github.com/adobe-fonts/source-sans). The regeneration contract
records release `3.006R`, its upstream commit locator, and the exact accepted bytes for these input
programs:

- `SourceSansPro-Regular.otf`
  (`7134d229b15cdd0827376d8a24f6f531f616eb1b3fecd16e1cf8a86d0bf6bc51`)
- `SourceSansPro-Semibold.otf`
  (`aa53ed4fc17334a0c2ee8412c1e4e728bfb732a96b119164f7354343dad8f2f2`)
- `SourceSansPro-Bold.otf`
  (`daccddbe3dd60fe10f6e8a785eda187925da6b611141024dffa43626998dfc7c`)

The installed TeX package `LICENSE.txt` begins with a generic “Copyright 2010, 2012” package
license header. That retained file is evidence for the license text shipped in the observed TeX
Live installation. Its generic header is not substituted for, and does not supersede, the
2010–2019 copyright metadata in the three accepted OTF programs.

## Latin Modern Sans 2.004

Copyright © 2003–2009 Bogusław Jackowski and Janusz M. Nowacki, on behalf of TeX Users Groups.

Latin Modern is released under the GUST Font License. This repository retains exact local copies
of the installed TeX Live package's [GUST Font License
1.0](audit/formal/latex/mathematical-results-guide/font-licenses/gust-font-license-1.0-tex-live-2024.txt)
and [Latin Modern v2.004
manifest](audit/formal/latex/mathematical-results-guide/font-licenses/manifest-latin-modern-2.004-tex-live-2024.txt).
The retained GUST Font License states that LPPL 1.3c-or-later conditions apply and adds a request,
which it says is not legally required, to rename fonts and manifest-listed files in derived works.
The repository's LPPL copy is [here](LICENSE-LPPL-1.3c). The GUST license is also available from
[TUG](https://tug.org/fonts/licenses/GUST-FONT-LICENSE.txt), and the upstream project is [GUST
e-foundry Latin Modern](https://www.gust.org.pl/projects/e-foundry/latin-modern). The regeneration
contract accepts these exact input programs:

- `lmsans10-regular.otf`
  (`d431b786b9b603662718e79cfe9b441f47a8b0b3e854dde89d5acb3ed7cfd682`)
- `lmsans10-bold.otf`
  (`a597b710326c1a8a2c7238d808e5d38711638a72a32383478db4829d63afd687`)

The local license and manifest files preserve the exact installed-source bytes recorded by the
regeneration contract. These files and hashes identify observed or accepted bytes. They do not
authenticate a download, distribution package, maintainer, upstream history, or legal conclusion,
and this notice is not legal advice. See
`audit/formal/latex/mathematical-results-guide/open-font-figure-regeneration-v1.json` for the
bounded regeneration and provenance record.
