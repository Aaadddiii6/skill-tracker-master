// static/js/admin_dashboard.js

document.addEventListener("DOMContentLoaded", async () => {
  // Only run on admin dashboard page which contains the status cards
  const requestedEl = document.querySelector(".card.requested");
  const inReviewEl = document.querySelector(".card.in-review");
  const approvedEl = document.querySelector(".card.approved");
  const completedEl = document.querySelector(".card.completed");
  const rejectedEl = document.querySelector(".card.rejected");
  if (
    !requestedEl ||
    !inReviewEl ||
    !approvedEl ||
    !completedEl ||
    !rejectedEl
  ) {
    return; // Not the dashboard page
  }
  try {
    // Fetch course status counts
    const stats = await apiFetch("/api/admin/stats");

    // Update status cards
    requestedEl.textContent = `Requested: ${stats.requested}`;
    inReviewEl.textContent = `In Review: ${stats.in_review}`;
    approvedEl.textContent = `Approved: ${stats.approved}`;
    completedEl.textContent = `Completed: ${stats.completed}`;
    rejectedEl.textContent = `Rejected: ${stats.rejected}`;

    // Fetch table data for courses
    const courses = await apiFetch("/api/admin/courses");
    populateCoursesTable(courses);
  } catch (err) {
    console.error("Dashboard data fetch error:", err);
    // Show user-friendly error message
    const errorMsg = "Dashboard data loading failed. Please refresh the page.";
    console.log(errorMsg);
    // Don't show popup, just log to console
  }
});

function populateCoursesTable(courses) {
  const tableContainer = document.querySelector(".table-container");
  if (!tableContainer) return;

  let html = `<table>
        <thead>
            <tr>
                <th>Title</th>
                <th>Trainer</th>
                <th>Status</th>
                <th>Scheduled</th>
            </tr>
        </thead>
        <tbody>`;

  courses.forEach((c) => {
    html += `
            <tr>
                <td>${c.title}</td>
                <td>${c.trainer_name || "Unassigned"}</td>
                <td>${c.status}</td>
                <td>${c.scheduled_time || "-"}</td>
            </tr>`;
  });

  html += "</tbody></table>";
  tableContainer.innerHTML = html;
}
