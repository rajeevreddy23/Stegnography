"""
API Route Handlers for CMD-Stego+.
"""

import os
import io
import time
import uuid
import base64
from datetime import datetime
import cv2
import numpy as np
import pandas as pd
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import Response, JSONResponse

from ..core.cmd_stego import cmd_stego_embed, cmd_stego_extract
from ..core.metrics import compute_all_metrics
from ..core.steganalysis import extract_spam_686, SteganalysisEnsemble
from ..core.srnet import SRNetLite, predict_stego_probability

router = APIRouter()

# In-memory history of recent operations
RUN_HISTORY = []

# Pre-load or initialize SRNet steganalyzer
MODELS_DIR = "d:/Stegnography/results/models"
srnet_weights = os.path.join(MODELS_DIR, "srnet_lite_best.pt")
srnet_model = SRNetLite()
if os.path.exists(srnet_weights):
    try:
        import torch
        srnet_model.load_state_dict(torch.load(srnet_weights, map_location="cpu"))
        srnet_model.eval()
    except Exception as e:
        print(f"Warning: Failed to load pre-trained SRNet weights: {e}")


def ndarray_to_base64_png(img: np.ndarray) -> str:
    """Converts a numpy uint8 grayscale/RGB image to a base64 PNG data URL."""
    success, buffer = cv2.imencode(".png", img)
    if not success:
        raise ValueError("Failed to encode image to PNG.")
    b64_str = base64.b64encode(buffer).decode("utf-8")
    return f"data:image/png;base64,{b64_str}"


def generate_diff_heatmap(cover: np.ndarray, stego: np.ndarray) -> np.ndarray:
    """
    Generates difference heatmap matching IEEE TIFS 2015 paper Fig. 7:
    - Neutral pixels (no change, D=0): Neutral gray (128)
    - Positive modifications (D = +1): Pure white (255)
    - Negative modifications (D = -1): Pure black (0)
    """
    diff = stego.astype(np.int16) - cover.astype(np.int16)
    heatmap = np.full(cover.shape, 128, dtype=np.uint8)
    heatmap[diff == 1] = 255
    heatmap[diff == -1] = 0
    return heatmap


@router.post("/embed")
async def embed_endpoint(
    cover_file: UploadFile = File(...),
    message: Optional[str] = Form(None),
    payload_file: Optional[UploadFile] = File(None),
    password: Optional[str] = Form(None),
    stego_key: Optional[str] = Form(None),
    scheme: str = Form("HILL"),
    L: int = Form(2),
    alpha: float = Form(9.0),
    adaptive_alpha: bool = Form(True),
    neighborhood_8: bool = Form(True),
    key_randomized: bool = Form(True),
):
    try:
        # Read cover image
        cover_bytes = await cover_file.read()
        nparr = np.frombuffer(cover_bytes, np.uint8)
        cover_img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
        if cover_img is None:
            raise HTTPException(status_code=400, detail="Invalid image file format.")

        # Read payload data
        if payload_file is not None:
            payload_data = await payload_file.read()
        elif message is not None:
            payload_data = message.encode("utf-8")
        else:
            raise HTTPException(status_code=400, detail="Either message text or payload_file must be provided.")

        t0 = time.time()
        stego_img, stats = cmd_stego_embed(
            cover=cover_img,
            payload_data=payload_data,
            password=password if password else None,
            stego_key=stego_key if stego_key else None,
            scheme=scheme,
            L=L,
            alpha=alpha,
            adaptive_alpha=adaptive_alpha,
            neighborhood_8=neighborhood_8,
            key_randomized=key_randomized,
        )
        t1 = time.time()
        metrics = compute_all_metrics(cover_img, stego_img, embed_time_sec=t1 - t0)

        # Generate difference heatmap
        diff_heatmap = generate_diff_heatmap(cover_img, stego_img)

        # Base64 encodings
        cover_b64 = ndarray_to_base64_png(cover_img)
        stego_b64 = ndarray_to_base64_png(stego_img)
        heatmap_b64 = ndarray_to_base64_png(diff_heatmap)

        # Live Steganalysis Scoring
        srnet_score = predict_stego_probability(srnet_model, stego_img)

        run_id = str(uuid.uuid4())[:8]
        history_item = {
            'id': run_id,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'action': 'Embed',
            'scheme': f"{scheme}-CMD+" if (adaptive_alpha or neighborhood_8) else f"{scheme}-CMD",
            'bpp': stats['bpp'],
            'change_rate': stats['change_rate'],
            'psnr': metrics['psnr'],
            'details': {**stats, **metrics, 'srnet_score': srnet_score},
        }
        RUN_HISTORY.insert(0, history_item)
        if len(RUN_HISTORY) > 30:
            RUN_HISTORY.pop()

        return {
            'success': True,
            'run_id': run_id,
            'cover_image': cover_b64,
            'stego_image': stego_b64,
            'diff_heatmap': heatmap_b64,
            'stats': stats,
            'metrics': metrics,
            'srnet_score': srnet_score,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract")
async def extract_endpoint(
    stego_file: UploadFile = File(...),
    password: Optional[str] = Form(None),
    stego_key: Optional[str] = Form(None),
    L: int = Form(2),
    key_randomized: bool = Form(True),
):
    try:
        stego_bytes = await stego_file.read()
        nparr = np.frombuffer(stego_bytes, np.uint8)
        stego_img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
        if stego_img is None:
            raise HTTPException(status_code=400, detail="Invalid stego image file.")

        payload_bytes, metadata = cmd_stego_extract(
            stego=stego_img,
            password=password if password else None,
            stego_key=stego_key if stego_key else None,
            L=L,
            key_randomized=key_randomized,
        )

        # Try decoding as UTF-8 string
        is_text = True
        try:
            text_message = payload_bytes.decode("utf-8")
        except UnicodeDecodeError:
            is_text = False
            text_message = f"[Binary data: {len(payload_bytes)} bytes]"

        run_id = str(uuid.uuid4())[:8]
        history_item = {
            'id': run_id,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'action': 'Extract',
            'scheme': 'CMD-Extract',
            'details': {
                'payload_bytes': len(payload_bytes),
                'is_text': is_text,
                'metadata': metadata,
            },
        }
        RUN_HISTORY.insert(0, history_item)

        return {
            'success': True,
            'run_id': run_id,
            'is_text': is_text,
            'message': text_message,
            'payload_length': len(payload_bytes),
            'metadata': metadata,
            'payload_base64': base64.b64encode(payload_bytes).decode("utf-8"),
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Extraction failed: {str(e)}")


@router.post("/analyze")
async def analyze_endpoint(
    cover_file: UploadFile = File(...),
    stego_file: UploadFile = File(...),
):
    try:
        cover_bytes = await cover_file.read()
        stego_bytes = await stego_file.read()

        cov = cv2.imdecode(np.frombuffer(cover_bytes, np.uint8), cv2.IMREAD_GRAYSCALE)
        stg = cv2.imdecode(np.frombuffer(stego_bytes, np.uint8), cv2.IMREAD_GRAYSCALE)

        if cov is None or stg is None:
            raise HTTPException(status_code=400, detail="Invalid image input.")
        if cov.shape != stg.shape:
            raise HTTPException(status_code=400, detail="Cover and Stego dimensions must match.")

        metrics = compute_all_metrics(cov, stg)
        diff_heatmap = generate_diff_heatmap(cov, stg)

        srnet_score = predict_stego_probability(srnet_model, stg)

        # SPAM extraction
        spam_feat = extract_spam_686(stg)
        spam_norm = float(np.linalg.norm(spam_feat))

        return {
            'success': True,
            'cover_image': ndarray_to_base64_png(cov),
            'stego_image': ndarray_to_base64_png(stg),
            'diff_heatmap': ndarray_to_base64_png(diff_heatmap),
            'metrics': metrics,
            'srnet_score': srnet_score,
            'spam_norm': round(spam_norm, 4),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/experiments")
async def experiments_endpoint():
    """
    Returns CSV benchmark data for interactive charts.
    """
    csv_dir = "d:/Stegnography/results/csv"
    try:
        payload_df = pd.read_csv(os.path.join(csv_dir, "payload_sweep.csv")).to_dict(orient="records")
        alpha_df = pd.read_csv(os.path.join(csv_dir, "alpha_sweep.csv")).to_dict(orient="records")
        lattice_df = pd.read_csv(os.path.join(csv_dir, "lattice_sweep.csv")).to_dict(orient="records")
        ablation_df = pd.read_csv(os.path.join(csv_dir, "ablation_study.csv")).to_dict(orient="records")

        return {
            'payload_sweep': payload_df,
            'alpha_sweep': alpha_df,
            'lattice_sweep': lattice_df,
            'ablation_study': ablation_df,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load experiment CSVs: {str(e)}")


@router.get("/history")
async def history_endpoint():
    return {'history': RUN_HISTORY}
