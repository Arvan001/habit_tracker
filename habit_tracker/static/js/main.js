// Global variables
let tasks = [];
let searchTimeout;

// Load tasks
async function loadTasks() {
    try {
        const response = await fetch('/api/tasks');
        if (!response.ok) throw new Error('Failed to load tasks');
        tasks = await response.json();
        renderTasks();
    } catch (error) {
        showToast('Error loading tasks: ' + error.message, 'error');
    }
}

// Render tasks with search filter
function renderTasks() {
    const searchTerm = document.getElementById('searchTask')?.value.toLowerCase() || '';
    const filteredTasks = tasks.filter(task => task.name.toLowerCase().includes(searchTerm));
    const taskList = document.getElementById('taskList');
    
    if (!taskList) return;
    
    if (filteredTasks.length === 0) {
        taskList.innerHTML = '<div class="text-center text-gray-500 py-8">No tasks found. Create your first task!</div>';
        return;
    }
    
    taskList.innerHTML = filteredTasks.map(task => `
        <div class="task-item flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg hover:shadow-md transition" data-id="${task.id}">
            <div class="flex items-center gap-3 flex-1">
                <input type="checkbox" ${task.completed ? 'checked' : ''} data-id="${task.id}" class="task-checkbox w-5 h-5 rounded">
                <span class="${task.completed ? 'line-through text-gray-500' : ''} flex-1">${escapeHtml(task.name)}</span>
                <span class="text-xs px-2 py-1 rounded-full ${getCategoryColor(task.category)}">${task.category}</span>
            </div>
            <div class="flex gap-2">
                <button class="edit-task text-blue-500 hover:text-blue-700" data-id="${task.id}" data-name="${task.name}" data-category="${task.category}">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="delete-task text-red-500 hover:text-red-700" data-id="${task.id}">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
    `).join('');
    
    // Attach event listeners
    document.querySelectorAll('.task-checkbox').forEach(cb => {
        cb.addEventListener('change', (e) => toggleTask(cb.dataset.id));
    });
    document.querySelectorAll('.edit-task').forEach(btn => {
        btn.addEventListener('click', (e) => editTask(btn.dataset.id, btn.dataset.name, btn.dataset.category));
    });
    document.querySelectorAll('.delete-task').forEach(btn => {
        btn.addEventListener('click', (e) => deleteTask(btn.dataset.id));
    });
}

// Helper functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function getCategoryColor(category) {
    const colors = {
        'Kerja': 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300',
        'Belajar': 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300',
        'Olahraga': 'bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300',
        'Custom': 'bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300'
    };
    return colors[category] || colors['Custom'];
}

// Toggle task completion
async function toggleTask(taskId) {
    try {
        const response = await fetch(`/api/tasks/${taskId}/toggle`, { method: 'POST' });
        if (response.ok) {
            await loadTasks();
            updateStats();
            showToast('Task updated!', 'success');
        }
    } catch (error) {
        showToast('Error toggling task', 'error');
    }
}

// Edit task
async function editTask(taskId, currentName, currentCategory) {
    const newName = prompt('Edit task name:', currentName);
    if (newName && newName.trim()) {
        try {
            const response = await fetch(`/api/tasks/${taskId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: newName.trim(), category: currentCategory })
            });
            if (response.ok) {
                await loadTasks();
                showToast('Task updated!', 'success');
            }
        } catch (error) {
            showToast('Error updating task', 'error');
        }
    }
}

// Delete task
async function deleteTask(taskId) {
    if (confirm('Are you sure you want to delete this task?')) {
        try {
            const response = await fetch(`/api/tasks/${taskId}`, { method: 'DELETE' });
            if (response.ok) {
                await loadTasks();
                updateStats();
                showToast('Task deleted!', 'success');
            }
        } catch (error) {
            showToast('Error deleting task', 'error');
        }
    }
}

// Update dashboard stats
async function updateStats() {
    try {
        const response = await fetch('/api/stats/dashboard');
        if (!response.ok) throw new Error('Failed to load stats');
        const stats = await response.json();
        
        document.getElementById('todayHours').innerText = stats.hours_today;
        document.getElementById('dailyProgress').innerText = stats.daily_progress + '%';
        document.getElementById('weekHours').innerText = stats.hours_week;
        document.getElementById('monthHours').innerText = stats.hours_month;
        document.getElementById('streak').innerText = stats.streak;
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Add new task
document.getElementById('addTaskBtn')?.addEventListener('click', async () => {
    const name = prompt('Enter task name:');
    if (name && name.trim()) {
        const category = prompt('Category (Kerja/Belajar/Olahraga/Custom):', 'Custom');
        try {
            const response = await fetch('/api/tasks', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: name.trim(), category: category || 'Custom' })
            });
            if (response.ok) {
                await loadTasks();
                showToast('Task added!', 'success');
            }
        } catch (error) {
            showToast('Error adding task', 'error');
        }
    }
});

// Search with debounce
document.getElementById('searchTask')?.addEventListener('input', (e) => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => renderTasks(), 300);
});

// Load routines
async function loadRoutines() {
    try {
        const response = await fetch('/api/routines');
        const routines = await response.json();
        const routineList = document.getElementById('routineList');
        if (!routineList) return;
        
        if (routines.length === 0) {
            routineList.innerHTML = '<div class="text-center text-gray-500 py-4">No routines set. Add your daily routine!</div>';
            return;
        }
        
        routineList.innerHTML = routines.map(routine => `
            <div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div>
                    <p class="font-semibold">${escapeHtml(routine.name)}</p>
                    <p class="text-sm text-gray-500">${routine.start_time} - ${routine.end_time} | ${routine.category}</p>
                </div>
                <button class="delete-routine text-red-500" data-id="${routine.id}">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        `).join('');
        
        document.querySelectorAll('.delete-routine').forEach(btn => {
            btn.addEventListener('click', () => deleteRoutine(btn.dataset.id));
        });
    } catch (error) {
        console.error('Error loading routines:', error);
    }
}

async function deleteRoutine(routineId) {
    if (confirm('Delete this routine?')) {
        await fetch(`/api/routines/${routineId}`, { method: 'DELETE' });
        await loadRoutines();
        showToast('Routine deleted', 'success');
    }
}

document.getElementById('addRoutineBtn')?.addEventListener('click', async () => {
    const name = prompt('Routine name:');
    if (!name) return;
    const startTime = prompt('Start time (HH:MM, e.g., 06:00):', '06:00');
    const endTime = prompt('End time (HH:MM, e.g., 08:00):', '08:00');
    const category = prompt('Category:', 'Belajar');
    
    if (startTime && endTime) {
        await fetch('/api/routines', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, start_time: startTime, end_time: endTime, category })
        });
        await loadRoutines();
        showToast('Routine added!', 'success');
    }
});

// Initialize
if (document.getElementById('taskList')) {
    loadTasks();
    updateStats();
    loadRoutines();
    setInterval(updateStats, 30000);
}