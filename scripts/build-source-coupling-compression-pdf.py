#!/usr/bin/env python3
"""Check the source-partition report through two retained exact-profile builds.

This is bounded source reproduction, not a native dependency closure, visual review,
scientific check or cross-toolchain relation. No existing output slot is reused.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import logging
import math
import os
from pathlib import Path, PurePosixPath
import re
import resource
import selectors
import shutil
import signal
import stat
import subprocess
import sys
import time
from urllib.parse import unquote, urlsplit
import warnings

ROOT = Path(__file__).resolve().parents[1]
ASSETS = "audit/formal/latex/source-coupling-compression/"
SOURCE = "audit/research/source-coupling-compression/EXPOSITION.md"
FIGURES = "audit/research/source-coupling-compression/figures/"
PDF = "output/pdf/source-coupling-compression.pdf"
JOB = "source-coupling-compression"
TITLE = "Source partitions and shared-exclusions information"
AUTHOR = "Sepehr Mahmoudian"
SUBJECT = "Finite categorical coupling bounds, exact conditional comparison and exposed recorded-data checks"
EPOCH = 1792800000
MAX_WORK_BYTES = 32 * 1024 * 1024
MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_LOG_BYTES = 512 * 1024
MAX_FILES = 1024
MAX_CHILD_SECONDS = 45.0
MAX_CAMPAIGN_SECONDS = 600.0
PDF_PIN = {"bytes": 152881, "sha256": "5bd3be5b2541f2c84e6e46bb6aa63aaafd1b145ef09e24b56d3e9dc51f597342"}
# Populated only from the reviewed public input packet before execution admission.
INPUTS: dict[str, dict] = {
    "audit/formal/latex/source-coupling-compression/fonts/LICENSE-latin-modern-math.txt": {
        "bytes": 1456,
        "sha256": "2bd69affc3da00715116f713f57eab9707e96daf3562ad0215987b15b9c16f73"
    },
    "audit/formal/latex/source-coupling-compression/fonts/LICENSE-latin-modern.txt": {
        "bytes": 1377,
        "sha256": "49ea6cb9257bbee0a3979c48a774cd221550ac1c20c95549efe45fc99cc18050"
    },
    "audit/formal/latex/source-coupling-compression/fonts/LICENSE-source-sans.txt": {
        "bytes": 4529,
        "sha256": "4a4a4179a96b5ef6786186d199f0d049b151352f460b8d2f3c00083792f37dd9"
    },
    "audit/formal/latex/source-coupling-compression/fonts/LPPL.txt": {
        "bytes": 19106,
        "sha256": "5f05fcf6ef25a6c31bccd2df7c0c46b23107bbeb2ce5cdba74efb5cc357f4dbb"
    },
    "audit/formal/latex/source-coupling-compression/fonts/NOTICE-latin-modern-math.txt": {
        "bytes": 4588,
        "sha256": "e6fdd5fb44b656146fa988d191f58901c09a347d3f4fbaa3b45b24a6ad7ec30b"
    },
    "audit/formal/latex/source-coupling-compression/fonts/NOTICE-latin-modern.txt": {
        "bytes": 33548,
        "sha256": "7cac4a4a78985ccb1ed429bb2eddf32eeb2e413c94493c7b268385bb7b525250"
    },
    "audit/formal/latex/source-coupling-compression/fonts/SourceSansPro-Regular.otf": {
        "bytes": 293200,
        "sha256": "7134d229b15cdd0827376d8a24f6f531f616eb1b3fecd16e1cf8a86d0bf6bc51"
    },
    "audit/formal/latex/source-coupling-compression/fonts/SourceSansPro-RegularIt.otf": {
        "bytes": 208408,
        "sha256": "d38e0d70cd4f4aa072457c5ae647b987f10c3cea34bff581ee358a7c2a526053"
    },
    "audit/formal/latex/source-coupling-compression/fonts/SourceSansPro-Semibold.otf": {
        "bytes": 295952,
        "sha256": "aa53ed4fc17334a0c2ee8412c1e4e728bfb732a96b119164f7354343dad8f2f2"
    },
    "audit/formal/latex/source-coupling-compression/fonts/SourceSansPro-SemiboldIt.otf": {
        "bytes": 210012,
        "sha256": "cdeddc767fdb11770451c5fac8f98b7d343b7fc9604f9db5034f50f7f437047a"
    },
    "audit/formal/latex/source-coupling-compression/fonts/latinmodern-math.otf": {
        "bytes": 733736,
        "sha256": "6075562b771f8b82f0c179e363389684f2dd09de30038269e2628e504bd7be0f"
    },
    "audit/formal/latex/source-coupling-compression/fonts/lmmono10-italic.otf": {
        "bytes": 63584,
        "sha256": "14e6328a5383d2b927c47051093ce0aff60deea07e6df71b8b99ee8d9c2ff8f2"
    },
    "audit/formal/latex/source-coupling-compression/fonts/lmmono10-regular.otf": {
        "bytes": 64684,
        "sha256": "22deb6d3be3ffcb40b33f0e010afb256c677d97c2a2bdee1f5740cdc97751558"
    },
    "audit/formal/latex/source-coupling-compression/fonts/lmmonolt10-bold.otf": {
        "bytes": 66332,
        "sha256": "2f4ae1bd30d4203a1c74c61d61dddbd5e2c2d5a7001d456b1b98e08b7c47ffb9"
    },
    "audit/formal/latex/source-coupling-compression/fonts/lmmonolt10-boldoblique.otf": {
        "bytes": 75300,
        "sha256": "a739b6deaafe0b9e8ae1eec9db1f425c52e1f6f483ca8e07e359bdd118310bba"
    },
    "audit/formal/latex/source-coupling-compression/fonts/lmroman10-bold.otf": {
        "bytes": 111240,
        "sha256": "102fe06c430a8b681b2bf6876b7cd967ae4d47b4b6b41d915eb7913b726d9fb1"
    },
    "audit/formal/latex/source-coupling-compression/fonts/lmroman10-bolditalic.otf": {
        "bytes": 118204,
        "sha256": "c37a28eed7a6e03f792b98b5e5f637b2fcda378bb4855f99284f1a88fe35f124"
    },
    "audit/formal/latex/source-coupling-compression/fonts/lmroman10-italic.otf": {
        "bytes": 118828,
        "sha256": "c1fce25075567bb8dbf2151658c3b442690041db17a2d49fc9e55905ea5b7169"
    },
    "audit/formal/latex/source-coupling-compression/fonts/lmroman10-regular.otf": {
        "bytes": 111536,
        "sha256": "1aa18cfefa58132c52ce5de70db1fd1154201c19cd2b2cdaffba4906a33e6852"
    },
    "audit/formal/latex/source-coupling-compression/pid-rs-report-tables.sty": {
        "bytes": 4051,
        "sha256": "90da44cc2cecf922bc755a5337fa1cd4fbc9681b558d6d33620837de807550a6"
    },
    "audit/formal/latex/source-coupling-compression/pid-rs-workflow-publication.sty": {
        "bytes": 8607,
        "sha256": "1e472a06a3c9ee7952e6485b42afd1ccbc65e98d2f7d947dfa5b6a8c4f7fd4c9"
    },
    "audit/formal/latex/source-coupling-compression/publication.tex": {
        "bytes": 1863,
        "sha256": "9b67e0c5ae502e311528c84ddd7f3a643a200b1f222a0f794639840e104bbc7e"
    },
    "audit/formal/latex/source-coupling-compression/report-filter.lua": {
        "bytes": 1161,
        "sha256": "3bc546bd0a225c613fee7fd6c429a0eea9d9f7f4e698c150cf7761e0bc8a66bf"
    },
    "audit/research/source-coupling-compression/EXPOSITION.md": {
        "bytes": 27318,
        "sha256": "53dd9a17a534e2fc408fa5018db24aaef8a7487ec0698103f3ae74daf51f7c5e"
    },
    "audit/research/source-coupling-compression/figures/allocation-comparison.pdf": {
        "bytes": 10090,
        "sha256": "1748b7748ea99381c565aea5d8e6aabb279ddde958b954548005ea67c49ae3de"
    },
    "audit/research/source-coupling-compression/figures/allocation-comparison.svg": {
        "bytes": 46933,
        "sha256": "f15a4e9d83158e3dc9edeadc083963fb8734b84571d736a26b88b8e976984580"
    },
    "audit/research/source-coupling-compression/figures/allocation-comparison.tex": {
        "bytes": 762,
        "sha256": "0e14173bcddeb7d3960c9722b26915e512469eecc655bf3c2ba4cf79ba821dfb"
    },
    "audit/research/source-coupling-compression/figures/allocation.dat": {
        "bytes": 127,
        "sha256": "8d555f13bf3601fd1d6c2e112cf347042b1a4697d74299e4bed2ddc1be65da94"
    },
    "audit/research/source-coupling-compression/figures/figure-preamble.tex": {
        "bytes": 1028,
        "sha256": "688100a1cbc15d8cc477e04bd287e883316f720294d5de649ae4bb5ac33bc067"
    },
    "audit/research/source-coupling-compression/figures/office-mechanism.json": {
        "bytes": 462,
        "sha256": "a0dce1eaeb088aac86863018b359d440f03296af3f254d768a51f2170d9d4d86"
    },
    "audit/research/source-coupling-compression/figures/office-recoding.pdf": {
        "bytes": 13494,
        "sha256": "6fb2c049f63e90504cef14a362c0e36dd46c02672aec50b1e175539ae8875871"
    },
    "audit/research/source-coupling-compression/figures/office-recoding.svg": {
        "bytes": 74585,
        "sha256": "b755e7779f41a830f012292eb1457333b2d78ed13629486de4ab261933c4a65d"
    },
    "audit/research/source-coupling-compression/figures/office-recoding.tex": {
        "bytes": 1230,
        "sha256": "9655e4dffc0c9d46a4be74ab706eb92087776091c522971259b9023ed74e12e7"
    },
    "audit/research/source-coupling-compression/figures/prediction-comparison-v2.pdf": {
        "bytes": 7795,
        "sha256": "19e2c7183e3e6027fac9ca885ce912bcaae6718d68394151a2605fd91026d1d9"
    },
    "audit/research/source-coupling-compression/figures/prediction-comparison-v2.svg": {
        "bytes": 44268,
        "sha256": "7f4e04d9be992e09d5e5cad0625094c19ca1a4a3ef04587386a21fb428c594ca"
    },
    "audit/research/source-coupling-compression/figures/prediction-comparison-v2.tex": {
        "bytes": 779,
        "sha256": "f842e7cbad8919424304878b9af3ca339ebbd0ac1a8f2132d822110f5c247955"
    },
    "audit/research/source-coupling-compression/figures/prediction.dat": {
        "bytes": 195,
        "sha256": "7271a15b6dace8d03e227ff73030db5edd328ea0227a7c69f5dde5bdd5fa04cb"
    }
}
NATIVE_INPUTS: dict[str, dict] = {
    "texmf-dist/tex/context/base/mkii/supp-pdf.mkii": {
        "bytes": 71627,
        "sha256": "5dd3675b88c7b61d3703e6bf35ed75623acc6b163dff7b1477b485cee8ad71cb"
    },
    "texmf-dist/tex/generic/bigintcalc/bigintcalc.sty": {
        "bytes": 40635,
        "sha256": "050f2ad3a3671a1f4f9bcf97784836301bc751507e7ada546632379406aea103"
    },
    "texmf-dist/tex/generic/bitset/bitset.sty": {
        "bytes": 33961,
        "sha256": "af5c7196c69dc9d28225189169b60c9b9039125bc1756c04d54886f0a3e1891e"
    },
    "texmf-dist/tex/generic/iftex/iftex.sty": {
        "bytes": 7237,
        "sha256": "2de50639c1f27201f2b4d04e9083e0a51fc5a73b8908eea2e80d6e3205636d4a"
    },
    "texmf-dist/tex/generic/iftex/ifvtex.sty": {
        "bytes": 1057,
        "sha256": "1138730b9ad7d9f664b4760a4ea0ae0945afd21c006b76b67e623e863bbf3756"
    },
    "texmf-dist/tex/generic/infwarerr/infwarerr.sty": {
        "bytes": 8356,
        "sha256": "8c3e23b8bb7d940ff26cb0cf96e0151f540acf55020dc3c1aa8bcdb2eb66305c"
    },
    "texmf-dist/tex/generic/intcalc/intcalc.sty": {
        "bytes": 31769,
        "sha256": "1343ba1b10b245bfd199c22947249af1d756808690c7811c90f07fe0a3772080"
    },
    "texmf-dist/tex/generic/kvdefinekeys/kvdefinekeys.sty": {
        "bytes": 5412,
        "sha256": "c42f0c2628dc5fbd95b535cf8cd3cc964347653c099d38c0d416f896d84e8240"
    },
    "texmf-dist/tex/generic/ltxcmds/ltxcmds.sty": {
        "bytes": 17865,
        "sha256": "8fea89995d37ba4c69137186faafc589c470edcc5026d8a31aadbe5cef47dcb4"
    },
    "texmf-dist/tex/generic/pdfescape/pdfescape.sty": {
        "bytes": 19007,
        "sha256": "b3f0e56366c11b85dae521f9a48a6fd415dec1ce8c83152fde813a9f64445b49"
    },
    "texmf-dist/tex/generic/pdftexcmds/pdftexcmds.sty": {
        "bytes": 20089,
        "sha256": "2df7e0bd148c99d8097352b8ac9948dccf91d61ba360dcf43f82206933b6045b"
    },
    "texmf-dist/tex/generic/pgf/basiclayer/pgfcore.code.tex": {
        "bytes": 1016,
        "sha256": "ec94fcfeeda3204c4e43d2008be50b6005da0e642deafaead137284d66e82926"
    },
    "texmf-dist/tex/generic/pgf/math/pgfint.code.tex": {
        "bytes": 3063,
        "sha256": "95f8053efeeb2267d543d8d1afb10195d6114765eea7b90755b4e0c359324d64"
    },
    "texmf-dist/tex/generic/pgf/math/pgfmath.code.tex": {
        "bytes": 949,
        "sha256": "7fa0ff434e9cdeb14c40f326d53e6ea0273ef2046daf28987992e2488d186c85"
    },
    "texmf-dist/tex/generic/pgf/math/pgfmathcalc.code.tex": {
        "bytes": 13270,
        "sha256": "14bf1941381e7eb35dce4850d0aa819360f1db9ba9752c81cff19920f2c4c7b7"
    },
    "texmf-dist/tex/generic/pgf/math/pgfmathfloat.code.tex": {
        "bytes": 104717,
        "sha256": "ccd576f7cebab3a0c5d5cdef41fc44e638d7bb4a20e0a0465160eba1757795e5"
    },
    "texmf-dist/tex/generic/pgf/math/pgfmathparser.code.tex": {
        "bytes": 37466,
        "sha256": "8986f92b517f94415ae5642fc03eb9a8998fdaab446ab2e10f97985d5a9589da"
    },
    "texmf-dist/tex/generic/pgf/math/pgfmathutil.code.tex": {
        "bytes": 8471,
        "sha256": "cda208d98bdc556a06f5915571c6ce4d98c18aa639c4782a56c6d32a6ba68055"
    },
    "texmf-dist/tex/generic/pgf/pgf.revision.tex": {
        "bytes": 114,
        "sha256": "ac54ea0a31097f28b4e37b09fa17985728d589c10640cf220d7e959f63b9e731"
    },
    "texmf-dist/tex/generic/pgf/systemlayer/pgf.cfg": {
        "bytes": 926,
        "sha256": "eb308ac3d665db8dd3c03b18328c551609346c659c2ce0e5029223fbcc339cb3"
    },
    "texmf-dist/tex/generic/pgf/systemlayer/pgfsys.code.tex": {
        "bytes": 61351,
        "sha256": "aa771cadef59f480af688c690c5de28e23636ef4890842b9758b7d8943ede4ac"
    },
    "texmf-dist/tex/generic/pgf/utilities/pgffor.code.tex": {
        "bytes": 24033,
        "sha256": "5787859fab7c72cc3dfd7134e78bbb0e770a43e7da39f93732c24232249fdde8"
    },
    "texmf-dist/tex/generic/pgf/utilities/pgfkeys.code.tex": {
        "bytes": 39784,
        "sha256": "212f64f8641fb944a006a3c0825e78d30b0a2c5e3b4c4d62ff59ef61214caeed"
    },
    "texmf-dist/tex/generic/pgf/utilities/pgfrcs.code.tex": {
        "bytes": 4385,
        "sha256": "6d28f51c1b4cb933969339982286f86bb1c9af70ed34535482321de4cd491664"
    },
    "texmf-dist/tex/generic/pgf/utilities/pgfutil-latex.def": {
        "bytes": 6950,
        "sha256": "6afcd415b6831a153969f66e8b06e9045fe5a5a40239ef51d76de757105396a2"
    },
    "texmf-dist/tex/generic/stringenc/stringenc.sty": {
        "bytes": 21514,
        "sha256": "b134a7bba648a6987afc83ddfb6a3fcdad43bcae6b616e533eb484306d56ac45"
    },
    "texmf-dist/tex/generic/uniquecounter/uniquecounter.sty": {
        "bytes": 7008,
        "sha256": "9d11c81501953d689787ff14c073d2f1eda5874068db9e882b8dbbf9a9d863b0"
    },
    "texmf-dist/tex/latex/amsmath/amsbsy.sty": {
        "bytes": 2222,
        "sha256": "f69355f4b0a8b650296fe2fd9471783a6940e6525efd5d7d306b5477daef494d"
    },
    "texmf-dist/tex/latex/amsmath/amsgen.sty": {
        "bytes": 4173,
        "sha256": "1232e78c8af6c4bc16c024fe33b9c4c3322679ad6887be22bc013ddb8d254ed9"
    },
    "texmf-dist/tex/latex/amsmath/amsmath.sty": {
        "bytes": 88371,
        "sha256": "da22219a49c094141141bb29034c438d1ccba8a9afe6cdd5d15b96c15bf56901"
    },
    "texmf-dist/tex/latex/amsmath/amsopn.sty": {
        "bytes": 4474,
        "sha256": "981dbcccfc3a2449768ae5b1cb7b8b1468bb1f7842429067cd6f6ef0ade42fc2"
    },
    "texmf-dist/tex/latex/amsmath/amstext.sty": {
        "bytes": 2444,
        "sha256": "2bf2e4f0efe99c33bfd757e1dee1b4267742f8af3e449d6bdb4342c2917b1bce"
    },
    "texmf-dist/tex/latex/auxhook/auxhook.sty": {
        "bytes": 3935,
        "sha256": "1d9f36f4e9674bef594a47cac7d5781e9f7e0c7c8edf9f72769f4dc6f10d1b5f"
    },
    "texmf-dist/tex/latex/base/article.cls": {
        "bytes": 20144,
        "sha256": "859217b3457cca472e5a96ef193218c87a4e62a6445cdd501ba7e1954fa32afa"
    },
    "texmf-dist/tex/latex/base/atbegshi-ltx.sty": {
        "bytes": 3045,
        "sha256": "6720c4cf09cf91e8055b9ad4b54275cbd690be65b1f36805fa457c059d2e29a2"
    },
    "texmf-dist/tex/latex/base/atveryend-ltx.sty": {
        "bytes": 2462,
        "sha256": "95a2509f9ade1283bc842ed5c90084853892b67ab7acccfbf85b8acd38e1d7e3"
    },
    "texmf-dist/tex/latex/base/fix-cm.sty": {
        "bytes": 14741,
        "sha256": "e138d7499fd8ebcf48de16a6caa88a7da1ad04e0608b2975adb013bf6e86359b"
    },
    "texmf-dist/tex/latex/base/fontenc.sty": {
        "bytes": 5119,
        "sha256": "b17f7346c2d881bba3bde28711e53cc7d3125e5ea440672f59bbbdbbd95499ed"
    },
    "texmf-dist/tex/latex/base/size11.clo": {
        "bytes": 8464,
        "sha256": "9ecfd9ff838f6e15cce1dfbdde454e92f13228cd08b2fb26e11f821bf95055c7"
    },
    "texmf-dist/tex/latex/base/ts1enc.def": {
        "bytes": 8090,
        "sha256": "046c866dbc903cc8f66f4e86eacc121edd77fd3ea3b9a2ba6a5bae19990415ad"
    },
    "texmf-dist/tex/latex/bookmark/bkm-pdftex.def": {
        "bytes": 8818,
        "sha256": "8e01370bb81faebfaf5715cb3f7ef242b34dac04d38d6c9542cd6790a8b4eb44"
    },
    "texmf-dist/tex/latex/bookmark/bookmark.sty": {
        "bytes": 18245,
        "sha256": "81cb5aeb52520a14445b3bdd6ee4cd6b4c32404cda6ba3106a9049b9672e7203"
    },
    "texmf-dist/tex/latex/booktabs/booktabs.sty": {
        "bytes": 6078,
        "sha256": "3fe694a5406f84847143e56ba1841385364277cfe7694a9f4bc0072ca8656abc"
    },
    "texmf-dist/tex/latex/caption/caption.sty": {
        "bytes": 56128,
        "sha256": "94b3a07d83bfdc9171d3fcb5ea510e6a9ce01ff9bebac37a1dc066e55f6ad48f"
    },
    "texmf-dist/tex/latex/caption/caption3.sty": {
        "bytes": 72619,
        "sha256": "73f00aabd0be454c9e552841856c573e096ef42d032fe9fd1801763b1b37bea5"
    },
    "texmf-dist/tex/latex/caption/ltcaption.sty": {
        "bytes": 7418,
        "sha256": "314e0af4d7edcc038eb4dab681b2ccb472d4282f282f4188c8154c2403eb842e"
    },
    "texmf-dist/tex/latex/colortbl/colortbl.sty": {
        "bytes": 12355,
        "sha256": "a696d6c768edfd5e6697f7435254903efaa4f8a3a188b1980d67c70544cdfd71"
    },
    "texmf-dist/tex/latex/enumitem/enumitem.sty": {
        "bytes": 51697,
        "sha256": "a217353d233e54e8c0944d87ea2924ec1f20d849a35b749698df03884856e5e3"
    },
    "texmf-dist/tex/latex/eso-pic/eso-pic.sty": {
        "bytes": 11876,
        "sha256": "8554cb0a5449a031f5d78cc67c824d23afb4b1a4dd11ca9946447185bb274464"
    },
    "texmf-dist/tex/latex/etoolbox/etoolbox.sty": {
        "bytes": 46845,
        "sha256": "b10381f0017ae75bd03dc9175b35ad56b93fdd24f2a47dd4aa9c6987ef35ccdb"
    },
    "texmf-dist/tex/latex/fancyhdr/fancyhdr.sty": {
        "bytes": 18450,
        "sha256": "cc6791065900f898299156662bf8a8d7d462daf2bb9af5a84bca6eb63dcac0a0"
    },
    "texmf-dist/tex/latex/float/float.sty": {
        "bytes": 6749,
        "sha256": "be4a09ab7ded44b4ce97ba20a3a3efbb061d186327d5db61f8de6a3cab5019aa"
    },
    "texmf-dist/tex/latex/fontspec/fontspec.cfg": {
        "bytes": 549,
        "sha256": "f31d038ca5322ef4fc3fbe391f42695bf1305567a04b6ac1005964703dd1232a"
    },
    "texmf-dist/tex/latex/fontspec/fontspec.sty": {
        "bytes": 3484,
        "sha256": "245664cea4030dd170b7d9fdc839104a63c0156aba8e8a996720ea3dd02e7d1d"
    },
    "texmf-dist/tex/latex/geometry/geometry.sty": {
        "bytes": 41601,
        "sha256": "d5d36ad74051ad36288242b51438e2d9a5db2bd6c063b9b5704d0931fbc9f439"
    },
    "texmf-dist/tex/latex/graphics-cfg/color.cfg": {
        "bytes": 1213,
        "sha256": "a3529ccdadc8248b4c5d7c34ceea53bdc1509b54f18a192ad51b924bd297d8df"
    },
    "texmf-dist/tex/latex/graphics-cfg/graphics.cfg": {
        "bytes": 1224,
        "sha256": "feb91e48789a21e4acced98e952c77a2e2cf4a77e01bf147b59fa56a1b3f2008"
    },
    "texmf-dist/tex/latex/graphics-def/luatex.def": {
        "bytes": 19478,
        "sha256": "13a061e52073fad9e8acb60d2d7174821dec95b554c8678b24c4fdd85bc4aa77"
    },
    "texmf-dist/tex/latex/graphics/graphics.sty": {
        "bytes": 18387,
        "sha256": "36e2e612e708d04785971d6bcfed324d0a0f9ce337ea73680e69dd2603d0327a"
    },
    "texmf-dist/tex/latex/graphics/graphicx.sty": {
        "bytes": 8010,
        "sha256": "e9fe8e56401707f18a3d18716dadfd1dab999d02118c82af05691599cedec445"
    },
    "texmf-dist/tex/latex/graphics/keyval.sty": {
        "bytes": 2671,
        "sha256": "8434ad08617159240fd19b4fcae8bf79a6137af413f3798c8a750e9839f8902e"
    },
    "texmf-dist/tex/latex/graphics/mathcolor.ltx": {
        "bytes": 2885,
        "sha256": "0804bb6e9e1eeeaeda861f29206d308194ea7cc846e38abaa344cdefa1d408cd"
    },
    "texmf-dist/tex/latex/graphics/trig.sty": {
        "bytes": 4023,
        "sha256": "c2a4f1d01abaf7ad739f1af03238ebb6ab35a7bbfbd5d713acceddda4fb043d5"
    },
    "texmf-dist/tex/latex/hycolor/hycolor.sty": {
        "bytes": 17914,
        "sha256": "8acaa03eda19a8158780356701e905e354e1dc47dc736e6e26fc860c12a15e14"
    },
    "texmf-dist/tex/latex/hyperref/hluatex.def": {
        "bytes": 51074,
        "sha256": "40905b3430fe0bf1173bff444678ffb4f24acf00f0a3a0e1055fee2c4d86cdb6"
    },
    "texmf-dist/tex/latex/hyperref/hyperref.sty": {
        "bytes": 220920,
        "sha256": "3e2bd51be23486a776165ebda8bdef7d442c0b779db14652dcc1e40429b1c1ad"
    },
    "texmf-dist/tex/latex/hyperref/nameref.sty": {
        "bytes": 11026,
        "sha256": "1bd958ef4ce46f3d15f7c77f6c2d084289e0e6d6017d5a3a341d83f0998b99a7"
    },
    "texmf-dist/tex/latex/hyperref/pd1enc.def": {
        "bytes": 14249,
        "sha256": "860fb14ebfbd12904aca6dff9e05fad399529d7fe8c00d9b130f02bbc892925d"
    },
    "texmf-dist/tex/latex/hyperref/puenc.def": {
        "bytes": 117112,
        "sha256": "70942bf5c0f0725234b8677e18170952b39b5959d6b1d5f9ccfb1ec88a049bf5"
    },
    "texmf-dist/tex/latex/kvoptions/kvoptions.sty": {
        "bytes": 22555,
        "sha256": "70595629ec990ba8c0b6e6a54afcff2603464e6fce380a54a98549a78d2fc74a"
    },
    "texmf-dist/tex/latex/kvsetkeys/kvsetkeys.sty": {
        "bytes": 13815,
        "sha256": "e3fcf7f3372a27bb478eb9488eca1e25ed382480d02a6898f190bd955388e055"
    },
    "texmf-dist/tex/latex/l3backend/l3backend-luatex.def": {
        "bytes": 30427,
        "sha256": "1bd728b36fb7d777c7a7072684d8ef24fe0e61447580f2db4404a03b9b8c3445"
    },
    "texmf-dist/tex/latex/l3kernel/expl3.sty": {
        "bytes": 6565,
        "sha256": "031f0ee8e4751aff29af9cfda2ced8a8e3f52eb158e682c510856e3ed36d9361"
    },
    "texmf-dist/tex/latex/l3packages/l3keys2e/l3keys2e.sty": {
        "bytes": 4674,
        "sha256": "abc88154119ab6fb15ec11da3643c68519d6a6ad1bbe19a2762eec08cccf15c4"
    },
    "texmf-dist/tex/latex/l3packages/xparse/xparse.sty": {
        "bytes": 9327,
        "sha256": "f5d74008cd05735dfcc8b972eae85a6bf6a9fe286da4a86fece0a9fad37a8297"
    },
    "texmf-dist/tex/latex/microtype/microtype-luatex.def": {
        "bytes": 38850,
        "sha256": "1dc739c9ce9b42b041a81cc1ae93483e587efc46a7ed94feedc01c5cfc783082"
    },
    "texmf-dist/tex/latex/microtype/microtype.cfg": {
        "bytes": 26842,
        "sha256": "a4bd4486751d955ae22f96563e5306c9a45227e5ffd25d19dffda84c4d90a5d5"
    },
    "texmf-dist/tex/latex/microtype/microtype.sty": {
        "bytes": 98531,
        "sha256": "1a41c71483a682e5443508d023fc2d01a3b96e8bdf914f0331a39760ef281549"
    },
    "texmf-dist/tex/latex/needspace/needspace.sty": {
        "bytes": 852,
        "sha256": "5ae673ce2a80fb868c954373252294d9e6469feeb78b445182772fd043eb0914"
    },
    "texmf-dist/tex/latex/pgf/basiclayer/pgf.sty": {
        "bytes": 1090,
        "sha256": "99e08946749446e0b9b7faa985f8202740a94476f9e99bab5286cca5ce4766e9"
    },
    "texmf-dist/tex/latex/pgf/basiclayer/pgfcore.sty": {
        "bytes": 373,
        "sha256": "3a52a05062a74a763ee604b4a3d20f0be4a4b99fe8182373e30ccea0abafc96e"
    },
    "texmf-dist/tex/latex/pgf/frontendlayer/tikz.sty": {
        "bytes": 339,
        "sha256": "6e39ff4fdf9f126aff28880a7dd59fccc0e6735409d92ca455cdd2a4f2b4db53"
    },
    "texmf-dist/tex/latex/pgf/math/pgfmath.sty": {
        "bytes": 306,
        "sha256": "4abed7d8c88642201dd1a932a435ae05a1f2659f1f7e95c72d6b5347c83d232a"
    },
    "texmf-dist/tex/latex/pgf/systemlayer/pgfsys.sty": {
        "bytes": 443,
        "sha256": "cc7121c5706c5c52807aea879ca0a9083a8dc81b04d96303d0d398804d9d3d52"
    },
    "texmf-dist/tex/latex/pgf/utilities/pgffor.sty": {
        "bytes": 348,
        "sha256": "5ae03317ea221a6f68d807775bd06a10625aa9fb1f590dbe2114688f735c447d"
    },
    "texmf-dist/tex/latex/pgf/utilities/pgfkeys.sty": {
        "bytes": 274,
        "sha256": "b90072b20d0590f23fd0ad273d059e3b7737319b3fb61e3bea6102fd77f24b3d"
    },
    "texmf-dist/tex/latex/pgf/utilities/pgfrcs.sty": {
        "bytes": 325,
        "sha256": "9653b8fae6bba95bec40ffbedd7d6c2b8f3be4a85b8b39580ab3ee6c3590041a"
    },
    "texmf-dist/tex/latex/ragged2e/ragged2e.sty": {
        "bytes": 10085,
        "sha256": "bbaa95d82bff14cd13fdead40edcdd31d7bd1e84127fe85f6b20dccff474cf4d"
    },
    "texmf-dist/tex/latex/refcount/refcount.sty": {
        "bytes": 9878,
        "sha256": "1bd5d42025520bef74f8808af99cf3f3be7d2e3774b9931bf85c11ba81bb6cab"
    },
    "texmf-dist/tex/latex/rerunfilecheck/rerunfilecheck.sty": {
        "bytes": 9714,
        "sha256": "7e22b1ca949259c61d3721bca0a56bcccf7e47cfc776027c5863941635c07aa1"
    },
    "texmf-dist/tex/latex/seqsplit/seqsplit.sty": {
        "bytes": 1346,
        "sha256": "35556c982cf26ae65d9c904cf0ec76f320c42f9fae28de6e466dcefaf13775f7"
    },
    "texmf-dist/tex/latex/titlesec/titlesec.sty": {
        "bytes": 48766,
        "sha256": "c78182a0719ca00b7fa6cfbc5d8fbb58c341314954413b8d5b016d67a9e17f41"
    },
    "texmf-dist/tex/latex/tools/array.sty": {
        "bytes": 12667,
        "sha256": "dc2b9a0057f8455ac0f74960618e7af3de9bf08da0e7078ef8dd0570a2924427"
    },
    "texmf-dist/tex/latex/tools/calc.sty": {
        "bytes": 10214,
        "sha256": "9c9da7f39469dd6ab1cb765cd5ef87dd72792c8eb9426e4619faecd00e9f2345"
    },
    "texmf-dist/tex/latex/tools/longtable.sty": {
        "bytes": 12935,
        "sha256": "83e32c4a880712340080225b239967442eb7dca5dc22bf0ca85f4ffd52506bd6"
    },
    "texmf-dist/tex/latex/unicode-math/unicode-math.sty": {
        "bytes": 1474,
        "sha256": "91388a2e1332388bcf8393d79a9fb67f4bd197f982503297dbf971f5f7cec111"
    },
    "texmf-dist/tex/latex/url/url.sty": {
        "bytes": 12796,
        "sha256": "2373f56849ac606473e77053e5c1d14c92aba312b3f684e02a130eaf36f2de47"
    },
    "texmf-dist/tex/latex/xcolor/xcolor.sty": {
        "bytes": 55487,
        "sha256": "6d66da8f16088689c2f4995b4e920703cc94faade57911ed7aabd32b04367824"
    },
    "texmf-dist/tex/latex/xurl/xurl.sty": {
        "bytes": 4675,
        "sha256": "5cf09de8dd52b5e77a12145d4987ab4df75a304174d224aa9562eed3dd141ef3"
    },
    "texmf-dist/web2c/texmf.cnf": {
        "bytes": 41649,
        "sha256": "7668d2e2311cba5564b8ee7271a9120e614579f7ff4c49f6d8b86a9bf29f5035"
    },
    "texmf-var/web2c/luahbtex/lualatex.fmt": {
        "bytes": 12255194,
        "sha256": "e254bc4c8dc1304a4cc099c92ad6e4d81da90805d113069c954da5a69d04bffa"
    },
    "texmf.cnf": {
        "bytes": 577,
        "sha256": "4c46e2698d0c438c16490273f6c40e67d15ffc4ba1601abe3d741e67d426cde5"
    }
}
TOOL_PINS: dict[str, dict] = {
    "lualatex": {
        "bytes": 15041936,
        "sha256": "8522fe5f3d9e78dc36a1d39236da77757c8584b3b21e9806af4ba7bfc8b54ed3"
    },
    "pandoc": {
        "bytes": 277291920,
        "sha256": "1662f49c035168d1e608ad9d923df75e4b00ac014d096349b2027ad38f84dd6e"
    },
    "pdffonts": {
        "bytes": 53848,
        "sha256": "09bac53ccfd92f65c58e52716766c31e41ea9867acfccfa1ba2538c2188e4198"
    },
    "pdfinfo": {
        "bytes": 112952,
        "sha256": "fb3efce3511f41cdaba07b433676d3603d80a10e35d61c99830e1a2d1a44bb66"
    },
    "pdftotext": {
        "bytes": 110856,
        "sha256": "81aa90ed17f1da12588ea396971f999a8aa352a228b76e9d53cadf9da47ae66c"
    }
}
PYTHON_PIN: dict = {
    "bytes": 34640,
    "sha256": "6463bf4bc31d94a758f6bec34b28c89bcf5f56f73e7122dd7223cdffa93499fc"
}
PYPDF_PIN: dict = {
    "files": 57,
    "sha256": "658fbfc01516c9d8c3c08e5334919decdae4977150e78463488dce6468bb42fc",
    "version": "6.16.1"
}
BODY_PIN: dict = {
    "bytes": 32151,
    "sha256": "39c2539f9dec8f992c8410ae4844f5a0b36c31309e292b1a0ab4e5f09e9f22e9"
}
RELATIVE_URIS: frozenset[str] = frozenset()  # every PDF link is absolute
SENTINELS = (
    "Question, definitions and assumptions", "Main upper certificate",
    "A cheaper lower certificate", "Exact invariance and a recoverable-tuple counterexample",
    "A conditional exact eighteen-position comparison", "Recorded-data design and exact arithmetic",
    "Results and limitations", "Evidence, failures and research process",
    "Rust implementation and computational cost", "Reproduction and citation",
)
DIAGNOSTIC = re.compile(
    r"^(?:(?:LaTeX|Package[ \t]|Class[ \t]|Lua(?:HB)?TeX|pdfTeX).*?\bwarning\b"
    r"|warning\b|(?:Over|Under)full|Missing character:|!)", re.I | re.M)


class AdmissionError(ValueError):
    """An exact publication predicate was not met."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AdmissionError(message)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def pin_shape(pin: dict, maximum: int = MAX_FILE_BYTES) -> None:
    require(type(pin) is dict and set(pin) == {"bytes", "sha256"}, "invalid pin shape")
    require(type(pin["bytes"]) is int and 0 < pin["bytes"] <= maximum, "invalid pin size")
    require(type(pin["sha256"]) is str and re.fullmatch(r"[0-9a-f]{64}", pin["sha256"]) is not None,
            "invalid pin digest")


def regular_path(path: Path) -> None:
    require(path.is_absolute(), "input path is not absolute")
    for node in (path, *path.parents):
        require(not node.is_symlink(), f"symbolic path: {node.name}")
    require(stat.S_ISREG(path.stat().st_mode), f"input is not regular: {path.name}")


def checked_file(path: Path, pin: dict, *, tool: bool = False) -> bytes | None:
    pin_shape(pin, 512 * 1024 * 1024 if tool else MAX_FILE_BYTES)
    regular_path(path)
    before = path.stat()
    require(before.st_size == pin["bytes"], f"input size differs: {path.name}")
    h = hashlib.sha256()
    chunks = []
    count = 0
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            count += len(chunk)
            require(count <= pin["bytes"], f"input grew: {path.name}")
            h.update(chunk)
            if not tool:
                chunks.append(chunk)
    after = path.stat()
    fields = ("st_dev", "st_ino", "st_mode", "st_size", "st_mtime_ns", "st_ctime_ns")
    require(all(getattr(before, key) == getattr(after, key) for key in fields),
            f"input changed during read: {path.name}")
    require(count == pin["bytes"] and h.hexdigest() == pin["sha256"],
            f"input digest differs: {path.name}")
    return None if tool else b"".join(chunks)


def relative_path(value: str) -> PurePosixPath:
    require(type(value) is str, "unsafe relative input")
    path = PurePosixPath(value)
    require(not path.is_absolute() and str(path) == value
            and all(part not in ("", ".", "..") for part in path.parts), "unsafe relative input")
    return path


def input_inventory(base: Path, declared: set[str]) -> None:
    directories = {str(parent) for name in declared for parent in PurePosixPath(name).parents}
    actual = set()
    for path in base.rglob("*"):
        relative = str(path.relative_to(base))
        require(not path.is_symlink(), "symbolic producer input")
        if path.is_dir():
            require(relative in directories, "unexpected producer input directory")
        else:
            require(stat.S_ISREG(path.stat().st_mode), "nonregular producer input")
            actual.add(relative)
    require(actual == declared, "publication input inventory differs")


def tree_usage(root: Path) -> int:
    total = count = 0
    for directory, dirs, files in os.walk(root, followlinks=False):
        for name in dirs:
            require(not (Path(directory) / name).is_symlink(), "symbolic output directory")
        for name in files:
            path = Path(directory) / name
            try:
                info = path.lstat()
            except FileNotFoundError:
                continue  # a live child removed it after the listing (LuaTeX's cache probe)
            require(stat.S_ISREG(info.st_mode), "nonregular output")
            count += 1
            total += info.st_size
            require(count <= MAX_FILES and info.st_size <= MAX_FILE_BYTES, "output file budget exceeded")
            require(total <= MAX_WORK_BYTES, "aggregate output budget exceeded")
    return total


def deadline_check(deadline: float, *, initial: bool = False) -> None:
    remaining = deadline - time.monotonic()
    require(math.isfinite(deadline) and remaining > 0, "deadline is expired or nonfinite")
    require(not initial or remaining <= MAX_CAMPAIGN_SECONDS, "deadline exceeds admitted window")


def fresh_directory(path: Path) -> Path:
    require(path.is_absolute() and path.name not in ("", ".", ".."), "work directory must be absolute")
    parent = path.parent.resolve(strict=True)
    require(path.parent == parent, "work directory parent must be canonical")
    require(not path.exists() and not path.is_symlink(), "work directory already exists")
    path.mkdir(mode=0o700)
    return path


def write_new(root: Path, path: Path, raw: bytes) -> None:
    require(path.is_relative_to(root) and not path.exists() and not path.is_symlink(), "output slot is spent")
    require(len(raw) <= MAX_FILE_BYTES and tree_usage(root) + len(raw) <= MAX_WORK_BYTES,
            "output reservation exceeds budget")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(raw)


def write_json(root: Path, path: Path, value: object) -> None:
    write_new(root, path, (json.dumps(value, sort_keys=True, indent=2) + "\n").encode())


def run_child(argv: list[str], cwd: Path, env: dict[str, str], label: str,
              root: Path, deadline: float, *, allow_stderr: bool = False) -> bytes:
    """Retain bounded pipes; terminate the owned process group on a limit breach."""
    deadline_check(deadline)
    require(re.fullmatch(r"[a-z0-9-]+", label) is not None, "invalid child label")
    record = {"argv": argv, "cwd": str(cwd), "started_monotonic": time.monotonic(),
              "deadline": deadline, "terminal": False, "failure": None}
    captured = [bytearray(), bytearray()]
    child = None
    streams = []
    try:
        require(tree_usage(root) + MAX_FILE_BYTES + 2 * MAX_LOG_BYTES + 32768 <= MAX_WORK_BYTES,
                "child output reservation exceeds budget")
        for suffix in ("stdout", "stderr"):
            path = cwd / f"{label}.{suffix}"
            require(not path.exists(), "child log slot is spent")
            streams.append(path.open("xb"))
        def limits() -> None:
            resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_FILE_BYTES, MAX_FILE_BYTES))
            resource.setrlimit(resource.RLIMIT_CPU, (45, 45))

        child = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 start_new_session=True, preexec_fn=limits)
        end = min(deadline, record["started_monotonic"] + MAX_CHILD_SECONDS)
        with selectors.DefaultSelector() as selector:
            selector.register(child.stdout, selectors.EVENT_READ, 0)
            selector.register(child.stderr, selectors.EVENT_READ, 1)
            while selector.get_map():
                require(time.monotonic() < end, f"{label} timed out")
                tree_usage(root)
                for key, _ in selector.select(timeout=min(0.05, max(0, end - time.monotonic()))):
                    chunk = os.read(key.fileobj.fileno(), 65536)
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    index = key.data
                    available = MAX_LOG_BYTES - len(captured[index])
                    kept = chunk[:available]
                    captured[index].extend(kept)
                    streams[index].write(kept)
                    streams[index].flush()
                    require(len(chunk) <= available, f"{label} log budget exceeded; prefix retained")
            require(time.monotonic() < end, f"{label} timed out")
            child.wait(timeout=max(0.001, end - time.monotonic()))
        record["terminal"] = True
        record["exit"] = child.returncode
        require(child.returncode == 0, f"{label} exited {child.returncode}")
        require(allow_stderr or not captured[1], f"{label} wrote stderr")
        deadline_check(deadline)
        tree_usage(root)
    except BaseException as error:
        record["failure"] = f"{type(error).__name__}: {error}"
        if child is not None:
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            child.wait(timeout=5)
            record["terminal"] = True
            record["exit"] = child.returncode
        raise
    finally:
        for stream in streams:
            stream.close()
        if child is not None:
            child.stdout.close()
            child.stderr.close()
        record["finished_monotonic"] = time.monotonic()
        record["streams"] = [{"bytes": len(raw), "sha256": sha256(raw)} for raw in captured]
        # Reserve this small terminal receipt independently, even on a budget breach.
        raw = (json.dumps(record, sort_keys=True, indent=2) + "\n").encode()
        require(len(raw) <= 32768, "terminal receipt exceeds reservation")
        with (cwd / f"{label}.json").open("xb") as stream:
            stream.write(raw)
    return bytes(captured[0] + (captured[1] if allow_stderr else bytearray()))


def validate_uri(value: str) -> None:
    require(type(value) is str and value and not any(ord(c) < 32 for c in value), "invalid URI")
    decoded = unquote(value)
    require(not any(x in decoded for x in (".local", "file:", "/Users/", "\\")), "private or file URI")
    if value in RELATIVE_URIS:
        return
    parts = urlsplit(value)
    require(parts.scheme in ("https", "http", "mailto"), "unadmitted URI scheme or relative target")
    require((parts.scheme == "mailto" and "@" in parts.path) or
            (parts.scheme in ("https", "http") and parts.hostname and not parts.username and not parts.password),
            "invalid public URI")


def validate_reader(reader) -> dict:
    """Semantic predicates run before the separate final committed-byte predicate."""
    from pypdf.generic import ArrayObject, DictionaryObject, IndirectObject

    require(not reader.is_encrypted, "encrypted PDF")
    require(reader.pdf_header == "%PDF-1.7", "PDF version differs")
    require(len(reader.pages) == 11, "PDF page count differs")
    metadata = reader.metadata
    require(metadata is not None and metadata.get("/Author") == AUTHOR, "PDF author differs")
    require(metadata.get("/Title") == TITLE, "PDF title differs")
    require(metadata.get("/Subject") == SUBJECT, "PDF subject differs")
    # publication.tex sets \pdfvariable suppressoptionalinfo=767, which omits the producer.
    require("/Producer" not in metadata, "PDF producer is present although the wrapper suppresses it")
    require(metadata.get("/Creator") == "LaTeX with hyperref", "PDF creator differs")
    require(set(metadata).issubset({"/Author", "/Title", "/Subject", "/Producer", "/Creator", "/Keywords",
                                  "/CreationDate", "/ModDate", "/Trapped", "/PTEX.Fullbanner"}),
            "unexpected PDF metadata key")
    catalog = reader.trailer["/Root"]
    require(catalog.get("/Lang") == "en", "PDF language differs")
    require("/StructTreeRoot" not in catalog, "PDF tagging profile differs")
    mark_info = catalog.get("/MarkInfo")
    if mark_info is not None:
        mark_info = mark_info.get_object()
        require(isinstance(mark_info, DictionaryObject), "invalid PDF marking dictionary")
        marked = mark_info.get("/Marked", False)
        require(getattr(marked, "value", marked) is False, "PDF tagging profile differs")
    forbidden = {"/JavaScript", "/JS", "/Launch", "/AA", "/AcroForm", "/EmbeddedFiles", "/EF", "/XFA",
                 "/RichMediaContent", "/RichMediaSettings", "/Collection", "/3D", "/Sound", "/Movie"}
    page_ids = {page.indirect_reference.idnum for page in reader.pages}
    named = reader.named_destinations
    for destination in named.values():
        require(reader.get_destination_page_number(destination) in range(11), "broken named destination")

    def destination(value) -> None:
        value = value.get_object() if hasattr(value, "get_object") else value
        if isinstance(value, (str, bytes)):
            require(str(value) in named, "unknown named destination")
        else:
            require(isinstance(value, (list, ArrayObject)) and len(value) >= 2,
                    "invalid destination array")
            page = value[0]
            require(isinstance(page, IndirectObject) and page.idnum in page_ids, "destination page is absent")
            require(str(value[1]) in ("/Fit", "/FitH", "/FitV", "/XYZ", "/FitR", "/FitB", "/FitBH", "/FitBV"),
                    "unknown destination operation")

    visited = set()
    nodes = actions = fonts = 0

    def visit(value) -> None:
        nonlocal nodes, actions, fonts
        if isinstance(value, IndirectObject):
            ident = (value.idnum, value.generation)
            if ident in visited:
                return
            visited.add(ident)
            value = value.get_object()
        nodes += 1
        require(nodes <= 20000, "PDF object budget exceeded")
        if isinstance(value, (dict, DictionaryObject)):
            require(not (set(value) & forbidden), "forbidden PDF action or payload key")
            if "/S" in value:
                operation = str(value["/S"])
                # /S also identifies transparency groups; these are passive content.
                if operation == "/Transparency":
                    require(value.get("/Type") == "/Group", "invalid transparency group")
                elif operation in ("/D", "/R", "/r", "/A", "/a"):
                    require(set(value).issubset({"/S", "/P", "/St"}), "invalid page-label style")
                else:
                    require(operation in ("/URI", "/GoTo"), "unadmitted PDF action")
                    actions += 1
                    require("/Next" not in value, "chained PDF action")
                    if operation == "/URI":
                        require(set(value).issubset({"/S", "/URI", "/Type"}), "unexpected URI action key")
                        validate_uri(str(value.get("/URI", "")))
                    else:
                        require(set(value).issubset({"/S", "/D", "/Type"}), "unexpected GoTo action key")
                        destination(value.get("/D"))
            if "/OpenAction" in value:
                # An open action is a destination or an action dictionary; a GoTo action is checked
                # with the other actions when visit reaches it.
                opening = value["/OpenAction"]
                opening = opening.get_object() if hasattr(opening, "get_object") else opening
                if isinstance(opening, (dict, DictionaryObject)):
                    require(str(opening.get("/S")) == "/GoTo", "unadmitted open action")
                else:
                    destination(opening)
            if "/Dest" in value:
                destination(value["/Dest"])
            if value.get("/Type") == "/Font" and value.get("/Subtype") == "/Type0":
                fonts += 1
                require("/ToUnicode" in value and value["/ToUnicode"].get_data(), "font has no ToUnicode")
                descendants = value.get("/DescendantFonts", [])
                require(len(descendants) == 1, "unexpected descendant font roster")
                descriptor = descendants[0].get_object().get("/FontDescriptor")
                require(descriptor is not None, "font descriptor is absent")
                descriptor = descriptor.get_object()
                require(any(key in descriptor and descriptor[key].get_object().get_data()
                            for key in ("/FontFile", "/FontFile2", "/FontFile3")), "font is not embedded")
            elif value.get("/Type") == "/Font":
                require(value.get("/Subtype") in ("/CIDFontType0", "/CIDFontType2"), "unadmitted font subtype")
            for member in value.values():
                visit(member)
        elif isinstance(value, (list, ArrayObject)):
            for member in value:
                visit(member)

    visit(reader.trailer)
    texts = []
    for page in reader.pages:
        box = [float(x) for x in page.mediabox]
        require(abs(box[0]) < 0.01 and abs(box[1]) < 0.01 and
                abs(box[2] - 595.276) < 0.02 and abs(box[3] - 841.89) < 0.02, "PDF page is not A4")
        require(int(page.get("/Rotate", 0)) == 0, "rotated PDF page")
        page.get_contents()
        text = page.extract_text()
        require(type(text) is str and len(text.strip()) >= 80, "page text is absent")
        texts.append(text)
    text = " ".join(" ".join(texts).split())
    require(fonts > 0 and actions > 0, "PDF font or link inventory is empty")
    require(AUTHOR in texts[0], "visible author is absent")
    # pypdf drops the spaces of the letter-spaced heading face; Poppler keeps them. Compare the
    # section sentinels without whitespace.
    dense = re.sub(r"\s", "", text)
    require(all(re.sub(r"\s", "", sentinel) in dense for sentinel in SENTINELS),
            "PDF report sentinel is absent")
    require(not any(token in text for token in ("\ufffd", "/Users/", ".local/", "\\begin{", "\\frac{")),
            "PDF text has private paths, replacement glyphs or raw TeX")
    return {"pages": 11, "fonts": fonts, "actions": actions, "nodes": nodes,
            "text_sha256": sha256(text.encode()), "tagged": False}


def validate_pdf(raw: bytes) -> dict:
    require(0 < len(raw) <= MAX_FILE_BYTES, "PDF byte budget exceeded")
    from pypdf import PdfReader
    diagnostic = io.StringIO()
    handler = logging.StreamHandler(diagnostic)
    logger = logging.getLogger("pypdf")
    logger.addHandler(handler)
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            reader = PdfReader(io.BytesIO(raw), strict=True)
            result = validate_reader(reader)
        require(not caught and not diagnostic.getvalue(), "PDF parser emitted diagnostics")
        return result
    finally:
        logger.removeHandler(handler)


def check_pdf_relation(first: bytes, second: bytes, committed: bytes) -> None:
    require(first == second, "fresh PDF builds differ")
    require(first == committed, "committed PDF differs from rebuilt bytes")


def build_one(work: Path, sources: dict[str, bytes], tools: dict[str, str],
              tex_root: Path, campaign: Path, deadline: float) -> bytes:
    fresh_directory(work)
    for name in ("tmp", "cache", "texmf-var", "texmf-config", "texmf-home"):
        (work / name).mkdir(mode=0o700)
    write_new(campaign, work / "body.md", sources[SOURCE])
    for path, raw in sources.items():
        if path.startswith(ASSETS):
            write_new(campaign, work / path.removeprefix(ASSETS), raw)
        elif path.startswith(FIGURES):
            write_new(campaign, work / "figures" / path.removeprefix(FIGURES), raw)
    env = {"PATH": os.pathsep.join(dict.fromkeys(str(Path(p).parent) for p in tools.values())),
           "LC_ALL": "C", "LANG": "C", "TZ": "UTC", "SOURCE_DATE_EPOCH": str(EPOCH),
           "FORCE_SOURCE_DATE": "1", "TEXINPUTS": str(work) + ":", "TMPDIR": str(work / "tmp"),
           "TEXMFVAR": str(work / "texmf-var"), "TEXMFCONFIG": str(work / "texmf-config"),
           "TEXMFHOME": str(work / "texmf-home"), "TEXMFCACHE": str(work / "cache"),
           "TEXMFOUTPUT": str(work)}
    run_child([tools["pandoc"], "--from", "markdown+tex_math_single_backslash", "--to", "latex",
               "--lua-filter=report-filter.lua", "body.md", "--output=body.tex"],
              work, env, "pandoc", campaign, deadline)
    checked_file(work / "body.tex", BODY_PIN)
    # An absolute --fmt path makes LuaTeX open its first recorder file beside the format, inside
    # the read-only TeX tree. The bare name resolves through kpathsea; the recorder must then show
    # that exactly the pinned format was loaded.
    pinned_format = "INPUT " + str(tex_root / "texmf-var/web2c/luahbtex/lualatex.fmt")
    for number in (1, 2):
        run_child([tools["lualatex"], "--no-shell-escape", "--interaction=nonstopmode", "--halt-on-error",
                   "--recorder", "--jobname=" + JOB, "--fmt=lualatex", "publication.tex"],
                  work, env, "tex-" + str(number), campaign, deadline)
        formats = [line for line in (work / (JOB + ".fls")).read_text(encoding="utf-8").splitlines()
                   if line.startswith("INPUT ") and line.endswith(".fmt")]
        require(formats == [pinned_format], "TeX loaded a format other than the pinned one")
    log = (work / (JOB + ".log")).read_text(encoding="utf-8")
    require(DIAGNOSTIC.search(log) is None, "final TeX log contains a diagnostic")
    raw = (work / (JOB + ".pdf")).read_bytes()
    write_json(campaign, work / "semantic-check.json", validate_pdf(raw))
    for tool in ("pdfinfo", "pdffonts"):
        run_child([tools[tool], str(work / (JOB + ".pdf"))], work, env, tool, campaign, deadline)
    run_child([tools["pdftotext"], "-layout", str(work / (JOB + ".pdf")), str(work / "extracted.txt")],
              work, env, "pdftotext", campaign, deadline)
    require((work / "extracted.txt").stat().st_size > 1000, "Poppler extraction is empty")
    tree_usage(campaign)
    return raw


def parser_identity() -> None:
    checked_file(Path(sys.executable).resolve(strict=True), PYTHON_PIN, tool=True)
    import pypdf
    require(pypdf.__version__ == "6.16.1", "pypdf version differs")
    package = Path(pypdf.__file__).resolve().parent
    roster = [{"path": str(p.relative_to(package)), "sha256": sha256(p.read_bytes())}
              for p in sorted(package.rglob("*.py"))]
    require(len(roster) == PYPDF_PIN["files"] and
            sha256(json.dumps(roster, sort_keys=True, separators=(",", ":")).encode()) == PYPDF_PIN["sha256"],
            "pypdf source package differs")


def admitted_inputs(tex_root: Path) -> tuple[dict[str, bytes], dict[str, str]]:
    require(INPUTS and NATIVE_INPUTS and TOOL_PINS and PYTHON_PIN and PYPDF_PIN and BODY_PIN,
            "publication input packet has not been sealed")
    sources = {}
    for path, pin in INPUTS.items():
        relative_path(path)
        require(path == SOURCE or path.startswith((ASSETS, FIGURES)), "source is outside the declared packet")
        sources[path] = checked_file(ROOT / path, pin)
    declared = {name.removeprefix(ASSETS) for name in INPUTS if name.startswith(ASSETS)}
    input_inventory(ROOT / ASSETS, declared)
    declared_figures = {name.removeprefix(FIGURES) for name in INPUTS if name.startswith(FIGURES)}
    input_inventory(ROOT / FIGURES, declared_figures)
    require(sources[SOURCE].decode().startswith("# " + TITLE + "\n"), "canonical source title differs")
    require(AUTHOR in sources[SOURCE].decode().splitlines()[2], "canonical source author differs")
    for path, pin in NATIVE_INPUTS.items():
        checked_file(tex_root / relative_path(path), pin, tool=True)
    parser_identity()
    tools = {}
    for name, pin in TOOL_PINS.items():
        path = shutil.which(name)
        require(path is not None, f"missing tool: {name}")
        selected = Path(os.path.abspath(path))
        checked_file(selected.resolve(strict=True), pin, tool=True)
        tools[name] = str(selected)
    require(Path(tools["lualatex"]).resolve().is_relative_to(tex_root), "TeX executable is outside selected tree")
    return sources, tools


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--cross-toolchain", action="store_true")
    parser.add_argument("--tex-root", type=Path)
    parser.add_argument("--work-dir", type=Path)
    parser.add_argument("--deadline", type=float)
    args = parser.parse_args()
    if args.cross_toolchain:
        if any(value is not None for value in (args.tex_root, args.work_dir, args.deadline)):
            parser.error("cross-toolchain refusal accepts no build options")
        print("source-coupling PDF: no reviewed cross-toolchain relation; refusing with zero build credit")
        return 2
    work = None
    receipt = {"schema": "pid-rs-source-coupling-pdf-exact-v1", "accepted": False,
               "scope": "two exact-profile source builds; no native closure, visual or scientific acceptance"}
    try:
        require(args.tex_root is not None and args.work_dir is not None and args.deadline is not None,
                "exact check requires --tex-root, --work-dir and --deadline")
        deadline_check(args.deadline, initial=True)
        tex_root = args.tex_root.resolve(strict=True)
        script = Path(__file__).read_bytes()
        sources, tools = admitted_inputs(tex_root)
        committed = checked_file(ROOT / PDF, PDF_PIN)
        # Refuse before native work if the selected public artifact is semantically inadmissible.
        semantics = validate_pdf(committed)
        work = fresh_directory(args.work_dir)
        write_json(work, work / "admission.json", {"script_sha256": sha256(script), "inputs": INPUTS,
                   "native_inputs": NATIVE_INPUTS, "tools": TOOL_PINS, "python": PYTHON_PIN,
                   "pypdf": PYPDF_PIN, "deadline": args.deadline, "work_byte_cap": MAX_WORK_BYTES,
                   "committed_pdf": PDF_PIN, "committed_semantics": semantics})
        env = {"PATH": os.pathsep.join(str(Path(p).parent) for p in tools.values()), "LC_ALL": "C", "LANG": "C"}
        for name, selected in tools.items():
            run_child([selected, "--version" if name in ("pandoc", "lualatex") else "-v"],
                      work, env, "version-" + name, work, args.deadline, allow_stderr=True)
        first = build_one(work / "first", sources, tools, tex_root, work, args.deadline)
        second = build_one(work / "second", sources, tools, tex_root, work, args.deadline)
        check_pdf_relation(first, second, committed)
        later_sources, later_tools = admitted_inputs(tex_root)
        require(later_sources == sources and later_tools == tools and Path(__file__).read_bytes() == script,
                "publication input or controller changed during execution")
        checked_file(ROOT / PDF, PDF_PIN)
        deadline_check(args.deadline)
        receipt.update(accepted=True, repeated_builds=2, pdf_sha256=sha256(first), pdf_bytes=len(first),
                       source_sha256=sha256(sources[SOURCE]), work_bytes=tree_usage(work))
        print(json.dumps(receipt, sort_keys=True))
        return 0
    except Exception as error:
        receipt["failure"] = f"{type(error).__name__}: {error}"
        print("source-coupling PDF: " + receipt["failure"], file=sys.stderr)
        return 1
    finally:
        if work is not None:
            # Fresh reserved terminal evidence; never delete failed native outputs.
            raw = (json.dumps(receipt, sort_keys=True, indent=2) + "\n").encode()
            with (work / "result.json").open("xb") as stream:
                stream.write(raw)


if __name__ == "__main__":
    raise SystemExit(main())
