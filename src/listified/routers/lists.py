"""API router for list management endpoints."""

from datetime import UTC
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import List, get_db
from ..schemas import ListCreate, ListResponse, ListUpdate

router = APIRouter(prefix="/lists", tags=["lists"])


@router.get("", response_model=list[ListResponse])
async def get_lists(db: AsyncSession = Depends(get_db)) -> list[ListResponse]:
    """Get all non-deleted lists.

    Returns:
        List of all lists that have not been soft deleted.
    """
    stmt = select(List).where(List.deleted_at.is_(None))
    result = await db.execute(stmt)
    lists = result.scalars().all()
    return [ListResponse.model_validate(list_obj) for list_obj in lists]


@router.post("", response_model=ListResponse, status_code=status.HTTP_201_CREATED)
async def create_list(list_data: ListCreate, db: AsyncSession = Depends(get_db)) -> ListResponse:
    """Create a new list.

    Args:
        list_data: The list data to create.
        db: Database session.

    Returns:
        The created list with all fields populated.
    """
    from uuid import uuid4

    new_list = List(
        id=uuid4(),
        name=list_data.name,
        description=list_data.description,
    )
    db.add(new_list)
    await db.commit()
    await db.refresh(new_list)
    return ListResponse.model_validate(new_list)


@router.get("/{list_id}", response_model=ListResponse)
async def get_list(list_id: UUID, db: AsyncSession = Depends(get_db)) -> ListResponse:
    """Get a specific list by ID.

    Args:
        list_id: The ID of the list to retrieve.
        db: Database session.

    Returns:
        The requested list.

    Raises:
        HTTPException: If list not found or has been deleted.
    """
    stmt = select(List).where((List.id == list_id) & (List.deleted_at.is_(None)))
    result = await db.execute(stmt)
    list_obj = result.scalar_one_or_none()

    if not list_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="List not found")

    return ListResponse.model_validate(list_obj)


@router.put("/{list_id}", response_model=ListResponse)
async def update_list(
    list_id: UUID, list_data: ListUpdate, db: AsyncSession = Depends(get_db)
) -> ListResponse:
    """Update an existing list.

    Args:
        list_id: The ID of the list to update.
        list_data: The updated list data.
        db: Database session.

    Returns:
        The updated list.

    Raises:
        HTTPException: If list not found or has been deleted.
    """
    from datetime import datetime

    stmt = select(List).where((List.id == list_id) & (List.deleted_at.is_(None)))
    result = await db.execute(stmt)
    list_obj = result.scalar_one_or_none()

    if not list_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="List not found")

    # Update fields only if provided
    if list_data.name is not None:
        list_obj.name = list_data.name
    if list_data.description is not None:
        list_obj.description = list_data.description
    if list_data.completed_at is not None:
        list_obj.completed_at = list_data.completed_at

    list_obj.updated_at = datetime.now(UTC)

    await db.commit()
    await db.refresh(list_obj)
    return ListResponse.model_validate(list_obj)


@router.patch("/{list_id}", response_model=ListResponse)
async def patch_list(
    list_id: UUID, list_data: ListUpdate, db: AsyncSession = Depends(get_db)
) -> ListResponse:
    """Partially update a list (PATCH).

    This endpoint is functionally identical to PUT in this implementation
    as we use optional fields in the update model.

    Args:
        list_id: The ID of the list to update.
        list_data: The fields to update.
        db: Database session.

    Returns:
        The updated list.

    Raises:
        HTTPException: If list not found or has been deleted.
    """
    from datetime import datetime

    stmt = select(List).where((List.id == list_id) & (List.deleted_at.is_(None)))
    result = await db.execute(stmt)
    list_obj = result.scalar_one_or_none()

    if not list_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="List not found")

    # Update fields only if provided
    if list_data.name is not None:
        list_obj.name = list_data.name
    if list_data.description is not None:
        list_obj.description = list_data.description
    if list_data.completed_at is not None:
        list_obj.completed_at = list_data.completed_at

    list_obj.updated_at = datetime.now(UTC)

    await db.commit()
    await db.refresh(list_obj)
    return ListResponse.model_validate(list_obj)


@router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_list(list_id: UUID, db: AsyncSession = Depends(get_db)) -> None:
    """Soft delete a list by ID.

    The list is marked as deleted via the deleted_at timestamp rather than
    being permanently removed from the database.

    Args:
        list_id: The ID of the list to delete.
        db: Database session.

    Raises:
        HTTPException: If list not found or already deleted.
    """
    from datetime import datetime

    stmt = select(List).where((List.id == list_id) & (List.deleted_at.is_(None)))
    result = await db.execute(stmt)
    list_obj = result.scalar_one_or_none()

    if not list_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="List not found")

    list_obj.deleted_at = datetime.now(UTC)
    await db.commit()
