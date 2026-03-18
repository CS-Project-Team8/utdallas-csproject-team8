from pydantic import BaseModel
from typing import List, Optional, Union


class StudioOut(BaseModel):
    id: str
    name: str
    brandAccent: str
    initials: str
    logoTextLeft: Optional[str] = None
    logoTextRight: Optional[str] = None


class MetricsOut(BaseModel):
    totalMovies: int
    avgRating: float
    creatorRiskScore: float
    extraLabel: str
    extraValue: Union[str, int, float]


class MovieCardOut(BaseModel):
    id: str
    title: str
    year: Optional[int] = None
    posterUrl: Optional[str] = None
    summary: Optional[str] = None
    sentimentLabel: Optional[str] = None
    engagementLabel: Optional[str] = None


class StudioDashboardOut(BaseModel):
    studio: StudioOut
    metrics: MetricsOut
    recentMovies: List[MovieCardOut]