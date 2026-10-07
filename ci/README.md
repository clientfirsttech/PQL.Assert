# CI scripts

Scripts behind the PR gate for `main`. See [docs/ci-test-gate-plan.md](../docs/ci-test-gate-plan.md) for the design and [docs/ci-setup.md](../docs/ci-setup.md) for the one-time workspace and repo setup.

## Local setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install pql-test==0.1.19
pql-test check-prereqs
```

## `build_stage.py`

`build_stage.py` keeps the test models' `functions.tmdl` in step with the library in `src/lib`. Each model's own test-suite UDFs (`*.Tests`), `lineageTag`s and annotations are always kept.

| Command | What it does |
|---|---|
| `python ci/build_stage.py check` | Exits 1 if any `PQL.Assert.*` function in a test model differs from `src/lib`. Add `-v` to see token diffs. Formatting, comments, `lineageTag` and annotations are ignored. |
| `python ci/build_stage.py sync` | Rewrites a drifting model's `functions.tmdl` from `src/lib`. Models that already match are left alone. |
| `python ci/build_stage.py stage` | Copies both PBIPs to `_stage/` with the merged library, ready to deploy. |

When you change a function in `src/lib`, run `sync`. Then open the model in Power BI Desktop to confirm it loads, and commit both the source and the model changes. CI runs `check` and fails the PR if they drift.

## Writing test suites

pql-test only runs suites that are **UDFs in the model** (`PQL.Assert.RetrieveTestsV2()`). A `DAXQueries/*.dax` file on its own never runs in CI. For each suite:

- Add a function named `[Area].[Env].Tests` to `definition/functions.tmdl`, returning `TestName`, `Expected`, `Actual`, `Passed`.
- Keep `DAXQueries/<same name>.dax` as `DEFINE FUNCTION <name> = () => … EVALUATE <name>()` for DAX query view.
- For deliberate "should fail" cases, follow the validation pattern in `Col.ANY.Tests`: `Passed` means the assertion behaved as its name says.

## Running the tests locally

With TestingModel open in Power BI Desktop:

```powershell
pql-test run-tests local/TestingModel --verbose
```

Locally, impersonation applies through the `PQLAssert_RoleName` annotation (`Roles=`). `PQLAssert_ImpersonatedUserName` is ignored by local Analysis Services, and a service principal can't use it in CI.
