# CHANGELOG



## v1.0.0 (2023-12-04)

### Breaking

* fix: Fix Dockerfile

BREAKING CHANGE: Dummy to trigger 1.0.0 ([`de5cfc0`](https://github.com/EUCANCan/oncoliner/commit/de5cfc0c9cb30dbd8651464584b593811d93464c))

### Feature

* feat(UI): Prettify tables ([`b009917`](https://github.com/EUCANCan/oncoliner/commit/b009917c5683b94a1531ee9090afce9a60c8e9c6))

* feat(UI): Prettify variant callers names ([`aeb8cf8`](https://github.com/EUCANCan/oncoliner/commit/aeb8cf8e7c840620c36d235fdff1e848af744e45))

* feat(UI): Add harmonization text and style ([`c67d1c7`](https://github.com/EUCANCan/oncoliner/commit/c67d1c76647795baf1696d8b8731678b6e8eb326))

* feat(UI): Add style and text for improvement tab ([`738b3f7`](https://github.com/EUCANCan/oncoliner/commit/738b3f7a1499083cff1549b8ebf8cc9321a07e51))

* feat(UI): Add default column ordering ([`6f792fc`](https://github.com/EUCANCan/oncoliner/commit/6f792fcf399af30013dc0b45e33dde87e88083cf))

* feat: Add fixed row with the baseline ([`3907eab`](https://github.com/EUCANCan/oncoliner/commit/3907eabed350d85ce2f30e8d30267f93b61af02e))

* feat: Add variant callers combinations ([`4fbc459`](https://github.com/EUCANCan/oncoliner/commit/4fbc4595b2de0390fc9600db6d162a29c74469e2))

* feat(Harmonization): Add heterogeneity scores ([`91c2907`](https://github.com/EUCANCan/oncoliner/commit/91c29074f3af436133b25ed45fed4c0e962facde))

* feat: Add VCF intersect and union tools ([`d4b9686`](https://github.com/EUCANCan/oncoliner/commit/d4b9686e5873443765acab9fff2448f10d28d95e))

* feat(UI): Add text to improvement and harmonization ([`6dd652d`](https://github.com/EUCANCan/oncoliner/commit/6dd652dae15194327f474cc30eab724f16d6c6e7))

* feat: Add actionable genes ([`d87bcfe`](https://github.com/EUCANCan/oncoliner/commit/d87bcfed8664c6687193e19949d8588e9d1987ff))

* feat: Add prunning to harmonization ([`d34155b`](https://github.com/EUCANCan/oncoliner/commit/d34155ba55bb1951a0399c5fc38346035dd6333b))

* feat: Add PipelineDesigner prunning ([`e7224d4`](https://github.com/EUCANCan/oncoliner/commit/e7224d4cc659f1c9d5a68959c8a88a439a487ff8))

* feat: Add improvement pruning ([`3611188`](https://github.com/EUCANCan/oncoliner/commit/3611188a951324031603ce4ad9b0e971f75af598))

* feat: Rework pipeline designer to work with configuration files ([`1b871fd`](https://github.com/EUCANCan/oncoliner/commit/1b871fda092e51aba6b4ba25f7ea795f77aae485))

* feat: Rework harmonizator ([`b36e0f9`](https://github.com/EUCANCan/oncoliner/commit/b36e0f914454c9dd9d833f6dc26847b86baee253))

* feat: Add variant types parameter for filtering ([`5e6ff2f`](https://github.com/EUCANCan/oncoliner/commit/5e6ff2f28791f8e4452eead8f0c49a5cf6397a29))

### Fix

* fix(UI): Fix harmonization display ([`6501a55`](https://github.com/EUCANCan/oncoliner/commit/6501a5573e9f5f7abe5b4a80c966f93f16d86023))

* fix(UI): Selection in dropdown accordion now displays its hierarchy (#3)

Co-authored-by: Henri de Soyres &lt;henri.de-soyres@curie.fr&gt; ([`23cea50`](https://github.com/EUCANCan/oncoliner/commit/23cea5053d4ba4678e383baee27988b90edeca6e))

* fix(UI): Add clarifications for improvement and harmonization ([`59ab36c`](https://github.com/EUCANCan/oncoliner/commit/59ab36c75b51da2a8b350dbfffe458c0ef42c698))

* fix(UI): Fix loading screen not appearing ([`4c88a3a`](https://github.com/EUCANCan/oncoliner/commit/4c88a3ad5250a2fdda6e9e35abbd0d3191575cf6))

* fix(UI): Remove callers folders parameter ([`b628991`](https://github.com/EUCANCan/oncoliner/commit/b628991147ab3e379fa29ac5914a0df0822bbaf9))

* fix(UI): Hide callers in collapsable for improvement ([`efd2e8b`](https://github.com/EUCANCan/oncoliner/commit/efd2e8be0834ae2267e0b0dad80340cd22871114))

* fix: Remove variant callers combinations from repo ([`3489187`](https://github.com/EUCANCan/oncoliner/commit/34891873b4ec75df171745e63c8f5812f699918f))

* fix(Assesment): Remove genes from stdout output ([`f9ea399`](https://github.com/EUCANCan/oncoliner/commit/f9ea399aaaf57e41ce7e0abfe95adc28847317bd))

* fix(UI): Remove lateral panels in improvement and harmonization (#2)

* removed left panel for improvement and harmonization views, changed into tab and new component: dropdown tree

* replaced variant type and size dropdown menu from list to accordion tree

---------

Co-authored-by: Henri de Soyres &lt;henri.de-soyres@curie.fr&gt; ([`a2bc9f9`](https://github.com/EUCANCan/oncoliner/commit/a2bc9f9afe454ce1074f62f6cdf935d7c158bc74))

* fix(UI): Improve FP visibility in assesment ([`9b5c62b`](https://github.com/EUCANCan/oncoliner/commit/9b5c62ba9a1695330617b5a9e827551a74caf244))

* fix(Harmonizator): Fix misordering of pipelines recomendations ([`2ae66ab`](https://github.com/EUCANCan/oncoliner/commit/2ae66abb9923c07044f10006ffcf280c04709d35))

* fix(UI): Remove genes from output tables ([`53bd5b5`](https://github.com/EUCANCan/oncoliner/commit/53bd5b5e8629b846d7acc3f85050c8c4382ce648))

* fix: Fix gene aggregation ([`a7dc290`](https://github.com/EUCANCan/oncoliner/commit/a7dc290cdb1d4fad0e125f75620892f138d67a2d))

* fix: Fix gene annotation I/O ([`e31f9e1`](https://github.com/EUCANCan/oncoliner/commit/e31f9e15f74f686b6aeeca100487bc1e50459c52))

* fix: Fix missing &#34;samples&#34; subfolder in improvement ([`8d3c2a5`](https://github.com/EUCANCan/oncoliner/commit/8d3c2a546763003ab20de3ff0d90b6b78e09d55b))

* fix: Fix missing baseline output in improvement ([`b5b7e64`](https://github.com/EUCANCan/oncoliner/commit/b5b7e649ef3434755330d5bbc54f7ba7b854f036))

* fix: Remove pandas deprecation warning ([`dbec680`](https://github.com/EUCANCan/oncoliner/commit/dbec6808cc27a30341e142439300c3c9bae8a22c))

* fix: Remove extra prints ([`52939bf`](https://github.com/EUCANCan/oncoliner/commit/52939bfb73664859a94ee27783b2ce99bbdbe5a4))

* fix: Fix VCFs with mixed chr and non-chr contigs ([`3d4371f`](https://github.com/EUCANCan/oncoliner/commit/3d4371f440134eac96cc917a3885267b622cc352))

* fix: Improve input ingestion ([`5eef8bc`](https://github.com/EUCANCan/oncoliner/commit/5eef8bcf7ca777a149fb90e0fa36957b82ca7ef5))

### Performance

* perf(UI): Use default OS fonts ([`f7e0851`](https://github.com/EUCANCan/oncoliner/commit/f7e0851b132e204ec076fc93110fbd81fdfac3ff))

* perf(UI): Improve performance when generating report ([`d0e0228`](https://github.com/EUCANCan/oncoliner/commit/d0e0228e5fc6b779f4966cf2ee2e78aca5088692))

* perf: Improve VCF intersection performance ([`3af5c5d`](https://github.com/EUCANCan/oncoliner/commit/3af5c5d0932933b00030bcd18ec3d6892c384d68))

### Unknown

* deps(UI): Change HTML minify library ([`8c67f1a`](https://github.com/EUCANCan/oncoliner/commit/8c67f1a7045db1e89bc5f83813538861716f14b7))


## v0.1.0 (2023-10-17)

### Feature

* feat(PipelineDesigner): Check for combination improvement ([`03152ae`](https://github.com/EUCANCan/oncoliner/commit/03152ae2522a7930b9407c512c6f2b37708c29cd))

* feat: Include UI module ([`1df8532`](https://github.com/EUCANCan/oncoliner/commit/1df8532fec303b97575d7c2186a2032fbb57377e))

* feat: Add example to improvement module ([`6d024f1`](https://github.com/EUCANCan/oncoliner/commit/6d024f1fe97d0028f06a02fb560d764baffc270f))

* feat: Add public data example ([`40cb24d`](https://github.com/EUCANCan/oncoliner/commit/40cb24db518059a0c5b52e7031f99accd9feef38))

* feat: Complete pipeline designer ([`775caaa`](https://github.com/EUCANCan/oncoliner/commit/775caaae46150e23e0b24906b835688fbae1eafd))

* feat: Add pipeline designer tool ([`d17058d`](https://github.com/EUCANCan/oncoliner/commit/d17058d3319f21bc4a7d5eab9b39f87ee4d09ccc))

* feat: Add Dockerfile and singularity.def ([`4f6d8c6`](https://github.com/EUCANCan/oncoliner/commit/4f6d8c66e96fbd2455b898fcbd5255395f0bf55d))

* feat: Add improvement and harmonization ([`26c2418`](https://github.com/EUCANCan/oncoliner/commit/26c2418d338ce7df98a126ca3ff8e205390afe29))

* feat: Include assesment module ([`08090f2`](https://github.com/EUCANCan/oncoliner/commit/08090f2967f8ddd79b890225c6893442d53d315a))

* feat: Add harmonization and UI ([`7b7623a`](https://github.com/EUCANCan/oncoliner/commit/7b7623a2ea033a484d2519fbd8e4537cd80b4dfb))

* feat: Integrate with evaluation module ([`4876ebb`](https://github.com/EUCANCan/oncoliner/commit/4876ebb018481ea00f735bfb320513d43c7dd0a5))

### Fix

* fix: Add vcf_ops command tools ([`99972af`](https://github.com/EUCANCan/oncoliner/commit/99972af37b1aad83d5cfede479425c01f184a2f9))

* fix: Update Docker and Singularity recipies ([`59deac9`](https://github.com/EUCANCan/oncoliner/commit/59deac9790c46fd213e5a36a15477dfb8278da4c))

* fix(UI): Change minification packages ([`683e3fa`](https://github.com/EUCANCan/oncoliner/commit/683e3fa97fa12d546d116109563f5fc1770fd6db))

* fix(UI): Add missing columns ([`a3731df`](https://github.com/EUCANCan/oncoliner/commit/a3731df9206015e98366dc11898c47e9da41913d))

* fix(UI): Remove empty warnings ([`6ea051d`](https://github.com/EUCANCan/oncoliner/commit/6ea051d7f720d4527c67a478c255f93b2a90b0e4))

* fix: Change to window_radius in harmonization ([`45e28fb`](https://github.com/EUCANCan/oncoliner/commit/45e28fb6276d0e367d2e26be07e5936aa0e03ba0))

* fix: Fix container files ([`20f8497`](https://github.com/EUCANCan/oncoliner/commit/20f84975edaef73c508a2d1a726dab8e22211034))

* fix: Remove deprecated .warn ([`07742e4`](https://github.com/EUCANCan/oncoliner/commit/07742e4c7af8385cf6dee39b9742d874c7c466bc))

* fix: Change to warning if pipeline folder has more samples than config ([`567d042`](https://github.com/EUCANCan/oncoliner/commit/567d042eb7006185b5ec59e177d06c09fffb5512))
