"""
Pydantic Schemas for FastAPI backend.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class EmbedRequestSchema(BaseModel):
    message: str = Field(..., description="Secret text message to embed")
    password: Optional[str] = Field(None, description="Encryption password for AES-256-GCM (Improvement D)")
    stego_key: Optional[str] = Field(None, description="Stego key for lattice/pixel randomization (Improvement B)")
    scheme: str = Field("HILL", description="Baseline scheme (HILL, S-UNIWARD, WOW)")
    L: int = Field(2, ge=2, le=8, description="Lattice parameter (L x L sub-images)")
    alpha: float = Field(9.0, ge=1.0, le=25.0, description="Base clustering parameter alpha")
    adaptive_alpha: bool = Field(True, description="Enable Novel Adaptive-alpha texture complexity (Improvement A)")
    neighborhood_8: bool = Field(True, description="Enable Novel 8-neighborhood weighted voting (Improvement C)")
    key_randomized: bool = Field(True, description="Enable Key-based spatial lattice randomization (Improvement B)")


class ExtractRequestSchema(BaseModel):
    password: Optional[str] = None
    stego_key: Optional[str] = None
    L: int = 2
    key_randomized: bool = True


class MetricResponseSchema(BaseModel):
    psnr: float
    ssim: float
    changes: int
    pos_changes: int
    neg_changes: int
    change_rate: float
    fcc2: float
    fcc3: float
    fcc4: float
    embed_time_ms: float
    spam_score: Optional[float] = None
    srnet_score: Optional[float] = None


class RunHistoryItem(BaseModel):
    id: str
    timestamp: str
    action: str
    scheme: str
    bpp: Optional[float] = None
    change_rate: Optional[float] = None
    psnr: Optional[float] = None
    details: Dict[str, Any]
