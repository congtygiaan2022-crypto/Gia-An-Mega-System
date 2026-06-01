import pandas as pd
from tools.tool_registry import tool

@tool(description="Save data to an Excel file. Arguments: data (list)")
def save_excel(data):

    df = pd.DataFrame({"result": data})

    file = "results.xlsx"

    df.to_excel(file)

    return f"Saved to {file}"
