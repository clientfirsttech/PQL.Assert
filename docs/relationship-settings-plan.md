# Plan: Cross-Filter Direction and Active State in `Relationship.ShouldExist` (0.9.1)

**Status:** Implemented on `dev` (2026-11-17). Checked in Power BI Desktop on TestingModel: `Assert.ANY.Tests` passes 167 of 167, and every other ANY suite passes. The CI gate run is still to do · **Branch:** `dev` · **Created:** 2026-11-17

## Goal

`PQL.Assert.Relationship.ShouldExist` can check every setting on Power BI's **Edit relationship** dialog that changes how the model filters, without a new function and without changing any existing call or result:

1. Add two optional arguments at the end: `crossFilteringBehavior` and `isActive`.
2. Fix the description of `securityFilteringBehavior`, which reads like the cross-filter direction but is the RLS checkbox.

Out of scope: **Assume referential integrity** (`relyOnReferentialIntegrity`), which only DirectQuery relationships can set (it is greyed out on Import), and `joinOnDateBehavior`, which is not on the dialog. Both can be appended later as arguments 11 and up without breaking calls.

## The problem

The 8th argument, `securityFilteringBehavior`, is named after the model property it checks, and that part is correct. The documentation calls it the "expected filter direction", which most readers take to mean the **Cross-filter direction** dropdown. It is the **Apply security filter in both directions** checkbox, which only affects row-level security.

On a relationship set to cross-filter **Both** with the security box unchecked (checked in Power BI Desktop on 2026-11-17):

| Source | Cross-filter | Security filter |
|---|---|---|
| Edit relationship dialog | Both | unchecked |
| TMDL | `crossFilteringBehavior: bothDirections` | (no line: default `oneDirection`) |
| `INFO.VIEW.RELATIONSHIPS()` | `BothDirections` | `Single` |
| `ShouldExist(…, "", "", "BothDirections")` | — | **fails**: `SecurityFiltering: OneDirection` |

So a test written to guard "this relationship is single direction" with `"OneDirection"` keeps passing after someone switches the relationship to Both, and nothing can check whether a relationship is active. Both changes alter the numbers every visual shows.

The test model has the same trap: `TestData[ID] → TestData-Fact[ID]` is cross-filter Both, and `Assert.ANY.Tests` asserts that `SecurityFiltering=BothDirections` fails on it, which is correct but easy to misread.

## Dialog, TMDL, and arguments

| Edit relationship dialog | TMDL (written only when not the default) | `INFO.RELATIONSHIPS()` | `ShouldExist` argument | Values |
|---|---|---|---|---|
| Cardinality | `fromCardinality: one`, `toCardinality: many` (defaults `many`, `one`) | `FromCardinality`, `ToCardinality` (1 One, 2 Many) | `fromCardinality`, `toCardinality` (6, 7) | `One`, `Many` |
| Apply security filter in both directions | `securityFilteringBehavior: bothDirections` (default `oneDirection`) | `SecurityFilteringBehavior` (1 OneDirection, 2 BothDirections, 3 None) | `securityFilteringBehavior` (8) | `OneDirection` (unchecked), `BothDirections` (checked), `None` (see D4) |
| **Cross-filter direction** | `crossFilteringBehavior: bothDirections` (default `oneDirection`) | `CrossFilteringBehavior` (1 OneDirection, 2 BothDirections, 3 Automatic) | **`crossFilteringBehavior` (9, new)** | `OneDirection` (Single), `BothDirections` (Both), `Automatic` |
| **Make this relationship active** | `isActive: false` (default true) | `IsActive` | **`isActive` (10, new)** | `TRUE`, `FALSE` |

Each argument keeps the TMDL property name of the setting it checks, the convention the existing arguments already follow. Values are the TOM enum names, which TMDL writes in camelCase (`bothDirections`); comparison is case-insensitive, so either spelling passes.

Two values are not on the dialog. `Automatic` (cross-filter) and `None` (security filter) can only be set through TMSL, TMDL, or an external tool. `None` blocks RLS filter propagation on limited relationships to another semantic model or Analysis Services database.

## Design

```dax
function 'PQL.Assert.Relationship.ShouldExist' =
    (
        testName : STRING,
        fromTable : STRING, fromColumn : STRING,
        toTable : STRING, toColumn : STRING,
        fromCardinality : STRING = "",
        toCardinality : STRING = "",
        securityFilteringBehavior : STRING = "",
        crossFilteringBehavior : STRING = "",   // new in 0.9.1
        isActive : STRING = ""                  // new in 0.9.1
    ) => …
        // CrossFilteringBehavior: 1 = OneDirection, 2 = BothDirections, 3 = Automatic
        VAR _ActualCrossFiltering = MAXX(_MatchingRel, SWITCH([CrossFilteringBehavior], 1, "OneDirection", 2, "BothDirections", 3, "Automatic", "Unknown"))
        VAR _ActualIsActive = MAXX(_MatchingRel, IF([IsActive], "TRUE", "FALSE"))
        VAR _CrossFilterOk = IF(crossFilteringBehavior = "" || NOT _Found, TRUE, UPPER(_ActualCrossFiltering) = UPPER(crossFilteringBehavior))
        VAR _IsActiveOk = IF(isActive = "" || NOT _Found, TRUE, UPPER(_ActualIsActive) = UPPER(isActive))
        VAR _Passed = _Found && _FromCardOk && _ToCardOk && _SecFilterOk && _CrossFilterOk && _IsActiveOk

        // Existing line, extended (D4): 3 = None, which 0.9.0 reports as "Unknown"
        VAR _ActualSecFiltering = MAXX(_MatchingRel, SWITCH([SecurityFilteringBehavior], 1, "OneDirection", 2, "BothDirections", 3, "None", "Unknown"))
```

- `Expected` gains ` | CrossFiltering: <value>` and ` | IsActive: <value>`, and `Actual` the same with the model's values, each **only when that argument is not `""`**, appended after the existing parts. `CrossFiltering` mirrors the existing `SecurityFiltering` label (D5), so a failure message shows which of the two settings failed.
- `isActive` is `STRING`, not `BOOLEAN`, so `""` can mean "skip", like every other optional argument. Values compare case-insensitively.
- Both reads reuse `_MatchingRel`, which the function already computes from `INFO.RELATIONSHIPS()`: no new INFO call and no new permission.

## Compatibility (non-breaking)

- DAX function arguments are positional. Every existing call passes 5 to 8 arguments, and arguments 9 and 10 default to `""`, so each existing call evaluates exactly as on 0.9.0.
- With the new arguments empty, `Expected`, `Actual` and `Passed` are byte-for-byte the 0.9.0 text. A 0.9.0 suite gives the same results on 0.9.1.
- No function is added, renamed or removed. The CHANGELOG entry opens "Additive only", as 0.9.0's does.
- The new parameter names match `INFO.RELATIONSHIPS()` columns (`[CrossFilteringBehavior]`, `[IsActive]`) the way `fromCardinality` already matches `[FromCardinality]`. Column references are bracketed, so they cannot collide with parameter names, and neither name is in `ReservedDAXWords.md`.
- The one result that can change is D4's: a call that passes `securityFilteringBehavior` on a limited relationship now reports `None` instead of `Unknown`. That call could only pass on 0.9.0 with the undocumented value `"Unknown"`. The CHANGELOG says so under Fixed.
- Tools that detect the library by function name cannot tell 0.9.0 and 0.9.1 apart. They need `PQL.Assert.LibraryVersion()`, the `DAXLIB_PackageVersion` annotation, or the parameter count (10).
- Released as a patch, 0.9.1: the change fixes how `Relationship.ShouldExist` describes and reports its settings, and the two new arguments are optional and skipped by default. Strict Semantic Versioning would call new optional arguments a minor release (0.9.1); the patch number was chosen because no existing call changes.
- Checked in Power BI Desktop on 2026-11-17 against a model with 0.9.0 installed, a many-to-one relationship with cross-filter Both. Six existing 5- to 8-argument calls were run through both the installed 0.9.0 function and the new one, and returned identical `Expected`, `Actual` and `Passed`. The new arguments passed and failed as designed. `isActive` given a boolean `TRUE()` is converted to text and passes. `INFO.VIEW.RELATIONSHIPS()` showed the security filter as `Single`.

## Tasks

1. `src/lib/functions-assertions.tmdl`: add the two parameters and checks; rewrite the `///` description and `@param` lines (below); bump `DAXLIB_PackageVersion` to `0.9.1` on every function, `LibraryVersion()` to `"0.9.1"`, and `src/manifest.daxlib` to `0.9.1`.
2. Test model: add one **inactive** relationship to `tests/model/TestingModel` (none exists today), on a table pair that already has an active path, so `isActive` has a `FALSE` case. A candidate is `TestData-Fact[CreatedDate] → Calendar[Date]`: both columns are `dateTime`, and an active relationship there would be ambiguous through `Calendar → TestData → TestData-Fact`. It has a readable name instead of a GUID, and an annotation (`PQLAssert_Purpose`) saying why it is inactive and what uses it. TOM relationships have no `Description` property, so a `///` description is not used. No `USERELATIONSHIP` test uses it: `Calendar` also reaches `TestData-Fact` through two-way relationships via `TestData`, so filtering through it is ambiguous. The best-practice tests that see it (`ShouldMarkPrimaryKeys`, `ShouldHaveSameDataTypeInRelationships`) already expect to fail on this model. Run `ci/build_stage.py check` so the CI gate deploys it.
3. `tests/model/TestingModel.SemanticModel/DAXQueries/Assert.ANY.Tests.dax`, new cases:
   - `TestData[ID] → TestData-Fact[ID]` (cross-filter Both): `crossFilteringBehavior` `"BothDirections"` passes, `"OneDirection"` fails.
   - A default relationship (`Mock-Fact[Date ID] → Calendar[Date ID]`): `"OneDirection"` passes, `"BothDirections"` fails.
   - `isActive` `"TRUE"` passes on an active relationship, `"FALSE"` fails; the reverse on the new inactive one.
   - Case-insensitive values (`"bothdirections"`, `"true"`) pass.
   - `isActive` given the boolean `TRUE()` instead of `"TRUE"` passes (DAX converts it to text; checked in Desktop).
   - All ten arguments correct passes; a missing relationship with the new arguments fails with `NOT FOUND`.
   - Rename the existing security-filter cases to say "security filter (RLS)" and add a comment that the relationship's **cross-filter** is Both, so the two settings are not confused again.
   - Regression: one existing 8-argument call asserts its exact 0.9.0 `Expected` and `Actual` text.

   `tests/model/TestingModel.SemanticModel/TMDLScripts/Load PQL.tmdl` is `createOrReplace` plus a copy of `functions-assertions.tmdl`, so it gets the same `ShouldExist` change. `ci/build_stage.py sync` updates the three test models' `functions.tmdl`.
4. Docs: correct the `securityFilteringBehavior` description and document the new arguments in `src/README.md` (signature, argument list, and the "Many-to-One, single direction" example, which today passes `"OneDirection"` as the security filter), and in the three copies: `examples/cloud-agent/.github/pql-assert/SKILLS.md`, `examples/custom-agents/skills/pql-assert/SKILL.md`, `examples/custom-agents/agents/power-query-tester.agent.md`. Add the dialog-to-argument table above to `src/README.md`. Merge `main` into `dev` first: #50 rewrote the agent file on `main`, and that version has four places to change:
   - the `RelationshipAssertions` type: add `crossFilteringBehavior?: "OneDirection" | "BothDirections" | "Automatic" | ""` and `isActive?: "TRUE" | "FALSE" | ""`, and add `"None"` to `securityFilteringBehavior`;
   - the validation `match` row `relationship => Relationship.ShouldExist with cardinality and filter direction`: say "cardinality, cross-filter direction, active state, and security filter (RLS)";
   - the function list entry, which calls `securityFilteringBehavior` the "expected filter direction";
   - the "Many-to-One, single direction" example, which should pass `"OneDirection"` as `crossFilteringBehavior` (argument 9), not as the security filter.
5. `CHANGELOG.md`: a `[0.9.1]` entry: Added (the two arguments), Fixed (the `securityFilteringBehavior` description, and `None` reported as `None`, not `Unknown`), and the compatibility note.
6. Run the CI gate (`pql-test run-tests` on the staged models) and check the new cases in Power BI Desktop, including a cross-filter **Automatic** relationship if one can be made, recording the result in the function description as 0.9.0 did for refresh times.

Proposed description:

```
/// Asserts that a relationship exists between two columns, with optional checks of the settings on Power BI's Edit relationship dialog.
/// Arguments are named after the TMDL property each one checks. Omit or pass "" for any optional argument to skip that check.
/// @param {STRING} fromCardinality - Optional. Cardinality on the From side: "One" or "Many".
/// @param {STRING} toCardinality - Optional. Cardinality on the To side: "One" or "Many".
/// @param {STRING} securityFilteringBehavior - Optional. "Apply security filter in both directions" (row-level security only): "OneDirection" (unchecked) or "BothDirections" (checked); "None" for limited relationships, set outside Power BI Desktop. Not the cross-filter direction.
/// @param {STRING} crossFilteringBehavior - Optional. "Cross-filter direction": "OneDirection" (Single) or "BothDirections" (Both); "Automatic" is set outside Power BI Desktop.
/// @param {STRING} isActive - Optional. "Make this relationship active": "TRUE" or "FALSE".
```

## Decisions

| # | Topic | Proposal |
|---|---|---|
| D1 | New function or new arguments | New arguments on `ShouldExist` (decided 2026-11-17): no new function, no breaking change |
| D2 | Dialog words (`Single`, `Both`) as aliases | Not in 0.9.1: one vocabulary, the TMDL names, with the dialog words in the docs table. `INFO.VIEW.RELATIONSHIPS()` shows the security filter as `Single`, so aliases may come later if users trip on it |
| D3 | `isActive` type | `STRING` (`"TRUE"`/`"FALSE"`), so `""` skips like every other optional argument |
| D4 | Security filter value 3 (`None`) | Report it as `None` instead of `Unknown`, so a limited relationship's security filter can be checked. Changes `Actual` only for that value (see Compatibility) |
| D5 | Label in `Expected`/`Actual` | `CrossFiltering:`, parallel to the existing `SecurityFiltering:`, rather than `CrossFilter:` or the full property name. The existing labels stay as they are, because changing them would change 0.9.0 text |

## Definition of done

- Every 0.9.0 case in `Assert.ANY.Tests` passes unchanged, and the new cases pass, in Power BI Desktop and in the CI gate.
- `Expected`/`Actual` text for calls without the new arguments is unchanged.
- `src/README.md`, the three example copies, and the function description agree, and none calls `securityFilteringBehavior` the filter direction.
- `CHANGELOG.md` has the `[0.9.1]` entry; every `DAXLIB_PackageVersion`, `LibraryVersion()`, and the manifest say `0.9.1`.
