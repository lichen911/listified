"""Tests for list endpoints."""

from datetime import UTC
from uuid import uuid4

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from listified.database import List


class TestGetLists:
    """Tests for GET /lists endpoint."""

    async def test_get_empty_lists(self, client: AsyncClient) -> None:
        """Test retrieving lists when none exist."""
        response = await client.get("/lists")
        assert response.status_code == 200
        assert response.json() == []

    async def test_get_lists_with_data(self, client: AsyncClient, test_db: AsyncSession) -> None:
        """Test retrieving multiple lists."""
        # Create test lists
        list1 = List(id=uuid4(), name="List 1", description="First list")
        list2 = List(id=uuid4(), name="List 2", description="Second list")
        test_db.add(list1)
        test_db.add(list2)
        await test_db.commit()

        response = await client.get("/lists")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "List 1"
        assert data[1]["name"] == "List 2"

    async def test_get_lists_excludes_deleted(
        self, client: AsyncClient, test_db: AsyncSession
    ) -> None:
        """Test that deleted lists are not returned."""
        from datetime import datetime

        list1 = List(id=uuid4(), name="Active List")
        list2 = List(
            id=uuid4(),
            name="Deleted List",
            deleted_at=datetime.now(UTC),
        )
        test_db.add(list1)
        test_db.add(list2)
        await test_db.commit()

        response = await client.get("/lists")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Active List"


class TestCreateList:
    """Tests for POST /lists endpoint."""

    async def test_create_list_minimal(self, client: AsyncClient) -> None:
        """Test creating a list with minimal data."""
        payload = {"name": "My List"}
        response = await client.post("/lists", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "My List"
        assert data["description"] is None
        assert "id" in data
        assert "created_at" in data

    async def test_create_list_with_description(self, client: AsyncClient) -> None:
        """Test creating a list with description."""
        payload = {"name": "My List", "description": "A test list"}
        response = await client.post("/lists", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "My List"
        assert data["description"] == "A test list"

    async def test_create_list_missing_name(self, client: AsyncClient) -> None:
        """Test creating a list without a name fails."""
        payload = {"description": "No name"}
        response = await client.post("/lists", json=payload)
        assert response.status_code == 422

    async def test_create_list_empty_name(self, client: AsyncClient) -> None:
        """Test creating a list with empty name fails."""
        payload = {"name": ""}
        response = await client.post("/lists", json=payload)
        assert response.status_code == 422


class TestGetList:
    """Tests for GET /lists/{list_id} endpoint."""

    async def test_get_list_success(self, client: AsyncClient, test_db: AsyncSession) -> None:
        """Test retrieving a specific list."""
        list_id = uuid4()
        test_list = List(id=list_id, name="Test List", description="Test")
        test_db.add(test_list)
        await test_db.commit()

        response = await client.get(f"/lists/{list_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(list_id)
        assert data["name"] == "Test List"
        assert data["description"] == "Test"

    async def test_get_list_not_found(self, client: AsyncClient) -> None:
        """Test retrieving a non-existent list."""
        fake_id = uuid4()
        response = await client.get(f"/lists/{fake_id}")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    async def test_get_deleted_list(self, client: AsyncClient, test_db: AsyncSession) -> None:
        """Test that deleted lists cannot be retrieved."""
        from datetime import datetime

        list_id = uuid4()
        test_list = List(
            id=list_id,
            name="Deleted List",
            deleted_at=datetime.now(UTC),
        )
        test_db.add(test_list)
        await test_db.commit()

        response = await client.get(f"/lists/{list_id}")
        assert response.status_code == 404


class TestUpdateList:
    """Tests for PUT /lists/{list_id} endpoint."""

    async def test_update_list_name(self, client: AsyncClient, test_db: AsyncSession) -> None:
        """Test updating a list name."""
        list_id = uuid4()
        test_list = List(id=list_id, name="Original Name")
        test_db.add(test_list)
        await test_db.commit()

        payload = {"name": "New Name"}
        response = await client.put(f"/lists/{list_id}", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"

    async def test_update_list_description(
        self, client: AsyncClient, test_db: AsyncSession
    ) -> None:
        """Test updating a list description."""
        list_id = uuid4()
        test_list = List(id=list_id, name="Test List")
        test_db.add(test_list)
        await test_db.commit()

        payload = {"description": "New description"}
        response = await client.put(f"/lists/{list_id}", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "New description"

    async def test_update_list_not_found(self, client: AsyncClient) -> None:
        """Test updating a non-existent list."""
        fake_id = uuid4()
        payload = {"name": "New Name"}
        response = await client.put(f"/lists/{fake_id}", json=payload)
        assert response.status_code == 404

    async def test_update_list_mark_completed(
        self, client: AsyncClient, test_db: AsyncSession
    ) -> None:
        """Test marking a list as completed."""
        from datetime import datetime

        list_id = uuid4()
        test_list = List(id=list_id, name="Test List")
        test_db.add(test_list)
        await test_db.commit()

        now = datetime.now(UTC)
        payload = {"completed_at": now.isoformat()}
        response = await client.put(f"/lists/{list_id}", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["completed_at"] is not None


class TestPatchList:
    """Tests for PATCH /lists/{list_id} endpoint."""

    async def test_patch_list_name_only(self, client: AsyncClient, test_db: AsyncSession) -> None:
        """Test patching only the name."""
        list_id = uuid4()
        test_list = List(id=list_id, name="Original", description="Original desc")
        test_db.add(test_list)
        await test_db.commit()

        payload = {"name": "Updated"}
        response = await client.patch(f"/lists/{list_id}", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated"
        assert data["description"] == "Original desc"

    async def test_patch_list_empty_payload(
        self, client: AsyncClient, test_db: AsyncSession
    ) -> None:
        """Test patching with empty payload."""
        list_id = uuid4()
        original_name = "Original Name"
        test_list = List(id=list_id, name=original_name)
        test_db.add(test_list)
        await test_db.commit()

        response = await client.patch(f"/lists/{list_id}", json={})
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == original_name


class TestDeleteList:
    """Tests for DELETE /lists/{list_id} endpoint."""

    async def test_delete_list_success(self, client: AsyncClient, test_db: AsyncSession) -> None:
        """Test soft deleting a list."""
        list_id = uuid4()
        test_list = List(id=list_id, name="Test List")
        test_db.add(test_list)
        await test_db.commit()

        response = await client.delete(f"/lists/{list_id}")
        assert response.status_code == 204

        # Verify list is marked as deleted
        await test_db.refresh(test_list)
        assert test_list.deleted_at is not None

    async def test_delete_list_not_found(self, client: AsyncClient) -> None:
        """Test deleting a non-existent list."""
        fake_id = uuid4()
        response = await client.delete(f"/lists/{fake_id}")
        assert response.status_code == 404

    async def test_get_deleted_list_returns_404(
        self, client: AsyncClient, test_db: AsyncSession
    ) -> None:
        """Test that deleted list is no longer retrievable."""
        list_id = uuid4()
        test_list = List(id=list_id, name="Test List")
        test_db.add(test_list)
        await test_db.commit()

        # Delete the list
        await client.delete(f"/lists/{list_id}")

        # Try to retrieve it
        response = await client.get(f"/lists/{list_id}")
        assert response.status_code == 404
