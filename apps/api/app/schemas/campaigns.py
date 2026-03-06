from pydantic import BaseModel, Field
from typing import Optional, List


class CreateCampaignRequest(BaseModel):
    workspace_id: int = 1
    objective: str = Field(default="lead-gen")
    source_type: str = Field(default="notes")
    source_input: str


class AssetOut(BaseModel):
    id: int
    asset_type: str
    channel: str
    content: str
    score: float
    status: str


class CampaignOut(BaseModel):
    id: int
    workspace_id: int
    objective: str
    source_type: str
    source_input: str
    status: str
    assets: List[AssetOut] = []


class AssetActionRequest(BaseModel):
    note: Optional[str] = ""
