from fastapi import FastAPI, APIRouter
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ.get('MONGO_URL')
if not mongo_url:
    raise RuntimeError(
        "MONGO_URL is not set. Create backend/.env from backend/.env.example "
        "(a free MongoDB Atlas connection string works fine)."
    )
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'bk_decomart')]

# All product/site images live here — see README for how to add or replace them.
STATIC_DIR = ROOT_DIR / "static"
STATIC_DIR.mkdir(exist_ok=True)
(STATIC_DIR / "img" / "generated").mkdir(parents=True, exist_ok=True)

app = FastAPI(title="BK Decomart API")
api_router = APIRouter(prefix="/api")


@api_router.get("/")
async def root():
    return {"service": "BK Decomart", "status": "ok"}


@api_router.get("/health")
async def health():
    return {"status": "ok"}


@api_router.get("/generated-images")
async def list_generated_images():
    """Returns the list of interior image names available under static/img/generated."""
    d = STATIC_DIR / "img" / "generated"
    if not d.exists():
        return {"images": []}
    files = sorted([p.stem for p in d.glob("*.png") if p.stat().st_size > 5000])
    return {"images": files}


app.include_router(api_router)

# Serve images under /api/static so ingress routes to backend
app.mount("/api/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
