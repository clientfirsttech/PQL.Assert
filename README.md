# PQL.Assert - DAX Unit Testing Library

A comprehensive DAX assertion library for writing unit tests in Power BI and Analysis Services semantic models.

## 📚 Documentation

For complete library documentation, usage examples, and API reference, see the **[Library Documentation](src/README.md)**.

## 📝 Release Notes

See [CHANGELOG.md](CHANGELOG.md) for the full version history and per-release notes.

## 🤝 Contributing

We welcome contributions to PQL.Assert! Here's how you can help:

### Reporting Issues

If you find a bug or have a feature request:

1. **Search existing issues** to avoid duplicates
2. **Create a new issue** with:
   - Clear description of the problem or feature
   - Steps to reproduce (for bugs)
   - Expected vs actual behavior
   - DAX code samples when relevant
   - Power BI version information

### Contributing Code

1. **Fork the repository**
2. **Create a feature branch** from `dev`
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**
   - Add new assertion functions to `src/lib/functions.tmdl`
   - Update tests in `tests/` directory
   - Follow existing code patterns and naming conventions
4. **Test your changes**
   - Run the test suite to ensure nothing breaks
   - Add tests for new functionality
5. **Submit a Pull Request**
   - Target the `dev` branch
   - Include clear description of changes
   - Reference any related issues

### Development Guidelines

- **Follow DAX Query View Testing Pattern** naming conventions
- **Use environment-specific naming** (`[name].[environment].test(s)`)
- **Include comprehensive tests** for new assertion functions
- **Document new functions** with examples
- **Maintain backward compatibility** when possible

### Code Structure

```
src/
├── lib/functions.tmdl          # Core assertion functions
├── manifest.daxlib             # Library metadata
└── README.md                   # Library documentation

tests/
└── model/TestingModel.SemanticModel/
    └── DAXQueries/
        ├── Complete Function Tests.dax    # Comprehensive test suite - validates assert functions run appropriately and indicate pass or failure consistently
        ├── Measure.Tests.dax             # Advanced measure testing
        └── [other test files]
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚡ Power Automate Integration

The `examples/power-automate/` folder contains a Power Automate solution (`PQLAssertviaPowerAutomate_1_0_0_1.zip`) that enables automated test execution against your semantic models.

### Importing the Solution

1. **Download** the solution ZIP file from `examples/power-automate/PQLAssertviaPowerAutomate_1_0_0_1.zip`
2. **Navigate** to [Power Automate](https://make.powerautomate.com) or [Power Apps](https://make.powerapps.com)
3. **Import** the solution following Microsoft's guide: [Import solutions](https://learn.microsoft.com/en-us/power-apps/maker/data-platform/import-update-export-solutions)
4. **Set environment variables** when prompted during import:
   - **Workspace GUID**: The unique identifier of your Power BI workspace (found in the workspace URL)
   - **Semantic Model ID**: The unique identifier of your semantic model (found in the dataset URL or settings)

### Finding Your IDs

- **Workspace GUID**: Navigate to your workspace in Power BI Service. The URL will contain: `https://app.powerbi.com/groups/{workspace-guid}/...`
- **Semantic Model ID**: Open your semantic model settings or view the URL when accessing the dataset: `https://app.powerbi.com/groups/{workspace-guid}/datasets/{semantic-model-id}/...`

## 🤖 GitHub Copilot Custom Agent

The `examples/custom-agents/` folder contains a custom GitHub Copilot agent configuration for automated semantic model testing. This agent specializes in creating and managing DAX Query View tests using PQL.Assert.

### What is the Custom Agent?

The **Power BI Semantic Model Test Specialist** is a custom Copilot agent that:
- Creates DAX Query View tests following best practices
- Validates data quality, schema, and calculations
- Follows environment-specific testing patterns (DEV, TEST, PROD, ANY)
- Integrates directly with your semantic model via MCP (Model Context Protocol)

### Setting Up the Custom Agent

#### Prerequisites

- GitHub Copilot subscription with Copilot Chat
- VS Code with GitHub Copilot extension
- Power BI Model Context Protocol (MCP) extension for VS Code
- Access to a Power BI semantic model (.pbip format)

#### Installation Steps

1. **Install Required VS Code Extensions**
   - [GitHub Copilot](https://marketplace.visualstudio.com/items?itemName=GitHub.copilot)
   - [GitHub Copilot Chat](https://marketplace.visualstudio.com/items?itemName=GitHub.copilot-chat)
   - [Power BI Model Context Protocol](https://marketplace.visualstudio.com/items?itemName=powerbi.powerbi-modeling-mcp)

2. **Configure the Custom Agent**
    - Copy `examples/custom-agents/agents/power-query-tester.agent.md` to your workspace `.github/agents` folder:
     ```
     .github/
       agents/
             power-query-tester.agent.md
     ```
   - Or place it in your global Copilot instructions folder (varies by OS)

3. **Connect to Your Semantic Model**
   - Open your Power BI project (.pbip) in VS Code
   - Use the Power BI MCP extension to connect to your semantic model
   - The agent will automatically detect the connection

4. **Start Using the Agent**
   - Open GitHub Copilot Chat in VS Code
   - Reference the agent by name or let Copilot detect it
   - Ask it to create tests:
     ```
     @workspace Create data quality tests for the Customers table
     ```
     ```
     @workspace Create DEV environment tests for Total Revenue measure
     ```
     ```
     @workspace Validate schema for all fact tables
     ```

### Agent Capabilities

The custom agent can:
- **Create Tests**: Generate DAX Query View tests with proper naming conventions
- **Validate Data Quality**: Check for nulls, blanks, uniqueness, and referential integrity
- **Test Calculations**: Validate measure logic in DEV environments
- **Validate Schema**: Ensure tables, columns, and relationships exist
- **Run Best Practice Checks**: Execute built-in semantic model validations
- **Discover Tests**: Find and filter existing test functions by environment
- **Rename Tests**: Update test names and manage environment transitions
- **Audit Model Independence**: Review reusable assertion functions for TABLE parameter schema assumptions
- **Maintain Release Notes**: Use the cloud-agent Sudolang `updateChangelog` workflow to keep `CHANGELOG.md` aligned with `src/manifest.daxlib`

### Example Usage

```text
# In VS Code Copilot Chat:

User: Create content validation tests for the Sales table in ANY environment

Agent: [Creates DAX Query View test function with assertions for:
  - Table has rows
  - Key columns not null
  - Data within expected ranges]

User: Run all DEV tests

Agent: [Executes PQL.Assert.RetrieveTestsByEnvironment("DEV") and shows results]

User: Validate best practices for performance

Agent: [Runs PQL.Assert.BP.CheckPerformance() and reports findings]
```

### Agent Configuration

The agent follows strict constraints:
- Must ask for environment (DEV, TEST, PROD, ANY) before creating tests
- Places all test files in DAXQueries folder root (no subfolders)
- Updates daxQueries.json for tab ordering
- Verifies PQL.Assert installation before test creation
- Does not modify production measures or model structure unless explicitly asked
- Returns complete DAX queries (not fragments)

For complete agent documentation, see [examples/custom-agents/agents/power-query-tester.agent.md](examples/custom-agents/agents/power-query-tester.agent.md).

### Cloud Agent Workflow

The [examples/cloud-agent/.github/pql-tester-sudo.md](examples/cloud-agent/.github/pql-tester-sudo.md) prompt includes a compact Sudolang workflow for semantic-model test automation. In addition to test creation and execution, it now includes `updateChangelog(releaseVersion, releaseDate, changes)` for maintaining release notes. The workflow validates the requested release against `src/manifest.daxlib`, writes Keep a Changelog sections, and checks for duplicate release headings.

When reviewing reusable assertion functions, pair the `pql-assert` skill with the `model-independence` skill. Functions that accept TABLE parameters should avoid hard-coded column assumptions on those parameters. Row-count checks, string-list schema checks, and set operations over normalized `SELECTCOLUMNS` projections are preferred patterns.

## 🆘 Support

- **Documentation**: [src/README.md](src/README.md)
- **Issues**: [GitHub Issues](https://github.com/clientfirsttech/PQL.Assert/issues)
- **Discussions**: [GitHub Discussions](https://github.com/clientfirsttech/PQL.Assert/discussions)

