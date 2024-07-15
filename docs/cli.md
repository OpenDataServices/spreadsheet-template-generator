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
:-d --codelist-docs-url:    The URL at which codelists documentation is available. The documentation must feature an HTML anchor matching the name of each codelist CSV file.
:-w --wkt:                  Use well-known text format in place of GeoJSON geometry objects.
:-i --input-rows:           The number of input rows.
:-m --main-sheet-name:      The name of the main (parent) sheet.
:-t --truncation-length:    The maximum length of the components of sheet names.
:-r --rollup:               'Roll up' columns from subsheets into the main sheet if they are specified in a rollUp attribute in the schema.

Option defaults and further options can be specified in a YAML-formatted configuration file:

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

