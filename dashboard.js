/**
 * Personal Finance Advisor - Dashboard & Chart Engine
 */

document.addEventListener('DOMContentLoaded', () => {
  // Mobile Sidebar Toggle
  const sidebar = document.getElementById('sidebar');
  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebarBackdrop = document.getElementById('sidebarBackdrop');

  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener('click', () => {
      sidebar.classList.toggle('show');
      if (sidebarBackdrop) sidebarBackdrop.classList.toggle('show');
    });
  }

  if (sidebarBackdrop) {
    sidebarBackdrop.addEventListener('click', () => {
      sidebar.classList.remove('show');
      sidebarBackdrop.classList.remove('show');
    });
  }

  // Initialize Dashboard Charts if canvas elements exist
  initDashboardCharts();
});

const FINTECH_COLORS = [
  '#10b981', // Emerald
  '#3b82f6', // Blue
  '#f59e0b', // Amber
  '#8b5cf6', // Purple
  '#ec4899', // Pink
  '#06b6d4', // Cyan
  '#f97316', // Orange
  '#6366f1', // Indigo
  '#14b8a6', // Teal
  '#64748b'  // Slate
];

function initDashboardCharts() {
  const expenseBreakdownEl = document.getElementById('expenseBreakdownChart');
  const incomeVsExpenseEl = document.getElementById('incomeVsExpenseChart');
  const spendingTrendEl = document.getElementById('spendingTrendChart');

  if (!expenseBreakdownEl && !incomeVsExpenseEl && !spendingTrendEl) {
    return;
  }

  // Fetch chart data from our API
  fetch('/api/dashboard-charts' + window.location.search)
    .then(response => {
      if (!response.ok) throw new Error('Network error loading charts');
      return response.json();
    })
    .then(data => {
      // 1. Doughnut Chart: Expense Breakdown
      if (expenseBreakdownEl) {
        if (data.categories.labels.length === 0) {
          const ctx = expenseBreakdownEl.getContext('2d');
          new Chart(ctx, {
            type: 'doughnut',
            data: {
              labels: ['No Expenses Logged'],
              datasets: [{
                data: [1],
                backgroundColor: ['#e2e8f0'],
                borderWidth: 0
              }]
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              plugins: {
                tooltip: { enabled: false },
                legend: { position: 'bottom' }
              }
            }
          });
        } else {
          new Chart(expenseBreakdownEl, {
            type: 'doughnut',
            data: {
              labels: data.categories.labels,
              datasets: [{
                data: data.categories.values,
                backgroundColor: FINTECH_COLORS.slice(0, data.categories.labels.length),
                borderWidth: 2,
                borderColor: '#ffffff',
                hoverOffset: 6
              }]
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              plugins: {
                legend: {
                  position: 'bottom',
                  labels: {
                    boxWidth: 12,
                    font: { size: 12, family: 'Inter, sans-serif' }
                  }
                },
                tooltip: {
                  callbacks: {
                    label: function(context) {
                      const val = context.raw || 0;
                      return ` ${context.label}: ₹${val.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
                    }
                  }
                }
              },
              cutout: '70%'
            }
          });
        }
      }

      // 2. Bar Chart: Income vs Expenses
      if (incomeVsExpenseEl) {
        new Chart(incomeVsExpenseEl, {
          type: 'bar',
          data: {
            labels: data.six_months.labels,
            datasets: [
              {
                label: 'Income',
                data: data.six_months.income,
                backgroundColor: 'rgba(16, 185, 129, 0.85)',
                borderColor: '#10b981',
                borderWidth: 1,
                borderRadius: 6
              },
              {
                label: 'Expenses',
                data: data.six_months.expense,
                backgroundColor: 'rgba(239, 68, 68, 0.85)',
                borderColor: '#ef4444',
                borderWidth: 1,
                borderRadius: 6
              }
            ]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
              y: {
                beginAtZero: true,
                ticks: {
                  callback: function(value) {
                    return '₹' + Number(value).toLocaleString('en-IN');
                  },
                  font: { size: 11 }
                },
                grid: { color: '#f1f5f9' }
              },
              x: {
                grid: { display: false },
                font: { size: 11 }
              }
            },
            plugins: {
              legend: {
                position: 'top',
                labels: { boxWidth: 12 }
              },
              tooltip: {
                callbacks: {
                  label: function(context) {
                    const val = context.raw || 0;
                    return ` ${context.dataset.label}: ₹${val.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
                  }
                }
              }
            }
          }
        });
      }

      // 3. Line Chart: Spending Trend
      if (spendingTrendEl) {
        if (data.daily_trend.labels.length === 0) {
          data.daily_trend.labels = ['1st', '8th', '15th', '22nd', '28th'];
          data.daily_trend.values = [0, 0, 0, 0, 0];
        }

        const ctx = spendingTrendEl.getContext('2d');
        const gradient = ctx.createLinearGradient(0, 0, 0, 300);
        gradient.addColorStop(0, 'rgba(37, 99, 235, 0.3)');
        gradient.addColorStop(1, 'rgba(37, 99, 235, 0.0)');

        new Chart(ctx, {
          type: 'line',
          data: {
            labels: data.daily_trend.labels,
            datasets: [{
              label: 'Daily Spending',
              data: data.daily_trend.values,
              borderColor: '#2563eb',
              backgroundColor: gradient,
              fill: true,
              tension: 0.35,
              pointRadius: 4,
              pointHoverRadius: 6,
              pointBackgroundColor: '#2563eb'
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
              y: {
                beginAtZero: true,
                ticks: {
                  callback: function(value) {
                    return '₹' + Number(value).toLocaleString('en-IN');
                  },
                  font: { size: 11 }
                },
                grid: { color: '#f1f5f9' }
              },
              x: {
                grid: { display: false },
                font: { size: 11 }
              }
            },
            plugins: {
              legend: { display: false },
              tooltip: {
                callbacks: {
                  label: function(context) {
                    const val = context.raw || 0;
                    return ` Spent: ₹${val.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
                  }
                }
              }
            }
          }
        });
      }
    })
    .catch(err => {
      console.warn('Dashboard charts could not be initialized:', err);
    });
}
