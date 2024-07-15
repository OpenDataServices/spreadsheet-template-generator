# JSON Schema Spreadsheet Template Generator

This Python package provides a command-line tool for generating a spreadsheet input template for standards that use JSON Schema and CSV codelists with [custom JSON Schema properties](https://os4d.opendataservices.coop/development/schema/#extended-json-schema), including:

* Open Contracting Data Standard (OCDS) and its profiles
* Open Contracting for Infrastructure Data Standard (OC4IDS)
* Risk Data Library Standard (RDLS)
* Open Fibre Data Standard (OFDS)
* 360Giving Standard
* Beneficial Ownership Data Standard (BODS)

The tool produces a template for entering data in spreadsheet format with the following features:

* Metadata for each field (title, description, whether the field is required, types, string formats, codelist enums)
* For fields that reference a codelist, a link to the codelist documentation
* Additional data input guidance for arrays of strings and Well-Known-Text geometries.
* Type validation
* Drop-down list validation for codelists
* Drop-down list validation for `id` fields in arrays
* Support for Well-Known Text format for geometries
* Compatibility with [Flatten Tool](https://flatten-tool.readthedocs.io/en/latest/) for converting entered data to JSON format
* Customisable per-field user guidance
* Fixed (pre-populated) field values
* Formulae (calculated) field values
* User-editable variables, for use in formulae

The tool is based on two other tools that also support multiple standards: [Flatten Tool](https://flatten-tool.readthedocs.io/en/latest/), which converts data between tabular and JSON formats, and [OCDS Kit](https://ocdskit.readthedocs.io/en/latest/), which provides a command for generating a tabular list of a schema's fields and their metadata.

If you are viewing this on GitHub or PyPI, open the full documentation for additional details.

```{toctree}
get_started.md
cli.md
user.md
example.md
```