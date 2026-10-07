# Changelog

All notable changes to the **PQL.Assert** DAX unit-testing library are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html). The version numbers below
match the `version` value in [src/manifest.daxlib](src/manifest.daxlib) and the
`DAXLIB_PackageVersion` annotation on each assertion function.

---

## [0.7.0] - 2026-10-07

### Added
- Text prefix, suffix, and containment column assertions. DAX has no `STARTSWITH`/`ENDSWITH`
  functions, so these use `LEFT()` and `RIGHT()`:
  - `PQL.Assert.Col.ShouldStartWith(testName, columnRef, prefix, [matchCase])`
  - `PQL.Assert.Col.ShouldNotStartWith(testName, columnRef, prefix, [matchCase])`
  - `PQL.Assert.Col.ShouldEndWith(testName, columnRef, suffix, [matchCase])`
  - `PQL.Assert.Col.ShouldNotEndWith(testName, columnRef, suffix, [matchCase])`
  - `PQL.Assert.Col.ShouldContainString(testName, columnRef, substring, [matchCase])`
  - `PQL.Assert.Col.ShouldNotContainString(testName, columnRef, substring, [matchCase])`
- Optional `matchCase` argument on each of the six new assertions. Omit it for case-insensitive
  comparison, or pass `"Y"`/`"YES"`/`"TRUE"`/`"1"` for case-sensitive comparison.
- TestingModel fixture columns `TestData[Order Code]` (`ORD-001-US` … `ORD-005-US`),
  `TestData[Sparse Code]` (the same codes with blanks on even rows) and `TestData[Short Text]`
  (`"x"`, `""`, `"Error - Timeout"`, `"Err"`, blank), plus 38 pass/fail cases in `Col.Tests.dax`.
  The cases cover the omitted and explicit `matchCase` argument, blank values (skipped), values shorter
  than the prefix/suffix (where `LEFT()`/`RIGHT()` go past the end of the value), and an empty prefix/suffix.

---

## [0.6.2] - 2026-09-08

### Added
- `PQL.Assert.Col.IsAvailableInMDX(testName, tableName, columnName)` validates that a column is
  available to MDX clients such as Analyze in Excel.
- TestingModel fixture coverage for MDX availability using a real `MDX Disabled Column` with
  `isAvailableInMdx: false`, plus pass/fail cases in `Col.Tests.dax`.
- Cloud-agent Sudolang workflow for maintaining release notes via `updateChangelog`, including
  manifest-version validation, Keep a Changelog section grouping, duplicate-heading checks, and
  command/pattern routing for changelog and release-note requests.
- Documentation guidance for model-independence audits so reusable assertion functions avoid
  schema assumptions on TABLE parameters and distinguish user-supplied tables from `INFO.*`
  metadata tables.

### Changed
- `PQL.Assert.Col.IsAvailableInMDX` resolves the target column ID from `INFO.VIEW.COLUMNS()` and
  reads `IsAvailableInMDX` from `INFO.COLUMNS()` so the assertion checks the reliable metadata
  source while still accepting table and column names.
- Custom-agent documentation now lists changelog maintenance and model-independence review as
  supported semantic-model testing workflows.
- Clarified that set operations are acceptable after normalizing table expressions with explicit
  value columns, and that joins over `INFO.*` metadata are not the same risk as joins over
  user-supplied TABLE parameters.

---

## [0.6.0] - 2026-08-31

### Added
- `PQL.Assert.Relationship.ShouldExist` now accepts three optional parameters for validating
  relationship configuration in addition to existence:
  - `fromCardinality` (`"One"` / `"Many"`)
  - `toCardinality` (`"One"` / `"Many"`)
  - `securityFilteringBehavior` (`"OneDirection"` / `"BothDirections"`)
- Expected / Actual messages now include the checked cardinality and security-filtering values so
  failures are easier to diagnose.

### Changed
- Bumped `DAXLIB_PackageVersion` to `0.6.0` on all assertion functions.
- Reorganized example assets: `PQL Assert Test Results Template.pbit` moved under
  `examples/customconnector/`, and `nb-verified-backups.ipynb` moved under
  `examples/verified-backups/`.

### Fixed
- Short-circuit the optional cardinality / security-filtering checks when a relationship is not
  found so the assertion reports a single, clear "NOT FOUND" failure instead of cascading errors.

---

## [0.5.0] - 2026-06-29

### Added
- **Perspective assertions** — new `functions-perspective-assertions.tmdl` with checks for
  perspectives, perspective tables, columns, and measures.
- **Partition assertions** — new `functions-partition-assertions.tmdl` including
  `PQL.Assert.Partition.ShouldExist` with optional parameters, and Direct Lake residency
  assertions.
- **Model-independent perspective validation**: `ShouldContain` refactored to accept
  comma-separated `STRING` lists for tables, columns, and measures so tests don't need to be
  regenerated for every model.
- New `model-independence` skill documenting the pattern for authoring model-independent tests.
- New `PQLAssert_RoleName` annotation surfaced by `RetrieveTests*` metadata (companion to the
  existing `PQLAssert_ImpersonatedUserName`).
- `PQL.Assert` skill (`SKILL.md`) documenting the DAX unit-testing library for custom agents.

### Changed
- Bumped `DAXLIB_PackageVersion` to `0.5.0` on all assertion functions.
- README updated to document `PQLAssert_RoleName` in `RetrieveTestsV2` metadata.
- Perspective schema checks and partition existence assertions now expose optional parameters for
  more flexible validation.

---

## [0.4.0] - 2026-05-27

### Added
- **Cloud/custom agent support**: `pql-tester-sudo.md` cloud agent and `power-query-tester.agent.md`
  custom agent added under `examples/`.
- `SKILLS.md` and `dax-query-guidelines` skill for agent tooling.
- `ReservedDAXWords.md` reference documenting DAX reserved words to avoid in test naming.
- Consolidated `functions.tmdl` build artifact for downstream consumers on `0.3.0`+.

### Changed
- Bumped `DAXLIB_PackageVersion` to `0.4.0` across all `PQL.Assert.*` functions.
- Documentation and examples updated to target `0.3.0` and higher.

---

## [0.3.1] - 2026-04-07

### Added
- **Object-Level Security (OLS) assertions** — new `functions-ols-assertions.tmdl` with
  assertions for validating column and table OLS configuration.
- OLS-focused refactor of the PQL.Assert function tester in the `TestingModel` and `RLS_Model`.

### Changed
- Bumped `DAXLIB_PackageVersion` to `0.3.1` for the `PQL.Assert` namespace only; best-practice
  (`BP`), column (`Col`), and table (`Tbl`) namespaces reverted to `0.2.0` so their version numbers
  reflect their actual change cadence.
- Cleaned up obsolete `localSettings.json` files and cached `.abf` files from the test models.

### Removed
- Deprecated error-assertion functions superseded by the new OLS pattern.

---

## [0.3.0] - 2026-04-05

### Added
- **Row-Level Security (RLS) testing**:
  - New `RLS_Model.pbip` test model with security roles and impersonation configuration.
  - `PQL.Assert.ShouldThrow` and `PQL.Assert.ShouldNotThrow` for validating that RLS-protected
    queries fail (or don't fail) as expected.
  - Assertion functions updated to honor user impersonation.
- **Fabric Notebook example** (`examples/fabric-notebook/RunPQLAssertTests.ipynb`) — multi-workspace
  test runner that uses `sempy_labs.evaluate_dax_impersonation` and the Fabric REST API to discover
  semantic models via OData filters.
- Environment-aware test discovery: `RetrieveTests` / `RetrieveTestsByEnvironment` now support a
  `callFromPowerAutomate` mode for compatibility with the Power Automate *Execute Dataset Query*
  action.
- V2 discovery functions (`RetrieveTestsV2`, `RetrieveTestsByEnvironmentV2`) returning full
  metadata (Description, `PQLAssert_ImpersonatedUserName`).
- Power BI file patterns added to `.gitignore`.

### Changed
- Bumped package version from `0.2.0` to `0.3.0`.
- Documentation clarified around V1 vs V2 discovery functions and their Power Automate
  compatibility.

### Removed
- Assertions for invalid characters in object names and foreign-key visibility checks (replaced by
  newer best-practice functions).

---

## [0.2.0] - 2026-03-19

### Added
- Initial RLS testing scaffolding and updates in preparation for full RLS support in `0.3.0`.
- Skills and custom-agent examples introduced under `examples/custom-agents/`.
- Sample models for Part 1, Part 2, and Part 3 of the video series added under
  `examples/samples-from-videos/`.
- `Combine-TmdlFiles.ps1` script improvements — inserts blank lines between functions for
  readability.

### Changed
- Bumped package version from `0.1.10` to `0.2.0`.
- Renamed `ValueShould*` assertions to reflect the newer naming convention.
- TMDL combining script now handles spacing and PowerShell edge cases correctly.

---

## [0.1.10] - 2026-02-23

### Added
- Additional testing patterns and expanded test coverage.
- Sample models for Part 1 and Part 2 of the video series.

### Changed
- Bumped package version to `0.1.10`.
- Refined tests and removed obsolete pattern-based helper functions.
- Improved `Combine-TmdlFiles.ps1` and related agent instructions.

### Fixed
- Icon (`icon.png`) is now correctly copied by the publish GitHub Action.

---

## [0.1.9] - 2026-02-09

### Added
- DAX test files for `Col` and `Tbl` assertions.
- `ShouldHaveColumns` documentation now describes the column-count limit.

### Changed
- Bumped package version to `0.1.9`.
- Expanded testing and agent setup.

### Fixed
- Removed an unused variable in `PQL.Assert.Col.ShouldBeUniqueWithin`.

---

## [0.1.8] - 2026-02-09

### Added
- New library files: `functions-col-assertions.tmdl` and `functions-tbl-assertions.tmdl`, splitting
  column and table assertions out of the monolithic `functions.tmdl`.
- `PQL.Assert.BP.ShouldHideFactTableColumns` best-practice assertion.

### Changed
- Bumped all annotations to `0.1.8`.

---

## [0.1.7] - 2026-02-09

### Added
- New testing functions for column and table validations.

### Fixed
- `PQL.Assert.BP.ShouldMarkPrimaryKeys` corrected.
- Fixed extraneous newline in the TMDL combining script.
- Updated tabs / whitespace in the TMDL combining scripts.

---

## [0.1.6] - 2026-02-08

### Added
- New best-practice (BP) functions covering preliminary best-practice checks via
  `INFO.VIEW.*`.
- Custom agent logic in the examples folder.
- Updated publishing process.

### Changed
- Bumped package version to `0.1.6`.
- Revised DAX queries used by the test model.

---

## [0.1.5] - 2026-02-02

### Added
- `PQL.Assert.BP.ShouldAvoidBiDirectionalOnHighCardinalityColumn` best-practice assertion.

### Changed
- Performance-testing stopping-point checkpoint.

---

## [0.1.4] - 2026-02-02

### Changed
- Updates to `PQL.Assert.Col.ShouldNotBeBlank` and related column-assertion behaviors.
- Bumped package version to `0.1.4`.

---

## [0.1.3] - 2026-01-29

### Added
- `PQL.Assert.RetrieveTestsByEnvironment` for filtering test discovery by environment
  (`DEV`, `TEST`, `PROD`, `ANY`, etc.).
- Power Automate testing example.

### Fixed
- Corrected `DAXLIB_PackageVersion` annotations that were out of sync across functions.

---

## [0.1.2] - 2026-01-27

### Changed
- Revised the `PQL.Assert` library description used in the DAXLIB manifest.
- Renamed `GLOBAL` environment token to `ANY` — `GLOBAL` is a reserved DAX word and caused issues
  with the environment-based naming convention.

---

## [0.1.1] - 2026-01-27

### Added
- Library icon (`icon.png`) referenced from `src/manifest.daxlib`.

### Changed
- Removed usage of `ALL` from the library documentation (reserved word in DAX).
- Updated tests and annotations following the first round of PR review.

---

## [0.1.0] - 2026-01-21

### Added
- Initial public release of **PQL.Assert**.
- Core `PQL.Assert.*` assertion functions:
  - Boolean / null / blank: `ShouldBeTrue`, `ShouldBeFalse`, `ShouldBeNull`, `ShouldNotBeNull`,
    `ShouldBeBlank`, `ShouldNotBeBlank`, `ShouldBeNullOrBlank`, `ShouldNotBeNullOrBlank`.
  - Equality / comparison: `ShouldEqual`, `ShouldNotEqual`, `ShouldEqualExactly`,
    `ShouldBeGreaterThan`, `ShouldBeLessThan`, `ShouldBeGreaterOrEqual`, `ShouldBeLessOrEqual`,
    `ShouldBeBetween`.
  - String: `ShouldStartWith`, `ShouldEndWith`, `ShouldContainString`, `ShouldMatch`.
  - Discovery: `PQL.Assert.RetrieveTests`.
- Initial `TestingModel.pbip` with DAX Query View test files.
- Baseline documentation, licensing, and repository scaffolding.

---

[0.6.0]: https://github.com/clientfirsttech/PQL.Assert/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/clientfirsttech/PQL.Assert/compare/v0.4.0...v0.5.0
[0.4.0]: https://github.com/clientfirsttech/PQL.Assert/compare/v0.3.1...v0.4.0
[0.3.1]: https://github.com/clientfirsttech/PQL.Assert/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/clientfirsttech/PQL.Assert/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/clientfirsttech/PQL.Assert/compare/v0.1.10...v0.2.0
[0.1.10]: https://github.com/clientfirsttech/PQL.Assert/compare/v0.1.9...v0.1.10
[0.1.9]: https://github.com/clientfirsttech/PQL.Assert/compare/v0.1.8...v0.1.9
[0.1.8]: https://github.com/clientfirsttech/PQL.Assert/compare/v0.1.7...v0.1.8
[0.1.7]: https://github.com/clientfirsttech/PQL.Assert/compare/v0.1.6...v0.1.7
[0.1.6]: https://github.com/clientfirsttech/PQL.Assert/compare/v0.1.5...v0.1.6
[0.1.5]: https://github.com/clientfirsttech/PQL.Assert/compare/v0.1.4...v0.1.5
[0.1.4]: https://github.com/clientfirsttech/PQL.Assert/compare/v0.1.3...v0.1.4
[0.1.3]: https://github.com/clientfirsttech/PQL.Assert/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/clientfirsttech/PQL.Assert/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/clientfirsttech/PQL.Assert/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/clientfirsttech/PQL.Assert/releases/tag/v0.1.0
