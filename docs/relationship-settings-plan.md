# Plan: Cross-Filter Direction and Active State in `Relationship.ShouldExist` (0.10.0)

**Status:** Proposed · **Branch:** `dev` · **Created:** 2026-11-17

## Goal

`PQL.Assert.Relationship.ShouldExist` can check every setting on Power BI's **Edit relationship** dialog that changes how the model filters, without a new function and without changing any existing call or result:

1. Add two optional arguments at the end: `crossFilteringBehavior` and `isActive`.
2. Fix the description of `securityFilteringBehavior`, which reads like the cross-filter direction but is the RLS checkbox.

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
| Apply security filter in both directions | `securityFilteringBehavior: bothDirections` | `SecurityFilteringBehavior` (1, 2) | `securityFilteringBehavior` (8) | `OneDirection`, `BothDirections` |
| **Cross-filter direction** | `crossFilteringBehavior: bothDirections` (default `oneDirection`) | `CrossFilteringBehavior` (1 OneDirection, 2 BothDirections, 3 Automatic) | **`crossFilteringBehavior` (9, new)** | `OneDirection`, `BothDirections`, `Automatic` |
| **Make this relationship active** | `isActive: false` (default true) | `IsActive` | **`isActive` (10, new)** | `TRUE`, `FALSE` |

Each argument keeps the TMDL property name of the setting it checks, the convention the existing arguments already follow.

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
        crossFilteringBehavior : STRING = "",   // new in 0.10.0
        isActive : STRING = ""                  // new in 0.10.0
    ) => …
        // CrossFilteringBehavior: 1 = OneDirection, 2 = BothDirections, 3 = Automatic
        VAR _ActualCrossFiltering = MAXX(_MatchingRel, SWITCH([CrossFilteringBehavior], 1, "OneDirection", 2, "BothDirections", 3, "Automatic", "Unknown"))
        VAR _ActualIsActive = MAXX(_MatchingRel, IF([IsActive], "TRUE", "FALSE"))
        VAR _CrossFilterOk = IF(crossFilteringBehavior = "" || NOT _Found, TRUE, UPPER(_ActualCrossFiltering) = UPPER(crossFilteringBehavior))
        VAR _IsActiveOk = IF(isActive = "" || NOT _Found, TRUE, UPPER(_ActualIsActive) = UPPER(isActive))
        VAR _Passed = _Found && _FromCardOk && _ToCardOk && _SecFilterOk && _CrossFilterOk && _IsActiveOk
```

- `Expected` gains ` | CrossFilter: <value>` and ` | IsActive: <value>`, and `Actual` the same with the model's values, each **only when that argument is not `""`**, appended after the existing parts.
- `isActive` is `STRING`, not `BOOLEAN`, so `""` can mean "skip", like every other optional argument. Values compare case-insensitively.
- Both reads reuse `_MatchingRel`, which the function already computes from `INFO.RELATIONSHIPS()`: no new INFO call and no new permission.

## Compatibility (non-breaking)

- DAX function arguments are positional. Every existing call passes 5 to 8 arguments, and arguments 9 and 10 default to `""`, so each existing call evaluates exactly as on 0.9.0.
- With the new arguments empty, `Expected`, `Actual` and `Passed` are byte-for-byte the 0.9.0 text. A 0.9.0 suite gives the same results on 0.10.0.
- No function is added, renamed or removed. The CHANGELOG entry opens "Additive only", as 0.9.0's does.
- Callers that detect the library by function name (pql-test does, from TMDL) cannot tell 0.9 and 0.10 apart. They need `PQL.Assert.LibraryVersion()`, the `DAXLIB_PackageVersion` annotation, or the parameter count (10). pql-test tracks this on its side.

## Tasks

1. `src/lib/functions-assertions.tmdl`: add the two parameters and checks; rewrite the `///` description and `@param` lines (below); bump `DAXLIB_PackageVersion` to `0.10.0` on every function, `LibraryVersion()` to `"0.10.0"`, and `src/manifest.daxlib` to `0.10.0`.
2. Test model: add one **inactive** relationship to `tests/model/TestingModel` (none exists today), on a table pair that already has an active path, so `isActive` has a `FALSE` case. Run `ci/build_stage.py` checks so the CI gate deploys it.
3. `tests/model/TestingModel.SemanticModel/DAXQueries/Assert.ANY.Tests.dax`, new cases:
   - `TestData[ID] → TestData-Fact[ID]` (cross-filter Both): `crossFilteringBehavior` `"BothDirections"` passes, `"OneDirection"` fails.
   - A default relationship (`Mock-Fact[Date ID] → Calendar[Date ID]`): `"OneDirection"` passes, `"BothDirections"` fails.
   - `isActive` `"TRUE"` passes on an active relationship, `"FALSE"` fails; the reverse on the new inactive one.
   - Case-insensitive values (`"bothdirections"`, `"true"`) pass.
   - All ten arguments correct passes; a missing relationship with the new arguments fails with `NOT FOUND`.
   - Rename the existing security-filter cases to say "security filter (RLS)" and add a comment that the relationship's **cross-filter** is Both, so the two settings are not confused again.
   - Regression: one existing 8-argument call asserts its exact 0.9.0 `Expected` text.
4. Docs: correct the `securityFilteringBehavior` description and document the new arguments in `src/README.md` (signature, argument list, and the "Many-to-One, single direction" example, which today passes `"OneDirection"` as the security filter), and in the three copies: `examples/cloud-agent/.github/pql-assert/SKILLS.md`, `examples/custom-agents/skills/pql-assert/SKILL.md`, `examples/custom-agents/agents/power-query-tester.agent.md`. Add the dialog-to-argument table above to `src/README.md`.
5. `CHANGELOG.md`: a `[0.10.0]` entry: Added (the two arguments), Fixed (the `securityFilteringBehavior` description), and the compatibility note.
6. Run the CI gate (`pql-test run-tests` on the staged models) and check the new cases in Power BI Desktop, including a cross-filter **Automatic** relationship if one can be made, recording the result in the function description as 0.9.0 did for refresh times.

Proposed description:

```
/// Asserts that a relationship exists between two columns, with optional checks of the settings on Power BI's Edit relationship dialog.
/// Arguments are named after the TMDL property each one checks. Omit or pass "" for any optional argument to skip that check.
/// @param {STRING} fromCardinality - Optional. Cardinality on the From side: "One" or "Many".
/// @param {STRING} toCardinality - Optional. Cardinality on the To side: "One" or "Many".
/// @param {STRING} securityFilteringBehavior - Optional. "Apply security filter in both directions" (row-level security only): "OneDirection" (unchecked) or "BothDirections" (checked). Not the cross-filter direction.
/// @param {STRING} crossFilteringBehavior - Optional. "Cross-filter direction": "OneDirection" (Single), "BothDirections" (Both), or "Automatic".
/// @param {STRING} isActive - Optional. "Make this relationship active": "TRUE" or "FALSE".
```

## Decisions

| # | Topic | Proposal |
|---|---|---|
| D1 | New function or new arguments | New arguments on `ShouldExist` (decided 2026-11-17): no new function, no breaking change |
| D2 | Dialog words (`Single`, `Both`) as aliases | Not in 0.10.0: one vocabulary, the TMDL names, with the dialog words in the docs table. `INFO.VIEW.RELATIONSHIPS()` shows the security filter as `Single`, so aliases may come later if users trip on it |
| D3 | `isActive` type | `STRING` (`"TRUE"`/`"FALSE"`), so `""` skips like every other optional argument |

## Downstream

pql-test maps ODCS contract relationships to `ShouldExist`. Its plans, in the pql-test repository:

- `tasks/relationship-settings-epic.md`: contract properties for cardinality, cross-filter, active, and security filter on PQL.Assert 0.8 and 0.9, checking cross-filter and active through `INFO.VIEW.RELATIONSHIPS()` until 0.10.0 ships, and telling 0.9 from 0.10 by parameter count.
- `tasks/pql-assert-0-10-relationship-epic.md`: once 0.10.0 is released, a `pql_assert_0_10` catalog that moves those checks into the single `ShouldExist` call.

## Definition of done

- Every 0.9.0 case in `Assert.ANY.Tests` passes unchanged, and the new cases pass, in Power BI Desktop and in the CI gate.
- `Expected`/`Actual` text for calls without the new arguments is unchanged.
- `src/README.md`, the three example copies, and the function description agree, and none calls `securityFilteringBehavior` the filter direction.
- `CHANGELOG.md` has the `[0.10.0]` entry; every `DAXLIB_PackageVersion`, `LibraryVersion()`, and the manifest say `0.10.0`.
