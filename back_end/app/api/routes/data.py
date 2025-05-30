from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from scripts.feature_pipeline import process_pipeline

router = APIRouter()
BASE_DIR      = Path(__file__).parent.parent.parent
UPLOAD_DIR    = BASE_DIR / "uploads";   UPLOAD_DIR.mkdir(exist_ok=True)
PROCESSED_DIR = BASE_DIR / "data";      PROCESSED_DIR.mkdir(exist_ok=True)

@router.post("/upload")
async def upload_files(
    payers_file: UploadFile       = File(...),
    sellers_file: UploadFile      = File(...),
    transactions_file: UploadFile = File(...)
):
    paths = {
        "payers":       UPLOAD_DIR / "payers.feather",
        "sellers":      UPLOAD_DIR / "sellers.feather",
        "transactions": UPLOAD_DIR / "transactions.feather",
    }
    try:
        for key, upload in [("payers", payers_file),
                            ("sellers", sellers_file),
                            ("transactions", transactions_file)]:
            dest = paths[key]
            with open(dest, "wb") as f:
                f.write(await upload.read())
    except Exception as e:
        raise HTTPException(500, f"Erro ao salvar: {e}")
    return {"message": "Arquivos recebidos", "paths": [str(p) for p in paths.values()]}

@router.post("/process")
def process_data():
    p = UPLOAD_DIR
    for name in ["payers.feather", "sellers.feather", "transactions.feather"]:
        if not (p / name).exists():
            raise HTTPException(404, f"Falta arquivo upload: {name}")
    df = process_pipeline(
        p/"payers.feather", p/"sellers.feather", p/"transactions.feather"
    )
    out = PROCESSED_DIR / "processed_data.parquet"
    df.to_parquet(out, index=False)
    return {"message": "Processado", "output": str(out)}

@router.get("/download_processed")
def download_processed():
    out = PROCESSED_DIR / "processed_data.parquet"
    if not out.exists():
        raise HTTPException(404, "Processado não encontrado")
    return FileResponse(out, media_type="application/octet-stream")
