"""
Title verification system - FastAPI app.
Uses xlsx input (replacing previous HTML). Configured for Render via PORT.
"""
import os
from io import BytesIO
from typing import Any

import pandas as pd
from fastapi import FastAPI, File, UploadFile, HTTPException

app = FastAPI(title="Title Verification System")

# Render sets PORT; fallback for local dev
PORT = int(os.environ.get("PORT", "8000"))


def load_xlsx(content: bytes) -> pd.DataFrame:
    """Load first sheet of an xlsx file into a DataFrame."""
    return pd.read_excel(BytesIO(content), engine="openpyxl")


@app.get("/")
async def root() -> dict[str, str]:
    return {"service": "title-verification-system", "status": "ok"}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.post("/verify")
async def verify_titles(file: UploadFile = File(...)) -> dict[str, Any]:
    """Upload an xlsx file; parse and return titles (and optional verification)."""
    if not file.filename or not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(400, "Expected an .xlsx or .xls file")
    try:
        content = await file.read()
        df = load_xlsx(content)
    except Exception as e:
        raise HTTPException(400, f"Invalid xlsx: {e!s}") from e

    # Assume first column or column named 'title' / 'Title' holds titles
    title_col = None
    for c in ["title", "Title", "TITLE"]:
        if c in df.columns:
            title_col = c
            break
    if title_col is None and len(df.columns) > 0:
        title_col = df.columns[0]

    titles = df[title_col].dropna().astype(str).tolist() if title_col else []

    return {
        "filename": file.filename,
        "row_count": len(df),
        "titles": titles,
        "columns": list(df.columns),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
