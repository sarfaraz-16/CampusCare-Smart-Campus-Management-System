/**
 * CampusCare - Analytics & Chart.js Visualizations
 * Theme: Midnight Mineral × Arctic Signal
 */

document.addEventListener('DOMContentLoaded', () => {
    initAnalyticsCharts();
});

function initAnalyticsCharts() {
    const categoryCtx = document.getElementById('categoryDistributionChart');
    const statusCtx = document.getElementById('statusPipelineChart');
    const priorityCtx = document.getElementById('priorityMatrixChart');
    const departmentCtx = document.getElementById('departmentActivityChart');

    if (!categoryCtx) return;

    // Fetch dynamic aggregated data
    fetch('/api/analytics-data')
        .then(response => response.json())
        .then(data => {
            renderCategoryChart(categoryCtx, data.categories);
            if (statusCtx) renderStatusChart(statusCtx, data.status);
            if (priorityCtx) renderPriorityChart(priorityCtx, data.priority);
            if (departmentCtx) renderDepartmentChart(departmentCtx, data.departments);
        })
        .catch(error => {
            console.error('Error fetching analytics data:', error);
        });
}

function renderCategoryChart(ctx, catData) {
    // Arctic Signal & Midnight Mineral category palette
    const mineralPalette = [
        '#70D6C6', // Aqua (Arctic Signal)
        '#C3E88D', // Moss Lime (Primary)
        '#5EB5D6', // Sky Blue
        '#70C9A0', // Mint Resolved
        '#E5B45C', // Warning Amber
        '#F07868', // Hazard Coral
        '#8DA89F'  // Mineral Sage
    ];

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: catData.labels,
            datasets: [{
                data: catData.data,
                backgroundColor: mineralPalette.slice(0, catData.labels.length),
                borderWidth: 2,
                borderColor: '#10191B',
                hoverOffset: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '72%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#A7B6B0',
                        font: { family: 'Plus Jakarta Sans', size: 12 },
                        padding: 16,
                        usePointStyle: true,
                        pointStyle: 'circle'
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(25, 39, 41, 0.95)',
                    titleColor: '#F0F2E9',
                    bodyColor: '#A7B6B0',
                    borderColor: '#344847',
                    borderWidth: 1,
                    padding: 12,
                    boxPadding: 6,
                    usePointStyle: true
                }
            }
        }
    });
}

function renderStatusChart(ctx, statusData) {
    const statusColors = {
        'Reported': '#E5B45C',
        'Pending': '#E5B45C',
        'Under Review': '#70D6C6',
        'In Progress': '#5EB5D6',
        'Resolved': '#70C9A0',
        'Closed': '#6B7F7A'
    };

    const bgColors = statusData.labels.map(l => statusColors[l] || '#70D6C6');

    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: statusData.labels,
            datasets: [{
                data: statusData.data,
                backgroundColor: bgColors,
                borderColor: '#10191B',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#A7B6B0',
                        font: { family: 'Plus Jakarta Sans', size: 12 },
                        padding: 16,
                        usePointStyle: true
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(25, 39, 41, 0.95)',
                    titleColor: '#F0F2E9',
                    bodyColor: '#A7B6B0',
                    borderColor: '#344847',
                    borderWidth: 1,
                    padding: 12
                }
            }
        }
    });
}

function renderPriorityChart(ctx, prioData) {
    const priorityColors = {
        'Urgent': 'rgba(240, 120, 104, 0.9)',
        'High': 'rgba(229, 180, 92, 0.9)',
        'Medium': 'rgba(112, 214, 198, 0.9)',
        'Low': 'rgba(112, 201, 160, 0.9)'
    };

    const bgColors = prioData.labels.map(l => priorityColors[l] || '#70D6C6');

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: prioData.labels,
            datasets: [{
                label: 'Reported Issues',
                data: prioData.data,
                backgroundColor: bgColors,
                borderRadius: 8,
                borderSkipped: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(25, 39, 41, 0.95)',
                    titleColor: '#F0F2E9',
                    bodyColor: '#A7B6B0',
                    borderColor: '#344847',
                    borderWidth: 1,
                    padding: 10
                }
            },
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: '#A7B6B0', font: { family: 'Plus Jakarta Sans' } }
                },
                y: {
                    grid: { color: 'rgba(52, 72, 71, 0.4)' },
                    ticks: {
                        color: '#A7B6B0',
                        font: { family: 'JetBrains Mono' },
                        precision: 0
                    }
                }
            }
        }
    });
}

function renderDepartmentChart(ctx, deptData) {
    new Chart(ctx, {
        type: 'bar',
        indexAxis: 'y',
        data: {
            labels: deptData.labels,
            datasets: [{
                label: 'Issues Reported',
                data: deptData.data,
                backgroundColor: 'rgba(112, 214, 198, 0.8)',
                borderColor: '#70D6C6',
                borderWidth: 1,
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(25, 39, 41, 0.95)',
                    titleColor: '#F0F2E9',
                    bodyColor: '#A7B6B0',
                    borderColor: '#344847',
                    borderWidth: 1,
                    padding: 10
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(52, 72, 71, 0.4)' },
                    ticks: {
                        color: '#A7B6B0',
                        font: { family: 'JetBrains Mono' },
                        precision: 0
                    }
                },
                y: {
                    grid: { display: false },
                    ticks: { color: '#A7B6B0', font: { family: 'Plus Jakarta Sans' } }
                }
            }
        }
    });
}
