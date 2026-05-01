let currentYear = new Date().getFullYear();
let currentMonth = new Date().getMonth() + 1;

// Load calendar data
async function loadCalendar(year, month) {
    try {
        const response = await fetch(`/api/calendar/data?year=${year}&month=${month}`);
        const data = await response.json();
        renderCalendar(year, month, data.data);
    } catch (error) {
        console.error('Error loading calendar:', error);
    }
}

// Render calendar
function renderCalendar(year, month, activityData) {
    const firstDay = new Date(year, month - 1, 1);
    const startDay = firstDay.getDay();
    const daysInMonth = new Date(year, month, 0).getDate();
    const today = new Date();
    
    let html = `
        <div class="flex justify-between items-center mb-4">
            <button onclick="previousMonth()" class="p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded">
                <i class="fas fa-chevron-left"></i>
            </button>
            <h4 class="font-bold">${getMonthName(month)} ${year}</h4>
            <button onclick="nextMonth()" class="p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded">
                <i class="fas fa-chevron-right"></i>
            </button>
        </div>
        <div class="grid grid-cols-7 gap-1 text-center text-sm font-bold mb-2">
            <div class="text-red-500">Sun</div>
            <div>Mon</div>
            <div>Tue</div>
            <div>Wed</div>
            <div>Thu</div>
            <div>Fri</div>
            <div class="text-blue-500">Sat</div>
        </div>
        <div class="grid grid-cols-7 gap-1">
    `;
    
    // Empty cells before first day
    for (let i = 0; i < (startDay === 0 ? 6 : startDay - 1); i++) {
        html += `<div class="p-2 text-center text-gray-400"></div>`;
    }
    
    // Days of month
    for (let d = 1; d <= daysInMonth; d++) {
        const dateStr = `${year}-${String(month).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
        const hours = activityData[dateStr] || 0;
        let bgColor = 'bg-gray-100 dark:bg-gray-700';
        
        if (hours > 4) bgColor = 'bg-green-700 text-white';
        else if (hours > 2) bgColor = 'bg-green-500 text-white';
        else if (hours > 0) bgColor = 'bg-green-300 dark:bg-green-800';
        
        const isToday = today.getFullYear() === year && today.getMonth() + 1 === month && today.getDate() === d;
        const todayClass = isToday ? 'ring-2 ring-indigo-500' : '';
        
        html += `
            <div class="p-2 text-center ${bgColor} rounded-lg ${todayClass}">
                <div class="font-semibold">${d}</div>
                <div class="text-xs ${hours > 4 ? 'text-white' : 'text-gray-600 dark:text-gray-300'}">${hours}h</div>
            </div>
        `;
    }
    
    html += `</div>`;
    document.getElementById('calendar').innerHTML = html;
}

function getMonthName(month) {
    const months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
    return months[month - 1];
}

function previousMonth() {
    currentMonth--;
    if (currentMonth < 1) {
        currentMonth = 12;
        currentYear--;
    }
    loadCalendar(currentYear, currentMonth);
}

function nextMonth() {
    currentMonth++;
    if (currentMonth > 12) {
        currentMonth = 1;
        currentYear++;
    }
    loadCalendar(currentYear, currentMonth);
}

// Initialize calendar
if (document.getElementById('calendar')) {
    loadCalendar(currentYear, currentMonth);
}