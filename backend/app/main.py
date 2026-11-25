"""
FastAPI Main Application for CMD-Stego+.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .routes import router

app = FastAPI(
    title="CMD-Stego+ API",
    description="Adaptive Clustering of Modification Directions for Secure Spatial Image Steganography",
    version="1.0.0",
)

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api")

# Mount plots directory for direct asset serving
plots_dir = "d:/Stegnography/results/plots"
if os.path.exists(plots_dir):
    app.mount("/plots", StaticFiles(directory=plots_dir), name="plots")


@app.get("/")
def read_root():
    return {
        "project": "CMD-Stego+",
        "status": "Online",
        "description": "Adaptive Clustering of Modification Directions for Secure Spatial Image Steganography",
        "version": "1.0.0",
        "endpoints": ["/api/embed", "/api/extract", "/api/analyze", "/api/experiments", "/api/history"],
    }
