# Changelog

All notable changes to the **PQL.Assert** DAX unit-testing library are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html). The version numbers below
match the `version` value in [src/manifest.daxlib](src/manifest.daxlib) and the
`DAXLIB_PackageVersion` annotation on each assertion function.

---

## [0.9.0] - 2026-10-29

Additive only. No existing function changes name, parameters or result, and no existing `Expected` or
`Actual` text changes. A 0.8.0 suite gives the same results on 0.9.0, apart from freshness ages, which
depend on when the suite runs.

### Added
- `Tbl.LastRefreshShouldBeWithinHours(testName, tableName, maxAgeHours)` checks refresh recency
  (ODCS `frequency`): the table's newest partition `RefreshedTime` from `INFO.PARTITIONS()` must be at
  most `maxAgeHours` before `UTCNOW()`. `Actual` is `Last refresh N hour(s) ago`, `TABLE NOT FOUND` or
  `NEVER REFRESHED`; the last two fail. An empty table that refreshed passes.
- README section "Freshness: latency vs frequency", with an ODCS SLA mapping, and a note on the
  permissions `INFO.PARTITIONS()` needs (workspace Contributor or above).
- Live checks in Power BI Desktop, recorded in the function description: a never-refreshed partition
  reports `RefreshedTime` 1699-12-31 (`NEVER REFRESHED`), `RefreshedTime` is UTC, and calculated
  tables get a `RefreshedTime` from the model refresh.
- Tests: five cases in `Tbl.ANY.Tests` (pass, tight-threshold fail, unknown table, and checks on the
  `Actual` text), and a 24-hour case in `Partition.SVC.Tests`, which runs in the service after the CI
  refresh.

### Changed (documentation only)
- `Col.MaxDateShouldBeWithinDays` / `…Hours` descriptions say what the column decides: a load or
  ingestion timestamp checks data age (ODCS `latency`), a refresh-log column checks refresh recency
  (use `Tbl.LastRefreshShouldBeWithinHours` instead), and a business date gives false failures. The
  refresh-log example is replaced by a load timestamp.
- `Partitions.ShouldBe`, `Partitions.ShouldExist` and `Partitions.ShouldBeAtLeast` descriptions say
  they check partition structure, not freshness.
- `LibraryVersion()` returns `"0.9.0"`.

---

## [0.8.0] - 2026-10-26

No existing function changes name or parameters. 0.8.0 applies one NULL (`BLANK()`) policy across the
library (see "Changed (behavior)" and the README section "NULL vs blank"). Results change only for NULL
input, all-NULL columns and empty tables, plus mean, percentile and standard deviation on columns with
repeated values, which 0.7.x computed over distinct values. Deprecated functions keep their 0.7.x
behavior. A 0.7.1 test on columns and values without NULLs gives the same result on 0.8.0.

### Added
- `PQL.Assert.LibraryVersion()` returns the installed version (`"0.8.0"`). Tools can detect 0.8.0+
  with `EVALUATE { PQL.Assert.LibraryVersion() }`; an error means 0.7.x or older.
- Row-based null and blank checks. They take `tableRef` as well as `columnRef` because a column
  reference alone gives distinct values, not rows. Percentages are 0-100.
  - `Col.NullCountShouldBeAtMost(testName, tableRef, columnRef, maxCount)`. Pass `0` for "no row is NULL".
  - `Col.NullRateShouldBeAtMostV2`, `Col.BlankRateShouldBeAtMostV2`,
    `Col.NullOrBlankRateShouldBeAtMostV2`, `Col.PopulatedRateShouldBeAtLeastV2`
    `(testName, tableRef, columnRef, pct)`. NULL means `BLANK()`, blank means `""`, and the blank
    check works on columns of any data type.
- Row-based, NULL-safe share checks: `Col.ShareOfZerosAtMostV2`, `Col.ShareOfEvensAtLeastV2` and
  `Col.ShareOfOddsAtLeastV2` `(testName, tableRef, columnRef, pct)`. They skip NULL rows instead of
  treating NULL as 0, like the other numeric checks, and divide by non-NULL rows.
- NULL-aware uniqueness: `Col.NonNullValuesShouldBeDistinct(testName, columnRef)` (NULLs ignored),
  `Col.ShouldBePrimaryKey(testName, columnRef)` (no NULL or `""`, all distinct) and
  `Col.DuplicateCountShouldBeAtMost(testName, columnRef, maxCount)`.
- `Tbl.RowsShouldBeDistinct(testName, keyTable)` for composite keys of any width, passed as a
  `SELECTCOLUMNS` projection.
- `Tbl.RowCountShouldBeAtMost(testName, filteredTable, maxCount)` and
  `Tbl.RowRateShouldBeAtMost(testName, filteredTable, baseTable, maxPct)` for "at most N / N% of rows
  break a rule" checks.
- `PQL.Assert.ShouldNotBeBetween(testName, lowerBound, upperBound, actual)`, the inverse of
  `ShouldBeBetween` with the same argument order.
- Freshness checks against `UTCNOW()`. An empty column fails, and the column should be stored in UTC.
  - `Col.MaxDateShouldBeWithinDays(testName, columnRef, maxAgeDays)`
  - `Col.MaxDateShouldBeWithinHours(testName, columnRef, maxAgeHours)`, e.g. a refresh-log
    timestamp that must be no older than 3 hours.
- TestingModel fixture columns `TestData[Dup With Blank]` (`1, 1, 2, 3, NULL`),
  `TestData[Distinct With Blank]` (`10, 20, 30, 40, NULL`), `TestData[Signed With Blank]`
  (`-1, 0, 0, 2, NULL`) and `TestData[Empty Text]` (all `""`), plus 57 pass/fail cases across
  `Col.ANY.Tests`, `Tbl.ANY.Tests` and `Assert.ANY.Tests`. They include cases that pin the deprecated
  behavior (the `{1, 1, NULL}` false pass of `Col.ShouldBeDistinct`, `Col.ShouldBeBlank` passing an
  all-NULL column, `Col.ShouldNotBeBlank` failing on NULL), cases for the `ShouldBePositive` and
  `ShouldBeNonZero` behavior change, and a check that `LibraryVersion()` matches its
  `DAXLIB_PackageVersion` annotation.
- `NullHandling.ANY.Tests`, a TestingModel suite of 68 cases for the NULL policy: value checks on
  all-NULL columns (fixture `TestData[Null Text]` and `TestData-Fact[Blank Column]`), row-based
  statistics, set membership with NULL, empty tables, and scalar checks with a NULL `actual`. It is
  registered in `daxQueries.json` and the CI gate.
- `ModelIndependence.ANY.Tests`, 18 cases that run every TABLE-parameter function on virtual tables
  (`DATATABLE`) that are not in the model, with column names such as `Weird Col #1`, `Name` and
  `Allowed Code (x)`. No library function assumes a column name on a TABLE parameter; the same
  functions were also checked against RLS_Model, which has a different schema.
- `examples/custom-agents/skills/dax-blank-handling/SKILL.md`, a SudoLang skill for reviewing NULL
  (`BLANK()`) and empty-string handling in DAX. Its language rules are summarized from
  [Handling BLANK in DAX](https://www.sqlbi.com/articles/blank-handling-in-dax/) by Marco Russo
  (SQLBI). It adds the PQL.Assert NULL/blank vocabulary and the aggregation behavior verified on
  TestingModel. The 0.8.0 NULL/blank review was done with this skill.

### Deprecated
Kept unchanged until 1.0; the descriptions now say what to use instead. The README section
"Deprecated functions and replacements" maps each one to its replacement and explains the difference.
- `Col.NullRateShouldBeAtMost`, `Col.BlankRateShouldBeAtMost`, `Col.NullOrBlankRateShouldBeAtMost`
  and `Col.PopulatedRateShouldBeAtLeast` divide by the number of distinct values, not rows, so the
  reported rate is wrong for any column with repeated values. Use the `V2` functions, which take
  `tableRef` as a new second argument. `Col.NullRateShouldBeAtMost` also counts `""` as NULL
  (it uses `COUNTBLANK`); `NullRateShouldBeAtMostV2` counts only `BLANK()`, so use
  `NullOrBlankRateShouldBeAtMostV2` to keep counting both.
- `Col.ShouldBeBlank` and `Col.ShouldNotBeBlank` are duplicates of `Col.ShouldBeNullOrBlank` and
  `Col.ShouldNotBeNullOrBlank` (same logic and results), although their names suggest empty strings
  only: `Col.ShouldBeBlank` passes an all-NULL column and `Col.ShouldNotBeBlank` fails on NULL rows,
  unlike the scalar versions. Use the `NullOrBlank` functions, or
  `Col.BlankRateShouldBeAtMostV2(…, 0)` to check for empty strings only.
- `Col.ShareOfZerosAtMost`, `Col.ShareOfEvensAtLeast` and `Col.ShareOfOddsAtLeast` count NULL as 0
  (`BLANK() = 0` and `MOD(BLANK(), 2) = 0` are TRUE in DAX) and divide by distinct values. Use the
  `V2` functions.
- `Col.ShouldBeDistinct` and `Col.ShouldNotContainDuplicates` compare `DISTINCTCOUNT` (counts BLANK)
  with `COUNTA` (ignores BLANK). One BLANK fails a distinct column, and `{1, 1, BLANK}` passes. Use
  `Col.NonNullValuesShouldBeDistinct` or `Col.ShouldBePrimaryKey`.

### Changed (behavior)
NULL policy, from a review with the `dax-blank-handling` skill. In DAX `BLANK() = 0`, `BLANK() = ""`
and `BLANK() = FALSE` are TRUE, so several checks treated NULL as a value:
- `Col.ShouldBePositive` and `Col.ShouldBeNonZero` skip NULL. In 0.7.x `{10, 20, 30, 40, NULL}` failed
  both (`BLANK() <= 0` and `BLANK() = 0`); it now passes.
- `Col.MeanShouldBeInRange`, `Col.PctileShouldBeInRange` and `Col.StdDevShouldBeAtMost` are computed
  over rows with NULL skipped. 0.7.x used distinct values, ranked NULL as the lowest value in the
  percentile and counted it as 0 in the standard deviation: on `{10, 20, 30, 40, NULL}` P50 was 20
  (now 25) and StdDev 16.77 (now 12.91); on `{1, 1, 2, 3, NULL}` the mean was 2 (now 1.75).
- Value checks fail with NO VALUES when the column has no non-NULL value: range, min, max, mean,
  percentile, standard deviation, sign, the text checks, set membership, `ShouldBeUniqueWithin`,
  `ComboShouldBeDistinct`, and the new uniqueness and share V2 functions. In 0.7.x they passed, or
  passed only when 0 was inside the range (`ShouldBeInRange(-5, 5)` passed an all-NULL column).
- The row-based rate V2 functions, `Tbl.RowRateShouldBeAtMost` and `Tbl.RowsShouldBeDistinct` fail
  with NO ROWS on an empty table. Problem counts (`NullCountShouldBeAtMost`,
  `Tbl.RowCountShouldBeAtMost`) still pass at zero.
- `Col.ValuesShouldBeInSet` and `Col.ValuesShouldNotBeInSet` skip NULL. 0.7.x reported a NULL as
  outside the allowed set.
- Scalar `ShouldBeGreaterThan`, `ShouldBeLessThan`, `ShouldBeGreaterOrEqual`, `ShouldBeLessOrEqual`,
  `ShouldBeBetween`, `ShouldStartWith`, `ShouldEndWith`, `ShouldContainString` and `ShouldMatch` fail
  when `actual` is NULL, shown as "NULL". 0.7.x compared it as 0 or `""`, so
  `ShouldBeGreaterThan(-1, BLANK())` passed.
- `ShouldEqualExactly` treats NULL and `""` as different, like `ShouldEqual`.
- Not changed: `ShouldBeTrue` / `ShouldBeFalse`. Their BOOLEAN parameter converts `BLANK()` to FALSE
  before the function runs, so `ShouldBeFalse(BLANK())` still passes; the descriptions now say so.
  Changing it would need a different parameter type.

### Changed
- Documentation only: `Col.ShouldNotBeNull` checks that a column has at least one non-NULL value,
  not that no row is NULL. `ShouldMatch` is a case-insensitive substring match with `?`/`*`
  wildcards, not a regular expression. README examples now use `Col.NullCountShouldBeAtMost(…, 0)`
  and `Col.ShouldBePrimaryKey`.
- `scripts/Bump-Version.ps1` also updates `src/manifest.daxlib` and the `LibraryVersion` literal,
  keeps each file's BOM state, and runs under Windows PowerShell 5.1 (it previously failed to parse
  there because of a non-ASCII character).
- Regenerated TestingModel `TMDLScripts/Load PQL*.tmdl` from `src/lib`. They had drifted since
  before 0.7.0 (17 functions missing, older bodies in the BP and Col scripts). `Load PQL.tmdl` is
  `functions-assertions` plus `functions-ols-assertions`, and `Load PQL.BP.tmdl` is now the full
  `functions-bp-performance` file. `tests/clear-functions.tmdl` lists the new functions.

---

## [0.7.1] - 2026-10-15

### Changed
- Renamed the `tableRef` parameter to `tableName` on `Tbl.ShouldHaveColumns`,
  `Tbl.ShouldNotHaveExtraColumns` and `Tbl.ColumnDataTypeShouldBe`. These take the table as a
  STRING name (for example `"Sales"`), not a table reference; the old name suggested otherwise.
  Only affects callers passing the argument by name.
- Added `@param` doc comments to those three functions and updated the README signatures.

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
