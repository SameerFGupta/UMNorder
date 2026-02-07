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

// Load and display presets
async function loadPresets() {
    const presetsList = document.getElementById('presets-list');
    presetsList.innerHTML = '<div class="loading">Loading presets...</div>';
    
    try {
        const response = await fetch(`${API_BASE}/api/presets`, {
            headers: { 'ngrok-skip-browser-warning': 'true' }
        });
        if (!response.ok) throw new Error('Failed to load presets');
        
        const presets = await response.json();
        
        if (presets.length === 0) {
            presetsList.innerHTML = '<div class="loading">No presets yet. Create one to get started!</div>';
            return;
        }
        
        // Load users to get names
        const usersResponse = await fetch(`${API_BASE}/api/users`, {
            headers: { 'ngrok-skip-browser-warning': 'true' }
        });
        const users = await usersResponse.json();
        const userMap = {};
        users.forEach(u => userMap[u.id] = u);
        
        presetsList.innerHTML = presets.map(preset => {
            const user = userMap[preset.user_id] || { name: 'Unknown', phone_number: 'N/A' };
            
            // Handle both old format (list of strings) and new format (list of objects)
            let itemsList = '';
            if (preset.items && preset.items.length > 0) {
                if (typeof preset.items[0] === 'string') {
                    // Old format
                    itemsList = preset.items.map(item => `<li>${item}</li>`).join('');
                } else {
                    // New format with modifiers
                    itemsList = preset.items.map(item => {
                        const modifiersText = item.modifiers && item.modifiers.length > 0 
                            ? ` <span style="color: #666; font-size: 0.9em;">(${item.modifiers.join(', ')})</span>`
                            : '';
                        return `<li>${item.name}${modifiersText}</li>`;
                    }).join('');
                }
            }
            
            return `
                <div class="preset-card">
                    <h3>${preset.preset_name}</h3>
                    <div class="items">
                        <strong>Items:</strong>
                        <ul>${itemsList}</ul>
                    </div>
                    <div style="margin-bottom: 10px; font-size: 0.9rem; color: #666;">
                        <strong>User:</strong> ${user.name} (${user.phone_number})<br>
                        ${preset.location_name ? `<strong>Location:</strong> ${preset.location_name}` : '<strong>Location:</strong> <em>Any available</em>'}
                    </div>
                    <button class="btn btn-order" onclick="placeOrder(${preset.id}, '${preset.preset_name}', this)">
                        ORDER NOW
                    </button>
                    <button class="btn btn-delete" onclick="deletePreset(${preset.id})">
                        Delete Preset
                    </button>
                </div>
            `;
        }).join('');
    } catch (error) {
        presetsList.innerHTML = `<div class="loading" style="color: #ff6b6b;">Error loading presets: ${error.message}</div>`;
    }
}

// Load and display users
async function loadUsers() {
    const usersList = document.getElementById('users-list');
    usersList.innerHTML = '<div class="loading">Loading users...</div>';
    
    try {
        const response = await fetch(`${API_BASE}/api/users`, {
            headers: { 'ngrok-skip-browser-warning': 'true' }
        });
        if (!response.ok) throw new Error('Failed to load users');
        
        const users = await response.json();
        
        if (users.length === 0) {
            usersList.innerHTML = '<div class="loading">No users yet. Add one to get started!</div>';
            return;
        }
        
        usersList.innerHTML = users.map(user => `
            <div class="user-card">
                <div>
                    <strong>${user.name}</strong><br>
                    <span style="color: #666;">${user.phone_number}</span>
                </div>
            </div>
        `).join('');
    } catch (error) {
        usersList.innerHTML = `<div class="loading" style="color: #ff6b6b;">Error loading users: ${error.message}</div>`;
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
        
        userSelect.innerHTML = '<option value="">Select a user...</option>' +
            users.map(user => `<option value="${user.id}">${user.name} (${user.phone_number})</option>`).join('');
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
    // Removed the inline style.cssText that was forcing white background
    
    itemDiv.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
            <strong>Item ${itemIndex + 1}</strong>
            <button type="button" class="btn btn-sm" onclick="removeItemRow(this)">Remove</button>
        </div>
        <div class="form-group" style="margin-bottom: 15px;">
            <label>Item Name:</label>
            <input type="text" class="item-name" placeholder="e.g., Hamburger" value="${itemName}" required>
        </div>
        <div class="form-group" style="margin-bottom: 0;">
            <label>Modifiers (comma-separated):</label>
            <input type="text" class="item-modifiers" placeholder="e.g., Bun, American Cheese" value="${modifiers.join(', ')}">
            <small style="display: block; color: #888; margin-top: 8px; font-size: 0.85rem;">Enter modifier names exactly as they appear</small>
        </div>
    `;
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
        document.getElementById('items-container').innerHTML = '';
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
    messageDiv.innerHTML = message;
    
    if (type === 'processing') {
        messageDiv.innerHTML += '<div class="spinner"></div>';
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