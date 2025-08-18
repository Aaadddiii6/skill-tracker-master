// static/js/trainer_dashboard.js

document.addEventListener("DOMContentLoaded", async () => {
    try {
        const stats = await apiFetch("/api/trainer/stats");

        document.querySelector(".card.requested").textContent = `Requested: ${stats.requested}`;
        document.querySelector(".card.in-review").textContent = `In Review: ${stats.in_review}`;
        document.querySelector(".card.approved").textContent = `Approved: ${stats.approved}`;
        document.querySelector(".card.completed").textContent = `Completed: ${stats.completed}`;

        const myCourses = await apiFetch("/api/trainer/my-courses");
        populateCoursesTable(myCourses);

    } catch (err) {
        console.error(err);
        alert("Failed to load trainer dashboard data");
    }
});

function populateCoursesTable(courses) {
    const tableContainer = document.querySelector(".table-container");
    if (!tableContainer) return;

    let html = `<table>
        <thead>
            <tr>
                <th>Title</th>
                <th>Status</th>
                <th>Last Update</th>
            </tr>
        </thead>
        <tbody>`;

    courses.forEach(c => {
        html += `
            <tr>
                <td>${c.title}</td>
                <td>${c.status}</td>
                <td>${c.updated_at}</td>
            </tr>`;
    });

    html += "</tbody></table>";
    tableContainer.innerHTML = html;
}
