import click
import codecs
import csv
import datetime
import json
import os
import requests
import subprocess
import warnings
import xlsxwriter
import yaml

from ocdskit.mapping_sheet import mapping_sheet
from xlsxwriter.utility import xl_col_to_name

# https://flatten-tool.readthedocs.io/en/latest/unflatten/#metadata-tab
# https://flatten-tool.readthedocs.io/en/latest/unflatten/#configuration-properties-skip-and-header-rows
META_CONFIG = ["#", "hashComments"]


def get(url):
    """
    GETs a URL and returns the response. Raises an exception if the status code is not successful.
    """
    response = requests.get(url)
    response.raise_for_status()
    response.encoding = response.apparent_encoding
    return response


def json_dump(filename, data):
    """
    Writes JSON data to the given filename.
    """
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def delete_directory_contents(directory_path):
    """
    Deletes the contents of a directory on disk.
    """
    if os.path.isdir(directory_path):
        for filename in os.listdir(directory_path):
            file_path = os.path.join(directory_path, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print("Failed to delete %s. Reason: %s" % (file_path, e))


def configure(ctx, param, filename):
    if filename:
        with open(filename, "r") as f:
            config = yaml.safe_load(f)
        ctx.default_map = config


@click.group()
def cli():
    pass


@cli.command()
@click.argument('schemafile', type=click.Path(exists=True))
@click.option(
    "-c",
    "--config-file",
    type=click.Path(dir_okay=False),
    callback=configure,
    is_eager=True,
    expose_value=False,
    help="Read option defaults from the specified YAML file.",
    show_default=True,
)
@click.option(
    "-o",
    "--output-file",
    type=click.Path(dir_okay=False),
    default="template.xlsx",
    help="Path to which to write the template.",
    show_default=True,
)
@click.option(
    "-b",
    "--codelist-base-url",
    type=str,
    default=None,
    help="The base URL at which codelist CSV files are available.",
)
@click.option(
    "-d",
    "--codelist-docs-url",
    type=str,
    default=None,
    help="The URL at which codelists documentation is available. The documentation must feature an HTML anchor matching the name of each codelist CSV file.",
)
@click.option(
    "-w",
    "--wkt",
    is_flag=True,
    default=True,
    show_default=True,
    help="Whether to use well-known text format in place of GeoJSON geometry objects.",
)
@click.option(
    "-i",
    "--input-rows",
    type=int,
    default=1000,
    show_default=True,
    help="The number of input rows.",
)
@click.option(
    "-m",
    "--main-sheet-name",
    type=str,
    default="main",
    show_default=True,
    help="The name of the main (parent) sheet.",
)
@click.option(
    "-t",
    "--truncation-length",
    type=int,
    default=10,
    show_default=True,
    help="The length of the components of sheet names.",
)
@click.option(
    "-r",
    "--rollup",
    is_flag=True,
    default=False,
    show_default=True,
    help="Whether to 'Roll up' columns from subsheets into the main sheet if they are specified in a rollUp attribute in the schema.",
)
@click.pass_context
def create_template(
    ctx,
    schemafile,
    output_file,
    codelist_base_url,
    codelist_docs_url,
    wkt,
    input_rows,
    main_sheet_name,
    truncation_length,
    rollup
):
    """
    Generates a template from SCHEMAFILE for entering data in spreadsheet format.

    SCHEMAFILE the JSON Schema file from which to generate the template. Additional options can be specified in a configuration file.
    """

    # Parse configuration options not mapped to CLI options
    if ctx.default_map:

        option_types = {
            "sheets": list,
            "include_fields": list,
            "exclude_fields": list,
            "package_metadata": dict,
            "field_guidance": dict,
            "fixed_values": dict,
            "formulae": dict,
            "variables": dict,
            "source_fields": dict
        }

        # Validate types and set defaults
        for option, t in option_types.items():
            if ctx.default_map.get(option) and type(ctx.default_map.get(option)) != t:
                raise TypeError(f"Config: {option} is not a {t}.")
            elif ctx.default_map.get(option) is None:
                if t == list:
                    ctx.default_map[option] = []
                elif t == dict:
                    ctx.default_map[option] = {}
                else:
                    ctx.default_map[option] = None

        sheets = {sheet: [] for sheet in ctx.default_map['sheets']}
        include_fields = ctx.default_map['include_fields']
        exclude_fields = ctx.default_map['exclude_fields']
        package_metadata = ctx.default_map['package_metadata'] 
        field_guidance = ctx.default_map['field_guidance']
        fixed_values = ctx.default_map['fixed_values']
        formulae = ctx.default_map['formulae']
        variables = ctx.default_map['variables']
        source_fields = {f"# {path}": field for path, field in ctx.default_map['source_fields'].items()}

    else:
        sheets = {}
        include_fields = None
        exclude_fields = None
        package_metadata = {}
        field_guidance = {}
        fixed_values = {}
        formulae = {}
        variables = {}
        source_fields = {}

    if include_fields and exclude_fields:
        raise RuntimeError("Config file must specify at most one of `include_fields` and `exclude_fields`.")

    # Get schema file
    with open(schemafile, 'r') as f:
        schema = json.load(f)

    # Generate a temporary CSV template using Flatten Tool
    temp_path = ".temp"
    os.makedirs(temp_path, exist_ok=True)
    command = f"flatten-tool create-template -s {schemafile} -f csv -m {main_sheet_name} -o {temp_path} --truncation-length {truncation_length}"
    if wkt:
        command = f"{command} --convert-wkt"
    if rollup:
        command = f"{command} --rollup"
    print(f"Running Flatten Tool with command {command}")
    subprocess.run(command.split(" "))

    # Truncate CSV filenames to 31 characters for Excel compatibility
    filenames = os.listdir(temp_path)
    for index, filename in enumerate(filenames):
        if filename.split(".")[-1] == "csv":
            os.rename(
                os.path.join(temp_path, filename),
                os.path.join(
                    temp_path, "".join([filename.split(".csv")[0][:31], ".csv"])
                ),
            )

    # Get field metadata from schema
    schema_table = mapping_sheet(schema, include_codelist=True, base_uri=schemafile)
    field_metadata = {field["path"]: field for field in schema_table[1]}
    
    # Add source fields from config file
    field_metadata.update(source_fields)

    # Create XLSX template
    workbook = xlsxwriter.Workbook(output_file)

    # Define order, row heights and cell formats for header rows
    header_rows = {
        "path": {
            "row_height": None,
            "cell_format": workbook.add_format({"bold": True, "bg_color": "#efefef"}),
        },
        "title": {
            "row_height": None,
            "cell_format": workbook.add_format({"bg_color": "#efefef"}),
        },
        "description": {
            "row_height": 30,
            "cell_format": workbook.add_format(
                {
                    "font_size": 8,
                    "text_wrap": True,
                    "valign": "top",
                    "bg_color": "#efefef",
                }
            ),
        },
        "required": {
            "row_height": None,
            "cell_format": workbook.add_format({"font_size": 8, "bg_color": "#efefef"}),
        },
        "type": {
            "row_height": None,
            "cell_format": workbook.add_format({"font_size": 8, "bg_color": "#efefef"}),
        },
        "values": {
            "row_height": 30,
            "cell_format": workbook.add_format(
                {
                    "font_size": 8,
                    "text_wrap": True,
                    "valign": "top",
                    "bg_color": "#efefef",
                }
            ),
        },
        "codelist": {
            "row_height": None,
            "cell_format": workbook.add_format(
                {
                    "font_size": 8,
                    "font_color": "blue" if codelist_docs_url else "black",
                    "underline": True if codelist_docs_url else False,
                    "bg_color": "#efefef",
                }
            ),
        },
        "input guidance": {
            "row_height": 50,
            "cell_format": workbook.add_format(
                {
                    "font_size": 8,
                    "text_wrap": True,
                    "valign": "top",
                    "bg_color": "#efefef",
                    "bottom": 1,
                }
            ),
        },
    }

    META_CONFIG.append(f"HeaderRows {len(header_rows)}"),

    # Add header column cell format
    header_col_format = workbook.add_format(
        {
            "bold": True,
            "font_size": 11,
            "font_color": "black",
            "underline": False,
            "bg_color": "#efefef",
        }
    )

    # Add input cell formats
    input_format = workbook.add_format({})
    string_format = workbook.add_format({"num_format": "@"})
    date_format = workbook.add_format({"num_format": "yyyy-mm-dd"})
    number_format = workbook.add_format({"num_format": "#,##0.00"})

    # Add worksheet for enum validation
    enum_worksheet = workbook.add_worksheet("# Enums")
    enum_column = 0

    # Add meta worksheet for Flatten Tool configuration properties
    meta_worksheet = workbook.add_worksheet("Meta")
    meta_worksheet.hide()
    meta_worksheet.write_row(0, 0, META_CONFIG)
    for i, (key, value) in enumerate(package_metadata.items()):
        meta_worksheet.write_row(i , 0, [key, value])

    # Add variables worksheet for user-specified variables
    if variables and len(variables) > 0:
        variables_worksheet = workbook.add_worksheet("# Variables")
        variables_worksheet.write_row(0, 0, ['Name', 'Value'])
        for i, (key, value) in enumerate(variables.items()):
            variables_worksheet.write_row(i+1, 0, [key, value])
            workbook.define_name(key, f"='# Variables'!$B${i+2}")

    # Get list of CSV files produced by Flatten Tool
    filenames = os.listdir(temp_path)
    csv_files = [
        filename.split(".")[0]
        for filename in filenames
        if filename.split(".")[-1] == "csv"
    ]

    # If sheets are specified in config file, warn on missing sheets and extra sheets
    if len(sheets) > 0:
        for sheet in [sheet for sheet in csv_files if sheet not in sheets]:
            warnings.warn(
                f"Skipping {sheet}. Flatten Tool outputs this sheet, but it is missing from the config file. To include this sheet in the template, update your config file."
                )
        for sheet in [sheet for sheet in sheets if sheet not in csv_files]:
            warnings.warn(f"Ignoring sheet {sheet}. This sheet is specified in the config file but missing from Flatten Tool's output.")
            del sheets[sheet]
    # Otherwise, use sheets from Flatten Tool's output
    else:
        for sheet in csv_files:
            sheets[sheet] = []

    for sheet in sheets:

        # Read column headers
        file_path = os.path.join(temp_path, f"{sheet}.csv")
        with open(file_path, "r") as f:
            reader = csv.reader(f)
            paths = []
            for path in next(reader):
                
                # Add source fields from configuration file
                if source_fields:
                    for p, field in source_fields.items():
                        if path == field['successor']:
                            paths.append(p)
                
                if include_fields:
                    if path in include_fields:
                        paths.append(path)
                elif exclude_fields:
                    if path not in exclude_fields:
                        paths.append(path)
                else:
                    paths.append(path)
            
            sheets[sheet] = paths

        # Add worksheets, skip empty sheets and sheets that only include `id`
        if len(sheets[sheet]) > 0 and sheets[sheet] != ['id']:
            worksheet = workbook.add_worksheet(sheet)
            worksheet.freeze_panes(1, 1)

            # Set row formats
            row = 0
            for row_format in header_rows.values():
                worksheet.set_row(row, row_format["row_height"], row_format["cell_format"])
                row += 1

            # Write header column
            worksheet.write_column(0, 0, [f"# {row_name}" for row_name in header_rows])
            worksheet.set_column(0, 0, 11, header_col_format)
            column = 1

            # Write metadata, formatting, input cells and data validation
            for path in sheets[sheet]:

                # Array indices are omitted from field paths in mapping sheet
                metadata_path = "/".join([part for part in path.split("/") if part != "0"])

                # Write field metadata as header rows
                data_type = field_metadata[metadata_path].get("type")
                values = field_metadata[metadata_path].get("values")
                codelist = field_metadata[metadata_path].get("codelist")

                # Generate codelist hyperlink formula
                if codelist:
                    codelist_name = codelist.split(".")[0]
                    if codelist_docs_url:
                        codelist_formula = f"""=HYPERLINK("{codelist_docs_url}#{codelist_name.replace("_", "-")}","{codelist_name}")"""
                    else:
                        codelist_formula = f'="{codelist_name}"'
                else:
                    codelist_formula = ""

                metadata = {
                    "path": path,
                    "title": field_metadata[metadata_path].get("title"),
                    "description": field_metadata[metadata_path].get("description"),
                    "required": (
                        "Required"
                        if len(field_metadata[metadata_path].get("range", ""))
                        and field_metadata[metadata_path]["range"][0] == "1"
                        else ""
                    ),
                    "type": data_type,
                    "values": values,
                    "codelist": codelist_formula,
                }

                # Add data input guidance
                metadata["input guidance"] = ""
                if path in field_guidance:
                    metadata["input guidance"] += field_guidance[path]
                if data_type == "array":
                    if values[:4] == "Enum":
                        metadata["input guidance"] = (
                            "Select from list or enter multiple values as a semicolon-separated list, e.g. a;b;c. Each value must be a code from the codelist."
                        )
                    else:
                        metadata["input guidance"] = (
                            "Enter multiple values as a semicolon-separated list, e.g. a;b;c. Values must not contain semicolons or commas."
                        )
                elif wkt and path.split("/")[-1] == "geometry":
                    metadata["input guidance"] = (
                        "Enter a well-known text value, e.g. POLYGON ((30 10, 40 40, 20 40, 10 20, 30 10)). For more information on the well-known text representation of geometry, see https://en.wikipedia.org/wiki/Well-known_text_representation_of_geometry."
                    )

                worksheet.write_column(
                    0, column, [metadata[row_name] for row_name in header_rows]
                )

                # Set cell format for input rows
                if sheet == "links":
                    cell_format = workbook.add_format({})
                elif values == "date":
                    cell_format = date_format
                elif data_type == "number":
                    cell_format = number_format
                elif data_type in ["string", "array", "object"]:
                    cell_format = string_format
                else:
                    cell_format = input_format

                # Write input cells, use formulae to populate links sheet
                input_row_ref = len(header_rows) + 1
                if path in fixed_values:
                    for i in range(input_rows):
                            worksheet.write_formula(
                                len(header_rows) + i,
                                column,
                                f'=IF(B{i + input_row_ref}="","","{fixed_values[path]}")',
                                cell_format,
                                "",
                            )                     
                elif path in formulae:
                     for i in range(input_rows):
                            worksheet.write_formula(
                                len(header_rows) + i,
                                column,
                                formulae[path].replace("{row}", str(i + input_row_ref)),                      
                                cell_format,
                                "",
                            )                     
                elif sheet == "links":
                    for i in range(input_rows):
                        if path == "id":
                            worksheet.write_formula(
                                len(header_rows) + i,
                                column,
                                f'=IF(ISBLANK({main_sheet_name}!B{i + input_row_ref}),"",{main_sheet_name}!B{i + input_row_ref})',
                                cell_format,
                                "",
                            )
                        elif path == "links/0/href":
                            worksheet.write_formula(
                                len(header_rows) + i,
                                column,
                                f'=IF(B{i + input_row_ref}="","","{schema_url}")',
                                cell_format,
                                "",
                            )
                        elif path == "links/0/rel":
                            worksheet.write_formula(
                                len(header_rows) + i,
                                column,
                                f'=IF(B{i + input_row_ref}="","","describedby")',
                                cell_format,
                                "",
                            )
                else:
                    worksheet.write_column(
                        len(header_rows),
                        column,
                        ["" for i in range(input_rows)],
                        cell_format,
                    )

                # Set column width
                worksheet.set_column(column, column, max(len(path), 16))

                validation_options = None

                # Set data validation for identifiers
                # for name, paths in sheets.items():
                #     if sheet == name:
                #         break
                #     elif path in paths:
                #         column_ref = xl_col_to_name(paths.index(path) + 1)
                #         validation_options = {
                #             "validate": "list",
                #             "source": f"={name}!${column_ref}${len(header_rows) + 1}:${column_ref}${input_rows}",
                #         }
                #         break

                # Set data validation for codelists
                if codelist and (values[:4] == "Enum" or codelist_base_url):
                    validation_options = {"validate": "list"}

                    if values[:4] == "Enum":
                        codes = values[6:].split(", ")
                        validation_options["error_title"] = "Value not in codelist"
                        if data_type == "array":
                            validation_options["error_type"] = "warning"
                            validation_options["error_message"] = (
                                "You must use a code from the codelist.\n\nIf no code is appropriate, please create an issue in the standard repository. If you entered multiple values from the codelist, you can ignore this warning."
                            )
                        else:
                            validation_options["error_type"] = "stop"
                            validation_options["error_message"] = (
                                "You must use a code from the codelist.\n\nIf no code is appropriate, please create an issue in the standard."
                            )
                    elif codelist_base_url:
                        codelist_csv = get(f"{codelist_base_url}{codelist}")
                        codelist_reader = csv.DictReader(
                            codecs.iterdecode(codelist_csv.iter_lines(), "utf-8")
                        )
                        codes = [row["Code"] for row in codelist_reader]
                        validation_options["error_type"] = "warning"
                        validation_options["error_title"] = "Value not in codelist"
                        if data_type == "array":
                            validation_options["error_message"] = (
                                "You must use a code from the codelist, unless no code is appropriate.\n\nIf you use new codes outside those in an open codelist, please create an issue in the standard repository, so that the codes can be considered for inclusion in the codelist. If you entered multiple values from the codelist, you can ignore this warning."
                            )
                        else:
                            validation_options["error_message"] = (
                                "You must use a code from the codelist, unless no code is appropriate.\n\nIf you use new codes outside those in an open codelist, please create an issue in the standard repository, so that the codes can be considered for inclusion in the codelist."
                            )

                    enum_worksheet.write_column(0, enum_column, [path] + codes)
                    enum_column_ref = xl_col_to_name(enum_column)
                    validation_options["source"] = (
                        f"='# Enums'!${enum_column_ref}$2:${enum_column_ref}${len(codes)+1}"
                    )
                    enum_column += 1

                # Set data validation for dates
                elif values == "date":
                    validation_options = {
                        "validate": "date",
                        "criteria": ">=",
                        "value": datetime.datetime(1, 1, 1),
                    }

                if validation_options:
                    worksheet.data_validation(
                        len(header_rows), column, 1007, column, validation_options
                    )

                column += 1

    # Delete temp files
    delete_directory_contents(".temp")

    # Write template to drive
    workbook.get_worksheet_by_name(main_sheet_name).activate()
    enum_worksheet.hide()
    if workbook.get_worksheet_by_name("links"):
        workbook.get_worksheet_by_name("links").hide()

    workbook.close()


if __name__ == "__main__":
    cli()
