# PQL.Assert

A DAX assertion library for testing semantic models.

## Usage

```dax
EVALUATE
'PQL.Assert.ShouldBeTrue'("Test condition is true", 1 = 1)
```

```dax
EVALUATE
'PQL.Assert.ShouldEqual'("Test values match", 100, SUM(Sales[Amount]))
```

## Available Assertions

### Basic Assertions
- `PQL.Assert.ShouldBeTrue` - Asserts condition is TRUE
- `PQL.Assert.ShouldBeFalse` - Asserts condition is FALSE
- `PQL.Assert.ShouldEqual` - Asserts two values are equal (case-insensitive for strings)
- `PQL.Assert.ShouldNotEqual` - Asserts two values are not equal
- `PQL.Assert.ShouldEqualExactly` - Asserts two strings are exactly equal (case-sensitive)
- `PQL.Assert.ShouldBeGreaterThan` - Asserts value is greater than threshold
- `PQL.Assert.ShouldBeLessThan` - Asserts value is less than threshold
- `PQL.Assert.ShouldBeGreaterOrEqual` - Asserts value is >= threshold
- `PQL.Assert.ShouldBeLessOrEqual` - Asserts value is <= threshold
- `PQL.Assert.ShouldBeBetween` - Asserts value is within a range (inclusive)

### Null/Blank Assertions
- `PQL.Assert.ShouldBeNull` - Asserts value is NULL (DAX BLANK())
- `PQL.Assert.ShouldNotBeNull` - Asserts value is not NULL
- `PQL.Assert.ShouldBeBlank` - Asserts value is BLANK (empty string "")
- `PQL.Assert.ShouldNotBeBlank` - Asserts value is not BLANK (not empty string)
- `PQL.Assert.ShouldBeNullOrBlank` - Asserts value is NULL or BLANK
- `PQL.Assert.ShouldNotBeNullOrBlank` - Asserts value has actual content

### String Assertions
- `PQL.Assert.ShouldStartWith` - Asserts string starts with prefix (case-insensitive)
- `PQL.Assert.ShouldEndWith` - Asserts string ends with suffix (case-insensitive)
- `PQL.Assert.ShouldContainString` - Asserts string contains substring (case-insensitive)
- `PQL.Assert.ShouldMatch` - Asserts string matches pattern (case-insensitive)

### Col Assertions
- `PQL.Assert.Col.ShouldBeNull` - Asserts all column values are NULL
- `PQL.Assert.Col.ShouldNotBeNull` - Asserts column has non-NULL values
- `PQL.Assert.Col.ShouldBeBlank` - Asserts all column values are BLANK (empty string)
- `PQL.Assert.Col.ShouldNotBeBlank` - Asserts column has non-BLANK values
- `PQL.Assert.Col.ShouldBeNullOrBlank` - Asserts all column values are NULL or BLANK
- `PQL.Assert.Col.ShouldNotBeNullOrBlank` - Asserts column has actual content
- `PQL.Assert.Col.ShouldBeDistinct` - Asserts column values are unique
- `PQL.Assert.Col.ShouldExist` - Asserts column exists in model

### Tbl Assertions
- `PQL.Assert.Tbl.ShouldHaveRows` - Asserts table has rows
- `PQL.Assert.Tbl.ShouldHaveRowCount` - Asserts table has exact row count
- `PQL.Assert.Tbl.ShouldHaveMoreRowsThan` - Asserts table has more rows than threshold
- `PQL.Assert.Tbl.ShouldExist` - Asserts table exists in model

### Relationship Assertions
- `PQL.Assert.Relationship.ShouldExist` - Asserts relationship exists

## Documentation

- See the `lib/functions.tmdl` file for the functions included in this library.
- See the `manifest.daxlib` file for the library metadata and configuration.

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## License

This project is licensed under the MIT License.
