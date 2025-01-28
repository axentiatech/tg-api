from fastapi import APIRouter
from pydantic import BaseModel
from openai import OpenAI
from app.api.lib.idp import analyze_layout
from app.api.lib.parseToHtml import get_tables
from fastapi import HTTPException

client = OpenAI()


router = APIRouter()


class Payload(BaseModel):
    pdf_url: str


# student information
class StudentInformation(BaseModel):
    name: str
    board: str
    school: str
    city: str
    country: str


class Table(BaseModel):
    table_content: str
    is_marks_table: bool


# classify tables if there are multiple tables. tables would be html format
class TableClassification(BaseModel):
    tables: list[Table]


class ExtractedTable(BaseModel):
    subject_name: str
    subject_grade: str


class ExtractedOutput(BaseModel):
    data: list[ExtractedTable]


class IsMultipleGradingScale(BaseModel):
    is_multiple_grading_scale: bool


@router.post("/")
async def evaluate(payload: Payload):

    result = analyze_layout(payload.pdf_url)

    content = result["_data"]["content"]

    tables = get_tables(result)

    studentInformation = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[{
            "role": "system",
            "content": "You are an intelligent AI agent that can extract student information from a given text in HTML format."
        }, {
            "role": "user",
            "content": content
        }],
        response_format=StudentInformation
    )

    # convert tables to json format
    json_fmt = [{"table_content": table, "is_marks_table": "true/false"}
                for table in tables]

    response = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[{
            "role": "system",
            "content":
            """
                You are an intelligent AI classifier. Given a JSON list of dictionaries containing tables in markdown format, classify whether the table contains information about a student’s marks in the “is_marks_table” key of the response in boolean
            """
        }, {
            "role": "user",
            "content": f"""
            {json_fmt}
            """
        }],
        response_format=TableClassification

    )

    extracted_tables = []

    # check only if the number of marks table is more than 1 using the the key "is_marks_table"
    if len([table for table in response.choices[0].message.parsed.tables if table.is_marks_table]) > 1:
        raise HTTPException(
            status_code=500, detail="We are not able to process this transcript")

    for table in response.choices[0].message.parsed.tables:
        if table.is_marks_table:

            # check if the table has mulitple grading scales or result of multiple years in the same table
            is_multiple_grading_scale = client.beta.chat.completions.parse(
                model="gpt-4o",
                messages=[{
                    "role": "system",
                    "content": """
                    You are an intelligent AI agent that can check if the table has mulitple grading scales or result of multiple years in the same table
                    For example, if the table has the following content with multiple grading scales of a single country:
                    eg: Having GSCE and IGCSE in the same table , or having result of 2024 and 2025 in the same table , or having 9th , 10th and more grade in the same table.
                    Just return true if the table has multiple grading scales or result of multiple years in the same table.
                    """
                }, {
                    "role": "user",
                    "content": table.table_content
                }],
                response_format=IsMultipleGradingScale
            )

            if is_multiple_grading_scale.choices[0].message.parsed.is_multiple_grading_scale:
                raise HTTPException(
                    status_code=500, detail="We are not able to process this table")

            marks_table = client.beta.chat.completions.parse(
                model="gpt-4o",
                messages=[{
                    "role": "system",
                    "content": """
                    You are an intelligent AI agent that can extract marks of a student from a given table in HTML format. Extract the subject and its final marks or grades in the following JSON dictionary:
                    [{"subject_name": "Name of the subject", "subject_grade": "Grade of the subject" , "subject_marks": "Marks of the subject"}]

                    "subject_grade" can contain values from one of the following values:
                    - numeric grade in float format
                    - alphabet based grade containing alphabet and other character
                    
                    """
                }, {
                    "role": "user",
                    "content": table.table_content
                }],
                response_format=ExtractedOutput
            )

            extracted_tables.extend(
                marks_table.choices[0].message.parsed.data)

    if len(extracted_tables) == 0:
        raise HTTPException(
            status_code=500, detail="We are not able to process this transcript")

    return {"studentInformation": studentInformation.choices[0].message.parsed, "marks": extracted_tables}
