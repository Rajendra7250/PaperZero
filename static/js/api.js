// ─── API Base URL ──────────────────────────────────────────────────────────────
const API = "/api";

// ─── Generic fetch helper ──────────────────────────────────────────────────────
async function apiFetch(endpoint, options = {}) {
  const headers = options.headers || {};
  if (!(options.body instanceof FormData) && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  try {
    const res = await fetch(API + endpoint, {
      ...options,
      headers
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || `HTTP ${res.status}`);
    }
    return await res.json();
  } catch (e) {
    console.error("API Error:", e.message);
    showToast("Error: " + e.message);
    throw e;
  }
}

// ─── Dashboard ────────────────────────────────────────────────────────────────
const Api = {
  getDashboard:      ()           => apiFetch("/dashboard"),
  getWorkflows:      ()           => apiFetch("/workflows"),
  addWorkflow:       (data)       => apiFetch("/workflows", { method: "POST", body: JSON.stringify(data) }),
  getApprovals:      (status="") => apiFetch(`/approvals?status=${status}`),
  updateApproval:    (id, action, rejection_reason="") => apiFetch(`/approvals/${id}`, { method: "PATCH", body: JSON.stringify({ action, rejection_reason }) }),
  submitApproval:    (data)       => apiFetch("/approvals", { method: "POST", body: JSON.stringify(data) }),
  submitApprovalForm:(formData)   => apiFetch("/approvals", { method: "POST", body: formData }),
  resubmitApproval:  (id, formData) => apiFetch(`/approvals/${id}/resubmit`, { method: "PUT", body: formData }),
  getDocuments:      (q="", cat="") => apiFetch(`/documents?q=${encodeURIComponent(q)}&category=${encodeURIComponent(cat)}`),
  getAnalytics:      ()           => apiFetch("/analytics"),
  getRecommendations:(priority="") => apiFetch(`/recommendations?priority=${priority}`),
  getLeaderboard:    ()           => apiFetch("/leaderboard"),
  submitExam:        (data)       => apiFetch("/exams/submit", { method: "POST", body: JSON.stringify(data) }),
  getExamResults:    (dept="", year="") => {
    let url = "/exams/results?";
    if (dept) url += `dept=${encodeURIComponent(dept)}&`;
    if (year) url += `year=${encodeURIComponent(year)}&`;
    return apiFetch(url);
  },
  uploadDocument:    (formData)   => apiFetch("/documents/upload", { method: "POST", body: formData }),
  // Online Exam (department-scoped)
  getOnlineExams:    (dept="", year="") => {
    let url = "/online-exams?";
    if (dept) url += `dept=${encodeURIComponent(dept)}&`;
    if (year) url += `year=${encodeURIComponent(year)}&`;
    return apiFetch(url);
  },
  createOnlineExam:  (data)       => apiFetch("/online-exams", { method: "POST", body: JSON.stringify(data) }),
  deleteOnlineExam:  (id)         => apiFetch(`/online-exams/${id}`, { method: "DELETE" }),
};
