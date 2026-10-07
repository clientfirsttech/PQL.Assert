# CI Setup: Workspace, Service Principal and Repo

This is the one-time setup behind the PR gate described in [ci-test-gate-plan.md](ci-test-gate-plan.md). Do the sections in order. Each step ends with a **Verify** line.

| Section | Who can do it |
|---|---|
| 1. Entra ID | Entra admin, or anyone allowed to create app registrations |
| 2. Fabric tenant settings | Fabric / Power BI administrator |
| 3. CI workspace | Anyone with a PPU license |
| 4. SharePoint credentials | Workspace owner |
| 5. GitHub repo | Repo admin |
| 6. After the first CI run | Workspace owner and repo admin |

---

## 1. Entra ID

### 1.1 Service principal
1. Go to **portal.azure.com → Microsoft Entra ID → App registrations → New registration**.
2. Name it `pql-assert-ci`, choose single tenant, and leave the redirect URI empty.
3. Copy the **Application (client) ID** and the **Directory (tenant) ID**.
4. Go to **Certificates & secrets → New client secret** and copy the secret **value**, which is shown only once.
5. Note the secret's **expiry date** somewhere the team will see it. An expired secret turns the gate red.

API permissions: leave them empty for now. Workspace membership (step 3.2) grants the access. If the Phase 0 checks show pql-test needs `Dataset.Read.All`, add it then with admin consent.

**Verify:** the app appears under *Enterprise applications* with the same client ID.

### 1.2 Security group
1. Go to **Microsoft Entra ID → Groups → New group**. Choose type **Security** and name it `sg-pql-assert-ci`.
2. Add the `pql-assert-ci` service principal as a **member**.

**Verify:** the group's *Members* list shows the app.

---

## 2. Fabric tenant settings

Go to **app.powerbi.com → Settings (gear) → Admin portal**.

| Where | Setting | Value |
|---|---|---|
| Tenant settings → *Developer settings* | **Service principals can call Fabric public APIs** (older name: *Service principals can use Fabric APIs*) | Enabled, **specific security groups**: `sg-pql-assert-ci` |
| Tenant settings → *Integration settings* | **Allow XMLA endpoints and Analyze in Excel with on-premises semantic models** | Enabled |
| **Premium Per User** → *Semantic model workload settings* | **XMLA Endpoint** | **Read Write** |

PPU has its own XMLA setting, separate from capacity settings. Deploying needs **Read Write**.

**Verify:** tenant setting changes can take up to 15 minutes to apply. The Phase 0 checks confirm them end to end.

---

## 3. CI workspace

### 3.1 Create it
1. Go to **Workspaces → New workspace** and name it `PQL.Assert-CI`.
2. Under **Advanced → License mode**, choose **Premium per-user**.

### 3.2 Access
1. Go to **Manage access → Add people or groups**, add `pql-assert-ci` (the service principal) and give it **Member**. Contributor may be enough for deploy plus refresh, but role-impersonated test connections (`Roles=`) may need Member. Confirm in Phase 0 before you lower it.
2. Add the maintainers who should be able to inspect the workspace. Each one needs a PPU license.

### 3.3 Record the workspace ID
Copy the GUID after `/groups/` in the workspace URL, for example `https://app.powerbi.com/groups/<workspace-id>/list`.

**Verify:** the workspace shows the PPU diamond icon, and *Manage access* lists the service principal as Member.

---

## 4. SharePoint credentials

`Test Import 1 & 3` in TestingModel reads `SharePoint.Contents("https://kerski.sharepoint.com/sites/DocLibTest")`. A service principal can't authenticate to SharePoint, so the model's data source credentials are set **once, on the published model**, by a user who has **read** access to that site. No gateway or shareable connection is needed. See step 6.1.

Record whose account the credentials use. If that account loses access to the site or its sign-in expires, CI refreshes fail.

---

## 5. GitHub repo

Go to **Settings → Secrets and variables → Actions**.

| Kind | Name | Value |
|---|---|---|
| Secret | `PQL_TENANT_ID` | Directory (tenant) ID from step 1.1 |
| Secret | `PQL_CLIENT_ID` | Application (client) ID from step 1.1 |
| Secret | `PQL_CLIENT_SECRET` | Client secret value from step 1.1 |
| Variable | `PQL_WORKSPACE_ID` | Workspace ID from step 3.3 |

Then make these settings:
- **Issues → Labels → New label:** `safe-to-test`. When a maintainer adds it to a fork PR, the gate runs (decision D6). Only people with triage access or higher can add labels.
- **Settings → Actions → General:**
  - *Fork pull request workflows from outside collaborators:* **Require approval for all outside collaborators**
  - *Workflow permissions:* **Read repository contents and packages permissions**

**Verify:** the secrets and variable are listed (secret values stay hidden), and the label exists.

---

## 6. After the first CI run

### 6.1 Set the SharePoint credentials (one time)
Once TestingModel exists in `PQL.Assert-CI` (published by hand or by the first CI deploy):

1. In the workspace, open **TestingModel → Settings**.
2. If the settings are greyed out, select **Take over**.
3. Under **Data source credentials**, select **Edit credentials** for the SharePoint source, choose **OAuth2**, and sign in with an account that can read the site.
4. Re-run the workflow if it already failed at **Refresh models**.

Later deploys update the model in place and keep these credentials. **Redo this step only if** the model is deleted or recreated, or `SharePoint_URL` changes. To avoid that, never delete or rename the models in `PQL.Assert-CI` by hand.

**Verify:** a manual **Refresh now** on TestingModel succeeds.

### 6.2 Make the gate required
GitHub only offers a status check in rulesets after that check has run at least once.

1. Go to **Settings → Rules → Rulesets → New branch ruleset**.
2. Target the **default branch** (`main`).
3. Turn on **Require status checks to pass** and add `build-and-gate`.
4. Set **Enforcement status: Active**.

**Verify:** a test PR into `main` shows `build-and-gate` as **Required**.

---

## Ongoing upkeep

| What | When | Effect if missed |
|---|---|---|
| Rotate `PQL_CLIENT_SECRET` | Before the expiry date noted in step 1.1 | Every run fails to authenticate |
| The account behind the SharePoint credentials keeps access and its sign-in stays valid | Ongoing | TestingModel refresh fails with a credentials error |
| PPU licenses for workspace maintainers | When licenses renew | Maintainers lose access to inspect the workspace. CI itself is unaffected |
