# app/main.py
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
from app.routers import cves as cves_router
from app.services import fetch_and_store_all_cves  # Import
from app.db_schemas import create_cve_table # Import

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_cve_table() # Create table at the startup
    fetch_and_store_all_cves() # fetch and store all cves
    yield

app = FastAPI(lifespan=lifespan)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configure templates
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def read_root():
    return {"message": "Welcome to the CVE Data API"}


@app.get("/cves/list")
async def cve_list(request: Request):
    # No database interaction here, just render the template
    return templates.TemplateResponse("cve_list.html", {"request": request})


@app.get("/cves/details")
async def cve_details(request: Request, cve_id: str):
    # No database interaction in this route, just render template.  Details fetched by JavaScript.
     return templates.TemplateResponse("cve_details.html", {"request": request, "cve_id": cve_id})


app.include_router(cves_router.router)