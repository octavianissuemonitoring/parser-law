"""
API Routes for Categories (Domains/Tags for Legislative Acts).
"""
from typing import Dict, Any, List

from fastapi import APIRouter, HTTPException, Query, status, BackgroundTasks
from pydantic import BaseModel

from app.api.deps import DBSession
from app.services.category_service import CategoryService

router = APIRouter(prefix="/categories", tags=["Categories"])

category_service = CategoryService()


class CategoryAssignment(BaseModel):
    """Request body for assigning categories to an act."""
    category_ids: List[int]
    added_by: str = "user"


@router.get("")
async def list_categories(
    db: DBSession,
    active_only: bool = Query(True, description="Return only active categories"),
) -> Dict[str, Any]:
    """
    List all categories from local cache.
    
    Categories are synced from Issue Monitoring periodically.
    Use `/categories/sync` to manually refresh.
    
    **Returns:**
    ```json
    {
        "items": [
            {
                "id": 1,
                "im_category_id": 10,
                "name": "Sănătate Publică",
                "slug": "sanatate-publica",
                "description": "Legislație privind sistemul de sănătate",
                "color": "#4CAF50",
                "icon": "medical-cross",
                "ordine": 0,
                "is_active": true,
                "synced_at": "2025-11-10T22:00:00"
            }
        ],
        "total": 15,
        "synced_at": "2025-11-10T22:00:00"
    }
    ```
    """
    categories = await category_service.get_local_categories(db, active_only)
    
    # Get last sync time
    last_sync = None
    if categories:
        last_sync = max(c.get("synced_at") for c in categories if c.get("synced_at"))
    
    return {
        "items": categories,
        "total": len(categories),
        "synced_at": last_sync
    }


@router.post("/sync")
async def sync_categories(
    db: DBSession,
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    """
    Sync categories from Issue Monitoring API.
    
    This endpoint fetches the latest categories from Issue Monitoring
    and updates the local cache. New categories are created, existing
    ones are updated. Categories are never deleted, only deactivated.
    
    **Authentication:** May require API key (check config)
    
    **Returns:**
    ```json
    {
        "message": "Category sync completed",
        "stats": {
            "total_fetched": 15,
            "created": 2,
            "updated": 13,
            "errors": 0,
            "synced_at": "2025-11-10T22:00:00"
        }
    }
    ```
    """
    try:
        stats = await category_service.sync_categories(db)
        
        return {
            "message": "Category sync completed",
            "stats": stats
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Category sync failed: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during sync: {str(e)}"
        )


@router.get("/acts/{act_id}")
async def get_act_categories(
    act_id: int,
    db: DBSession,
) -> Dict[str, Any]:
    """
    Get all categories assigned to a legislative act.
    
    **Returns:**
    ```json
    {
        "act_id": 1,
        "categories": [
            {
                "id": 1,
                "im_category_id": 10,
                "name": "Sănătate Publică",
                "slug": "sanatate-publica",
                "description": "...",
                "color": "#4CAF50",
                "icon": "medical-cross",
                "added_at": "2025-11-10T20:00:00",
                "added_by": "user"
            }
        ],
        "total": 2
    }
    ```
    """
    categories = await category_service.get_act_categories(db, act_id)
    
    return {
        "act_id": act_id,
        "categories": categories,
        "total": len(categories)
    }


@router.post("/acts/{act_id}")
async def assign_categories_to_act(
    act_id: int,
    assignment: CategoryAssignment,
    db: DBSession,
) -> Dict[str, Any]:
    """
    Assign categories to a legislative act.
    
    This will ADD categories to the act without removing existing ones.
    Use DELETE endpoint to remove specific categories.
    
    **Request Body:**
    ```json
    {
        "category_ids": [1, 2, 5],
        "added_by": "john.doe"
    }
    ```
    
    **Returns:**
    ```json
    {
        "act_id": 1,
        "added": 2,
        "skipped": 1,
        "message": "Categories assigned successfully"
    }
    ```
    """
    if not assignment.category_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No category IDs provided"
        )
    
    try:
        stats = await category_service.add_categories_to_act(
            db, act_id, assignment.category_ids, assignment.added_by
        )
        
        return {
            "act_id": act_id,
            "added": stats["added"],
            "skipped": stats["skipped"],
            "message": "Categories assigned successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assign categories: {str(e)}"
        )


@router.delete("/acts/{act_id}")
async def remove_categories_from_act(
    act_id: int,
    category_ids: List[int] = Query(..., description="Category IDs to remove"),
    db: DBSession,
) -> Dict[str, Any]:
    """
    Remove specific categories from a legislative act.
    
    **Query Parameters:**
    - `category_ids`: One or more category IDs to remove (e.g., `?category_ids=1&category_ids=2`)
    
    **Returns:**
    ```json
    {
        "act_id": 1,
        "removed": 2,
        "message": "Categories removed successfully"
    }
    ```
    """
    if not category_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No category IDs provided"
        )
    
    try:
        removed = await category_service.remove_categories_from_act(
            db, act_id, category_ids
        )
        
        return {
            "act_id": act_id,
            "removed": removed,
            "message": "Categories removed successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove categories: {str(e)}"
        )


@router.put("/acts/{act_id}")
async def replace_act_categories(
    act_id: int,
    assignment: CategoryAssignment,
    db: DBSession,
) -> Dict[str, Any]:
    """
    Replace ALL categories for an act with a new set.
    
    This will:
    1. Remove all existing categories
    2. Add the new ones provided
    
    **Request Body:**
    ```json
    {
        "category_ids": [1, 3, 5],
        "added_by": "john.doe"
    }
    ```
    
    **Returns:**
    ```json
    {
        "act_id": 1,
        "removed": 3,
        "added": 3,
        "message": "Categories replaced successfully"
    }
    ```
    """
    try:
        # Get current categories
        current = await category_service.get_act_categories(db, act_id)
        current_ids = [c["id"] for c in current]
        
        # Remove all current
        removed = 0
        if current_ids:
            removed = await category_service.remove_categories_from_act(
                db, act_id, current_ids
            )
        
        # Add new ones
        added = 0
        if assignment.category_ids:
            stats = await category_service.add_categories_to_act(
                db, act_id, assignment.category_ids, assignment.added_by
            )
            added = stats["added"]
        
        return {
            "act_id": act_id,
            "removed": removed,
            "added": added,
            "message": "Categories replaced successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to replace categories: {str(e)}"
        )
