from bs4 import BeautifulSoup


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
    table_data = json_data
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


def get_table_headers(tables_array):
    all_headers = []

    for table_html in tables_array:
        # Create BeautifulSoup object for each table
        soup = BeautifulSoup(table_html, 'html.parser')

        # Find all header cells (th elements) in the table
        headers = soup.find_all('th')

        # Extract text from each header cell and add to the list
        table_headers = [header.get_text().strip() for header in headers]
        all_headers.append(table_headers)

    return all_headers


def get_tables(json_data):
    result_tables = json_data["_data"]["tables"]
    tables = []
    for i in range(len(result_tables)):
        tables.append(create_html_table(result_tables[i]["_data"]))
    return tables
