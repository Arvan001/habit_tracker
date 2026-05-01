let hoursChart = null;
let tasksChart = null;

// Load chart data
async function loadCharts() {
    try {
        const response = await fetch('/api/stats/charts');
        const data = await response.json();
        
        // Hours chart
        const hoursCtx = document.getElementById('hoursChart')?.getContext('2d');
        if (hoursCtx) {
            if (hoursChart) hoursChart.destroy();
            hoursChart = new Chart(hoursCtx, {
                type: 'line',
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: 'Study Hours',
                        data: data.hours_per_day,
                        borderColor: '#4f46e5',
                        backgroundColor: 'rgba(79, 70, 229, 0.1)',
                        tension: 0.4,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: { position: 'top' },
                        tooltip: { callbacks: { label: (ctx) => `${ctx.raw} hours` } }
                    }
                }
            });
        }
        
        // Tasks chart
        const tasksCtx = document.getElementById('tasksChart')?.getContext('2d');
        if (tasksCtx) {
            if (tasksChart) tasksChart.destroy();
            tasksChart = new Chart(tasksCtx, {
                type: 'bar',
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: 'Tasks Completed',
                        data: data.tasks_per_week,
                        backgroundColor: '#10b981',
                        borderRadius: 8
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: { position: 'top' }
                    }
                }
            });
        }
    } catch (error) {
        console.error('Error loading charts:', error);
    }
}

// Initialize charts
if (document.getElementById('hoursChart')) {
    loadCharts();
    // Refresh charts every minute
    setInterval(loadCharts, 60000);
}