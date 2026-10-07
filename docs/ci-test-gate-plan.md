# Plan: PR Gate for `main` Using `pql-test`

**Status:** Decisions made, Phase 0 next · **Branch:** `ci-cd` · **Created:** 2026-10-07

## Goal

Every pull request into `main` runs a GitHub Actions job that does the following:

1. **Builds** the PQL.Assert library from `src/lib/*.tmdl` and injects it into the test models.
2. **Publishes** the test PBIPs (`tests/model/TestingModel` and `tests/rls_model/RLS_Model`, semantic model and report) to a dedicated Fabric CI workspace.
3. **Refreshes** both semantic models and waits until each refresh finishes.
4. **Runs** the DAX test suites with `pql-test` (from PyPI) inside a Python virtual environment.
5. **Fails the PR check** if any test fails, except for suites that are expected to fail, which must fail.

The job becomes a required status check on `main`.

---

## What exists today

| Area | Current state | Impact on CI |
|---|---|---|
| CI | Only `publish-package.yml`, which is manual and pushes to the DaxLib fork | There is no PR validation yet |
| Test models | `tests/model/TestingModel.*` and `tests/rls_model/RLS_Model.*` as PBIP/TMDL | These are ready to deploy with fabric-cicd |
| Library in models | Each model has `definition/functions.tmdl`, which is a hand-synced copy of `src/lib` | Copies can drift from the source, so CI should build the library from `src/lib` |
| Test files | `DAXQueries/*.Tests.dax` (`Assert`, `Col`, `Tbl`, `BP.*`, `Partition`, `Perspective`, `RLS`, `Example.*`, …) | pql-test finds these files on disk |
| Intentional failures | `ShouldFail.TEST.Tests.dax` fails an assertion. `ShouldFailSchema.DEV.Tests.dax` returns the wrong schema | A plain exit-code gate would always be red. These suites must be handled as "expected to fail" |
| Naming quirks | `Table.DEV.Test.dax` (singular), `Example.prod.tests.dax` (function `Example.prod.test`), `Query 1.dax` | Some of these may be deliberate negative cases for discovery. Check each one |
| RLS_Model tests | `RLS 1.dax`, `OLS_West.dax`, `OLS_East.dax`, `OLS Admin.dax`, none named `*.Tests.dax` | pql-test will not discover them. They need renaming and `// ImpersonateRole:` headers |
| Data sources | Mostly inline `#table`/`Binary.FromText`. **`Test Import 1 & 3` uses `SharePoint.Contents(SharePoint_URL)` with an incremental refresh policy** | This is the hardest part of the refresh. A service principal cannot authenticate to SharePoint. See Decision D3 |

### What `pql-test` (0.1.19) provides

- **Windows only:** it uses ADOMD.NET and downloads it automatically from NuGet on first use. → **`runs-on: windows-latest`**
- **Commands:** `check-prereqs`, `retrieve-tests`, `run-tests`, `code-coverage`. Skill files ship in the package (`pql_test/skills/*/SKILL.md`).
- **Service connection:** set `PQL_TENANT_ID`, `PQL_CLIENT_ID`, `PQL_CLIENT_SECRET`, `PQL_WORKSPACE_ID` and `PQL_DATASET_ID`, or pass a `"<ws>.Workspace/<model>.SemanticModel"` path.
- **Output options:** `--output results.json`, `--log-format github` (PR annotations) and `--env <ENV>`.
- **Exit codes:** `0` means every test passed. `1` means a test failed, an error occurred, or every result was skipped because no connection could be made. That last case keeps a misconfigured CI run from passing.
- **Coverage gate:** `code-coverage --format json --min-coverage N`.
- **Gaps:** it does **not** publish or refresh models, and it has **no way to exclude a suite or mark it as expected to fail**.

---

## Target pipeline

```
pull_request → main   (concurrency group: pql-assert-ci-workspace, no cancel)
│
├─ job: build-and-gate   (windows-latest)
│   1. checkout
│   2. setup-python 3.12 → python -m venv .venv → pip install -r ci/requirements.txt
│        (pinned: pql-test==0.1.19, fabric-cicd==<x>, azure-identity)
│   3. Build library:     Combine-TmdlFiles.ps1 + placeholder replace
│   4. Stage models:      copy tests/* PBIPs → _stage/, inject built functions.tmdl
│                         (fail if checked-in functions.tmdl drifted from src/lib, or warn only. See D4)
│   5. Deploy:            fabric-cicd publish_all_items (SemanticModel, Report) → CI workspace
│   6. Refresh:           ci/refresh_models.py → POST /refreshes, poll until Completed/Failed
│   7. Prereqs:           pql-test check-prereqs
│   8. Test (per model):  pql-test run-tests <stage path> --output results-<model>.json --log-format github
│   9. Evaluate:          ci/evaluate_results.py --results-dir ci-results   (rules in ci/gate.json)
│   10. Always:           upload results artifacts, write $GITHUB_STEP_SUMMARY table
│   (Coverage is out of scope for now. See D7)
│
└─ Branch protection on main: require "build-and-gate" to pass
```

### Proposed new files

| Path | Purpose |
|---|---|
| `.github/workflows/pr-gate.yml` | The workflow above. **Written, not yet run** |
| `ci/requirements.txt` | Pinned `pql-test==0.1.19` and `fabric-cicd==1.4.0` (`azure-identity` and `requests` come with them). **Done** |
| `ci/parameter.yml` | fabric-cicd parameterization, only if `SharePoint_URL` needs a CI value. The connection binding is **not** here (see D3) |
| `ci/build_stage.py` | `check` (drift), `sync` (write `src/lib` into the models) and `stage` (copy the PBIPs with the merged library to `_stage/`). **Done** |
| `ci/deploy.py` | Deploys both models with `FabricWorkspace` + `publish_all_items`. Never unpublishes. **Written, not yet run** |
| `ci/refresh_models.py` | Runs an enhanced refresh through the Power BI REST API and polls it. **Written, not yet run** |
| `ci/evaluate_results.py` | Gate logic over the pql-test JSON files (matched on `suite_name`), plus the `--env` check. **Done**, tested against synthetic results |
| `ci/gate.json` | Expected-failure suites, and the suites each `--env` filter must return. **Done** |
| `ci/README.md` | How to run the same pipeline locally in a venv. **Started** |
| `docs/ci-setup.md` | One-time setup for Entra, the tenant, the workspace, the connection and the repo. **Done** |

Scripts that publish to the DaxLib fork stay in `scripts/`. Everything specific to CI lives in `ci/`.

---

## Decisions (made 2026-10-07)

| # | Topic | Decision | What it means for the build |
|---|---|---|---|
| **D1** | CI workspace | **One shared workspace** (`PQL.Assert-CI`) | `concurrency: { group: pql-assert-ci-workspace, cancel-in-progress: false }`. Model names stay fixed. |
| **D2** | Capacity | **Premium Per User (PPU)** | See *PPU caveats* below. These are the biggest unknown in Phase 0. |
| **D3** | SharePoint source in `Test Import 1 & 3` | **Data source credentials set once on the published model** (OAuth, by a user with site access) | No gateway, no shareable connection, and no connection ID in CI. Later in-place deploys keep the credentials. If they go missing, the refresh fails with Power BI's own error. The incremental refresh policy stays real (`applyRefreshPolicy: true`). |
| **D4** | `src/lib` drift | **Inject into the staged copy and fail on drift** | `ci/build_stage.py` writes the built library into `_stage/`, diffs it against the checked-in `functions.tmdl`, and fails with a message saying how to sync. |
| **D5** | Expected-failure suites | **Allowlist plus an evaluator script** | `ci/gate.json` and `ci/evaluate_results.py`. Also open a pql-test issue requesting `--exclude` and `--expect-fail` options. |
| **D6** | PRs from forks | **A maintainer label starts the run** | Fork PRs on `pull_request` get a skip notice. A `safe-to-test` label starts a `pull_request_target` job that takes workflow and scripts from `main` and only `src/` and `tests/` from the PR head. The label is removed when new commits are pushed. |
| **D7** | Coverage | **Skip for now** | No `code-coverage` step. Revisit in a later PR. |
| **D8** | Gated suites | **All suites, plus one `--env ANY` check** | One full run per model. Then a `retrieve-tests --env ANY` assertion on the suite count, so environment filtering is covered too. |
| **D9** | `.dax` query-file suites | **Register them as model UDFs** (stay on pql-test 0.1.19) | Each suite becomes `[Area].ANY.Tests` in TestingModel's `functions.tmdl`, and the `.dax` file is renamed to match as `DEFINE FUNCTION … EVALUATE`. Each suite returns one row per assertion, where `Passed` means it behaved as its name says ("should pass" / "should fail"). **Done 2026-10-07.** |

### PPU caveats to clear in Phase 0

PPU is a supported host for XMLA, but three things need to be proven before Phase 1 is finished:

1. **Service principal over XMLA on a PPU workspace:** confirm that pql-test can connect and query with the service principal and that `ImpersonateRole` works there.
2. **fabric-cicd on a PPU workspace:** fabric-cicd calls the Fabric item APIs. Confirm that SemanticModel and Report items can be created and updated in a PPU (non-Fabric-capacity) workspace. **Fallback:** deploy the semantic model over the XMLA endpoint (TMDL to TOM, e.g. with `pbi-tools` or Tabular Editor CLI) and skip report deployment, since reports aren't needed for testing.
3. **Licensing:** everyone who opens the CI workspace needs PPU. The CI identity behind the shareable cloud connection only needs SharePoint access.

If (1) or (2) fails, the next option is a Fabric trial capacity or the smallest F SKU (F2) with pause and resume.

---

## Phase 0 findings (2026-10-07)

**Environment:** `.venv` with Python 3.12.6 and `pql-test 0.1.19`. `check-prereqs` passes on this machine.

**Test suites live in the model, not just in `.dax` files.** Every suite (`Example.ANY.Tests`, `ShouldFail.TEST.Tests`, `RLS.ANY.Tests`, `OLS_West.ANY.Tests`, …) is a UDF in `definition/functions.tmdl`. pql-test finds them live through `PQL.Assert.RetrieveTestsV2()` and reads impersonation from annotations (`PQLAssert_RoleName`, `PQLAssert_ImpersonatedUserName`). As a result:
- The Phase 4 item about renaming the RLS `.dax` files isn't needed for discovery. Suites need to be UDFs with the right annotations.
- D4 injection has to **merge**, not overwrite. Replace the `PQL.Assert.*` functions with the `src/lib` build and keep every other UDF (the suites).

**Drift between `src/lib` and the models.** Compared function by function, ignoring `lineageTag`, annotations and comments:

| Model | Same as `src/lib` | Differs | Missing | Suite UDFs kept |
|---|---|---|---|---|
| TestingModel | 107 / 108 | `Relationship.ShouldExist`: only `//` comments, which Desktop strips | none | 7 |
| RLS_Model | 100 / 108 | `RetrieveTestsV2` and `RetrieveTestsByEnvironmentV2` lack the `PQLAssert_RoleName` column | 5 (`Partitions.*`, `Perspective.ShouldContain/ShouldExist`) | 3 |

- The drift check must **ignore `//` line comments** as well as `lineageTag`, or Desktop round-trips will always look like drift.
- **RLS_Model needs a resync before the gate can be enforced.** Its stale `RetrieveTestsV2` can't surface `PQLAssert_RoleName`.

**Impersonation as a service principal.** From `pql_test/runner/execution.py`: a service principal can **never** use `EffectiveUserName` on the Power BI XMLA endpoint, so `PQLAssert_ImpersonatedUserName` won't work in CI. Only `PQLAssert_RoleName` (`Roles=`) works.

| Suite | Current annotation | Needed for CI |
|---|---|---|
| RLS_Model `RLS.ANY.Tests` | `ImpersonatedUserName = atlas.kerski@…` | Add `PQLAssert_RoleName = West` |
| RLS_Model `OLS_West.ANY.Tests` / `OLS_East.ANY.Tests` | none, so the run isn't impersonated and the OLS "hidden" assertions would fail | Add `PQLAssert_RoleName = West` / `East` |
| TestingModel `RLS.ANY.Tests` | `RoleName = WestSales`, a role that doesn't exist | **Fixed:** changed to `West`, and the matching assertion in `Assert.Discovery.Tests.dax` updated |

**JSON results shape (from the pql-test 0.1.19 source):** `{model_path, passed, failed, skipped, total, results: [{test_name, suite_name, expected, actual, passed, skipped, error, duration_ms}]}`. `suite_name` is present, so expected failures are matched by suite.

**⚠ Gap: `.dax` query-file suites don't run against a deployed model.** With a live connection, pql-test discovers suites only through `RetrieveTestsV2()`, which returns model UDFs, and it filters them to names declared locally. It reads `DAXQueries/*.Tests.dax` files **only** when there is no connection, and then every result is skipped. As a result, these TestingModel suites, which are the core library tests, **would not run in CI**: `Assert.Tests`, `Assert.Discovery.Tests`, `Col.Tests`, `Tbl.Tests`, `Partition.Tests`, `Perspective.Tests` and all six `BP.*.Tests`. Only the 7 model-UDF suites would run. **Decided (D9): register the suites as model UDFs. Done.** 11 suites converted (`Assert`, `Assert.Discovery`, `Col`, `Tbl`, `Partition`, `Perspective`, `BP.DAXExpressions`, `BP.ErrorPrevention`, `BP.Formatting`, `BP.Maintenance`, `BP.Performance`). `RLS.Tests.dax` was renamed to `RLS.ANY.Tests.dax`. `BP.DEV.Tests.dax` became `BP.DEV.Checks.dax`, because it holds raw `BP.Check*()` calls that fail by design on TestingModel and isn't a suite.

**Still open in Phase 0:** the PPU checks, the D3 binding, and timing.

## Phased work plan

### Phase 0 – Spike (locally, in a venv)

- [x] `python -m venv .venv; .venv\Scripts\Activate.ps1; pip install pql-test==0.1.19; pql-test check-prereqs`
- [ ] With both PBIPs open in Desktop, run `pql-test retrieve-tests local/TestingModel` and `local/RLS_Model` and record which suites are discovered.
- [ ] Run `run-tests --output` and record the **JSON shape**. Does each result carry a suite or function name, or only `test_name`? This decides whether expected failures are matched by suite or by test.
- [ ] Decide what happens to `Table.DEV.Test.dax`, `Example.prod.tests.dax` and `Query 1.dax`: rename them, keep them as negative cases, or delete them.
- [x] Check whether `tests/model/.../functions.tmdl` equals the combined `src/lib` plus replaced placeholders. List any functions that only exist in tests and must be kept during injection. *(See findings above)*
- [ ] **PPU check 1:** run `pql-test run-tests` as the service principal against a model in a PPU workspace, including one `ImpersonateRole` suite.
- [ ] **PPU check 2:** deploy TestingModel by hand with fabric-cicd to a scratch PPU workspace. If the item APIs reject it, prototype the XMLA deploy fallback.
- [ ] **D3 check:** bind a shareable cloud connection (OAuth) to the SharePoint source by hand, then run an enhanced refresh with `applyRefreshPolicy: true` as the service principal. **Redeploy with fabric-cicd and confirm that the binding survives**, since D3 depends on it.
- [ ] Time a full deploy and refresh of both models (the `LargeTableOneMillion*` tables) to estimate how long the gate takes.

### Phase 1 – Azure and Fabric setup (requires an admin)

Step-by-step instructions: **[ci-setup.md](ci-setup.md)**.

- [ ] Create an Entra app registration (service principal) and a client secret. Store the expiry date somewhere it will be seen.
- [ ] In tenant settings, allow service principals to use Fabric/Power BI APIs (scoped to a security group). Turn on XMLA endpoints (read/write is needed for deployment).
- [ ] Create the `PQL.Assert-CI` workspace on **PPU** and add the service principal as **Member**. Contributor may be enough for deploy plus refresh, so verify. Admin is only needed for `ImpersonateUser`, and `ImpersonateRole` should be used instead.
- [ ] Create a CI identity with read access to `https://kerski.sharepoint.com/sites/DocLibTest`. Create a **shareable cloud connection** (SharePoint, OAuth) as that identity and add the service principal as *User*.
- [ ] After the first CI deploy, bind the connection by hand: open the TestingModel settings, go to *Gateway and cloud connections*, and map the SharePoint source to the connection. Redo this only if the model is ever deleted or recreated, or `SharePoint_URL` changes.
- [ ] Add GitHub secrets and variables: `PQL_TENANT_ID`, `PQL_CLIENT_ID`, `PQL_CLIENT_SECRET` (secrets), `PQL_WORKSPACE_ID` (variable). Use a `ci` GitHub environment if approval gates are wanted.

### Phase 2 – Build and stage

- [x] `ci/build_stage.py`: parses `src/lib/*.tmdl` directly, because the files mix tab and space indentation and `src/lib` has no placeholders to replace. It **merges** into `_stage/<Model>.SemanticModel/definition/functions.tmdl` (replace the `PQL.Assert.*` UDFs and keep the suite UDFs), and check for drift (D4) while ignoring `lineageTag`, annotations, `///` and `//` comments, and whitespace.
- [x] Add `_stage/`, `.venv/` and `results-*.json` to `.gitignore`. Also remove the stray `temp-test-output.tmdl` from the repo root, or ignore it.

### Phase 3 – Deploy and refresh

- [x] `ci/deploy.py`: call `FabricWorkspace(workspace_id, repository_directory="_stage", item_type_in_scope=["SemanticModel","Report"], token_credential=ClientSecretCredential(...))`, then `publish_all_items`. Check that the reports' `byPath` dataset reference gets rewritten.
- [ ] `ci/parameter.yml`: only needed if `SharePoint_URL` differs in CI. No connection binding (D3).
- [x] ~~Binding preflight~~ removed after the first CI run (2026-10-07). It required a shareable cloud connection, but credentials set directly on the model work too.
- [x] `ci/refresh_models.py`: look up the dataset IDs by name, then `POST .../datasets/{id}/refreshes` with `{"type":"full","commitMode":"transactional","applyRefreshPolicy":true}`. Poll the `Location` URL with backoff and a timeout of about 15 minutes. If the refresh fails, fail with its error details.

### Phase 4 – Test and gate

- [x] RLS_Model: resynced the library from `src/lib` (5 functions added, `RetrieveTests*V2` updated). Added `PQLAssert_RoleName` annotations to `RLS.ANY.Tests` (West), `OLS_West.ANY.Tests` (West) and `OLS_East.ANY.Tests` (East).
- [ ] Open RLS_Model in Power BI Desktop to confirm that the resynced `functions.tmdl` loads, then run its suites locally with `pql-test run-tests local/RLS_Model`.
- [ ] Confirm that `Roles=` works for the service principal on PPU.
- [x] TestingModel: changed `RLS.ANY.Tests` `PQLAssert_RoleName` from `WestSales` to `West`, and updated `Assert.Discovery.Tests.dax` to match.
- [x] Run `run-tests` for each model with `--output` and `--log-format github`. The step ends with `exit 0` so that the evaluator makes the final call.
- [x] `ci/evaluate_results.py` fails on any of the following:
  - an unexpected failure
  - an expected failure that passed
  - zero tests discovered for a model
  - all results skipped
- [x] D8: run `pql-test retrieve-tests <model> --env ANY` for both models (expected lists in `ci/gate.json`) and check that only the expected `*.ANY.Tests` suites come back.
- [x] The step summary shows a table of passed, failed, expected-failure and skipped counts per model, and the JSON is uploaded as the `pql-test-results` artifact.
- [x] **D9:** ran `pql-test run-tests local/TestingModel`: 316 of 327 passed. Fixed `Tbl.ShouldNotHaveExtraColumns`, which predated the conversion (TestingModel's `TestData` table had gained 4 columns).
- [x] `Partition.ANY.Tests` → **`Partition.SVC.Tests`** (service only). Desktop keeps a single partition, and the old exact counts were fixed to 2026-05-31. Expected counts are now computed from `TODAY()` using the policy's layout: 1 year, plus `QUARTER-1` quarters, plus `MOD(MONTH-1,3)` months, plus `DAY` days. This layout reproduces every old value for that date. It **fails in Desktop by design**, and the gate runs it against the refreshed service model.
- [ ] Optional: file a pql-test issue for D5 (`--exclude` / `--expect-fail`).
- [x] Fork PRs on `pull_request` **fail** (not skip) with instructions, because GitHub counts a skipped required check as passing.
- [ ] Open a pql-test issue requesting `--exclude` and `--expect-fail` (D5).

### Phase 5 – Forks and enforcement

- [ ] Set up the fork path (D6): the `pull_request_target` job, triggered by the `safe-to-test` label. Check out `main` for `ci/` and the PR head only for `src/` and `tests/`. A step removes the label on `synchronize`.
- [ ] Make `build-and-gate` a required check in the branch protection for `main`.
- [ ] Add a short "CI" section to the README and update `.github/agents/pql-function-tester.md` (its EndOfEpicWorkflow) to point at the gate.

### Phase 6 – Hardening (later)

- [ ] Add `pql-test code-coverage`, report-only at first and enforced later (D7 deferred this).
- [ ] Add a scheduled nightly run against `main` to catch capacity or credential problems early.
- [ ] Alert on client secret expiry, or switch to OIDC federated credentials (no secret to rotate). Check whether pql-test accepts a token or certificate in CI.
- [ ] Consider per-PR workspaces if the concurrency queue becomes a bottleneck.

---

## Risks

| Risk | Mitigation |
|---|---|
| PPU blocks the service principal over XMLA or blocks the fabric-cicd item APIs | Phase 0 PPU checks. Fallbacks: XMLA deploy, Fabric trial, or F2 |
| The shareable cloud connection's OAuth token expires, or the CI identity loses SharePoint access | Nightly run (Phase 6) catches it. Document who owns the CI identity |
| The model's SharePoint credentials are lost (model deleted or recreated, or `SharePoint_URL` changed) | The refresh fails with a credentials error. Redo docs/ci-setup.md step 6.1. Never delete or rename CI models by hand |
| Concurrent PRs overwrite each other in the shared workspace | `concurrency` group with `cancel-in-progress: false` |
| Secrets exposed to PRs from forks | D6: run scripts from `main` only, behind a maintainer label |
| A refresh hangs | Polling timeout and a clear error |
| pql-test changes behavior between versions | Pin the version in `ci/requirements.txt` and upgrade on purpose |
| A long run, because there are many large tables (`LargeTableOneMillion*`) | Measure in Phase 0. If needed, refresh in parallel or use `ImpersonateRole` instead of extra models |

## Definition of done

- A PR into `main` that breaks any assertion function shows a red required check, with the failing test names as annotations on the PR.
- A PR that leaves the library correct shows green. Both models are deployed and refreshed, and every suite runs.
- A contributor can run the same steps locally in a venv by following `ci/README.md`.
