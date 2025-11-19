"""Tests for item endpoints."""

from datetime import UTC, datetime
from uuid import uuid4

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from listified.database import Item, List


class TestGetItems:
    """Tests for GET /lists/{list_id}/items endpoint."""

    async def test_get_items_empty_list(self, client: AsyncClient, test_db: AsyncSession) -> None:
        """Test retrieving items from an empty list."""
        list_id = uuid4()
        test_list = List(id=list_id, name="Empty List")
        test_db.add(test_list)
        await test_db.commit()

        response = await client.get(f"/lists/{list_id}/items")
        assert response.status_code == 200
        assert response.json() == []

    async def test_get_items_with_data(self, client: AsyncClient, test_db: AsyncSession) -> None:
        """Test retrieving multiple items from a list."""
        list_id = uuid4()
        test_list = List(id=list_id, name="Test List")
        test_db.add(test_list)
        await test_db.commit()

        item1 = Item(id=uuid4(), list_id=list_id, name="Item 1", order=0)
        item2 = Item(id=uuid4(), list_id=list_id, name="Item 2", order=1)
        test_db.add(item1)
        test_db.add(item2)
        await test_db.commit()

        response = await client.get(f"/lists/{list_id}/items")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "Item 1"
        assert data[1]["name"] == "Item 2"

    async def test_get_items_ordered_by_order_column(
        self, client: AsyncClient, test_db: AsyncSession
    ) -> None:
        """Test that items are returned in order."""
        list_id = uuid4()
        test_list = List(id=list_id, name="Test List")
        test_db.add(test_list)
        await test_db.commit()

        # Add items in non-sequential order
        item1 = Item(id=uuid4(), list_id=list_id, name="Item 3", order=2)
        item2 = Item(id=uuid4(), list_id=list_id, name="Item 1", order=0)
        item3 = Item(id=uuid4(), list_id=list_id, name="Item 2", order=1)
        test_db.add(item1)
        test_db.add(item2)
        test_db.add(item3)
        await test_db.commit()

        response = await client.get(f"/lists/{list_id}/items")
        assert response.status_code == 200
        data = response.json()
        assert data[0]["name"] == "Item 1"
        assert data[1]["name"] == "Item 2"
        assert data[2]["name"] == "Item 3"

    async def test_get_items_excludes_deleted(
        self, client: AsyncClient, test_db: AsyncSession
    ) -> None:
        """Test that deleted items are not returned."""
        list_id = uuid4()
        test_list = List(id=list_id, name="Test List")
        test_db.add(test_list)
        await test_db.commit()

        item1 = Item(id=uuid4(), list_id=list_id, name="Active Item", order=0)
        item2 = Item(
            id=uuid4(),
            list_id=list_id,
            name="Deleted Item",
            order=1,
            deleted_at=datetime.now(UTC),
        )
        test_db.add(item1)
        test_db.add(item2)
        await test_db.commit()

        response = await client.get(f"/lists/{list_id}/items")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Active Item"

    async def test_get_items_list_not_found(self, client: AsyncClient) -> None:
        """Test retrieving items from non-existent list."""
        fake_id = uuid4()
        response = await client.get(f"/lists/{fake_id}/items")
        assert response.status_code == 404


class TestCreateItem:
    """Tests for POST /lists/{list_id}/items endpoint."""

    async def test_create_item_minimal(self, client: AsyncClient, test_db: AsyncSession) -> None:
        """Test creating an item with minimal data."""
        list_id = uuid4()
        test_list = List(id=list_id, name="Test List")
        test_db.add(test_list)
        await test_db.commit()

        payload = {"name": "My Item", "order": 0}
        response = await client.post(f"/lists/{list_id}/items", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "My Item"
        assert data["order"] == 0
        assert data["list_id"] == str(list_id)
        assert "id" in data

    async def test_create_item_with_description(
        self, client: AsyncClient, test_db: AsyncSession
    ) -> None:
        """Test creating an item with description."""
        list_id = uuid4()
        test_list = List(id=list_id, name="Test List")
        test_db.add(test_list)
        await test_db.commit()

        payload = {"name": "My Item", "order": 0, "description": "Item description"}
        response = await client.post(f"/lists/{list_id}/items", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["description"] == "Item description"

    async def test_create_item_missing_name(
        self, client: AsyncClient, test_db: AsyncSession
    ) -> None:
        """Test creating an item without name fails."""
        list_id = uuid4()
        test_list = List(id=list_id, name="Test List")
        test_db.add(test_list)
        await test_db.commit()

        payload = {"order": 0}
        response = await client.post(f"/lists/{list_id}/items", json=payload)
        assert response.status_code == 422

    async def test_create_item_missing_order(
        self, client: AsyncClient, test_db: AsyncSession
    ) -> None:
        """Test creating an item without order fails."""
        list_id = uuid4()
        test_list = List(id=list_id, name="Test List")
        test_db.add(test_list)
        await test_db.commit()

        payload = {"name": "My Item"}
        response = await client.post(f"/lists/{list_id}/items", json=payload)
        assert response.status_code == 422

    async def test_create_item_list_not_found(self, client: AsyncClient) -> None:
        """Test creating an item in non-existent list."""
        fake_id = uuid4()
        payload = {"name": "My Item", "order": 0}
        response = await client.post(f"/lists/{fake_id}/items", json=payload)
        assert response.status_code == 404

    async def test_create_item_negative_order(
        self, client: AsyncClient, test_db: AsyncSession
    ) -> None:
        """Test creating an item with negative order fails."""
        list_id = uuid4()
        test_list = List(id=list_id, name="Test List")
        test_db.add(test_list)
        await test_db.commit()

        payload = {"name": "My Item", "order": -1}
        response = await client.post(f"/lists/{list_id}/items", json=payload)
        assert response.status_code == 422


class TestGetItem:
    """Tests for GET /lists/{list_id}/items/{item_id} endpoint."""

    async def test_get_item_success(self, client: AsyncClient, test_db: AsyncSession) -> None:
        """Test retrieving a specific item."""
        list_id = uuid4()
        item_id = uuid4()
        test_list = List(id=list_id, name="Test List")
        test_item = Item(id=item_id, list_id=list_id, name="Test Item", order=0)
        test_db.add(test_list)
        test_db.add(test_item)
        await test_db.commit()

        response = await client.get(f"/lists/{list_id}/items/{item_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(item_id)
        assert data["name"] == "Test Item"

    async def test_get_item_not_found(self, client: AsyncClient, test_db: AsyncSession) -> None:
        """Test retrieving a non-existent item."""
        list_id = uuid4()
        fake_item_id = uuid4()
        test_list = List(id=list_id, name="Test List")
        test_db.add(test_list)
        await test_db.commit()

        response = await client.get(f"/lists/{list_id}/items/{fake_item_id}")
        assert response.status_code == 404

    async def test_get_item_wrong_list(self, client: AsyncClient, test_db: AsyncSession) -> None:
        """Test retrieving an item from wrong list."""
        list_id1 = uuid4()
        list_id2 = uuid4()
        item_id = uuid4()

        list1 = List(id=list_id1, name="List 1")
        list2 = List(id=list_id2, name="List 2")
        test_item = Item(id=item_id, list_id=list_id1, name="Item", order=0)

        test_db.add(list1)
        test_db.add(list2)
        test_db.add(test_item)
        await test_db.commit()

        response = await client.get(f"/lists/{list_id2}/items/{item_id}")
        assert response.status_code == 404

    async def test_get_deleted_item(self, client: AsyncClient, test_db: AsyncSession) -> None:
        """Test that deleted items cannot be retrieved."""
        list_id = uuid4()
        item_id = uuid4()
        test_list = List(id=list_id, name="Test List")
        test_item = Item(
            id=item_id,
            list_id=list_id,
            name="Deleted Item",
            order=0,
            deleted_at=datetime.now(UTC),
        )
        test_db.add(test_list)
        test_db.add(test_item)
        await test_db.commit()

        response = await client.get(f"/lists/{list_id}/items/{item_id}")
        assert response.status_code == 404


class TestUpdateItem:
    """Tests for PUT /lists/{list_id}/items/{item_id} endpoint."""

    async def test_update_item_name(self, client: AsyncClient, test_db: AsyncSession) -> None:
        """Test updating an item name."""
        list_id = uuid4()
        item_id = uuid4()
        test_list = List(id=list_id, name="Test List")
        test_item = Item(id=item_id, list_id=list_id, name="Original Name", order=0)
        test_db.add(test_list)
        test_db.add(test_item)
        await test_db.commit()

        payload = {"name": "New Name"}
        response = await client.put(f"/lists/{list_id}/items/{item_id}", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"

    async def test_update_item_order(self, client: AsyncClient, test_db: AsyncSession) -> None:
        """Test updating an item order."""
        list_id = uuid4()
        item_id = uuid4()
        test_list = List(id=list_id, name="Test List")
        test_item = Item(id=item_id, list_id=list_id, name="Item", order=0)
        test_db.add(test_list)
        test_db.add(test_item)
        await test_db.commit()

        payload = {"order": 5}
        response = await client.put(f"/lists/{list_id}/items/{item_id}", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["order"] == 5

    async def test_update_item_not_found(self, client: AsyncClient, test_db: AsyncSession) -> None:
        """Test updating a non-existent item."""
        list_id = uuid4()
        fake_item_id = uuid4()
        test_list = List(id=list_id, name="Test List")
        test_db.add(test_list)
        await test_db.commit()

        payload = {"name": "New Name"}
        response = await client.put(f"/lists/{list_id}/items/{fake_item_id}", json=payload)
        assert response.status_code == 404

    async def test_update_item_mark_completed(
        self, client: AsyncClient, test_db: AsyncSession
    ) -> None:
        """Test marking an item as completed."""
        list_id = uuid4()
        item_id = uuid4()
        test_list = List(id=list_id, name="Test List")
        test_item = Item(id=item_id, list_id=list_id, name="Item", order=0)
        test_db.add(test_list)
        test_db.add(test_item)
        await test_db.commit()

        now = datetime.now(UTC)
        payload = {"completed_at": now.isoformat()}
        response = await client.put(f"/lists/{list_id}/items/{item_id}", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["completed_at"] is not None


class TestPatchItem:
    """Tests for PATCH /lists/{list_id}/items/{item_id} endpoint."""

    async def test_patch_item_name_only(self, client: AsyncClient, test_db: AsyncSession) -> None:
        """Test patching only the name."""
        list_id = uuid4()
        item_id = uuid4()
        test_list = List(id=list_id, name="Test List")
        test_item = Item(
            id=item_id,
            list_id=list_id,
            name="Original",
            description="Original desc",
            order=0,
        )
        test_db.add(test_list)
        test_db.add(test_item)
        await test_db.commit()

        payload = {"name": "Updated"}
        response = await client.patch(f"/lists/{list_id}/items/{item_id}", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated"
        assert data["description"] == "Original desc"
        assert data["order"] == 0

    async def test_patch_item_empty_payload(
        self, client: AsyncClient, test_db: AsyncSession
    ) -> None:
        """Test patching with empty payload."""
        list_id = uuid4()
        item_id = uuid4()
        original_name = "Original Name"
        test_list = List(id=list_id, name="Test List")
        test_item = Item(id=item_id, list_id=list_id, name=original_name, order=0)
        test_db.add(test_list)
        test_db.add(test_item)
        await test_db.commit()

        response = await client.patch(f"/lists/{list_id}/items/{item_id}", json={})
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == original_name


class TestDeleteItem:
    """Tests for DELETE /lists/{list_id}/items/{item_id} endpoint."""

    async def test_delete_item_success(self, client: AsyncClient, test_db: AsyncSession) -> None:
        """Test soft deleting an item."""
        list_id = uuid4()
        item_id = uuid4()
        test_list = List(id=list_id, name="Test List")
        test_item = Item(id=item_id, list_id=list_id, name="Test Item", order=0)
        test_db.add(test_list)
        test_db.add(test_item)
        await test_db.commit()

        response = await client.delete(f"/lists/{list_id}/items/{item_id}")
        assert response.status_code == 204

        # Verify item is marked as deleted
        await test_db.refresh(test_item)
        assert test_item.deleted_at is not None

    async def test_delete_item_not_found(self, client: AsyncClient, test_db: AsyncSession) -> None:
        """Test deleting a non-existent item."""
        list_id = uuid4()
        fake_item_id = uuid4()
        test_list = List(id=list_id, name="Test List")
        test_db.add(test_list)
        await test_db.commit()

        response = await client.delete(f"/lists/{list_id}/items/{fake_item_id}")
        assert response.status_code == 404

    async def test_get_deleted_item_returns_404(
        self, client: AsyncClient, test_db: AsyncSession
    ) -> None:
        """Test that deleted item is no longer retrievable."""
        list_id = uuid4()
        item_id = uuid4()
        test_list = List(id=list_id, name="Test List")
        test_item = Item(id=item_id, list_id=list_id, name="Test Item", order=0)
        test_db.add(test_list)
        test_db.add(test_item)
        await test_db.commit()

        # Delete the item
        await client.delete(f"/lists/{list_id}/items/{item_id}")

        # Try to retrieve it
        response = await client.get(f"/lists/{list_id}/items/{item_id}")
        assert response.status_code == 404
