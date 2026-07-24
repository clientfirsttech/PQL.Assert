---
name: model-independence
description: Guidelines for writing model-independent DAX user-defined functions. Use when creating or reviewing DAX functions to ensure they don't assume specific schema structures. Based on SQLBI article about model-dependent vs model-independent UDFs.
user-invokable: false
---

# Model Independence in DAX User-Defined Functions

> Based on concepts from SQLBI's article "Model-dependent and model-independent user-defined functions in DAX"

## Overview

Model independence is a critical principle when designing reusable DAX user-defined functions (UDFs). A **model-independent** function can be used in any semantic model without requiring specific table or column structures, while a **model-dependent** function assumes the existence of particular schema elements.

## Key Concepts

### Model-Dependent Functions

A function is **model-dependent** when it:
- Explicitly references columns from tables passed as parameters (e.g., `MyTable[Name]`)
- Assumes a specific schema structure for TABLE parameters
- Uses implicit column names that must exist in the calling model
- Cannot be reused across different models with different schemas

**Example of Model-Dependent Code:**
```dax
// ❌ Model-dependent - assumes [Name] column exists
MyFunction = (inputTable: TABLE) =>
    FILTER(inputTable, [Name] = "Value")
```

### Model-Independent Functions

A function is **model-independent** when it:
- Uses row iteration (GENERATESERIES, ADDCOLUMNS) to access table data
- Does not assume any specific column names in TABLE parameters
- Works with table structure and row count without referencing columns
- Can be reused across any semantic model

**Example of Model-Independent Code:**
```dax
// ✅ Model-independent - no column assumptions
MyFunction = (inputTable: TABLE) =>
    VAR _RowCount = COUNTROWS(inputTable)
    RETURN _RowCount > 0
```

## Making Functions Model-Independent

### Problem: Direct Column References

When a function accepts a TABLE parameter and directly references columns by name, it becomes model-dependent:

```dax
// ❌ Model-dependent approach
PQL.Assert.Perspective.ShouldContain = 
    (testName: STRING, perspectiveName: STRING, expectedTables: TABLE) =>
    VAR _MissingTables = EXCEPT(expectedTables, _ActualTables)
    // This assumes expectedTables has a [Name] column!
    VAR _MissingCount = COUNTROWS(_MissingTables)
    RETURN ...
```

### Solution: Use GENERATESERIES for Row Iteration

Replace direct column references with row-by-row iteration using GENERATESERIES:

```dax
// ✅ Model-independent approach
PQL.Assert.Perspective.ShouldContain = 
    (testName: STRING, perspectiveName: STRING, expectedTables: TABLE) =>
    VAR _ExpectedTablesList = 
        CONCATENATEX(
            GENERATESERIES(1, COUNTROWS(expectedTables)),
            SELECTCOLUMNS(
                TOPN(1, expectedTables, 1, [VALUE]),
                "Value", CONCATENATEX(CURRENTTABLE(), "", "")
            ),
            ","
        )
    // Now we have a comma-separated string without assuming column names
    RETURN ...
```

### Pattern: Extract Single-Column Table to String List

A common pattern for model independence is converting a single-column TABLE parameter to a comma-separated string:

```dax
// Model-independent conversion pattern
VAR _StringList = 
    CONCATENATEX(
        GENERATESERIES(1, COUNTROWS(inputTable)),
        SELECTCOLUMNS(
            TOPN(1, inputTable, [VALUE], ASC),
            "IteratedValue", CONCATENATEX(CURRENTTABLE(), "", "")
        ),
        ","
    )
```

**How this works:**
1. `GENERATESERIES(1, COUNTROWS(inputTable))` - Creates a sequence from 1 to row count
2. For each iteration, `TOPN(1, inputTable, [VALUE], ASC)` - Gets rows from inputTable (NOTE: [VALUE] is the GENERATESERIES iterator, not a column name in inputTable. Row ordering may not be deterministic without an explicit sort key from the original table.)
3. `SELECTCOLUMNS(..., CONCATENATEX(CURRENTTABLE(), "", ""))` - Extracts the value from the first (and only) column of the current row, regardless of that column's actual name
4. `CONCATENATEX(...)` - Joins all values with a delimiter

**Important Notes:** 
- The [VALUE] reference is from the GENERATESERIES iterator, not a column in the input table
- This pattern works with any single-column table regardless of the column's actual name
- Row ordering is not guaranteed unless the input table has an explicit sort applied

### Alternative Pattern: Accept String Parameters Instead

Another approach to model independence is to avoid TABLE parameters entirely for simple lists:

```dax
// Instead of accepting TABLE parameter:
// ❌ MyFunction = (items: TABLE) => ...

// Accept comma-separated string:
// ✅ MyFunction = (itemsList: STRING) => ...
MyFunction = (itemsList: STRING) =>
    VAR _Items = itemsList
    VAR _ItemCount = 
        IF(
            LEN(TRIM(_Items)) = 0,
            0,
            LEN(_Items) - LEN(SUBSTITUTE(_Items, ",", "")) + 1
        )
    RETURN _ItemCount
```

## Best Practices

### 1. Avoid Column Assumptions in TABLE Parameters

```dax
// ❌ BAD - Assumes [Name] column
FILTER(inputTable, [Name] = "Value")

// ✅ GOOD - Works with any single-column table
VAR _Values = 
    CONCATENATEX(
        GENERATESERIES(1, COUNTROWS(inputTable)),
        SELECTCOLUMNS(
            TOPN(1, inputTable, [VALUE], ASC),
            "Value", CONCATENATEX(CURRENTTABLE(), "", "")
        ),
        ","
    )
```

### 2. Use STRING Parameters for Simple Lists

```dax
// ❌ Harder to use - requires table construction
MyFunction(
    DATATABLE("Name", STRING, {{"Item1"}, {"Item2"}, {"Item3"}})
)

// ✅ Easier to use - simple string
MyFunction("Item1,Item2,Item3")
```

### 3. Document Parameter Expectations

When TABLE parameters are necessary, clearly document expectations:

```dax
/// @param {TABLE} inputTable - Single-column table (any column name accepted)
/// The function extracts values from the first column regardless of name
```

### 4. Prefer Set Operations Over Row Iteration When Possible

If you need to perform set operations (EXCEPT, INTERSECT) and both tables come from the model (not parameters), those operations are inherently model-dependent but acceptable:

```dax
// This is acceptable - both tables from INFO functions
VAR _Missing = EXCEPT(_Expected, _Actual)
```

But when _Expected comes from a parameter, convert to string-based comparison:

```dax
// Model-independent approach using exact string matching with delimiters
VAR _ExpectedUpper = "," & UPPER(TRIM(_ExpectedList)) & ","
VAR _Matched = 
    FILTER(
        _Actual,
        CONTAINSSTRING(_ExpectedUpper, "," & TRIM(UPPER([Name])) & ",")
    )
// Note: Delimiters (commas) prevent most substring false matches
// but names should not contain commas themselves
```

**Limitation:** The string-based CONTAINSSTRING approach with delimiters works well for most cases, but names containing the delimiter character (comma) will cause issues. Document this limitation clearly, or use a different delimiter that won't appear in names (e.g., pipe `|` or semicolon `;`).

## Common Model-Dependent Antipatterns

### Antipattern 1: Direct Column Access on Parameter Tables

```dax
// ❌ Antipattern
MyFunction = (items: TABLE) =>
    FILTER(items, [Name] = "Value")  // Assumes [Name] column
```

### Antipattern 2: Using EXCEPT with Parameter Tables

```dax
// ❌ Antipattern
MyFunction = (expected: TABLE, actual: TABLE) =>
    VAR _Missing = EXCEPT(expected, actual)  // Assumes matching schemas
    RETURN _Missing
```

### Antipattern 3: JOIN Operations on Parameter Tables

```dax
// ❌ Antipattern
MyFunction = (table1: TABLE, table2: TABLE) =>
    NATURALINNERJOIN(table1, table2)  // Assumes compatible schemas
```

## Refactoring Checklist

When reviewing or creating DAX functions, ensure:

- [ ] No direct column references on TABLE parameters (e.g., `paramTable[ColumnName]`)
- [ ] Use GENERATESERIES pattern for row-by-row table iteration
- [ ] Consider STRING parameters instead of TABLE for simple lists
- [ ] Document any schema expectations clearly
- [ ] Test function with different table structures
- [ ] Verify function works without model-specific dependencies

## Example: Refactoring Model-Dependent to Model-Independent

**Before (Model-Dependent):**
```dax
function 'PQL.Assert.Perspective.ShouldContain' =
    (testName: STRING, perspectiveName: STRING, expectedTables: TABLE) =>
    VAR _ActualTables = /* ... query actual tables ... */
    VAR _MissingTables = EXCEPT(expectedTables, _ActualTables)
    // ❌ EXCEPT assumes expectedTables has same schema as _ActualTables
    VAR _MissingCount = COUNTROWS(_MissingTables)
    RETURN /* ... result ... */
```

**After (Model-Independent):**
```dax
function 'PQL.Assert.Perspective.ShouldContain' =
    (testName: STRING, perspectiveName: STRING, expectedTablesList: STRING) =>
    VAR _ActualTables = /* ... query actual tables ... */
    
    // Convert string list to comparable format
    VAR _ExpectedCount = 
        IF(
            LEN(TRIM(expectedTablesList)) = 0,
            0,
            LEN(expectedTablesList) - LEN(SUBSTITUTE(expectedTablesList, ",", "")) + 1
        )
    VAR _ExpectedUpper = "," & UPPER(expectedTablesList) & ","
    
    // Compare using string matching
    VAR _MatchedTables = 
        FILTER(
            _ActualTables,
            CONTAINSSTRING(_ExpectedUpper, "," & UPPER([Name]) & ",")
        )
    VAR _MissingCount = MAX(0, _ExpectedCount - COUNTROWS(_MatchedTables))
    
    RETURN /* ... result ... */
```

## Testing Model Independence

To verify a function is model-independent:

1. **Create test with arbitrary column names**: Pass a table with unusual column names
2. **Test across different models**: Use the function in models with different schemas
3. **Review function signature**: Ensure TABLE parameters don't imply schema requirements
4. **Check for column references**: Search for `[ColumnName]` patterns on parameter tables

## Summary

**Model-independent functions** are:
- More reusable across different semantic models
- Easier to maintain and test
- Less prone to breaking when model schemas change
- Better aligned with library/framework design principles

**Key technique**: Use **GENERATESERIES + TOPN + CONCATENATEX** pattern to iterate rows without assuming column names.

**Best practice**: For simple lists, prefer **STRING parameters** (comma-separated) over TABLE parameters to avoid schema dependencies entirely.

## See Also

- PQL.Assert function design guidelines
- DAX Query Guidelines (especially parameter handling)
- SQLBI article: "Model-dependent and model-independent user-defined functions in DAX"
