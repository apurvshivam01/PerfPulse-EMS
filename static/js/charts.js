// ========================================================
// PerfPulse — Modern Chart.js SaaS Visualizations
// ========================================================

// Plugin to draw total count in the center of the Doughnut chart
const centerTextPlugin = {
  id: 'centerTextPlugin',
  beforeDraw: function (chart) {
    if (chart.config.type !== 'doughnut') return;
    const { width, height, ctx } = chart;
    ctx.restore();

    const data = chart.data.datasets[0].data || [];
    const total = data.reduce((a, b) => a + (Number(b) || 0), 0);

    ctx.font = '700 1.65rem Inter, sans-serif';
    ctx.textBaseline = 'middle';
    ctx.textAlign = 'center';
    ctx.fillStyle = '#18212F';
    const centerX = width / 2;
    const centerY = (height / 2) - 10;
    ctx.fillText(total, centerX, centerY);

    ctx.font = '500 0.72rem Inter, sans-serif';
    ctx.fillStyle = '#667085';
    ctx.fillText('EVALUATIONS', centerX, centerY + 22);

    ctx.save();
  }
};

Chart.register(centerTextPlugin);

/**
 * Initialize charts on the Admin Dashboard
 */
function initAdminCharts(deptData, categoryData, trendData) {
  // 1. Performance Overview Line Chart (Smooth Area)
  const trendCanvas = document.getElementById('performanceTrendChart');
  if (trendCanvas && trendData) {
    const ctx = trendCanvas.getContext('2d');
    const gradient = ctx.createLinearGradient(0, 0, 0, 240);
    gradient.addColorStop(0, 'rgba(91, 91, 214, 0.16)');
    gradient.addColorStop(1, 'rgba(91, 91, 214, 0.00)');

    window.adminTrendChartInstance = new Chart(ctx, {
      type: 'line',
      data: {
        labels: trendData.labels || [],
        datasets: [{
          label: 'Avg Performance',
          data: trendData.scores || [],
          borderColor: '#5B5BD6',
          borderWidth: 2.5,
          backgroundColor: gradient,
          fill: true,
          tension: 0.38,
          pointBackgroundColor: '#FFFFFF',
          pointBorderColor: '#5B5BD6',
          pointBorderWidth: 2,
          pointRadius: 4,
          pointHoverRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: '#18212F',
            titleFont: { size: 12, family: 'Inter', weight: '600' },
            bodyFont: { size: 12, family: 'Inter' },
            padding: 10,
            cornerRadius: 8,
            displayColors: false,
            callbacks: {
              label: (ctx) => `Score: ${ctx.parsed.y} / 100`
            }
          }
        },
        scales: {
          y: {
            min: 50,
            max: 100,
            ticks: {
              stepSize: 10,
              color: '#98A2B3',
              font: { size: 11, family: 'Inter' }
            },
            grid: {
              color: '#F2F4F7',
              drawBorder: false
            },
            border: { display: false }
          },
          x: {
            ticks: {
              color: '#98A2B3',
              font: { size: 11, family: 'Inter' }
            },
            grid: { display: false },
            border: { display: false }
          }
        }
      }
    });
  }

  // 2. Performance Distribution Doughnut Chart
  const categoryCanvas = document.getElementById('categoryDistributionChart');
  if (categoryCanvas && categoryData) {
    new Chart(categoryCanvas.getContext('2d'), {
      type: 'doughnut',
      data: {
        labels: ['Outstanding', 'Excellent', 'Good', 'Average', 'Needs Attention'],
        datasets: [{
          data: [
            categoryData.outstanding || 0,
            categoryData.excellent || 0,
            categoryData.good || 0,
            categoryData.average || 0,
            categoryData.needs_improvement || 0
          ],
          backgroundColor: [
            '#6FAF9A', // Sage green
            '#5B5BD6', // Primary indigo
            '#38BDF8', // Sky blue
            '#E9A178', // Peach
            '#D96C75'  // Soft red
          ],
          borderWidth: 2,
          borderColor: '#FFFFFF',
          hoverOffset: 4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              boxWidth: 8,
              boxHeight: 8,
              usePointStyle: true,
              pointStyle: 'circle',
              padding: 12,
              font: { size: 11, family: 'Inter', weight: '500' },
              color: '#667085'
            }
          },
          tooltip: {
            backgroundColor: '#18212F',
            cornerRadius: 8,
            padding: 10,
            bodyFont: { size: 11, family: 'Inter' }
          }
        },
        cutout: '72%'
      }
    });
  }

  // 3. Department Performance Bar Chart (if container exists)
  const deptCanvas = document.getElementById('deptPerformanceChart');
  if (deptCanvas && deptData) {
    new Chart(deptCanvas.getContext('2d'), {
      type: 'bar',
      data: {
        labels: deptData.labels || [],
        datasets: [{
          label: 'Avg Score',
          data: deptData.scores || [],
          backgroundColor: '#5B5BD6',
          borderRadius: 6,
          maxBarThickness: 36
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: '#18212F',
            cornerRadius: 8,
            callbacks: {
              label: (ctx) => `Avg: ${ctx.parsed.y} / 100`
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            max: 100,
            ticks: { stepSize: 20, color: '#98A2B3' },
            grid: { color: '#F2F4F7' },
            border: { display: false }
          },
          x: {
            grid: { display: false },
            ticks: { color: '#667085' },
            border: { display: false }
          }
        }
      }
    });
  }
}

/**
 * Initialize charts on the Manager Dashboard
 */
function initManagerCharts(teamMembers, memberScores) {
  const teamCanvas = document.getElementById('teamScoresChart');
  if (teamCanvas && teamMembers) {
    new Chart(teamCanvas.getContext('2d'), {
      type: 'bar',
      data: {
        labels: teamMembers,
        datasets: [{
          label: 'Performance Score',
          data: memberScores,
          backgroundColor: memberScores.map(score => {
            if (score >= 90) return '#6FAF9A';
            if (score >= 80) return '#5B5BD6';
            if (score >= 70) return '#38BDF8';
            if (score >= 60) return '#E9A178';
            return '#D96C75';
          }),
          borderRadius: 6,
          maxBarThickness: 32
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: '#18212F',
            cornerRadius: 8,
            callbacks: {
              label: (ctx) => `Score: ${ctx.parsed.y} / 100`
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            max: 100,
            ticks: { color: '#98A2B3' },
            grid: { color: '#F2F4F7' },
            border: { display: false }
          },
          x: {
            grid: { display: false },
            ticks: { color: '#667085' },
            border: { display: false }
          }
        }
      }
    });
  }
}

/**
 * Initialize charts on the Employee Dashboard
 */
function initEmployeeHistoryChart(periods, scores) {
  const empCanvas = document.getElementById('employeeHistoryChart');
  if (empCanvas && periods) {
    const ctx = empCanvas.getContext('2d');
    const gradient = ctx.createLinearGradient(0, 0, 0, 200);
    gradient.addColorStop(0, 'rgba(111, 175, 154, 0.20)');
    gradient.addColorStop(1, 'rgba(111, 175, 154, 0.00)');

    new Chart(ctx, {
      type: 'line',
      data: {
        labels: periods,
        datasets: [{
          label: 'Your Score',
          data: scores,
          borderColor: '#6FAF9A',
          borderWidth: 2.5,
          backgroundColor: gradient,
          fill: true,
          tension: 0.35,
          pointRadius: 4,
          pointBackgroundColor: '#FFFFFF',
          pointBorderColor: '#6FAF9A',
          pointBorderWidth: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: '#18212F',
            cornerRadius: 8
          }
        },
        scales: {
          y: {
            min: 50,
            max: 100,
            grid: { color: '#F2F4F7' },
            border: { display: false },
            ticks: { color: '#98A2B3' }
          },
          x: {
            grid: { display: false },
            border: { display: false },
            ticks: { color: '#667085' }
          }
        }
      }
    });
  }
}
