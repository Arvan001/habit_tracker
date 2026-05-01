let timerInterval = null;
let isRunning = false;
let startTime = null;
let currentTimerId = null;

// Update timer display
function updateTimerDisplay() {
    if (!isRunning || !startTime) return;
    const elapsed = Math.floor((Date.now() - startTime) / 1000);
    const hours = Math.floor(elapsed / 3600);
    const minutes = Math.floor((elapsed % 3600) / 60);
    const seconds = elapsed % 60;
    const display = `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
    const timerDisplay = document.getElementById('timerDisplay');
    if (timerDisplay) timerDisplay.innerText = display;
}

// Start timer
async function startTimer() {
    const taskId = document.getElementById('timerTaskSelect')?.value;
    
    try {
        const response = await fetch('/api/time-tracker/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ task_id: taskId || null })
        });
        
        if (response.ok) {
            isRunning = true;
            startTime = Date.now();
            if (timerInterval) clearInterval(timerInterval);
            timerInterval = setInterval(updateTimerDisplay, 1000);
            
            document.getElementById('startTimerBtn').classList.add('hidden');
            document.getElementById('stopTimerBtn').classList.remove('hidden');
            showToast('Timer started! Focus on your task.', 'success');
        } else {
            const error = await response.json();
            showToast(error.error || 'Failed to start timer', 'error');
        }
    } catch (error) {
        showToast('Error starting timer', 'error');
    }
}

// Stop timer
async function stopTimer() {
    try {
        const response = await fetch('/api/time-tracker/stop', { method: 'POST' });
        
        if (response.ok) {
            const data = await response.json();
            const hours = (data.duration_seconds / 3600).toFixed(2);
            
            clearInterval(timerInterval);
            isRunning = false;
            startTime = null;
            
            document.getElementById('startTimerBtn').classList.remove('hidden');
            document.getElementById('stopTimerBtn').classList.add('hidden');
            document.getElementById('timerDisplay').innerText = '00:00:00';
            
            showToast(`Great job! You studied for ${hours} hours.`, 'success');
            updateStats();
        } else {
            const error = await response.json();
            showToast(error.error || 'Failed to stop timer', 'error');
        }
    } catch (error) {
        showToast('Error stopping timer', 'error');
    }
}

// Check running timer on page load
async function checkRunningTimer() {
    try {
        const response = await fetch('/api/time-tracker/status');
        const data = await response.json();
        
        if (data.running) {
            isRunning = true;
            startTime = Date.now() - (data.elapsed * 1000);
            if (timerInterval) clearInterval(timerInterval);
            timerInterval = setInterval(updateTimerDisplay, 1000);
            
            document.getElementById('startTimerBtn').classList.add('hidden');
            document.getElementById('stopTimerBtn').classList.remove('hidden');
            
            if (data.task_id) {
                document.getElementById('timerTaskSelect').value = data.task_id;
            }
        }
    } catch (error) {
        console.error('Error checking timer:', error);
    }
}

// Load tasks into dropdown
async function loadTasksForTimer() {
    try {
        const response = await fetch('/api/tasks');
        const tasks = await response.json();
        const select = document.getElementById('timerTaskSelect');
        if (!select) return;
        
        select.innerHTML = '<option value="">No task (just focus)</option>';
        tasks.forEach(task => {
            const option = document.createElement('option');
            option.value = task.id;
            option.textContent = `${task.name} (${task.category})`;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading tasks for timer:', error);
    }
}

// Event listeners
document.getElementById('startTimerBtn')?.addEventListener('click', startTimer);
document.getElementById('stopTimerBtn')?.addEventListener('click', stopTimer);

// Initialize timer
if (document.getElementById('timerTaskSelect')) {
    loadTasksForTimer();
    checkRunningTimer();
}