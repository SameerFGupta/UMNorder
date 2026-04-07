const API_BASE = "https://hyperangelic-zariyah-nonparentally.ngrok-free.dev";

// Tab switching
function showTab(tabName, clickedButton = null) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active class from all buttons
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(`${tabName}-tab`).classList.add('active');
    
    // Activate button - use clickedButton if provided, otherwise find by tab name
    if (clickedButton) {
        clickedButton.classList.add('active');
    } else {
        // Find the button that corresponds to this tab
        const buttons = document.querySelectorAll('.tab-button');
        buttons.forEach(btn => {
            const btnText = btn.textContent.toLowerCase();
            if ((tabName === 'presets' && btnText.includes('presets')) ||
                (tabName === 'create' && btnText.includes('create')) ||
                (tabName === 'users' && btnText.includes('users'))) {
                btn.classList.add('active');
            }
        });
    }
    
    // Load data if needed
    if (tabName === 'presets') {
        loadPresets();
    } else if (tabName === 'users') {
        loadUsers();
    }
}

// Helper to escape HTML and prevent XSS
function escapeHTML(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// Load and display presets
async function loadPresets() {
    const presetsList = document.getElementById('presets-list');
    presetsList.textContent = '';
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'loading';
    loadingDiv.textContent = 'Loading presets...';
    presetsList.appendChild(loadingDiv);
    
    try {
        const response = await fetch(`${API_BASE}/api/presets`, {
            headers: { 'ngrok-skip-browser-warning': 'true' }
        });
        if (!response.ok) throw new Error('Failed to load presets');
        
        const presets = await response.json();
        
        presetsList.textContent = '';
        if (presets.length === 0) {
            const noPresetsDiv = document.createElement('div');
            noPresetsDiv.className = 'loading';
            noPresetsDiv.textContent = 'No presets yet. Create one to get started!';
            presetsList.appendChild(noPresetsDiv);
            return;
        }
        
        // Load users to get names
        const usersResponse = await fetch(`${API_BASE}/api/users`, {
            headers: { 'ngrok-skip-browser-warning': 'true' }
        });
        const users = await usersResponse.json();
        const userMap = {};
        users.forEach(u => userMap[u.id] = u);
        
        presets.forEach(preset => {
            const user = userMap[preset.user_id] || { name: 'Unknown', phone_number: 'N/A' };
            const card = document.createElement('div');
            card.className = 'preset-card';

            const h3 = document.createElement('h3');
            h3.textContent = preset.preset_name;
            card.appendChild(h3);

            const itemsDiv = document.createElement('div');
            itemsDiv.className = 'items';
            const itemsStrong = document.createElement('strong');
            itemsStrong.textContent = 'Items:';
            itemsDiv.appendChild(itemsStrong);
            
            const ul = document.createElement('ul');
            if (preset.items && preset.items.length > 0) {
                preset.items.forEach(item => {
                    const li = document.createElement('li');
                    if (typeof item === 'string') {
                        // Old format
                        li.textContent = item;
                    } else {
                        // New format with modifiers
                        li.textContent = item.name;
                        if (item.modifiers && item.modifiers.length > 0) {
                            const span = document.createElement('span');
                            span.style.color = '#666';
                            span.style.fontSize = '0.9em';
                            span.textContent = ` (${item.modifiers.join(', ')})`;
                            li.appendChild(span);
                        }
                    }
                    ul.appendChild(li);
                });
            }
            itemsDiv.appendChild(ul);
            card.appendChild(itemsDiv);

            const userDiv = document.createElement('div');
            userDiv.style.marginBottom = '10px';
            userDiv.style.fontSize = '0.9rem';
            userDiv.style.color = '#666';

            const userStrong = document.createElement('strong');
            userStrong.textContent = 'User:';
            userDiv.appendChild(userStrong);
            userDiv.appendChild(document.createTextNode(` ${user.name} (${user.phone_number})`));
            userDiv.appendChild(document.createElement('br'));

            const locationStrong = document.createElement('strong');
            locationStrong.textContent = 'Location:';
            userDiv.appendChild(locationStrong);
            if (preset.location_name) {
                userDiv.appendChild(document.createTextNode(` ${preset.location_name}`));
            } else {
                const em = document.createElement('em');
                em.textContent = ' Any available';
                userDiv.appendChild(em);
            }
            card.appendChild(userDiv);

            const orderBtn = document.createElement('button');
            orderBtn.className = 'btn btn-order';
            orderBtn.textContent = 'ORDER NOW';
            orderBtn.onclick = (e) => placeOrder(preset.id, preset.preset_name, e.target);
            card.appendChild(orderBtn);
            
            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'btn btn-delete';
            deleteBtn.textContent = 'Delete Preset';
            deleteBtn.onclick = () => deletePreset(preset.id);
            card.appendChild(deleteBtn);

            presetsList.appendChild(card);
        });
    } catch (error) {
        presetsList.textContent = '';
        const errorDiv = document.createElement('div');
        errorDiv.className = 'loading';
        errorDiv.style.color = '#ff6b6b';
        errorDiv.textContent = `Error loading presets: ${error.message}`;
        presetsList.appendChild(errorDiv);
    }
}

// Load and display users
async function loadUsers() {
    const usersList = document.getElementById('users-list');
    usersList.textContent = '';
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'loading';
    loadingDiv.textContent = 'Loading users...';
    usersList.appendChild(loadingDiv);
    
    try {
        const response = await fetch(`${API_BASE}/api/users`, {
            headers: { 'ngrok-skip-browser-warning': 'true' }
        });
        if (!response.ok) throw new Error('Failed to load users');
        
        const users = await response.json();
        
        usersList.textContent = '';
        if (users.length === 0) {
            const noUsersDiv = document.createElement('div');
            noUsersDiv.className = 'loading';
            noUsersDiv.textContent = 'No users yet. Add one to get started!';
            usersList.appendChild(noUsersDiv);
            return;
        }
        
        users.forEach(user => {
            const card = document.createElement('div');
            card.className = 'user-card';
            const innerDiv = document.createElement('div');

            const strong = document.createElement('strong');
            strong.textContent = user.name;
            innerDiv.appendChild(strong);
            innerDiv.appendChild(document.createElement('br'));

            const span = document.createElement('span');
            span.style.color = '#666';
            span.textContent = user.phone_number;
            innerDiv.appendChild(span);

            card.appendChild(innerDiv);
            usersList.appendChild(card);
        });
    } catch (error) {
        usersList.textContent = '';
        const errorDiv = document.createElement('div');
        errorDiv.className = 'loading';
        errorDiv.style.color = '#ff6b6b';
        errorDiv.textContent = `Error loading users: ${error.message}`;
        usersList.appendChild(errorDiv);
    }
}

// Load users for dropdown
async function loadUsersForDropdown() {
    const userSelect = document.getElementById('user-select');
    
    try {
        const response = await fetch(`${API_BASE}/api/users`, {
            headers: { 'ngrok-skip-browser-warning': 'true' }
        });
        if (!response.ok) throw new Error('Failed to load users');
        
        const users = await response.json();
        
        userSelect.textContent = '';
        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.textContent = 'Select a user...';
        userSelect.appendChild(defaultOption);

        users.forEach(user => {
            const option = document.createElement('option');
            option.value = user.id;
            option.textContent = `${user.name} (${user.phone_number})`;
            userSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading users:', error);
    }
}

// Create user
document.getElementById('create-user-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const name = document.getElementById('user-name').value;
    const phone = document.getElementById('user-phone').value;
    
    try {
        const response = await fetch(`${API_BASE}/api/users`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'ngrok-skip-browser-warning': 'true',
            },
            body: JSON.stringify({ name, phone_number: phone }),
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to create user');
        }
        
        showStatus('User created successfully!', 'success');
        document.getElementById('create-user-form').reset();
        loadUsers();
        loadUsersForDropdown();
    } catch (error) {
        showStatus(`Error: ${error.message}`, 'error');
    }
});

// FIX: Add item row to form with correct Dark Mode visibility
function addItemRow(itemName = '', modifiers = []) {
    const container = document.getElementById('items-container');
    const itemIndex = container.children.length;
    const itemDiv = document.createElement('div');
    itemDiv.className = 'item-row';
    
    // Header row
    const headerDiv = document.createElement('div');
    headerDiv.style.display = 'flex';
    headerDiv.style.justifyContent = 'space-between';
    headerDiv.style.alignItems = 'center';
    headerDiv.style.marginBottom = '15px';

    const strong = document.createElement('strong');
    strong.textContent = `Item ${itemIndex + 1}`;
    headerDiv.appendChild(strong);

    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.className = 'btn btn-sm';
    removeBtn.textContent = 'Remove';
    removeBtn.onclick = (e) => removeItemRow(e.target);
    headerDiv.appendChild(removeBtn);
    itemDiv.appendChild(headerDiv);

    // Item Name group
    const nameGroup = document.createElement('div');
    nameGroup.className = 'form-group';
    nameGroup.style.marginBottom = '15px';

    const nameLabel = document.createElement('label');
    nameLabel.textContent = 'Item Name:';
    nameGroup.appendChild(nameLabel);

    const nameInput = document.createElement('input');
    nameInput.type = 'text';
    nameInput.className = 'item-name';
    nameInput.placeholder = 'e.g., Hamburger';
    nameInput.value = itemName;
    nameInput.required = true;
    nameGroup.appendChild(nameInput);
    itemDiv.appendChild(nameGroup);

    // Modifiers group
    const modGroup = document.createElement('div');
    modGroup.className = 'form-group';
    modGroup.style.marginBottom = '0';

    const modLabel = document.createElement('label');
    modLabel.textContent = 'Modifiers (comma-separated):';
    modGroup.appendChild(modLabel);

    const modInput = document.createElement('input');
    modInput.type = 'text';
    modInput.className = 'item-modifiers';
    modInput.placeholder = 'e.g., Bun, American Cheese';
    modInput.value = modifiers.join(', ');
    modGroup.appendChild(modInput);

    const small = document.createElement('small');
    small.style.display = 'block';
    small.style.color = '#888';
    small.style.marginTop = '8px';
    small.style.fontSize = '0.85rem';
    small.textContent = 'Enter modifier names exactly as they appear';
    modGroup.appendChild(small);
    itemDiv.appendChild(modGroup);

    container.appendChild(itemDiv);
}

// Remove item row
function removeItemRow(button) {
    button.closest('.item-row').remove();
    // Update item numbers
    const container = document.getElementById('items-container');
    Array.from(container.children).forEach((row, index) => {
        row.querySelector('strong').textContent = `Item ${index + 1}`;
    });
}

// Create preset
document.getElementById('create-preset-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const userId = parseInt(document.getElementById('user-select').value);
    const presetName = document.getElementById('preset-name').value;
    const locationName = document.getElementById('location-select').value || null;
    
    // Collect items with modifiers
    const itemRows = document.querySelectorAll('.item-row');
    const items = [];
    
    itemRows.forEach(row => {
        const itemName = row.querySelector('.item-name').value.trim();
        const modifiersText = row.querySelector('.item-modifiers').value.trim();
        
        if (itemName) {
            const modifiers = modifiersText
                ? modifiersText.split(',').map(m => m.trim()).filter(m => m.length > 0)
                : [];
            items.push({
                name: itemName,
                modifiers: modifiers
            });
        }
    });
    
    if (items.length === 0) {
        showStatus('Please add at least one item', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/presets`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'ngrok-skip-browser-warning': 'true',
            },
            body: JSON.stringify({
                user_id: userId,
                preset_name: presetName,
                items: items,
                location_name: locationName,
            }),
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to create preset');
        }
        
        showStatus('Preset created successfully!', 'success');
        document.getElementById('create-preset-form').reset();
        document.getElementById('items-container').textContent = '';
        showTab('presets');
        loadPresets();
    } catch (error) {
        showStatus(`Error: ${error.message}`, 'error');
    }
});

// Place order
async function placeOrder(presetId, presetName, buttonElement = null) {
    const button = buttonElement || (typeof event !== 'undefined' && event?.target) || document.querySelector(`button[onclick*="placeOrder(${presetId}"]`);
    if (!button) {
        showStatus('Error: Could not find order button', 'error');
        return;
    }
    const originalText = button.textContent;
    
    // Disable button and show processing
    button.disabled = true;
    button.textContent = '⏳ Processing...';
    button.classList.add('btn-processing');
    
    showStatus(`Placing order for "${presetName}"...`, 'processing');
    
    try {
        const response = await fetch(`${API_BASE}/api/order`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'ngrok-skip-browser-warning': 'true',
            },
            body: JSON.stringify({ preset_id: presetId }),
        });
        
        const result = await response.json();
        
        if (result.success) {
            showStatus(`✅ ${result.message}`, 'success');
        } else {
            let message = `❌ ${result.message}`;
            if (result.cooldown_remaining) {
                const minutes = Math.floor(result.cooldown_remaining / 60);
                const seconds = result.cooldown_remaining % 60;
                message += ` (${minutes}m ${seconds}s remaining)`;
            }
            showStatus(message, 'error');
        }
    } catch (error) {
        showStatus(`❌ Error: ${error.message}`, 'error');
    } finally {
        // Re-enable button
        button.disabled = false;
        button.textContent = originalText;
        button.classList.remove('btn-processing');
    }
}

// Delete preset
async function deletePreset(presetId) {
    if (!confirm('Are you sure you want to delete this preset?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/api/presets/${presetId}`, {
            method: 'DELETE',
            headers: { 'ngrok-skip-browser-warning': 'true' }
        });
        
        if (!response.ok) {
            throw new Error('Failed to delete preset');
        }
        
        showStatus('Preset deleted successfully!', 'success');
        loadPresets();
    } catch (error) {
        showStatus(`Error: ${error.message}`, 'error');
    }
}

// Show status modal
function showStatus(message, type) {
    const modal = document.getElementById('status-modal');
    const messageDiv = document.getElementById('status-message');
    
    messageDiv.className = `status-${type}`;
    messageDiv.textContent = message;
    
    if (type === 'processing') {
        const spinner = document.createElement('div');
        spinner.className = 'spinner';
        messageDiv.appendChild(spinner);
    }
    
    modal.style.display = 'block';
    
    // Auto-close after 5 seconds for success/error (not processing)
    if (type !== 'processing') {
        setTimeout(() => {
            closeModal();
        }, 5000);
    }
}

// Close modal
function closeModal() {
    document.getElementById('status-modal').style.display = 'none';
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('status-modal');
    if (event.target === modal) {
        closeModal();
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    loadPresets();
    loadUsers();
    loadUsersForDropdown();
    // Add one empty item row by default
    addItemRow();
});