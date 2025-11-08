"""Schemas package."""
from app.schemas.act_schema import (
    ActLegislativBase,
    ActLegislativCreate,
    ActLegislativUpdate,
    ActLegislativResponse,
    # ActLegislativWithArticole,  # DISABLED due to circular import
    ActLegislativList,
)
from app.schemas.articol_schema import (
    ArticolBase,
    ArticolCreate,
    ArticolUpdate,
    ArticolLabelsUpdate,
    ArticolResponse,
    # ArticolWithAct,  # DISABLED due to circular import
    ArticolBatchUpdate,
    ArticolList,
    ArticolSearchResult,
)

__all__ = [
    "ActLegislativBase",
    "ActLegislativCreate",
    "ActLegislativUpdate",
    "ActLegislativResponse",
    # "ActLegislativWithArticole",  # DISABLED
    "ActLegislativList",
    "ArticolBase",
    "ArticolCreate",
    "ArticolUpdate",
    "ArticolLabelsUpdate",
    "ArticolResponse",
    # "ArticolWithAct",  # DISABLED
    "ArticolBatchUpdate",
    "ArticolList",
    "ArticolSearchResult",
]
