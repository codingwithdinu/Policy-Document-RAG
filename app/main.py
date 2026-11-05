from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.routes import query, uploads
ROOT_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = ROOT_DIR / "frontend"
app = FastAPI(title="Policy Document AI",description="Evidence-grounded questions about insurance policy documents.",version="2.0.0")
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=False,allow_methods=["GET","POST"],allow_headers=["*"])
app.include_router(query.router,tags=["Questions"])
app.include_router(uploads.router,tags=["Documents"])
app.mount("/static",StaticFiles(directory=str(FRONTEND_DIR)),name="static")
@app.get("/health",tags=["System"])
def health(): return {"status":"ok","service":"policy-document-ai"}
@app.get("/")
async def home(): return FileResponse(FRONTEND_DIR/"index.html")
@app.get("/about")
async def about(): return FileResponse(FRONTEND_DIR/"about.html")
@app.get("/services")
async def services(): return FileResponse(FRONTEND_DIR/"services.html")
@app.get("/contact")
async def contact(): return FileResponse(FRONTEND_DIR/"contact.html")
