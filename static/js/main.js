// ========================================================
// Employee Performance Management System - Main JS
// ========================================================

document.addEventListener('DOMContentLoaded', function () {
  // 1. Mobile Sidebar Toggle
  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebar = document.getElementById('sidebar');
  const backdrop = document.getElementById('sidebarBackdrop');

  if (sidebarToggle && sidebar && backdrop) {
    sidebarToggle.addEventListener('click', function () {
      sidebar.classList.toggle('show');
      backdrop.classList.toggle('show');
    });

    backdrop.addEventListener('click', function () {
      sidebar.classList.remove('show');
      backdrop.classList.remove('show');
    });
  }

  // 2. Real-time Performance Score Calculator
  const taskInput = document.getElementById('task_completion');
  const qualityInput = document.getElementById('quality_of_work');
  const attendanceInput = document.getElementById('attendance');
  const teamworkInput = document.getElementById('teamwork');
  const managerInput = document.getElementById('manager_rating');

  const displayScore = document.getElementById('liveScoreDisplay');
  const displayCategory = document.getElementById('liveCategoryDisplay');
  const hiddenScore = document.getElementById('total_score');
  const hiddenCategory = document.getElementById('rating_category');

  function calculateScore() {
    if (!taskInput || !qualityInput || !attendanceInput || !teamworkInput || !managerInput) {
      return;
    }

    const t = parseFloat(taskInput.value) || 0;
    const q = parseFloat(qualityInput.value) || 0;
    const a = parseFloat(attendanceInput.value) || 0;
    const tw = parseFloat(teamworkInput.value) || 0;
    const m = parseFloat(managerInput.value) || 0;

    // Formula: (Task*0.30) + (Quality*0.25) + (Attendance*0.15) + (Teamwork*0.15) + (Manager*0.15)
    const score = (t * 0.30) + (q * 0.25) + (a * 0.15) + (tw * 0.15) + (m * 0.15);
    const roundedScore = Math.round(score * 100) / 100;

    let category = "Needs Improvement";
    let badgeClass = "badge-improvement";

    if (roundedScore >= 90) {
      category = "Outstanding";
      badgeClass = "badge-outstanding";
    } else if (roundedScore >= 80) {
      category = "Excellent";
      badgeClass = "badge-excellent";
    } else if (roundedScore >= 70) {
      category = "Good";
      badgeClass = "badge-good";
    } else if (roundedScore >= 60) {
      category = "Average";
      badgeClass = "badge-average";
    }

    if (displayScore) {
      displayScore.textContent = roundedScore.toFixed(2);
    }
    if (displayCategory) {
      displayCategory.textContent = category;
      displayCategory.className = 'badge-rating ' + badgeClass;
    }
    if (hiddenScore) {
      hiddenScore.value = roundedScore.toFixed(2);
    }
    if (hiddenCategory) {
      hiddenCategory.value = category;
    }
  }

  // Attach live calculation listeners
  [taskInput, qualityInput, attendanceInput, teamworkInput, managerInput].forEach(function (input) {
    if (input) {
      input.addEventListener('input', calculateScore);
    }
  });

  // Calculate once on initial load if elements exist
  if (taskInput) {
    calculateScore();
  }

  // 3. Quick Table Filter Search & Global Quick Search
  const tableSearchInput = document.getElementById('tableSearchInput');
  const globalQuickSearch = document.getElementById('globalQuickSearch');

  function filterTables(query) {
    const filterValue = query.toLowerCase().trim();
    const rows = document.querySelectorAll('.saas-table tbody tr, .filterable-table tbody tr');
    rows.forEach(function (row) {
      const text = row.innerText.toLowerCase();
      row.style.display = text.includes(filterValue) ? '' : 'none';
    });
  }

  if (tableSearchInput) {
    tableSearchInput.addEventListener('input', function () {
      filterTables(this.value);
    });
  }

  if (globalQuickSearch) {
    globalQuickSearch.addEventListener('input', function () {
      const tables = document.querySelectorAll('.saas-table tbody tr, .filterable-table tbody tr');
      if (tables.length > 0) {
        filterTables(this.value);
      }
    });

    globalQuickSearch.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') {
        e.preventDefault();
        const q = encodeURIComponent(this.value.trim());
        if (q) {
          window.location.href = '/employees?search=' + q;
        }
      }
    });
  }

  // 4. Auto-dismiss alerts after 5 seconds
  const alerts = document.querySelectorAll('.alert.alert-dismissible');
  alerts.forEach(function (alert) {
    setTimeout(function () {
      try {
        const bsAlert = new bootstrap.Alert(alert);
        bsAlert.close();
      } catch (e) {}
    }, 5000);
  });
});

// Confirmation helper for delete operations
function confirmAction(message, formId) {
  if (confirm(message || "Are you sure you want to perform this action?")) {
    document.getElementById(formId).submit();
  }
}
