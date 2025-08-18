// static/js/observer_dashboard.js

document.addEventListener("DOMContentLoaded", async () => {
    try {
        const stats = await apiFetch("/api/observer/stats");

        document.querySelector(".card.pending").textContent = `Pending: ${stats.pending}`;
        document.querySelector(".card.approved").textContent = `Approved: ${stats.approved}`;
        document.querySelector(".card.rejected").textContent = `Rejected: ${stats.rejected}`;

        const pendingDocs = await apiFetch("/api/observer/pending-docs");
        populateDocsTable(pendingDocs);

    } catch (err) {
        console.error(err);
        alert("Failed to load observer dashboard data");
    }
});

function populateDocsTable(docs) {
    const tableContainer = document.querySelector(".table-container");
    if (!tableContainer) return;

    let html = `<table>
        <thead>
            <tr>
                <th>Course Title</th>
                <th>Trainer</th>
                <th>Revision</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>`;

    docs.forEach(d => {
        html += `
            <tr>
                <td>${d.course_title}</td>
                <td>${d.trainer_name}</td>
                <td>${d.revision_number}</td>
                <td>${d.status}</td>
            </tr>`;
    });

    html += "</tbody></table>";
    tableContainer.innerHTML = html;
}
