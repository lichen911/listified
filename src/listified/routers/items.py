"""API router for item management endpoints."""

from datetime import UTC
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import Item, List, get_db
from ..schemas import ItemCreate, ItemResponse, ItemUpdate

router = APIRouter(prefix="/lists/{list_id}/items", tags=["items"])


@router.get("", response_model=list[ItemResponse])
async def get_items(list_id: UUID, db: AsyncSession = Depends(get_db)) -> list[ItemResponse]:
    """Get all non-deleted items in a list.

    Args:
        list_id: The ID of the parent list.
        db: Database session.

    Returns:
        List of all non-deleted items in the specified list.

    Raises:
        HTTPException: If parent list not found.
    """
    # Verify list exists and is not deleted
    list_stmt = select(List).where((List.id == list_id) & (List.deleted_at.is_(None)))
    list_result = await db.execute(list_stmt)
    if not list_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="List not found")

    # Get all non-deleted items in the list, ordered by order column
    stmt = (
        select(Item)
        .where((Item.list_id == list_id) & (Item.deleted_at.is_(None)))
        .order_by(Item.order)
    )
    result = await db.execute(stmt)
    items = result.scalars().all()
    return [ItemResponse.model_validate(item) for item in items]


@router.post("", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(
    list_id: UUID, item_data: ItemCreate, db: AsyncSession = Depends(get_db)
) -> ItemResponse:
    """Create a new item in a list.

    Args:
        list_id: The ID of the parent list.
        item_data: The item data to create.
        db: Database session.

    Returns:
        The created item with all fields populated.

    Raises:
        HTTPException: If parent list not found.
    """
    from uuid import uuid4

    # Verify list exists and is not deleted
    list_stmt = select(List).where((List.id == list_id) & (List.deleted_at.is_(None)))
    list_result = await db.execute(list_stmt)
    if not list_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="List not found")

    new_item = Item(
        id=uuid4(),
        list_id=list_id,
        name=item_data.name,
        description=item_data.description,
        order=item_data.order,
    )
    db.add(new_item)
    await db.commit()
    await db.refresh(new_item)
    return ItemResponse.model_validate(new_item)


@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(
    list_id: UUID, item_id: UUID, db: AsyncSession = Depends(get_db)
) -> ItemResponse:
    """Get a specific item by ID.

    Args:
        list_id: The ID of the parent list.
        item_id: The ID of the item to retrieve.
        db: Database session.

    Returns:
        The requested item.

    Raises:
        HTTPException: If parent list or item not found, or item belongs to different list.
    """
    # Verify list exists and is not deleted
    list_stmt = select(List).where((List.id == list_id) & (List.deleted_at.is_(None)))
    list_result = await db.execute(list_stmt)
    if not list_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="List not found")

    stmt = select(Item).where(
        (Item.id == item_id) & (Item.list_id == list_id) & (Item.deleted_at.is_(None))
    )
    result = await db.execute(stmt)
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    return ItemResponse.model_validate(item)


@router.put("/{item_id}", response_model=ItemResponse)
async def update_item(
    list_id: UUID, item_id: UUID, item_data: ItemUpdate, db: AsyncSession = Depends(get_db)
) -> ItemResponse:
    """Update an existing item.

    Args:
        list_id: The ID of the parent list.
        item_id: The ID of the item to update.
        item_data: The updated item data.
        db: Database session.

    Returns:
        The updated item.

    Raises:
        HTTPException: If parent list or item not found, or item belongs to different list.
    """
    from datetime import datetime

    # Verify list exists and is not deleted
    list_stmt = select(List).where((List.id == list_id) & (List.deleted_at.is_(None)))
    list_result = await db.execute(list_stmt)
    if not list_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="List not found")

    stmt = select(Item).where(
        (Item.id == item_id) & (Item.list_id == list_id) & (Item.deleted_at.is_(None))
    )
    result = await db.execute(stmt)
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    # Update fields only if provided
    if item_data.name is not None:
        item.name = item_data.name
    if item_data.description is not None:
        item.description = item_data.description
    if item_data.order is not None:
        item.order = item_data.order
    if item_data.completed_at is not None:
        item.completed_at = item_data.completed_at

    item.updated_at = datetime.now(UTC)

    await db.commit()
    await db.refresh(item)
    return ItemResponse.model_validate(item)


@router.patch("/{item_id}", response_model=ItemResponse)
async def patch_item(
    list_id: UUID, item_id: UUID, item_data: ItemUpdate, db: AsyncSession = Depends(get_db)
) -> ItemResponse:
    """Partially update an item (PATCH).

    This endpoint is functionally identical to PUT in this implementation
    as we use optional fields in the update model.

    Args:
        list_id: The ID of the parent list.
        item_id: The ID of the item to update.
        item_data: The fields to update.
        db: Database session.

    Returns:
        The updated item.

    Raises:
        HTTPException: If parent list or item not found, or item belongs to different list.
    """
    from datetime import datetime

    # Verify list exists and is not deleted
    list_stmt = select(List).where((List.id == list_id) & (List.deleted_at.is_(None)))
    list_result = await db.execute(list_stmt)
    if not list_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="List not found")

    stmt = select(Item).where(
        (Item.id == item_id) & (Item.list_id == list_id) & (Item.deleted_at.is_(None))
    )
    result = await db.execute(stmt)
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    # Update fields only if explicitly provided in the request
    if "name" in item_data.model_fields_set and item_data.name is not None:
        item.name = item_data.name
    if "description" in item_data.model_fields_set and item_data.description is not None:
        item.description = item_data.description
    if "order" in item_data.model_fields_set and item_data.order is not None:
        item.order = item_data.order
    if "completed_at" in item_data.model_fields_set:
        # Allow setting completed_at to null to mark as incomplete
        item.completed_at = item_data.completed_at

    item.updated_at = datetime.now(UTC)

    await db.commit()
    await db.refresh(item)
    return ItemResponse.model_validate(item)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(list_id: UUID, item_id: UUID, db: AsyncSession = Depends(get_db)) -> None:
    """Soft delete an item by ID.

    The item is marked as deleted via the deleted_at timestamp rather than
    being permanently removed from the database.

    Args:
        list_id: The ID of the parent list.
        item_id: The ID of the item to delete.
        db: Database session.

    Raises:
        HTTPException: If parent list or item not found, or item belongs to different list.
    """
    from datetime import datetime

    # Verify list exists and is not deleted
    list_stmt = select(List).where((List.id == list_id) & (List.deleted_at.is_(None)))
    list_result = await db.execute(list_stmt)
    if not list_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="List not found")

    stmt = select(Item).where(
        (Item.id == item_id) & (Item.list_id == list_id) & (Item.deleted_at.is_(None))
    )
    result = await db.execute(stmt)
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    item.deleted_at = datetime.now(UTC)
    await db.commit()
