from fastapi import FastAPI
from app.api.routes.health import router as health_router
from app.api.routes.assess import router as assess_router
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

app = FastAPI(
    title="Radiology Protocol & Risk Decision Support System",
    version="0.1.0"
)


@app.get("/")
def root():
    return {
        "message": "Radiology Protocol & Risk Decision Support System API is running"
    }


app.include_router(health_router)
app.include_router(assess_router)