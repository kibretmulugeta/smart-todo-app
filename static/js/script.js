// Load tasks and categories on page load
document.addEventListener('DOMContentLoaded', () => {
    loadCategories();
    loadTasks();
    document.getElementById('taskForm').addEventListener('submit', createTask);
});

async function loadCategories() {
    const response = await fetch('/api/categories');
    const categories = await response.json();
    const select = document.getElementById('category');
    
    select.innerHTML = '<option value="">Select category</option>';
    categories.forEach(cat => {
        select.innerHTML += `<option value="${cat.name}">${cat.icon} ${cat.name}</option>`;
    });
    
    // Add "Add custom category" option
    select.innerHTML += '<option value="__custom__">➕ Add custom category...</option>';
    select.onchange = function() {
        if (this.value === '__custom__') {
            addCustomCategory();
        }
    };
}

async function addCustomCategory() {
    const name = prompt('Enter category name:');
    if (!name) return;
    
    const icon = prompt('Enter emoji icon (e.g., 📚):', '📌');
    const color = prompt('Enter color (e.g., #FF5722):', '#808080');
    
    const response = await fetch('/api/categories', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({name, icon, color})
    });
    
    if (response.ok) {
        loadCategories();
    }
}

function showTimeFields() {
    const type = document.getElementById('timeType').value;
    const container = document.getElementById('dynamicFields');
    
    if (type === 'once') {
        container.innerHTML = `
            <label>Schedule for:</label>
            <input type="datetime-local" id="scheduledDatetime" required>
        `;
    } 
    else if (type === 'duration') {
        container.innerHTML = `
            <label>Remind me after:</label>
            <input type="number" id="durationValue" placeholder="3" required>
            <select id="durationUnit">
                <option value="hours">Hours</option>
                <option value="days">Days</option>
                <option value="weeks">Weeks</option>
            </select>
            <label>
                <input type="checkbox" id="startNow" checked> Start from now
            </label>
        `;
    }
    else if (type === 'recurring') {
        container.innerHTML = `
            <label>Every:</label>
            <input type="number" id="recurInterval" value="1">
            <select id="recurUnit">
                <option value="days">Day(s)</option>
                <option value="weeks">Week(s)</option>
                <option value="hours">Hour(s)</option>
            </select>
            <label>Starting from:</label>
            <input type="datetime-local" id="recurStart" required>
            <label>End (optional):</label>
            <select id="recurEndType">
                <option value="never">Never ends</option>
                <option value="date">End by date</option>
                <option value="count">After N times</option>
            </select>
            <div id="endOptions"></div>
        `;
        
        document.getElementById('recurEndType').onchange = function() {
            const endDiv = document.getElementById('endOptions');
            if (this.value === 'date') {
                endDiv.innerHTML = '<input type="datetime-local" id="recurEndDate">';
            } else if (this.value === 'count') {
                endDiv.innerHTML = '<input type="number" id="recurMaxCount" placeholder="Number of occurrences">';
            } else {
                endDiv.innerHTML = '';
            }
        };
    }
}

async function createTask(e) {
    e.preventDefault();
    
    const taskData = {
        title: document.getElementById('taskTitle').value,
        description: document.getElementById('taskDesc').value,
        category: document.getElementById('category').value,
        time_type: document.getElementById('timeType').value
    };
    
    // Add time-specific data
    if (taskData.time_type === 'once') {
        taskData.scheduled_datetime = document.getElementById('scheduledDatetime').value;
    }
    else if (taskData.time_type === 'duration') {
        taskData.duration_value = parseInt(document.getElementById('durationValue').value);
        taskData.duration_unit = document.getElementById('durationUnit').value;
        taskData.start_now = document.getElementById('startNow').checked;
    }
    else if (taskData.time_type === 'recurring') {
        taskData.interval = parseInt(document.getElementById('recurInterval').value);
        taskData.unit = document.getElementById('recurUnit').value;
        taskData.start_datetime = document.getElementById('recurStart').value;
        
        const endType = document.getElementById('recurEndType').value;
        if (endType === 'date') {
            taskData.end_datetime = document.getElementById('recurEndDate').value;
        } else if (endType === 'count') {
            taskData.max_occurrences = parseInt(document.getElementById('recurMaxCount').value);
        }
    }
    
    const response = await fetch('/api/tasks', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(taskData)
    });
    
    if (response.ok) {
        alert('✅ Smart task created!');
        document.getElementById('taskForm').reset();
        loadTasks();
    } else {
        const error = await response.json();
        alert('❌ Error: ' + error.error);
    }
}

async function loadTasks() {
    const response = await fetch('/api/tasks');
    const tasks = await response.json();
    displayTasks(tasks);
}

function displayTasks(tasks) {
    const container = document.getElementById('taskList');
    
    if (tasks.length === 0) {
        container.innerHTML = '<div class="empty">✨ No tasks yet. Create your first smart task!</div>';
        return;
    }
    
    container.innerHTML = tasks.map(task => `
        <div class="task-item ${task.status === 'completed' ? 'completed' : ''}">
            <input type="checkbox" ${task.status === 'completed' ? 'checked' : ''} 
                   onchange="toggleComplete(${task.id})">
            <div style="flex:1">
                <strong>${escapeHtml(task.title)}</strong>
                ${task.description ? `<br><small>${escapeHtml(task.description)}</small>` : ''}
                <div class="task-category" style="background: ${getCategoryColor(task.category)}20; color: ${getCategoryColor(task.category)}">
                    ${task.category}
                </div>
                <div class="task-due">📅 Due: ${formatDate(task.next_due)}</div>
            </div>
            <button class="delete-btn" onclick="deleteTask(${task.id})">Delete</button>
        </div>
    `).join('');
}

async function toggleComplete(taskId) {
    await fetch(`/api/tasks/${taskId}/complete`, {method: 'PUT'});
    loadTasks();
}

async function deleteTask(taskId) {
    if (confirm('Delete this task?')) {
        await fetch(`/api/tasks/${taskId}`, {method: 'DELETE'});
        loadTasks();
    }
}

function getCategoryColor(categoryName) {
    const colors = {
        'Work': '#4CAF50',
        'Personal': '#2196F3',
        'Health': '#FF9800',
        'Learning': '#9C27B0',
        'Shopping': '#F44336'
    };
    return colors[categoryName] || '#808080';
}

function formatDate(dateString) {
    if (!dateString) return 'No due date';
    const date = new Date(dateString);
    const now = new Date();
    const diff = date - now;
    
    if (diff < 0) return '🔴 Overdue';
    if (diff < 3600000) return '⚠️ Due within 1 hour';
    if (diff < 86400000) return 'Today';
    
    return date.toLocaleDateString();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showTab(tab) {
    // Implement tab switching
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    event.target.classList.add('active');
    loadTasks(); // Reload with filter
}