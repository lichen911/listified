/**
 * Listified Frontend Application
 * Alpine.js + Fetch API for list management with sidebar layout
 */

// API base URL
const API_BASE_URL = '';

/**
 * Main application state and logic
 */
function appState() {
    return {
        // State
        lists: [],
        currentList: null,
        currentListId: null,
        loading: false,
        error: '',
        darkMode: localStorage.getItem('darkMode') === 'true',
        sidebarCollapsed: localStorage.getItem('sidebarCollapsed') === 'true',

        // Editing state
        editingListName: false,
        editingListDesc: false,
        editingItemId: null,

        // Form data
        newList: {
            name: '',
            description: '',
        },
        newItem: {
            name: '',
            description: '',
        },

        // Original values for cancel operations
        originalListName: '',
        originalListDesc: '',
        originalItemData: {},

        // Initialization
        async init() {
            this.applyDarkMode();
            await this.loadLists();
            this.setupListsSortable();
        },

        // Dark mode
        toggleDarkMode() {
            this.darkMode = !this.darkMode;
            this.applyDarkMode();
            localStorage.setItem('darkMode', this.darkMode);
        },

        applyDarkMode() {
            const html = document.documentElement;
            if (this.darkMode) {
                html.setAttribute('data-theme', 'dark');
            } else {
                html.removeAttribute('data-theme');
            }
        },

        // Lists operations
        async loadLists() {
            try {
                this.loading = true;
                this.error = '';
                const response = await fetch(`${API_BASE_URL}/lists`);
                if (!response.ok) throw new Error('Failed to load lists');
                this.lists = await response.json();
            } catch (err) {
                this.error = err.message;
            } finally {
                this.loading = false;
                setTimeout(() => this.setupListsSortable(), 100);
            }
        },

        async createList() {
            if (!this.newList.name.trim()) {
                this.error = 'List name is required';
                return;
            }

            try {
                this.loading = true;
                this.error = '';
                const response = await fetch(`${API_BASE_URL}/lists`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(this.newList),
                });
                if (!response.ok) throw new Error('Failed to create list');

                // Reset form and reload
                this.newList = { name: '', description: '' };
                await this.loadLists();
            } catch (err) {
                this.error = err.message;
            } finally {
                this.loading = false;
            }
        },

        async toggleListCompletion(list) {
            try {
                this.loading = true;
                this.error = '';
                const completed_at = list.completed_at ? null : new Date().toISOString();
                const response = await fetch(`${API_BASE_URL}/lists/${list.id}`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ completed_at }),
                });
                if (!response.ok) throw new Error('Failed to update list');

                // Optimistic update - reload from API to ensure consistency
                await this.loadLists();
                if (this.currentListId) {
                    await this.loadItems();
                }
            } catch (err) {
                this.error = err.message;
                await this.loadLists();
            } finally {
                this.loading = false;
            }
        },

        async deleteList(listId) {
            if (!confirm('Delete this list?')) return;

            try {
                this.loading = true;
                this.error = '';
                const response = await fetch(`${API_BASE_URL}/lists/${listId}`, {
                    method: 'DELETE',
                });
                if (!response.ok) throw new Error('Failed to delete list');

                // Clear selection if deleted list was selected
                if (this.currentListId === listId) {
                    this.currentList = null;
                    this.currentListId = null;
                }

                await this.loadLists();
            } catch (err) {
                this.error = err.message;
            } finally {
                this.loading = false;
            }
        },

        // List selection
        selectList(list) {
            this.currentListId = list.id;
            this.currentList = { ...list, items: [] };
            this.loadItems();
        },

        // Inline list name editing
        startEditListName() {
            if (!this.currentList) return;
            this.originalListName = this.currentList.name;
            this.editingListName = true;
        },

        cancelListNameEdit() {
            if (!this.currentList) return;
            this.currentList.name = this.originalListName;
            this.editingListName = false;
        },

        async saveListName() {
            if (!this.currentList) return;
            if (!this.currentList.name.trim()) {
                this.error = 'List name cannot be empty';
                this.currentList.name = this.originalListName;
                this.editingListName = false;
                return;
            }

            try {
                this.error = '';
                const response = await fetch(`${API_BASE_URL}/lists/${this.currentList.id}`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name: this.currentList.name }),
                });
                if (!response.ok) throw new Error('Failed to update list name');

                // Update list in sidebar
                const listInSidebar = this.lists.find(l => l.id === this.currentList.id);
                if (listInSidebar) {
                    listInSidebar.name = this.currentList.name;
                }
            } catch (err) {
                this.error = err.message;
                this.currentList.name = this.originalListName;
            } finally {
                this.editingListName = false;
            }
        },

        // Inline list description editing
        startEditListDesc() {
            if (!this.currentList) return;
            this.originalListDesc = this.currentList.description || '';
            this.editingListDesc = true;
        },

        cancelListDescEdit() {
            if (!this.currentList) return;
            this.currentList.description = this.originalListDesc;
            this.editingListDesc = false;
        },

        async saveListDescription() {
            if (!this.currentList) return;
            try {
                this.error = '';
                const response = await fetch(`${API_BASE_URL}/lists/${this.currentList.id}`, {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ description: this.currentList.description }),
                });
                if (!response.ok) throw new Error('Failed to update list description');

                // Update list in sidebar
                const listInSidebar = this.lists.find(l => l.id === this.currentList.id);
                if (listInSidebar) {
                    listInSidebar.description = this.currentList.description;
                }
            } catch (err) {
                this.error = err.message;
                this.currentList.description = this.originalListDesc;
            } finally {
                this.editingListDesc = false;
            }
        },

        // Items operations
        async loadItems() {
            try {
                this.loading = true;
                this.error = '';
                const response = await fetch(`${API_BASE_URL}/lists/${this.currentListId}/items`);
                if (!response.ok) throw new Error('Failed to load items');
                const items = await response.json();
                if (this.currentList) {
                    this.currentList.items = items;
                }
            } catch (err) {
                this.error = err.message;
            } finally {
                this.loading = false;
                setTimeout(() => this.setupItemsSortable(), 100);
            }
        },

        async createItem() {
            if (!this.newItem.name.trim()) {
                this.error = 'Item name is required';
                return;
            }

            // Calculate next order value
            const items = this.currentList.items || [];
            const nextOrder = items.length > 0
                ? Math.max(...items.map(i => i.order)) + 1
                : 0;

            try {
                this.loading = true;
                this.error = '';
                const response = await fetch(
                    `${API_BASE_URL}/lists/${this.currentListId}/items`,
                    {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            ...this.newItem,
                            order: nextOrder,
                        }),
                    }
                );
                if (!response.ok) throw new Error('Failed to create item');

                // Reset form and reload
                this.newItem = { name: '', description: '' };
                await this.loadItems();
            } catch (err) {
                this.error = err.message;
            } finally {
                this.loading = false;
            }
        },

        async toggleItemCompletion(item) {
            try {
                this.loading = true;
                this.error = '';
                const completed_at = item.completed_at ? null : new Date().toISOString();
                const response = await fetch(
                    `${API_BASE_URL}/lists/${this.currentListId}/items/${item.id}`,
                    {
                        method: 'PATCH',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ completed_at }),
                    }
                );
                if (!response.ok) throw new Error('Failed to update item');

                // Optimistic update
                item.completed_at = completed_at;
            } catch (err) {
                this.error = err.message;
            } finally {
                this.loading = false;
            }
        },

        async deleteItem(itemId) {
            if (!confirm('Delete this item?')) return;

            try {
                this.loading = true;
                this.error = '';
                const response = await fetch(
                    `${API_BASE_URL}/lists/${this.currentListId}/items/${itemId}`,
                    {
                        method: 'DELETE',
                    }
                );
                if (!response.ok) throw new Error('Failed to delete item');

                await this.loadItems();
            } catch (err) {
                this.error = err.message;
            } finally {
                this.loading = false;
            }
        },

        // Inline item name editing
        startEditItemName(item) {
            this.editingItemId = item.id;
            this.originalItemData = { ...item };
        },

        // Inline item description editing
        startEditItemDesc(item) {
            this.editingItemId = item.id;
            this.originalItemData = { ...item };
        },

        cancelItemEdit(item) {
            item.name = this.originalItemData.name;
            item.description = this.originalItemData.description;
            this.editingItemId = null;
        },

        async saveItemName(item) {
            if (!item.name.trim()) {
                this.error = 'Item name cannot be empty';
                item.name = this.originalItemData.name;
                this.editingItemId = null;
                return;
            }

            try {
                this.error = '';
                const response = await fetch(
                    `${API_BASE_URL}/lists/${this.currentListId}/items/${item.id}`,
                    {
                        method: 'PATCH',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ name: item.name }),
                    }
                );
                if (!response.ok) throw new Error('Failed to update item');
            } catch (err) {
                this.error = err.message;
                item.name = this.originalItemData.name;
            } finally {
                this.editingItemId = null;
            }
        },

        async saveItemDescription(item) {
            try {
                this.error = '';
                const response = await fetch(
                    `${API_BASE_URL}/lists/${this.currentListId}/items/${item.id}`,
                    {
                        method: 'PATCH',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ description: item.description }),
                    }
                );
                if (!response.ok) throw new Error('Failed to update item');
            } catch (err) {
                this.error = err.message;
                item.description = this.originalItemData.description;
            } finally {
                this.editingItemId = null;
            }
        },

        // Drag and drop for lists (in sidebar)
        setupListsSortable() {
            const listsSortable = document.getElementById('lists-sortable');
            if (!listsSortable) return;

            // Destroy existing instance
            if (listsSortable.sortableInstance) {
                listsSortable.sortableInstance.destroy();
            }

            // Initialize Sortable for list reordering
            listsSortable.sortableInstance = Sortable.create(listsSortable, {
                animation: 150,
                ghostClass: 'sortable-ghost',
                dragClass: 'sortable-drag',
                handle: '.list-link',
                onEnd: (evt) => this.onListReordered(evt),
            });
        },

        async onListReordered(evt) {
            // Get reordered lists
            const listElements = document.querySelectorAll('.list-item');
            const reorderedIds = Array.from(listElements).map(el => el.dataset.id);

            // Update order values in state
            const updatePromises = reorderedIds.map((id, index) => {
                const list = this.lists.find(l => l.id === id);
                if (list && list.order !== index) {
                    list.order = index;
                    // Note: Backend doesn't have order field for lists yet
                    // This is a placeholder for future implementation
                    return Promise.resolve();
                }
                return Promise.resolve();
            });

            try {
                await Promise.all(updatePromises);
            } catch (err) {
                this.error = 'Failed to update list order';
                await this.loadLists();
            }
        },

        // Drag and drop for items
        setupItemsSortable() {
            const itemsSortable = document.getElementById('items-sortable');
            if (!itemsSortable) return;

            // Destroy existing instance
            if (itemsSortable.sortableInstance) {
                itemsSortable.sortableInstance.destroy();
            }

            // Initialize Sortable for item reordering
            itemsSortable.sortableInstance = Sortable.create(itemsSortable, {
                animation: 150,
                ghostClass: 'sortable-ghost',
                dragClass: 'sortable-drag',
                handle: '.item-card',
                onEnd: (evt) => this.onItemReordered(evt),
            });
        },

        async onItemReordered(evt) {
            if (!this.currentList?.items) return;

            // Get reordered items
            const itemElements = document.querySelectorAll('.item-card');
            const reorderedIds = Array.from(itemElements).map(el => el.dataset.id);

            // Update order values and send to server
            const updatePromises = reorderedIds.map((id, index) => {
                const item = this.currentList.items.find(i => i.id === id);
                if (item && item.order !== index) {
                    item.order = index;
                    return this.updateItemOrder(id, index);
                }
                return Promise.resolve();
            });

            try {
                await Promise.all(updatePromises);
            } catch (err) {
                this.error = 'Failed to update item order';
                await this.loadItems();
            }
        },

        async updateItemOrder(itemId, order) {
            const response = await fetch(
                `${API_BASE_URL}/lists/${this.currentListId}/items/${itemId}`,
                {
                    method: 'PATCH',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ order }),
                }
            );
            if (!response.ok) throw new Error('Failed to update item order');
        },

        // Utility functions
        formatDate(dateString) {
            const date = new Date(dateString);
            return date.toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
            });
        },
    };
}
