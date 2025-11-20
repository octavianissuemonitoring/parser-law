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
    ArticolWithIssues,
    ArticolWithFullContext,
)
from app.schemas.domeniu_schema import (
    DomeniuBase,
    DomeniuCreate,
    DomeniuUpdate,
    DomeniuResponse,
    DomeniuMinimal,
    DomeniuList,
    ActDomeniuAssign,
    ArticolDomeniuAssign,
    DomeniuWithSource,
)
from app.schemas.issue_schema import (
    IssueBase,
    IssueCreate,
    IssueUpdate,
    IssueResponse,
    IssueMinimal,
    IssueLinkCreate,
    IssueLinkResponse,
    IssueUnlink,
    StructureIssueLinkCreate,
    StructureIssueLinkResponse,
    StructureIssueUnlink,
    IssueWithContext,
    IssuesByDomain,
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
    "ArticolWithIssues",
    "ArticolWithFullContext",
    # Domenii schemas
    "DomeniuBase",
    "DomeniuCreate",
    "DomeniuUpdate",
    "DomeniuResponse",
    "DomeniuMinimal",
    "DomeniuList",
    "ActDomeniuAssign",
    "ArticolDomeniuAssign",
    "DomeniuWithSource",
    # Issues schemas
    "IssueBase",
    "IssueCreate",
    "IssueUpdate",
    "IssueResponse",
    "IssueMinimal",
    "IssueLinkCreate",
    "IssueLinkResponse",
    "IssueUnlink",
    "StructureIssueLinkCreate",
    "StructureIssueLinkResponse",
    "StructureIssueUnlink",
    "IssueWithContext",
    "IssuesByDomain",
]
