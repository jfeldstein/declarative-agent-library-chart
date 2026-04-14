## MODIFIED Requirements

### Requirement: [CFHA-VER-002] Tests explicitly claim which requirements they evidence

For **Python** tests under **`runtime/tests/`**: when the traceability matrix lists evidence as **`path.py::test_function`**, that **test function’s** docstring SHALL contain the **requirement ID** string. When the matrix lists only **`path.py`**, the ID SHALL appear in the **module, class, or any test function** docstring in that file. For **Helm unittest** suite files under **`helm/tests/`** (for example **`helm/tests/*_test.yaml`**), the ID SHALL appear in a **`#` comment** on the suite or on the relevant **`it:`** block; a single top-of-file **`# Traceability:`** line is acceptable when one file evidences many requirements, but **prefer** a comment adjacent to the **`it:`** when one case maps to one requirement.

#### Scenario: Pytest evidence references IDs

- **WHEN** a maintainer adds or changes a test that is the **primary** evidence for a promoted requirement
- **THEN** that test SHALL include the requirement’s **ID string** in the scope defined above so reviewers and automated checks can see the linkage

#### Scenario: Helm unittest evidence references IDs

- **WHEN** a maintainer adds or changes a helm unittest that evidences a chart-level **SHALL**
- **THEN** the suite or `it:` entry SHALL include the requirement’s **ID string** in a comment as above
