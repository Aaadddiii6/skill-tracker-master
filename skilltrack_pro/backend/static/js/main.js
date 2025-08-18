// static/js/main.js

// Base API URL of your Flask backend
const API_BASE = window.location.origin;

// Get JWT token from local storage
function getToken() {
    return localStorage.getItem("token");
}

// Fetch wrapper with auth header
async function apiFetch(endpoint, options = {}) {
    const token = getToken();
    const headers = options.headers || {};
    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }
    options.headers = headers;

    const res = await fetch(`${API_BASE}${endpoint}`, options);
    if (!res.ok) {
        throw new Error(`API error ${res.status}`);
    }
    return await res.json();
}

// Logout function
function logout() {
    localStorage.removeItem("token");
    window.location.href = "/login";
}

// Attach logout if button present
document.addEventListener("DOMContentLoaded", () => {
    const logoutBtn = document.querySelector(".logout");
    if (logoutBtn) {
        logoutBtn.addEventListener("click", e => {
            e.preventDefault();
            logout();
        });
    }
});
