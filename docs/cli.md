# Command-Line Interface

To see all commands available, run:

```shell
./manage.py --help
```

## create-template

Generates a template from SCHEMAFILE for entering data in spreadsheet format.

Required arguments:

* ``SCHEMAFILE`` the JSON Schema file

Optional arguments:

:-c --config-file:          Read option defaults from the specified YAML file.
:-b --codelist-base-url:    The base URL at which codelist CSV files are available.
:-d --codelist-docs-url:    The URL at which codelist documentation is available.
:-w --wkt:                  Use well-known text format in place of GeoJSON geometry objects.
:-i --input-rows:           The number of input rows.
:-m --main-sheet-name:      The name of the main (parent) sheet.
:-t --truncation-length:    The maximum length of the components of sheet names.
:-r --rollup:               'Roll up' columns from subsheets into the main sheet if they are specified in a rollUp attribute in the schema.

### Configuration file

Option defaults and further options can be specified in a YAML-formatted configuration file:

:codelist_base_url: The base URL at which codelist CSV files are available, e.g.

    ```yaml
    codelist_base_url: http://www.example.com/path/to/codelist/directory
    ```

    Codelist CSV files must be accessible by appending the CSV file name to this URL. For example, if the CSV files are available at URLs like [https://raw.githubusercontent.com/ThreeSixtyGiving/standard/main/codelists/currency.csv](https://raw.githubusercontent.com/ThreeSixtyGiving/standard/main/codelists/currency.csv), the base url is `https://raw.githubusercontent.com/ThreeSixtyGiving/standard/main/codelists/`.

:codelist_docs_url: The URL at which codelist documentation is available, e.g.

    ```yaml
    codelist_docs_url: http://www.example.com/path/to/codelist/docs
    ```

    Links to codelist documentation are constructed by appending the codelist filename, excluding the file type extension, to the codelist documentation URL. For example, if the URL is [https://open-fibre-data-standard.readthedocs.io/en/0.3/reference/codelists.html](https://open-fibre-data-standard.readthedocs.io/en/0.3/reference/codelists.html) and a field references `currency.CSV`, the link will be [https://open-fibre-data-standard.readthedocs.io/en/0.3/reference/codelists.html#currency](https://open-fibre-data-standard.readthedocs.io/en/0.3/reference/codelists.html#currency).

:wkt: Whether to use [Well-Known Text (WKT) format](https://en.wikipedia.org/wiki/Well-known_text_representation_of_geometry) in place of GeoJSON `Geometry` objects, e.g.

    ```yaml
    wkt: true
    ```

    If the schema includes a [GeoJSON `Geometry` definition](https://open-fibre-data-standard.readthedocs.io/en/0.3/reference/schema.html#geometry), each reference to the definition will be replaced with a WKT format `geometry`.

:input_rows: The number of input rows, e.g.

    ```yaml
    input_rows: 1000
    ```
:main_sheet_name: The name of the main (parent) sheet, e.g.

    ```yaml
    main_sheet_name: My sheet name
    ```

:truncation_length: The maximum length of the components of sheet names, e.g.

    ```yaml
    truncation_length: 10
    ```

:rollup: Whether to 'roll up' columns from subsheets into the main sheet if they are specified in a rollUp attribute in the schema, e.g.

    ```yaml
    rollup: true
    ```

    For more information, see Flatten Tool's [rolling up documentation](https://flatten-tool.readthedocs.io/en/latest/create-template/#rolling-up).

:sheets: An ordered list of sheets to include in the template, e.g.

    ```yaml
    sheets:
        - sheet1
        - sheet2
    ```

    If not specified, all sheets ouput by Flatten Tool are included in alphabetical order.

:include_fields: A list of fields to include in the template. When set, all other fields in the schema are omitted from the template. Specify fields using JSON Pointer syntax, e.g.

    ```yaml
    include_fields:
        - path/to/field
        - path/to/array/0/field
    ```

    You cannot set both `include_fields` and `exclude_fields` in the same config file.

:exclude_fields: A list of fields to exclude from the template. Specify fields using JSON Pointer syntax, e.g.

    ```yaml
    exclude_fields:
        - path/to/field
        - path/to/array/0/field
    ```

    You cannot set both `include_fields` and `exclude_fields` in the same config file.

:metadata: A map of metadata fields and values to add to the [metadata tab](https://flatten-tool.readthedocs.io/en/latest/unflatten/#metadata-tab), e.g.
  
    ```yaml
    metadata:
        version: 1.1
        title: My dataset
    ```

:field_guidance: A map of fields and user guidance. Specify fields using JSON Pointer syntax, e.g. 

    ```yaml
    field_guidance:
        path/to/field: Guidance associated with path/to/field
        path/to/array/0/field: Guidance associated with path/to/array/0/field
    ```

:fixed_values: A map of fields and fixed (pre-populated) values. A field's fixed values are populated when the first input column in the same sheet is populated. Fixed values are implemented using formulae of the form `IF(B{row}="","",fixed_value)`. For more complex logic, specify your own formulae using the `formulae` configuration option. Specify fields using JSON Pointer syntax, e.g. 

    ```yaml
    fixed_values:
        path/to/field: 123
        path/to/array/0/field: abc
    ```

:formulae: A map of fields and formulae to calculate their values. Specify formulae using Excel-compatible functions. To reference values on the same row, substitute the row number with `{row}`. Changes to the schema or configuration options (including `include_fields`, `exclude_fields`, `wkt` and `rollup`) may affect formulae. Specify fields using JSON Pointer syntax, e.g.

    ```yaml
    formulae:
        path/to/field: =IF(B{row}="","",123)
    ```

:variables: A map of user-editable variable names and default values, for use in formulae. A default value can be specified for each variable. Variables are listed in the `# Variables` sheet of the template and a named range is created for each variable. Variable names:

    * Can contain only letters, numbers, and underscores.
    * Can't start with a number, or the words "true" or "false."
    * Can't contain any spaces or punctuation.
    * Must be 1–250 characters.
    * Can't be in either A1 or R1C1 syntax, like "A1:B2" or "R1C1:R2C2."

    For example:

    ```yaml
    variables:
        currency: GBP
    ```
:source_fields: A map of source fields to include in the template, for use in formulae. Source fields are excluded when data is converted to JSON format, e.g.

    ```yaml
    field_name:
        sheet: The sheet to which to add the field.
        successor: The field before which to add the field.
        title: A human-readable title for the field.
        description: A human-readable description for the field.
        required: Whether the field is required (mandatory).
        type: The field's type, e.g. string (text), number (decimal), integer (whole number) etc.
    ```