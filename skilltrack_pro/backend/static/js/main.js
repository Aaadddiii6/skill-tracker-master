// static/js/main.js

// Base API URL of your Flask backend
const API_BASE = window.location.origin;

// Fetch wrapper for Flask-Login sessions
async function apiFetch(endpoint, options = {}) {
  // Flask-Login handles authentication via cookies/sessions
  // No need to manually add auth headers
  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    credentials: "same-origin", // Include cookies for session auth
  });

  if (!res.ok) {
    throw new Error(`API error ${res.status}`);
  }
  return await res.json();
}

// Logout function for Flask-Login
function logout() {
  // Flask-Login logout endpoint
  fetch("/auth/logout", {
    method: "POST",
    credentials: "same-origin",
  })
    .then(() => {
      window.location.href = "/auth/login";
    })
    .catch(() => {
      // Fallback to direct redirect
      window.location.href = "/auth/login";
    });
}

// Attach logout if button present
document.addEventListener("DOMContentLoaded", () => {
  const logoutBtn = document.querySelector(".logout");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", (e) => {
      e.preventDefault();
      logout();
    });
  }
});
