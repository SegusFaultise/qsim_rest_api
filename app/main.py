# app/main.py

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware  # <-- Import this
from .routers import auth, circuits, simulation

app = FastAPI(
    title="Quantum Circuit Simulator API",
    description="An API to create and simulate quantum circuits.",
    version="1.0.0"
)

# --- CORS Middleware ---
origins = [
    "http://localhost:5173",  # React development server
    "http://localhost:3000",  # Another common port for React dev servers
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the API routers
app.include_router(auth.router)
app.include_router(circuits.router, prefix="/api/v1")
app.include_router(simulation.router, prefix="/api/v1")

# (We will re-enable static file serving later for the production build)
# app.mount("/static", StaticFiles(directory="static"), name="static")
# @app.get("/")
# async def read_index():
#     return FileResponse('static/index.html')
