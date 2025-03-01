# Contributing to AWS Cost Optimizer - Unified Solution

First off, thank you for considering contributing to the AWS Cost Optimizer! It's people like you that make this tool better for everyone.

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the existing issues to avoid duplicates. When you create a bug report, please include as many details as possible:

* Use a clear and descriptive title
* Describe the exact steps to reproduce the problem
* Provide specific examples to demonstrate the steps
* Describe the behavior you observed after following the steps
* Explain which behavior you expected to see instead and why
* Include CloudWatch logs if applicable
* Include AWS CloudFormation template versions
* Specify which AWS services and regions are involved

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please provide:

* Use a clear and descriptive title
* Provide a step-by-step description of the suggested enhancement
* Provide specific examples to demonstrate the steps
* Describe the current behavior and explain which behavior you expected to see instead
* Explain why this enhancement would be useful
* List some other tools or applications where this enhancement exists

### Pull Requests

1. Fork the repo and create your branch from `main`
2. If you've added code that should be tested, add tests
3. If you've changed APIs, update the documentation
4. Ensure the test suite passes
5. Make sure your code lints
6. Issue that pull request!

## Development Process

### Setting Up Development Environment

1. **Install required tools:**
    ```bash
    # Install AWS CLI
    pip install awscli

    # Install development dependencies
    pip install -r requirements-dev.txt
    ```

2. **Configure AWS credentials:**
    ```bash
    aws configure
    ```

3. **Enable AWS Compute Optimizer:**
    ```bash
    aws compute-optimizer update-enrollment-status --status Active
    ```

### Testing

1. **Unit Tests:**
    ```bash
    python -m pytest tests/unit/
    ```

2. **Integration Tests:**
    ```bash
    python -m pytest tests/integration/
    ```

3. **CloudFormation Template Validation:**
    ```bash
    aws cloudformation validate-template \
        --template-body file://templates/unified-optimizer-template.yml
    ```

### Code Style Guidelines

1. **Python Code:**
    - Follow PEP 8 style guide
    - Use meaningful variable names
    - Add docstrings to functions and classes
    - Keep functions focused and small
    - Use type hints where appropriate

2. **CloudFormation Templates:**
    - Use consistent indentation (2 spaces)
    - Include descriptions for resources
    - Use logical naming conventions
    - Add relevant tags to resources

3. **Documentation:**
    - Keep README.md up to date
    - Document all parameters and configurations
    - Include examples where helpful
    - Update changelog for significant changes

### Commit Messages

1. Use the present tense ("Add feature" not "Added feature")
2. Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
3. Limit the first line to 72 characters or less
4. Reference issues and pull requests liberally after the first line
5. Consider starting the commit message with an applicable emoji:
    - 🎨 :art: when improving the format/structure of the code
    - 🐎 :racehorse: when improving performance
    - 🚱 :non-potable_water: when plugging memory leaks
    - 📝 :memo: when writing docs
    - 🐛 :bug: when fixing a bug
    - 🔥 :fire: when removing code or files
    - 💚 :green_heart: when fixing the CI build
    - ✅ :white_check_mark: when adding tests
    - 🔒 :lock: when dealing with security
    - ⬆️ :arrow_up: when upgrading dependencies
    - ⬇️ :arrow_down: when downgrading dependencies

### Branch Naming Convention

1. Feature branches: `feature/description`
2. Bug fix branches: `fix/description`
3. Documentation branches: `docs/description`
4. Release branches: `release/version`

### Project Structure

```
unified-cost-optimizer/
├── .github/
│   ├── ISSUE_TEMPLATE/
│   └── PULL_REQUEST_TEMPLATE.md
├── src/
│   ├── ec2/
│   ├── asg/
│   └── rds/
├── tests/
│   ├── unit/
│   └── integration/
├── templates/
│   └── unified-optimizer-template.yml
├── docs/
├── README.md
├── CONTRIBUTING.md
├── LICENSE
└── requirements.txt
```

### Release Process

1. **Version Bump:**
    - Update version in relevant files
    - Update CHANGELOG.md
    - Create release branch

2. **Testing:**
    - Run full test suite
    - Perform integration testing
    - Validate templates

3. **Documentation:**
    - Update README if needed
    - Update API documentation
    - Update examples

4. **Release:**
    - Create GitHub release
    - Tag version
    - Update release notes

### Additional Notes

1. **Issue and Pull Request Labels:**
    - `bug` - Something isn't working
    - `enhancement` - New feature or request
    - `documentation` - Documentation only changes
    - `good first issue` - Good for newcomers
    - `help wanted` - Extra attention is needed
    - `invalid` - Something's wrong
    - `question` - Further information is requested
    - `wontfix` - This will not be worked on

2. **Getting Help:**
    - Check the documentation
    - Open an issue with a clear description
    - Tag your issue with appropriate labels
    - Provide context and examples

3. **Recognition:**
    - Contributors will be recognized in:
        - GitHub repository's contributor list
        - Release notes when their contributions are included
        - Documentation when substantial changes are made

Thank you for contributing to AWS Cost Optimizer!