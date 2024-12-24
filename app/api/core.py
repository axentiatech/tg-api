from fastapi import APIRouter, HTTPException, Path
import os
import json
import base64
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
from azure.ai.documentintelligence.models import ContentFormat
import pathlib
from dotenv import load_dotenv


def create_html_table(json_data):
    """
    Convert JSON table data to HTML table format

    Args:
        json_data (dict): JSON data containing table information

    Returns:
        str: HTML table string
    """
    # Extract table cells
    # make getting this table dynamic
    table_data = json_data["_data"]["tables"][0]["_data"]
    cells = table_data["cells"]
    row_count = table_data["rowCount"]
    col_count = table_data["columnCount"]

    # Create 2D array to store cell data
    table_array = [['' for _ in range(col_count)] for _ in range(row_count)]

    # Fill the array with cell content
    for cell in cells:
        cell_data = cell["_data"]
        row = cell_data["rowIndex"]
        col = cell_data["columnIndex"]
        content = cell_data.get("content", "")

        # Handle rowSpan and columnSpan
        row_span = cell_data.get("rowSpan", 1)
        col_span = cell_data.get("columnSpan", 1)

        table_array[row][col] = {
            "content": content,
            "rowSpan": row_span,
            "colSpan": col_span
        }

    # Generate HTML
    html = ['<table border="1">']

    # Track cells that should be skipped due to rowspan/colspan
    skip_cells = set()

    for i in range(row_count):
        html.append('<tr>')
        for j in range(col_count):
            if (i, j) in skip_cells:
                continue

            cell = table_array[i][j]
            if isinstance(cell, dict):
                # Add spanning cells to skip set
                if cell["rowSpan"] > 1 or cell["colSpan"] > 1:
                    for r in range(i, i + cell["rowSpan"]):
                        for c in range(j, j + cell["colSpan"]):
                            if (r, c) != (i, j):
                                skip_cells.add((r, c))

                # Add cell with appropriate attributes
                attrs = []
                if cell["rowSpan"] > 1:
                    attrs.append(f'rowspan="{cell["rowSpan"]}"')
                if cell["colSpan"] > 1:
                    attrs.append(f'colspan="{cell["colSpan"]}"')

                # Add header style for first two rows
                tag = "th" if i < 2 else "td"

                html.append(
                    f'<{tag} {" ".join(attrs)}>{cell["content"]}</{tag}>')
            else:
                html.append(f'<td>{cell}</td>')

        html.append('</tr>')

    html.append('</table>')
    return '\n'.join(html)

# Example usage:
# html_table = create_html_table(json_data)
# print(html_table)


router = APIRouter()
load_dotenv()


current_file = pathlib.Path(__file__).parent.parent.parent

# workaround for now
pdf_path = current_file / "app/api/pre-board.pdf"


# set `<your-endpoint>` and `<your-key>` variables with the values from the Azure portal
key = os.getenv("AZURE_KEY")
endpoint = os.getenv("AZURE_ENDPOINT")


def get_words(page, line):
    result = []
    for word in page.words:
        if _in_span(word, line.spans):
            result.append(word)
    return result


def _in_span(word, spans):
    for span in spans:
        if word.span.offset >= span.offset and (
            word.span.offset + word.span.length
        ) <= (span.offset + span.length):
            return True
    return False


def analyze_layout():
    # sample document
    # formUrl = "https://raw.githubusercontent.com/Azure-Samples/cognitive-services-REST-api-samples/master/curl/form-recognizer/sample-layout.pdf"
    # file_bytes = open('/content/Al.Noor_GPAReports (2) (1).pdf', 'rb')

    document_intelligence_client = DocumentIntelligenceClient(
        endpoint=endpoint, credential=AzureKeyCredential(key)
    )

    # TODO: fetch content from a signed url
    poller = document_intelligence_client.begin_analyze_document(
        "prebuilt-layout", analyze_request={'base64Source': base64.b64encode(open(pdf_path, 'rb').read()).decode("utf-8")},
    )

    result: AnalyzeResult = poller.result()

    if result.styles and any([style.is_handwritten for style in result.styles]):
        print("Document contains handwritten content")
    else:
        print("Document does not contain handwritten content")

    for page in result.pages:
        print(f"----Analyzing layout from page #{page.page_number}----")
        print(
            f"Page has width: {page.width} and height: {page.height}, measured with unit: {page.unit}"
        )

        if page.lines:
            for line_idx, line in enumerate(page.lines):
                words = get_words(page, line)
                print(
                    f"...Line # {line_idx} has word count {len(words)} and text '{line.content}' "
                    f"within bounding polygon '{line.polygon}'"
                )

                for word in words:
                    print(
                        f"......Word '{word.content}' has a confidence of {word.confidence}"
                    )

        if page.selection_marks:
            for selection_mark in page.selection_marks:
                print(
                    f"Selection mark is '{selection_mark.state}' within bounding polygon "
                    f"'{selection_mark.polygon}' and has a confidence of {selection_mark.confidence}"
                )

    if result.tables:
        for table_idx, table in enumerate(result.tables):
            print(
                f"Table # {table_idx} has {table.row_count} rows and "
                f"{table.column_count} columns"
            )
            if table.bounding_regions:
                for region in table.bounding_regions:
                    print(
                        f"Table # {table_idx} location on page: {region.page_number} is {region.polygon}"
                    )
            for cell in table.cells:
                print(
                    f"...Cell[{cell.row_index}][{cell.column_index}] has text '{cell.content}'"
                )
                if cell.bounding_regions:
                    for region in cell.bounding_regions:
                        print(
                            f"...content on page {region.page_number} is within bounding polygon '{region.polygon}'"
                        )

    print("----------------------------------------")
    json_data = json.loads(json.dumps(result, default=lambda o: o.__dict__))
    return json_data


@router.post("/")
async def evaluate():

    result = analyze_layout()

    # with open("result.json", "w") as t:
    #     json.dump(result, t)

    html_table = create_html_table(result)

    return {"response": html_table}
