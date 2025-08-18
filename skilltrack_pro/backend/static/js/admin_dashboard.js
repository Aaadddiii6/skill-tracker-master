// static/js/admin_dashboard.js

document.addEventListener("DOMContentLoaded", async () => {
    try {
        // Fetch course status counts
        const stats = await apiFetch("/api/admin/stats");
        
        // Update status cards
        document.querySelector(".card.requested").textContent = `Requested: ${stats.requested}`;
        document.querySelector(".card.in-review").textContent = `In Review: ${stats.in_review}`;
        document.querySelector(".card.approved").textContent = `Approved: ${stats.approved}`;
        document.querySelector(".card.completed").textContent = `Completed: ${stats.completed}`;

        // Fetch table data for courses
        const courses = await apiFetch("/api/admin/courses");
        populateCoursesTable(courses);

    } catch (err) {
        console.error(err);
        alert("Failed to load admin dashboard data");
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

    courses.forEach(c => {
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
