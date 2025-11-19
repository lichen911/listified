"""Pydantic models for API request and response payloads."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ListBase(BaseModel):
    """Base model for list data."""

    name: str = Field(..., min_length=1, description="Name of the list")
    description: str | None = Field(None, description="Optional description of the list")


class ListCreate(ListBase):
    """Model for creating a new list."""

    pass


class ListUpdate(BaseModel):
    """Model for updating an existing list."""

    name: str | None = Field(None, min_length=1, description="Updated list name")
    description: str | None = Field(None, description="Updated list description")
    completed_at: datetime | None = Field(None, description="Mark list as completed")


class ListResponse(ListBase):
    """Model for list response payload."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="Unique identifier for the list")
    created_at: datetime = Field(..., description="Timestamp when list was created")
    updated_at: datetime = Field(..., description="Timestamp when list was last updated")
    completed_at: datetime | None = Field(None, description="Timestamp when list was completed")
    deleted_at: datetime | None = Field(None, description="Timestamp when list was soft deleted")


class ItemBase(BaseModel):
    """Base model for item data."""

    name: str = Field(..., min_length=1, description="Name of the item")
    description: str | None = Field(None, description="Optional description of the item")
    order: int = Field(..., ge=0, description="Order of the item in the list")


class ItemCreate(ItemBase):
    """Model for creating a new item."""

    pass


class ItemUpdate(BaseModel):
    """Model for updating an existing item."""

    name: str | None = Field(None, min_length=1, description="Updated item name")
    description: str | None = Field(None, description="Updated item description")
    order: int | None = Field(None, ge=0, description="Updated item order")
    completed_at: datetime | None = Field(None, description="Mark item as completed")


class ItemResponse(ItemBase):
    """Model for item response payload."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="Unique identifier for the item")
    list_id: UUID = Field(..., description="ID of the parent list")
    created_at: datetime = Field(..., description="Timestamp when item was created")
    updated_at: datetime = Field(..., description="Timestamp when item was last updated")
    completed_at: datetime | None = Field(None, description="Timestamp when item was completed")
    deleted_at: datetime | None = Field(None, description="Timestamp when item was soft deleted")
