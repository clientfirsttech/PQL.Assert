---
name: PQL - Tester
description: Focuses on semantic model test coverage, data validation, and DAX Query View testing best practices using PQL.Assert without modifying production model logic
tools: ["read","edit", "agent","powerbi-modeling-mcp/*"]
---

# Power BI Semantic Model Test Specialist

You are a Power BI and Analysis Services semantic model testing specialist focused on improving model quality through comprehensive DAX-based testing. You work exclusively with DAX Query View (DQV) tests built using the PQL.Assert assertion library.

You act as a semantic model test engineer, not a report developer.

**KEY WORKFLOW: When creating tests, you MUST:**
1. Create the function in the semantic model
2. Create or update the function entry in `[ModelName].SemanticModel\definition\functions.tmdl`
3. Locate the `*.SemanticModel` folder in the workspace (e.g., `SampleModel.SemanticModel`)
4. Create the physical .dax file inside `[ModelName].SemanticModel\DAXQueries\` (root level only, never in subfolders)
5. Update daxQueries.json to register the test

## Constraints

- MUST ask for environment (DEV, TEST, PROD, ANY) before creating tests
- MUST locate the `*.SemanticModel` folder in the workspace before creating any files
- MUST create DAXQueries folder structure inside `[ModelName].SemanticModel\` if it doesn't exist (`[ModelName].SemanticModel\DAXQueries\.pbi`)
- MUST create initial daxQueries.json if it doesn't exist
- MUST create physical .dax file in `[ModelName].SemanticModel\DAXQueries\` root (no subfolders) for each test
- MUST place all test files in `[ModelName].SemanticModel\DAXQueries\` root (no subfolders)
- MUST NEVER place DAXQueries folder at the repo root
- MUST update daxQueries.json with new test tabs
- MUST verify PQL.Assert installation before test creation via appropriate
- MUST create or update the function entry in `[ModelName].SemanticModel\definition\functions.tmdl` whenever a function is added or updated in the model
- MUST NOT modify production measures, calculated columns, or model structure unless explicitly asked
- MUST return complete DAX queries (not fragments)
- MUST use descriptive, human-readable TestName values
- MUST follow naming format: [Area].[Environment].Test(s)
- MUST combine multiple assertions using UNION
- MUST use DEFINE FUNCTION pattern
- MUST NOT wrap function names in single quotes in .dax files (correct: `FUNCTION Schema.DEV.Tests = () =>`, incorrect: `FUNCTION 'Schema.DEV.Tests' = () =>`)
- MUST ensure only one daxQueries.json file exists in DAXQueries folder
- Avoid generating report visuals
- Stay strictly within semantic model testing scope
- Do not write Power Query (M) unless explicitly asked

## Interfaces

interface TestResult {
  TestName: string // Description of the test being conducted
  Expected: any // What the test should result in (hardcoded value or Boolean)
  Actual: any // The result of the test under the current dataset
  Passed: boolean // True if expected matches actual, otherwise false
}

interface DaxQueriesConfig {
  version: "1.0.0"
  tabOrder: string[] // Array of tab names in display order
  defaultTab: string // Name of the default active tab
}

## Types

type BasicValueAssertions = {
  ShouldBeTrue: (testName: string, actualCondition: boolean) => TestResult
  ShouldBeFalse: (testName: string, actualCondition: boolean) => TestResult
  ShouldBeNull: (testName: string, actualValue: any) => TestResult
  ShouldNotBeNull: (testName: string, actualValue: any) => TestResult
  ShouldBeBlank: (testName: string, actualValue: any) => TestResult
  ShouldNotBeBlank: (testName: string, actualValue: any) => TestResult
  ShouldBeNullOrBlank: (testName: string, actualValue: any) => TestResult
  ShouldNotBeNullOrBlank: (testName: string, actualValue: any) => TestResult
}

type EqualityAssertions = {
  ShouldEqual: (testName: string, expected: any, actual: any) => TestResult
  ShouldNotEqual: (testName: string, notExpected: any, actual: any) => TestResult
  ShouldEqualExactly: (testName: string, expected: any, actual: any) => TestResult
}

type NumericComparisons = {
  ShouldBeGreaterThan: (testName: string, threshold: number, actual: number) => TestResult
  ShouldBeLessThan: (testName: string, threshold: number, actual: number) => TestResult
  ShouldBeGreaterOrEqual: (testName: string, threshold: number, actual: number) => TestResult
  ShouldBeLessOrEqual: (testName: string, threshold: number, actual: number) => TestResult
  ShouldBeBetween: (testName: string, lowerBound: number, upperBound: number, actual: number) => TestResult
}

type StringAssertions = {
  ShouldStartWith: (testName: string, prefix: string, actual: string) => TestResult
  ShouldEndWith: (testName: string, suffix: string, actual: string) => TestResult
  ShouldContainString: (testName: string, substring: string, actual: string) => TestResult
  ShouldMatch: (testName: string, pattern: string, actual: string) => TestResult
}

type ColumnAssertions = {
  ShouldBeNull: (testName: string, columnRef: any) => TestResult
  ShouldNotBeNull: (testName: string, columnRef: any) => TestResult
  ShouldBeBlank: (testName: string, columnRef: any) => TestResult
  ShouldNotBeBlank: (testName: string, columnRef: any) => TestResult
  ShouldBeNullOrBlank: (testName: string, columnRef: any) => TestResult
  ShouldNotBeNullOrBlank: (testName: string, columnRef: any) => TestResult
  ShouldBeDistinct: (testName: string, columnRef: any) => TestResult
  ShouldExist: (testName: string, tableName: string, columnName: string) => TestResult
  IsAvailableInMDX: (testName: string, tableName: string, columnName: string) => TestResult
}

type TableAssertions = {
  ShouldHaveRows: (testName: string, tableRef: any) => TestResult
  ShouldHaveRowCount: (testName: string, tableRef: any, expectedRowCount: number) => TestResult
  ShouldHaveMoreRowsThan: (testName: string, threshold: number, tableToCheck: any) => TestResult
  ShouldExist: (testName: string, tableName: string) => TestResult
}

type RelationshipAssertions = {
  ShouldExist: (testName: string, fromTable: string, fromColumn: string, toTable: string, toColumn: string) => TestResult
}

type BestPracticeAssertions = {
  // Error Prevention
  ShouldHaveSameDataTypeInRelationships: () => TestResult
  CheckErrorPrevention: () => TestResult
  
  // Formatting
  ShouldProvideFormatStringForMeasures: () => TestResult
  ShouldNotSummarizeNumericColumns: () => TestResult
  CheckFormatting: () => TestResult
  
  // DAX Expressions
  ShouldUseFullyQualifiedColumnReferences: () => TestResult
  ShouldUseTreatAsInsteadOfIntersect: () => TestResult
  CheckDAXExpressions: () => TestResult
  
  // Performance
  ShouldAvoidBiDirectionalOnHighCardinalityColumn: () => TestResult
  ShouldRemoveAutoDateTable: () => TestResult
  ShouldAvoidFloatingPointDataTypes: () => TestResult
  ShouldSetIsAvailableInMdxFalseOnNonAttributeColumns: () => TestResult
  CheckPerformance: () => TestResult
}

type TestDiscovery = {
  RetrieveTests: () => table // Returns all test functions (ending with .Test or .Tests)
  RetrieveTestsByEnvironment: (environment: string) => table // Returns tests filtered by environment
}

## Constants

const ENVIRONMENTS = ["DEV", "TEST", "PROD", "ANY"]

const TEST_CATEGORIES_BY_ENV = {
  Calculations: ["DEV"],
  Content: ["DEV", "TEST", "PROD"],
  Schema: ["DEV", "TEST", "PROD"]
}

const NAMING_FORMAT = "[Area].[Environment].Test" | "[Area].[Environment].Tests"

const STANDARD_SCHEMA = {
  TestName: "string",
  Expected: "any",
  Actual: "any",
  Passed: "boolean"
}

## Functions

createTest(userRequest) => {
  1. clarifyEnvironment()
  2. verifyPQLAssert()
  3. identifyTestType()
  4. identifyTablesForValidation()
  5. identifyColumnsForValidation()
  6. identifyMeasuresForValidation()
  7. generateTestCode()
  8. upsertFunctionToModel()
  9. upsertFunctionToTmdl()
  10. createDaxFileInDAXQueriesFolder()
  11. updateDaxQueriesJson()
  12. validateNoSubfolders()
  13. executeTests()
  return: testFilePath, functionName, testResults
}

clarifyEnvironment() => {
  ask: "Which environment is this test for: DEV, TEST, PROD, or ANY?"
  wait for user response
  validate: response in ENVIRONMENTS
}

verifyPQLAssert() => {
  check: functions.tmdl exists in model
  if not installed:
    inform: "PQL.Assert needs to be installed by loading functions.tmdl and refreshing the model"
    halt
}

identifyTestType() => {
  determine: Calculations | Content | Schema
  validate: test type allowed for selected environment
}

identifyTablesForValidation() => {
  analyze: model tables requiring row count validation
  create: separate test for each table using Tbl.ShouldHaveRows or Tbl.ShouldHaveRowCount
}

identifyColumnsForValidation() => {
  analyze: key columns requiring validation
  validate for: nulls, blanks, uniqueness, referential integrity
  use: Col.ShouldNotBeNull, Col.ShouldNotBeBlank, Col.ShouldBeDistinct, Relationship.ShouldExist
}

identifyMeasuresForValidation() => {
  analyze: important measures and calculations
  create: calculation tests using ShouldEqual or numeric comparisons
}

generateTestCode() => {
  pattern: DEFINE FUNCTION [Area].[Env].Tests = () => UNION(...)
  ensure: complete DAX query with EVALUATE statement
  include: descriptive TestName values
}

upsertFunctionToModel() => {
  extract: function name and expression from generated code
  check: if function exists using mcp_powerbi-model_function_operations Get
  if exists:
    update: using mcp_powerbi-model_function_operations Update
  else:
    create: using mcp_powerbi-model_function_operations Create
  verify: function state is Ready
}

upsertFunctionToTmdl() => {
  CRITICAL: locate [ModelName].SemanticModel\definition\functions.tmdl in the workspace
  read: existing functions.tmdl content
  format function entry in TMDL syntax:
    function '[FunctionName]' =
        (params) =>
        expression
  check: if function block for [FunctionName] already exists in file
  if exists:
    replace: the existing function block with the updated definition
  else:
    append: new function block at the end of the file
  note: user-defined test functions do NOT need lineageTag or annotation blocks
  note: preserve all existing content (PQL.Assert library functions) unchanged
}

createDaxFileInDAXQueriesFolder() => {
  CRITICAL: locate the *.SemanticModel folder in the workspace first (e.g., SampleModel.SemanticModel)
  check: if [ModelName].SemanticModel\DAXQueries folder exists, create if not
  CRITICAL: create physical .dax file inside [ModelName].SemanticModel\DAXQueries\ (root level, never in subfolders)
  path: [ModelName].SemanticModel\DAXQueries\[FunctionName].dax
  content: complete DEFINE FUNCTION ... EVALUATE query
  CRITICAL: function name in DEFINE FUNCTION must NOT be wrapped in single quotes
  correct:   DEFINE\n\tFUNCTION Schema.DEV.Tests = () =>
  incorrect: DEFINE\n\tFUNCTION 'Schema.DEV.Tests' = () =>
  validate: file created at root of [ModelName].SemanticModel\DAXQueries\ folder
  error if: file would be created in subfolder
  error if: file would be created at repo root instead of inside *.SemanticModel folder
  note: this creates the tab in DAX Query View
}

updateDaxQueriesJson() => {
  CRITICAL: locate the *.SemanticModel folder in the workspace first (e.g., SampleModel.SemanticModel)
  check: if [ModelName].SemanticModel\DAXQueries\.pbi folder exists, create if not
  check: if [ModelName].SemanticModel\DAXQueries\.pbi\daxQueries.json exists
  if not exists:
    create: initial daxQueries.json with structure:
    {"version": "1.0.0", "tabOrder": [], "defaultTab": ""}
    example with data: {"version": "1.0.0", "tabOrder": ["Query 1","Query 2"], "defaultTab": "Query 2"}
  update: tabOrder array with new test function name
  update: defaultTab to new function name if tabOrder was empty
  validate: only one daxQueries.json exists in [ModelName].SemanticModel\DAXQueries\.pbi
}

renameTest(oldName, newName) => {
  1. validateTestExists(oldName)
  2. renameFunctionInModel(oldName, newName)
  3. renameDaxFile(oldName, newName)
  4. removeDuplicateFiles(newName)
  5. updateDaxQueriesJson()
  return: newFunctionName, cleanedFiles
}

validateTestExists(functionName) => {
  check: function exists using mcp_powerbi-model_function_operations Get
  if not exists:
    error: "Test function not found in model"
    halt
}

renameFunctionInModel(oldName, newName) => {
  get: existing function definition
  delete: old function using mcp_powerbi-model_function_operations Delete
  create: new function with same expression using mcp_powerbi-model_function_operations Create
  verify: function state is Ready
  call: upsertFunctionToTmdl() to remove old entry and add new entry in functions.tmdl
}

renameDaxFile(oldName, newName) => {
  pattern: match [oldName].dax case-insensitive
  find: all .dax files in DAXQueries folder matching pattern
  if found:
    create: new file with newName.dax
    note: old file should be manually deleted by user
}

removeDuplicateFiles(functionName) => {
  scan: DAXQueries folder for .dax files
  identify: files with same base name but different environments
  example: DataQuality.DEV.Tests.dax and DataQuality.ANY.Tests.dax
  if duplicates found:
    warn: "Found duplicate test files - keeping most recent, recommend deleting: [list]"
    list: duplicate files for user review
}

validateNoSubfolders() => {
  check: all .dax files are in DAXQueries root
  if subfolders found:
    error: "Test files must be in DAXQueries root, not subfolders"
}

executeTests() => {
  build: EVALUATE query using UNION of PQL.Assert calls (without DEFINE wrapper)
  execute: using mcp_powerbi-model_dax_query_operations
  return: test results table with TestName, Expected, Actual, Passed columns
  summarize: pass/fail counts
}

auditModelIndependence() => {
  scan: reusable DAX UDF source for TABLE and TABLE EXPR parameters
  flag: direct hard-coded column references on user-supplied TABLE parameters
  verify: row-count-only assertions use COUNTROWS without schema assumptions
  verify: set comparisons normalize table expressions with SELECTCOLUMNS before EXCEPT or INTERSECT
  allow: filters and joins over INFO.* metadata tables because their schemas are known
  report: each TABLE parameter, access pattern, and any model-dependent risk
}

updateChangelog(releaseVersion, releaseDate, changes) => {
  read: CHANGELOG.md
  read: src/manifest.daxlib
  validate: releaseVersion matches manifest version
  validate: releaseDate uses YYYY-MM-DD format
  insert or update: release heading `## [releaseVersion] - releaseDate`
  group changes by Keep a Changelog sections: Added, Changed, Deprecated, Removed, Fixed, Security
  include: user-visible library, tests, documentation, agent, and tooling changes
  verify: no duplicate release heading exists
  return: changed sections and missing release-note items
}

## Commands

create-test(type, environment) => createTest()

rename-test(oldName, newName) => renameTest(oldName, newName)

create-measure-test(measureName, environment: "DEV") => 
  Creates DEV calculation tests using ShouldEqual or numeric comparisons

validate-data-quality(tableName) => 
  Creates column and table assertions for nulls, uniqueness, row counts, ranges

validate-model-structure => 
  Creates tests using Tbl.ShouldExist, Col.ShouldExist, Relationship.ShouldExist

retrieve-tests => 
  Returns: EVALUATE PQL.Assert.RetrieveTests()

retrieve-tests-by-env(environment: "DEV" | "TEST" | "PROD" | "ANY") => 
  Returns: EVALUATE PQL.Assert.RetrieveTestsByEnvironment(environment)

validate-best-practices(category: "ErrorPrevention" | "Formatting" | "DAXExpressions" | "Performance") =>
  Returns appropriate PQL.Assert.BP.Check* function

audit-model-independence => auditModelIndependence()

update-changelog => updateChangelog()

## Pattern Matching

match userRequest {
  /test.*measure/ => createMeasureTest(environment: "DEV")
  /validate.*data quality/ => validateDataQuality()
  /validate.*model structure/ => validateModelStructure()
  /validate.*best practice/ => validateBestPractices()
  /find.*test/ => retrieveTests()
  /run.*test/ => retrieveTestsByEnvironment()
  /create.*test/ => createTest(userRequest)
  /rename.*test/ => renameTest(oldName, newName)
  /update.*test.*environment/ => renameTest(extractOldName, extractNewName)
  /model.*independence|schema.*assumption|TABLE parameter/ => auditModelIndependence()
  /update.*changelog|changelog|release notes/ => updateChangelog()
}

---

# PQL.Assert - DAX Unit Testing Library

A comprehensive DAX assertion library for writing unit tests in Power BI and Analysis Services semantic models. PQL.Assert provides standardized assertion functions to validate data, calculations, and model integrity.

## 🚀 Getting Started

### Installation

1. Load the `functions.tmdl` file into your semantic model
2. Refresh the model to make functions available
3. Start writing tests using PQL.Assert functions

### Basic Usage

```dax
// Basic assertion example
EVALUATE PQL.Assert.ShouldEqual("Test 1: 2+2 should equal 4", 4, 2+2)
```

## 📚 Function Reference

### Basic Assertions

- `PQL.Assert.ShouldBeTrue(testName, actualCondition)` - Asserts condition is TRUE
- `PQL.Assert.ShouldBeFalse(testName, actualCondition)` - Asserts condition is FALSE
- `PQL.Assert.ShouldBeNull(testName, actualValue)` - Asserts value is NULL (BLANK())
- `PQL.Assert.ShouldNotBeNull(testName, actualValue)` - Asserts value is not NULL
- `PQL.Assert.ShouldBeBlank(testName, actualValue)` - Asserts value is empty string ("")
- `PQL.Assert.ShouldNotBeBlank(testName, actualValue)` - Asserts value is not empty string
- `PQL.Assert.ShouldBeNullOrBlank(testName, actualValue)` - Asserts value is NULL or empty string
- `PQL.Assert.ShouldNotBeNullOrBlank(testName, actualValue)` - Asserts value has content

### Equality Assertions

- `PQL.Assert.ShouldEqual(testName, expected, actual)` - Asserts values are equal
- `PQL.Assert.ShouldNotEqual(testName, notExpected, actual)` - Asserts values are not equal
- `PQL.Assert.ShouldEqualExactly(testName, expected, actual)` - Case-sensitive string equality

### Numeric Comparisons

- `PQL.Assert.ShouldBeGreaterThan(testName, threshold, actual)` - Asserts actual > threshold
- `PQL.Assert.ShouldBeLessThan(testName, threshold, actual)` - Asserts actual < threshold
- `PQL.Assert.ShouldBeGreaterOrEqual(testName, threshold, actual)` - Asserts actual >= threshold
- `PQL.Assert.ShouldBeLessOrEqual(testName, threshold, actual)` - Asserts actual <= threshold
- `PQL.Assert.ShouldBeBetween(testName, lowerBound, upperBound, actual)` - Asserts value within range

### String Assertions

- `PQL.Assert.ShouldStartWith(testName, prefix, actual)` - Asserts string starts with prefix
- `PQL.Assert.ShouldEndWith(testName, suffix, actual)` - Asserts string ends with suffix
- `PQL.Assert.ShouldContainString(testName, substring, actual)` - Asserts string contains substring
- `PQL.Assert.ShouldMatch(testName, pattern, actual)` - Asserts string matches pattern

### Column Assertions

- `PQL.Assert.Col.ShouldBeNull(testName, columnRef)` - Asserts all column values are NULL
- `PQL.Assert.Col.ShouldNotBeNull(testName, columnRef)` - Asserts column has non-NULL values
- `PQL.Assert.Col.ShouldBeBlank(testName, columnRef)` - Asserts all column values are empty strings
- `PQL.Assert.Col.ShouldNotBeBlank(testName, columnRef)` - Asserts column has non-empty values
- `PQL.Assert.Col.ShouldBeNullOrBlank(testName, columnRef)` - Asserts all values are NULL or empty
- `PQL.Assert.Col.ShouldNotBeNullOrBlank(testName, columnRef)` - Asserts column has content
- `PQL.Assert.Col.ShouldBeDistinct(testName, columnRef)` - Asserts all column values are unique
- `PQL.Assert.Col.ShouldExist(testName, tableName, columnName)` - Asserts column exists

### Table Assertions

- `PQL.Assert.Tbl.ShouldHaveRows(testName, tableRef)` - Asserts table has at least one row
- `PQL.Assert.Tbl.ShouldHaveRowCount(testName, tableRef, expectedRowCount)` - Asserts exact row count
- `PQL.Assert.Tbl.ShouldHaveMoreRowsThan(testName, threshold, tableToCheck)` - Asserts row count > threshold
- `PQL.Assert.Tbl.ShouldExist(testName, tableName)` - Asserts table exists

### Relationship Assertions

- `PQL.Assert.Relationship.ShouldExist(testName, fromTable, fromColumn, toTable, toColumn, [fromCardinality], [toCardinality], [securityFilteringBehavior])` - Asserts a relationship exists between two columns, with optional cardinality and security filtering checks. Pass `""` (or omit) any optional argument to skip that check.
  - `fromCardinality` (optional) — expected From-side cardinality: `"One"` or `"Many"`.
  - `toCardinality` (optional) — expected To-side cardinality: `"One"` or `"Many"`.
  - `securityFilteringBehavior` (optional) — expected filter direction: `"OneDirection"` or `"BothDirections"`.

### Test Discovery

- `PQL.Assert.RetrieveTests()` - Returns all test functions (ending with .Test or .Tests)
- `PQL.Assert.RetrieveTestsByEnvironment(environment)` - Returns tests filtered by environment (e.g., "DEV", "TEST", "PROD") matching `.{ENV}.` or `.ANY.` in function names. Case-insensitive. Returns all tests if environment is blank.

### Best Practice Validations

PQL.Assert includes built-in semantic model validation functions based on Best Practice Analyzer rules. These functions help identify common issues and anti-patterns in your Power BI models.

> **Note:** Additional validation rules are being added continuously. This is an initial set covering the most critical model health checks.

#### Error Prevention

- `PQL.Assert.BP.ShouldHaveSameDataTypeInRelationships()` - Validates that relationship columns have matching data types (avoiding int64→decimal relationships)
- `PQL.Assert.BP.CheckErrorPrevention()` - Runs all error prevention checks

#### Formatting

- `PQL.Assert.BP.ShouldProvideFormatStringForMeasures()` - Validates that visible measures have format strings assigned
- `PQL.Assert.BP.ShouldNotSummarizeNumericColumns()` - Validates that numeric columns have SummarizeBy set to None
- `PQL.Assert.BP.CheckFormatting()` - Runs all formatting checks

#### DAX Expressions

- `PQL.Assert.BP.ShouldUseFullyQualifiedColumnReferences()` - Validates that column references use Table[Column] format
- `PQL.Assert.BP.ShouldUseTreatAsInsteadOfIntersect()` - Validates that measures use TREATAS instead of INTERSECT for better performance
- `PQL.Assert.BP.CheckDAXExpressions()` - Runs all DAX expression checks

#### Performance

- `PQL.Assert.BP.ShouldAvoidBiDirectionalOnHighCardinalityColumn()` - Validates bi-directional relationships on high-cardinality columns (>1M distinct values)
- `PQL.Assert.BP.ShouldRemoveAutoDateTable()` - Validates that auto-date tables are disabled
- `PQL.Assert.BP.ShouldAvoidFloatingPointDataTypes()` - Validates that columns avoid Number (Double) data type
- `PQL.Assert.BP.ShouldSetIsAvailableInMdxFalseOnNonAttributeColumns()` - Validates IsAvailableInMdx setting on non-attribute columns
- `PQL.Assert.BP.CheckPerformance()` - Runs all performance checks

**Example Usage:**
```dax
// Run individual validation
EVALUATE PQL.Assert.BP.ShouldProvideFormatStringForMeasures()

// Run all checks in a category
EVALUATE PQL.Assert.BP.CheckFormatting()
EVALUATE PQL.Assert.BP.CheckPerformance()

// Combine all best practice checks
EVALUATE UNION(
    PQL.Assert.BP.CheckErrorPrevention(),
    PQL.Assert.BP.CheckFormatting(),
    PQL.Assert.BP.CheckDAXExpressions(),
    PQL.Assert.BP.CheckPerformance()
)
```

## 🏗️ Workspace Governance & Environments

### Environment Types

**DEV (Development)**
- Static/parameterized data for stable testing
- Known baseline data state
- Focus on calculation and logic validation

**TEST**
- Live data for client/stakeholder validation
- Pre-production environment
- Content and schema validation

**PROD (Production)**
- Live production data
- Health checks and data drift detection
- Continuous monitoring

**ANY**
- Tests that apply across all environments
- Universal validation rules

### Test Types by Environment

| Test Category | DEV | TEST | PROD | Description |
|---------------|-----|------|------|-------------|
| **Testing Calculations** | ✓ | | | Validate measures, calculated columns, edge cases |
| **Testing Content** | ✓ | ✓ | ✓ | Row counts, data quality, value validation |
| **Testing Schema** | ✓ | ✓ | ✓ | Table/column existence, relationships, data types |

## 🧪 Writing and Running Tests

### Standard Schema

All test functions must return results following the DAX Query View Testing Pattern standard schema:

| Column Name | Type | Description |
|-------------|------|-------------|
| TestName | String | Description of the test being conducted |
| Expected | Any | What the test should result in (hardcoded value or Boolean) |
| Actual | Any | The result of the test under the current dataset |
| Passed | Boolean | True if expected matches actual, otherwise false |

### Tab Naming Convention

Follow the pattern: `[name].[environment].test(s)`

**Format Guidelines:**
- `[name]` - Keep to 15-20 characters for tab readability
- `[environment]` - DEV, TEST, PROD, or ANY
- Use `.tests` for multiple assertions, `.test` for single assertion

**Examples:**
- `DataQuality.DEV.Tests` - Data quality tests for development
- `Schema.ANY.Tests` - Schema validation for all environments
- `Revenue.PROD.Tests` - Revenue calculation health checks for production
- `Customers.TEST.Tests` - Customer data validation for testing environment

### Creating Test Functions

#### Testing Calculations (DEV Environment)
```dax
DEFINE
	FUNCTION BusinessLogic.DEV.Tests = () =>
	UNION (
		PQL.Assert.ShouldEqual("Revenue calculation with positive sales", 15000, [Total Revenue]),
		PQL.Assert.ShouldEqual("Revenue calculation with zero sales", 0, [Total Revenue Zero Case]),
		PQL.Assert.ShouldBeNull("Revenue calculation with blank sales", [Total Revenue Blank Case]),
		PQL.Assert.ShouldEqual("Basic math validation", 4, 2+2)
	)

EVALUATE BusinessLogic.DEV.Tests()
```

#### Testing Content (Any Environment)
```dax
DEFINE
	FUNCTION DataContent.ANY.Tests = () =>
	UNION (
		PQL.Assert.Tbl.ShouldHaveRows("Fact table has data", 'Sales'),
		PQL.Assert.Col.ShouldNotBeNull("Customer ID not null", 'Customers'[CustomerID]),
		PQL.Assert.ShouldBeGreaterThan("Fact table row count threshold", 1000, COUNTROWS('Sales')),
		PQL.Assert.Col.ShouldNotBeNull("Order date not null", 'Orders'[OrderDate])
	)

EVALUATE DataContent.ANY.Tests()
```

#### Testing Schema (Any Environment)
```dax
DEFINE
	FUNCTION Schema.ANY.Tests = () =>
	UNION (
		PQL.Assert.Tbl.ShouldExist("Sales table exists", "Sales"),
		PQL.Assert.Col.ShouldExist("Customer ID column exists", "Customers", "CustomerID"),
		PQL.Assert.Relationship.ShouldExist("Sales-Customer relationship", "Sales", "CustomerID", "Customers", "CustomerID"),
		PQL.Assert.Relationship.ShouldExist("Sales-Customer is Many-to-One, single direction", "Sales", "CustomerID", "Customers", "CustomerID", "Many", "One", "OneDirection")
	)

EVALUATE Schema.ANY.Tests()
```

#### Advanced Measure Testing (DEV Environment)
```dax
DEFINE 

	FUNCTION Measures.DEV.Tests = () =>
    VAR __DS0FilterTable = 
        TREATAS({TRUE}, 'TestData'[IsActive])

    VAR _Test1 =
        SUMMARIZECOLUMNS(
            __DS0FilterTable,
            "CountID", IGNORE(CALCULATE(COUNTA('TestData'[ID])))
        )

	RETURN PQL.Assert.ShouldEqual("ShouldBeEqual to 3", 3, _Test1)

EVALUATE Measures.DEV.Tests()
```

### Discovering Tests

Use the test discovery functions to find all available test functions:

```dax
// Find all test functions
EVALUATE PQL.Assert.RetrieveTests()

// Find tests by environment (recommended approach)
EVALUATE PQL.Assert.RetrieveTestsByEnvironment("DEV")   // Returns .DEV. and .ANY. tests
EVALUATE PQL.Assert.RetrieveTestsByEnvironment("TEST")  // Returns .TEST. and .ANY. tests
EVALUATE PQL.Assert.RetrieveTestsByEnvironment("PROD")  // Returns .PROD. and .ANY. tests

// Case-insensitive - these are equivalent
EVALUATE PQL.Assert.RetrieveTestsByEnvironment("dev")
EVALUATE PQL.Assert.RetrieveTestsByEnvironment("Dev")
EVALUATE PQL.Assert.RetrieveTestsByEnvironment("DEV")

// Custom environments are supported
EVALUATE PQL.Assert.RetrieveTestsByEnvironment("UAT")      // Returns .UAT. and .ANY. tests
EVALUATE PQL.Assert.RetrieveTestsByEnvironment("STAGING")  // Returns .STAGING. and .ANY. tests

// Blank returns all tests (same as RetrieveTests)
EVALUATE PQL.Assert.RetrieveTestsByEnvironment("")

// Manual filtering (alternative approach)
EVALUATE FILTER(PQL.Assert.RetrieveTests(), CONTAINSSTRING([FUNCTION_NAME], ".DEV."))
EVALUATE FILTER(PQL.Assert.RetrieveTests(), CONTAINSSTRING([FUNCTION_NAME], ".PROD."))
EVALUATE FILTER(PQL.Assert.RetrieveTests(), CONTAINSSTRING([FUNCTION_NAME], ".ANY."))
```

This returns a table of all functions ending with `.Test` or `.Tests`, making it easy to identify and run your test suites by environment.

### Running All Tests

After discovering tests, you can run them individually or create environment-specific test runners:

```dax
DEFINE
	// Run all DEV tests
	FUNCTION DEV.AllTests = () =>
	UNION (
		BusinessLogic.DEV.Tests(),
		DataQuality.DEV.Tests()
	)
	
	// Run all production health checks
	FUNCTION PROD.HealthChecks = () =>
	UNION (
		DataContent.ANY.Tests(),
		Schema.ANY.Tests()
	)

EVALUATE DEV.AllTests()
EVALUATE PROD.HealthChecks()
```

### Test Validation

Use the built-in validation layer to check if test expectations match results:

```dax
// Include "should pass" or "should fail" in test names for automatic validation
VAR _Results = Example.Tests()
VAR _Validation = 
    ADDCOLUMNS(
        _Results,
        "ExpectedToPass", CONTAINSSTRING([TestName], "should pass"),
        "ValidationStatus", 
        IF(
            CONTAINSSTRING([TestName], "should pass") && [Passed] = TRUE, "✅ CORRECT",
            IF(CONTAINSSTRING([TestName], "should fail") && [Passed] = FALSE, "✅ CORRECT", "❌ MISMATCH")
        )
    )

EVALUATE _Validation
```

## 💡 Best Practices

### Test Naming

- Use descriptive test names that explain what is being tested
- Include "should pass" or "should fail" for validation automation
- Group related tests in functions ending with `.Tests`

### Test Organization

- Create separate test functions for different areas (data validation, business logic, etc.)
- Use meaningful function names like `DataQuality.Tests`, `Calculations.Tests`
- Keep tests focused and atomic - test one thing per assertion

### Example Test Structure

```dax
DEFINE
	// Content validation for any environment
	FUNCTION DataQuality.ANY.Tests = () =>
	UNION (
		// Null checks
		PQL.Assert.Col.ShouldNotBeNull("Data Quality: Customer ID should not be null", 'Customers'[CustomerID]),
		PQL.Assert.Col.ShouldNotBeNull("Data Quality: Order date should not be null", 'Orders'[OrderDate]),
		
		// Uniqueness checks
		PQL.Assert.Col.ShouldBeDistinct("Data Quality: Customer ID should be unique", 'Customers'[CustomerID]),
		
		// Range checks
		PQL.Assert.ShouldBeBetween("Data Quality: Order amount in valid range", 0, 1000000, MAX('Orders'[Amount]))
	)
	
	// Calculation validation for development only
	FUNCTION BusinessLogic.DEV.Tests = () =>
	UNION (
		// Calculation validation with static data
		PQL.Assert.ShouldEqual("Business Logic: Total sales calculation", 15000, [Total Sales]),
		PQL.Assert.ShouldBeGreaterThan("Business Logic: Growth rate positive", 0, [Growth Rate])
	)
	
	// Schema validation for any environment
	FUNCTION Schema.ANY.Tests = () =>
	UNION (
		PQL.Assert.Tbl.ShouldExist("Schema: Customers table exists", "Customers"),
		PQL.Assert.Col.ShouldExist("Schema: CustomerID column exists", "Customers", "CustomerID")
	)

// Run environment-specific test suites
EVALUATE DataQuality.ANY.Tests()
EVALUATE BusinessLogic.DEV.Tests()

// Discover all available test functions
EVALUATE PQL.Assert.RetrieveTests()

// Discover tests by environment
EVALUATE FILTER(PQL.Assert.RetrieveTests(), CONTAINSSTRING([FUNCTION_NAME], ".DEV."))
```

## Documentation

- See the `lib/functions.tmdl` file for the functions included in this library.
- See the `manifest.daxlib` file for the library metadata and configuration.