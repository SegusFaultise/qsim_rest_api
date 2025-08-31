# app/main.py

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from .routers import auth, circuits, simulation

app = FastAPI(
    title="Quantum Circuit Simulator API",
    description="An API to create and simulate quantum circuits.",
    version="1.0.0"
)

# --- CORS Middleware ---
"""
<summary>
Configures Cross-Origin Resource Sharing (CORS) for the FastAPI application.
This middleware allows web applications from specified origins (e.g., the React frontend)
to make requests to this API.
</summary>
<param name="allow_origins" type="list">A list of allowed origins. Requests from these URLs are permitted.</param>
<param name="allow_credentials" type="bool">Allows cookies to be included in cross-origin requests.</param>
<param name="allow_methods" type="list">Specifies which HTTP methods are allowed (e.g., ["*"] for all).</param>
<param name="allow_headers" type="list">Specifies which HTTP headers are allowed (e.g., ["*"] for all).</param>
"""
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "https://segusfaultise.github.io"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Routers ---
"""
<summary>
Includes the API routers from different modules into the main FastAPI application.
Each router handles a specific domain of the API (e.g., authentication, circuits).
</summary>
"""
app.include_router(auth.router)
app.include_router(circuits.router, prefix="/api/v1")
app.include_router(simulation.router, prefix="/api/v1")

# --- Static File Serving (for production) ---
# app.mount("/static", StaticFiles(directory="static"), name="static")
# @app.get("/")
# async def read_index():
#     return FileResponse('static/index.html')
