---
name: dax-blank-handling
description: Rules for BLANK (NULL) and empty-string ("") handling in DAX, written in SudoLang. Use when writing or reviewing DAX that compares, counts, aggregates or formats values that may be BLANK or "", and when reviewing PQL.Assert functions for consistent NULL vs blank semantics.
user-invokable: true
---

# DAX BLANK Handling

> Credit: the DAX language rules below are summarized from **"Handling BLANK in DAX"** by Marco Russo,
> [SQLBI](https://www.sqlbi.com/articles/blank-handling-in-dax/). Read the article for the full
> explanation and examples. The PQL.Assert sections are this repository's own conventions and
> findings, verified against `tests/model/TestingModel`.

```sudolang
# DaxBlankHandling {
  Review and write DAX so that BLANK (NULL) and empty strings ("") are handled deliberately,
  never by accident of implicit conversion.

  ## Vocabulary {
    NULL  = the DAX BLANK value: BLANK(), a missing value, or a NULL loaded from the source.
            Any data type can hold it.
    blank = the empty string "" (text only). It is a real value, not BLANK.
    // PQL.Assert uses these words strictly in function names:
    //   ...Null...        checks BLANK() only
    //   ...Blank...       checks "" only
    //   ...NullOrBlank... checks either
  }

  ## LanguageRules {
    // Source: SQLBI, "Handling BLANK in DAX"
    conversion {
      BLANK is not propagated like SQL NULL. It converts to 0, "" or FALSE, depending on the
      type the expression needs.
      exception: multiplication and division with BLANK as a term or numerator give BLANK
        (BLANK() * 4, BLANK() / 4). 4 / BLANK() gives infinity.
      BLANK() + 4 = 4; BLANK() - 4 = -4; BLANK() + BLANK() = BLANK.
      BLANK() & "A" = "A".
    }
    comparison {
      `=` converts BLANK first: BLANK() = 0, BLANK() = "", BLANK() = FALSE are all TRUE.
      `==` is strict: BLANK() == 0, BLANK() == "" and BLANK() == FALSE are FALSE;
        BLANK() == BLANK() is TRUE.
      BLANK() IN { 0 } is FALSE; BLANK() IN { BLANK() } is TRUE.
      to test for BLANK, use ISBLANK(x), never x = BLANK().
      a chain of IF tests with `=` matches BLANK, 0 and "" on the first test, so order matters.
    }
    switchRule {
      SWITCH matches BLANK internally like ISBLANK, but a BLANK input matches the first BLANK
        *or FALSE* option in the list.
      put the BLANK() option first, or convert the input before SWITCH.
    }
    tableToScalar {
      an empty table converted to a scalar is BLANK: COUNTROWS(FILTER(T, FALSE)) is BLANK, not 0.
      add `+ 0` when the result is compared, used in SWITCH, or formatted.
    }
    booleanIf {
      in IF, a BLANK branch takes the other branch's type. If that type is Boolean, BLANK is
        cast to FALSE: IF(1 = 1, BLANK(), TRUE) returns FALSE.
      a Boolean column read directly keeps its BLANKs.
    }
  }

  ## AggregationFacts {
    // Verified on TestingModel: TestData[Short Text] = { "x", "", "Error - Timeout", "Err", BLANK }
    COUNTBLANK(c)           counts BLANK *and* ""                          -> 2
    COUNTA(c)               counts "" but not BLANK                        -> 4
    ISBLANK("")             FALSE
    DISTINCTCOUNT(c)        counts BLANK as a value
    DISTINCTCOUNTNOBLANK(c) excludes BLANK, keeps ""
    LEN(BLANK())            0, so LEN(c) = 0 matches both BLANK and ""
    MOD(BLANK(), 2) = 0     TRUE, so an "is even" test counts NULL unless it checks ISBLANK first
    c = 0, c <= 0           TRUE for BLANK; guard numeric tests with NOT ISBLANK(c)
    MINX / MAXX / AVERAGEX  skip BLANK
    a bare column reference (VALUES, ALLNOBLANKROW, COUNTROWS(ALLNOBLANKROW(c))) gives
      *distinct values*, not rows. Use a table argument to count rows.
    ALLNOBLANKROW(c)        drops only the relationship "unknown member" row; real BLANK values stay
    FORMAT(BLANK(), "0")    returns "", so text like "% ( of 3)" appears unless counts use + 0
    x == ""                 errors when x is a number: "comparison operations do not support
                              comparing values of type Integer with values of type Text"
    COUNTAX(VALUES(c), IF(cond, 1, BLANK())) on a column whose only value is "" raised
      "Type mismatch" only for columns defined inside a query (DEFINE COLUMN). The same functions work on
      a real model column of only "", so test with model columns before concluding a function is broken.
  }

  ## Idioms {
    isNull(x)        = ISBLANK(x)
    isBlank(x)       = NOT ISBLANK(x) && LEN(x) = 0          // works for every data type
    isNullOrBlank(x) = LEN(x) = 0
    hasContent(x)    = LEN(x) > 0
    nullRows(T, c)   = COUNTROWS(FILTER(T, ISBLANK(c))) + 0
    blankRows(c)     = CALCULATE(COUNTBLANK(c), FILTER(ALLNOBLANKROW(c), NOT ISBLANK(c) && LEN(c) = 0)) + 0
                       // "" rows from a column reference alone
    nullRowsFromColumn(c) = (COUNTBLANK(c) + 0) - blankRows(c)
    contentRows(c)        = (COUNTA(c) + 0) - blankRows(c)
    count(...)       = <expr> + 0 before any comparison, SWITCH or FORMAT
  }

  ## Constraints {
    - Never test for NULL with `= BLANK()`, `= 0` or `= ""`; use ISBLANK.
    - Never treat COUNTBLANK as a NULL count; it includes "".
    - Never compare a column of unknown type with `== ""`; use LEN.
    - Never compare DISTINCTCOUNT with COUNTA; one counts BLANK and the other doesn't.
      Use DISTINCTCOUNTNOBLANK with COUNTA.
    - Always add `+ 0` to COUNTROWS / COUNTX / COUNTAX / DISTINCTCOUNT results that may be empty.
    - In SWITCH, put BLANK() first or normalize the input.
    - Rates need a row denominator from a table, not from a column reference.
    - A function's name, description, Expected/Actual text and tests must all use NULL and
      blank in the sense defined in Vocabulary.
  }

  ## UdfParameterFacts {
    // Verified on TestingModel (Power BI Desktop, 2026-10)
    DOUBLE, STRING, VARIANT, SCALAR VARIANT EXPR parameters keep BLANK: ISBLANK(param) works inside.
    BOOLEAN parameters convert BLANK to FALSE at the call, before the body runs: ISBLANK(param) is FALSE.
    AVERAGE / STDEV.S / PERCENTILE.INC / MIN / MAX / COUNTA on a column parameter work over rows
      and skip BLANK; wrap in CALCULATE(..., REMOVEFILTERS()) for whole-column scope.
    STDEV.S over a single value returns infinity/NaN; guard with a count > 1.
  }

  ## PQLAssertPolicy {
    // The rules PQL.Assert 0.8.0 follows. Use them when writing or reviewing a library function.
    - NULL is never treated as 0, "" or FALSE inside a check. Guard comparisons with NOT ISBLANK.
    - Value checks (range, statistics, sign, text, set membership, uniqueness, shares) skip NULL
      values and fail with "NO VALUES" when the column has no non-NULL value:
        VAR _HasValues = NOT ISEMPTY(FILTER(ALLNOBLANKROW(c), NOT ISBLANK(c)))
    - Statistics are computed over rows, not distinct values.
    - Row-based rates fail with "NO ROWS" on an empty table; problem counts pass at zero.
    - Scalar numeric and string checks fail when actual is NULL and show it as "NULL".
      ShouldEqual / ShouldEqualExactly treat NULL and "" as different.
    - BOOLEAN parameters cannot see BLANK (see UdfParameterFacts); document instead of guarding.
    - Shipped functions keep their name and parameters. Fix behavior in place when only NULL input
      changes; deprecate and add a V2 when the signature must change.
    - Every rule above has pass and fail cases in TestingModel NullHandling.ANY.Tests.
  }

  ## Functions {
    reviewExpression(dax) => {
      for each rule in Constraints:
        find: violations in dax
      for each comparison, count, SWITCH and FORMAT:
        decide: what happens for BLANK, for "", for 0, and for an empty table
      return: [{ location, rule, inputThatBreaks, fix }]
    }

    reviewAssertion(functionName) => {
      1. read: the function body and its /// description
      2. classify: what it treats as NULL, as blank, and as content (use AggregationFacts)
      3. compare: with the Vocabulary meaning of its name
      4. run or reason over the matrix
           { all NULL, all "", values + NULL, values + "", values only, empty table }
           for every data type the parameter accepts
      5. report: mismatches between name, description, behavior and tests
      6. if behavior is wrong and the function has shipped:
           do not change it; deprecate it and add a correctly named or V2 function
    }

    reviewLibrary() => {
      scan: src/lib/*.tmdl for ISBLANK, COUNTBLANK, COUNTA, DISTINCTCOUNT, ALLNOBLANKROW,
            VALUES(, FORMAT(, `= ""`, `== ""`, `= BLANK()`, SWITCH(, COUNTROWS(
      for each function using them: reviewAssertion(functionName)
      return: summary table { function, treatsAsNull, treatsAsBlank, consistentWithName, action }
    }
  }

  ## Commands {
    /review-blank(daxOrFunction) => reviewExpression or reviewAssertion
    /review-blank-library        => reviewLibrary()
  }
}
```
