# PQL.Assert - DAX Unit Testing Library

A comprehensive DAX assertion library for writing unit tests in Power BI and Analysis Services semantic models.

## 📚 Documentation

For complete library documentation, usage examples, and API reference, see the **[Library Documentation](src/README.md)**.

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

The `examples/` folder contains a Power Automate solution (`PQLAssertviaPowerAutomate_1_0_0_1.zip`) that enables automated test execution against your semantic models.

### Importing the Solution

1. **Download** the solution ZIP file from `examples/PQLAssertviaPowerAutomate_1_0_0_1.zip`
2. **Navigate** to [Power Automate](https://make.powerautomate.com) or [Power Apps](https://make.powerapps.com)
3. **Import** the solution following Microsoft's guide: [Import solutions](https://learn.microsoft.com/en-us/power-apps/maker/data-platform/import-update-export-solutions)
4. **Set environment variables** when prompted during import:
   - **Workspace GUID**: The unique identifier of your Power BI workspace (found in the workspace URL)
   - **Semantic Model ID**: The unique identifier of your semantic model (found in the dataset URL or settings)

### Finding Your IDs

- **Workspace GUID**: Navigate to your workspace in Power BI Service. The URL will contain: `https://app.powerbi.com/groups/{workspace-guid}/...`
- **Semantic Model ID**: Open your semantic model settings or view the URL when accessing the dataset: `https://app.powerbi.com/groups/{workspace-guid}/datasets/{semantic-model-id}/...`

## 🆘 Support

- **Documentation**: [src/README.md](src/README.md)
- **Issues**: [GitHub Issues](https://github.com/clientfirsttech/PQL.Assert/issues)
- **Discussions**: [GitHub Discussions](https://github.com/clientfirsttech/PQL.Assert/discussions)

