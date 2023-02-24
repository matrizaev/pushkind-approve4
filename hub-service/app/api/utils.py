import json
import re
from typing import BinaryIO

import pandas as pd

MANDATORY_COLUMNS = [
    "name",
    "sku",
    "price",
    "measurement",
    "category",
    "description",
    "input_required",
]


def product_columns_to_json(row: pd.Series) -> str:
    def parse_column(value: str) -> "list[str]":
        return (
            sorted(list({s.strip() for s in str(value).split(",")})) if value else None
        )

    result = {k: parse_column(v) for k, v in row.items() if v}
    return json.dumps(result, ensure_ascii=False) if result else ""


def clean_column_names(name: str) -> str:
    return re.sub(r"[^\w]+", "_", name.lower())


def products_excel_to_df(
    excel_data: BinaryIO, vendor_id: int, categories: "dict[str:int]"
) -> pd.DataFrame:
    df = pd.read_excel(excel_data, engine="openpyxl", dtype=str, keep_default_na=False)
    df.columns = [clean_column_names(name) for name in df.columns]
    mandatory_columns_set = set(MANDATORY_COLUMNS)
    if not mandatory_columns_set.issubset(df.columns):
        missing_columns = mandatory_columns_set - df.columns
        raise KeyError(
            f"The following mandatory columns are missing: {missing_columns}"
        )
    extra_columns = list(df.columns.difference(MANDATORY_COLUMNS))
    if "options" in extra_columns:
        extra_columns.remove("options")
    df["options"] = df[extra_columns].apply(product_columns_to_json, axis=1)
    df.drop(
        extra_columns,
        axis=1,
        inplace=True,
    )
    df = df.astype(
        dtype={
            "name": str,
            "sku": str,
            "price": float,
            "measurement": str,
            "description": str,
            "category": str,
            "options": str,
            "input_required": bool,
        }
    )
    df["options"] = df["options"].replace("", None)

    df["vendor_id"] = vendor_id
    df["cat_id"] = df["category"].apply(lambda x: categories.get(x.lower()))
    df.drop(["category"], axis=1, inplace=True)
    df.dropna(subset=["cat_id", "name", "sku", "price", "measurement"], inplace=True)

    df['image'] = df["sku"].apply(lambda x: f'/static/upload/vendor{vendor_id}/{x}')

    string_columns = ["name", "sku", "measurement", "description"]
    for column in string_columns:
        df[column] = (
            df[column].str.slice(0, 128)
            if column == "name"
            else df[column].str.slice(0, 512)
        )
    return df
