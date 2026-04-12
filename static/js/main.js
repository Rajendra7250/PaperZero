// ─── Toast ────────────────────────────────────────────────────────────────────
function showToast(msg) {
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), 3000);
}

// ─── Session (simulated) ───────────────────────────────────────────────────────
const SESSION_KEY = "ecoflow.session";

function getSession() {
  try {
    const raw = localStorage.getItem(SESSION_KEY);
    if (!raw) return null;
    const s = JSON.parse(raw);
    if (!s || !s.role || !s.name) return null;
    return s;
  } catch {
    return null;
  }
}

function clearSession() {
  localStorage.removeItem(SESSION_KEY);
}

function requireSession() {
  const s = getSession();
  if (!s) {
    window.location.href = "/login";
    return null;
  }
  return s;
}

function setWelcome(name) {
  const el = document.getElementById("welcomeMsg");
  if (el) el.textContent = name ? `Welcome, ${name}` : "";
}

// AFTER
function initLogout() {
  const btn = document.getElementById("logoutBtn");
  if (!btn) return;
  btn.addEventListener("click", async () => {
    try {
      await fetch("/api/logout", { method: "POST", credentials: "same-origin" });
    } catch (_) {}
    clearSession();
    window.location.href = "/login";
  });
}

// ─── Clock ────────────────────────────────────────────────────────────────────
function startClock() {
  const el = document.getElementById("clock");
  const tick = () => {
    el.textContent = new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });
  };
  tick();
  setInterval(tick, 1000);
}

function getActivePage() {
  const active = document.querySelector(".page.active");
  return active ? active.id.replace("page-", "") : null;
}

function setActivePage(pageId) {
  const target = document.getElementById("page-" + pageId);
  if (!target) return;

  document.querySelectorAll(".page").forEach((p) => p.classList.remove("active"));
  document.querySelectorAll(".nav-btn").forEach((b) => b.classList.remove("active"));

  target.classList.add("active");
  const navBtn = document.querySelector(`.nav-btn[data-page="${pageId}"]`);
  if (navBtn) navBtn.classList.add("active");

  if (pageId === "dashboard")       loadDashboard();
  if (pageId === "workflow")        loadWorkflows();
  if (pageId === "approvals")       loadApprovals();
  if (pageId === "documents")       loadDocuments();
  if (pageId === "analytics")       loadAnalytics();
  if (pageId === "recommendations") loadRecommendations();
  if (pageId === "leaderboard")     loadLeaderboard();
  if (pageId === "exams")           loadExams();
  if (pageId === "uploads")         loadUploads();
  if (pageId === "nexus")           initNexus();
}

// ─── Nexus AI Chat ────────────────────────────────────────────────────────────
async function initNexus() {
  const infoEl = document.getElementById("nexusModelInfo");
  if (!infoEl) return;
  
  try {
    const res = await fetch("/api/chat/info");
    const data = await res.json();
    if (data.model) {
      infoEl.innerHTML = `Model: <b>${data.model}</b>`;
      infoEl.className = "badge badge-done";
    } else {
      infoEl.innerHTML = "Offline - Needs API Key";
      infoEl.className = "badge badge-high";
    }
  } catch (e) {
    infoEl.innerHTML = "Offline - Server Error";
    infoEl.className = "badge badge-high";
  }
}

async function sendNexusMessage() {
  const input = document.getElementById("nexusInput");
  const chatBox = document.getElementById("nexusChatBox");
  if (!input || !chatBox) return;

  const msg = input.value.trim();
  if (!msg) return;

  // Add user message to UI
  chatBox.innerHTML += `
    <div style="align-self: flex-end; background: var(--primary); color: #fff; padding: 12px 16px; border-radius: 12px; border-bottom-right-radius: 2px; max-width: 80%; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
      <div style="line-height: 1.5;">${msg}</div>
    </div>
  `;
  
  input.value = "";
  chatBox.scrollTop = chatBox.scrollHeight;

  // Add typing indicator
  const typingId = "typing-" + Date.now();
  chatBox.innerHTML += `
    <div id="${typingId}" style="align-self: flex-start; background: #fff; padding: 12px 16px; border-radius: 12px; border-bottom-left-radius: 2px; border: 1px solid var(--border); color: var(--text-muted); font-style: italic;">
      Nexus is typing...
    </div>
  `;
  chatBox.scrollTop = chatBox.scrollHeight;

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt: msg })
    });
    const data = await res.json();
    
    document.getElementById(typingId).remove();
    
    // Add bot response to UI
    let botMsg = data.response;
    if (data.error) botMsg = `<i>Error: ${data.error}</i>`;
    
    // Simple markdown formatting for bold text from Gemini
    botMsg = botMsg.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>');
    botMsg = botMsg.replace(/\n/g, '<br>');

    chatBox.innerHTML += `
      <div style="align-self: flex-start; background: #fff; padding: 12px 16px; border-radius: 12px; border-bottom-left-radius: 2px; max-width: 80%; border: 1px solid var(--border); box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
        <div style="font-weight: 600; color: var(--primary); margin-bottom: 4px; font-size: 0.85rem;">Nexus AI</div>
        <div style="line-height: 1.5; color: var(--text);">${botMsg}</div>
      </div>
    `;
    
  } catch (err) {
    document.getElementById(typingId).remove();
    chatBox.innerHTML += `
      <div style="align-self: flex-start; background: #fff; padding: 12px 16px; border-radius: 12px; border-bottom-left-radius: 2px; max-width: 80%; border: 1px dashed var(--danger); color: var(--danger);">
        Could not connect to Nexus servers.
      </div>
    `;
  }
  
  chatBox.scrollTop = chatBox.scrollHeight;
}

// ─── Page Navigation ──────────────────────────────────────────────────────────
function initNavigation() {
  document.querySelectorAll(".nav-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const pageId = btn.dataset.page;
      setActivePage(pageId);
    });
  });
}

// ─── Tab switching ────────────────────────────────────────────────────────────
function initTabs() {
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const tabId = btn.dataset.tab;
      document.querySelectorAll('[id^="tab-"]').forEach((t) => (t.style.display = "none"));
      document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
      document.getElementById("tab-" + tabId).style.display = "";
      btn.classList.add("active");
    });
  });
}

function applyRoleUI(session) {
  const isStudent = session.role === "student";
  const isAdminOrHOD = ["admin", "hod"].includes(session.role);
  setWelcome(session.name);
  console.log("Current User Role:", session.role);

  if (isStudent) {
    document.querySelector('[data-page="workflow"]')?.setAttribute("style", "display:none");
    document.querySelector('[data-page="analytics"]')?.setAttribute("style", "display:none");
    document.querySelector('[data-page="recommendations"]')?.setAttribute("style", "display:none");
    document.querySelector('[data-page="dashboard"]')?.setAttribute("style", "display:none");
    
    const streakMsg = document.getElementById("streakMsg");
    if(streakMsg) {
      streakMsg.style.display = "inline-block";
      document.getElementById("streakCount").textContent = session.streak_count || 0;
    }
  } else {
    // Both students and non-students can see the Exams section
    document.querySelector('[data-page="exams"]').style.display = "";
  }

  // Nav visibility
  const dashboardBtn = document.querySelector('.nav-btn[data-page="dashboard"]');
  const analyticsBtn = document.querySelector('.nav-btn[data-page="analytics"]');
  const insightsBtn = document.querySelector('.nav-btn[data-page="recommendations"]');
  const workflowBtn = document.querySelector('.nav-btn[data-page="workflow"]');
  const documentsBtn = document.querySelector('.nav-btn[data-page="documents"]');

  if (dashboardBtn) dashboardBtn.style.display = isAdminOrHOD ? "" : "none";
  if (analyticsBtn) analyticsBtn.style.display = isAdminOrHOD ? "" : "none";
  if (insightsBtn) insightsBtn.style.display = isAdminOrHOD ? "" : "none";
  if (workflowBtn) workflowBtn.style.display = session.role === "admin" ? "" : "none";
  if (documentsBtn) documentsBtn.style.display = "none";
  
  // If not admin/hod tries to land on dashboard, redirect to approvals
  if (!isAdminOrHOD && getActivePage() === "dashboard") {
    setActivePage("approvals");
  }

  // Approvals becomes "My Requests" for students
  const approvalsBtn = document.querySelector('.nav-btn[data-page="approvals"]');
  if (approvalsBtn) approvalsBtn.textContent = isStudent ? "My Requests" : "Approvals";

  // In approvals page: students should not see pending approvals queue (approvals queue is HOD/staff)
  const approvalsPage = document.getElementById("page-approvals");
  if (approvalsPage) {
    const title = approvalsPage.querySelector("h1");
    const subtitle = approvalsPage.querySelector(".subtitle");
    if (title) title.textContent = isStudent ? "My Requests" : "Digital Approval System";
    if (subtitle) {
      subtitle.textContent = isStudent
        ? "Submit and track your requests — no printing needed"
        : "E-signatures and electronic approvals — no printing needed";
    }

    const pendingTabBtn = approvalsPage.querySelector('.tab-btn[data-tab="pending"]');
    const pendingTab = document.getElementById("tab-pending");
    if (pendingTabBtn) pendingTabBtn.style.display = isStudent ? "none" : "";
    if (pendingTab) pendingTab.style.display = isStudent ? "none" : "";

    // Default approvals tab for students = New Request
    if (isStudent) {
      approvalsPage.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
      const newReqBtn = approvalsPage.querySelector('.tab-btn[data-tab="newreq"]');
      if (newReqBtn) newReqBtn.classList.add("active");

      document.querySelectorAll('[id^="tab-"]').forEach((t) => (t.style.display = "none"));
      const newReqTab = document.getElementById("tab-newreq");
      if (newReqTab) newReqTab.style.display = "";
    }
  }

  // Default landing page
  if (isAdminOrHOD) {
    setActivePage("dashboard");
  } else {
    setActivePage("approvals");
  }
}

// ─── Dashboard ────────────────────────────────────────────────────────────────
async function loadDashboard() {
  console.log("Loading Dashboard...");
  const container = document.getElementById("dashStats");
  if (!container) return;
  
  try {
    const data = await Api.getDashboard();
    console.log("Dashboard Data:", data);

    document.getElementById("s-saved").textContent   = (data.paper_saved || 0).toLocaleString("en-IN");
    document.getElementById("s-cost").textContent    = "₹" + (data.cost_saved || 0).toLocaleString("en-IN");
    document.getElementById("s-pending").textContent = data.pending_approvals || 0;
    document.getElementById("s-co2").textContent     = data.co2_avoided || 0;
    
    const wfEl = document.getElementById("s-wf");
    if (wfEl) {
      wfEl.innerHTML = `${data.digitized_workflows || 0}<span style="font-size:1rem;color:var(--text-muted)">/${data.total_workflows || 0}</span>`;
    }

    renderProgressList("progressList", data.progress || []);

    const tbody = document.getElementById("activityTable");
    if (tbody && data.activity) {
      tbody.innerHTML = data.activity
        .map((a) => `
          <tr>
            <td>${a.event}</td>
            <td>${a.module}</td>
            <td>${a.by}</td>
            <td style="color:var(--text-muted)">${a.time}</td>
            <td><span class="badge ${a.status === "done" ? "badge-success" : "badge-warning"}">${a.status}</span></td>
          </tr>`)
        .join("");
    }

    const analytics = await Api.getAnalytics();
    renderBarChart("monthChart", analytics.monthly_labels || [], analytics.monthly_usage || [], "var(--primary)");
  } catch (err) {
    console.error("Dashboard error:", err);
  }
}

// ─── Workflows ────────────────────────────────────────────────────────────────
async function loadWorkflows() {
  const container = document.getElementById("workflowList");
  if (!container) return;
  const workflows = await Api.getWorkflows();
  renderWorkflowList(workflows);
}

function renderWorkflowList(workflows) {
  const container = document.getElementById("workflowList");
  container.innerHTML = workflows
    .map((w) => {
      const cls       = w.score > 70 ? "red"       : w.score > 40 ? "amber"      : "green";
      const badgeCls  = w.score > 70 ? "badge-high" : w.score > 40 ? "badge-med"  : "badge-done";
      const badgeText = w.score > 70 ? "High Priority" : w.score > 40 ? "Medium" : "Digitized";
      const fillCls   = w.score > 70 ? ""           : w.score > 40 ? "med"        : "low";
      return `
        <div class="workflow-item">
          <div class="wf-icon ${cls}">${w.digitized ? "✅" : "📋"}</div>
          <div class="wf-body">
            <div class="wf-title">${w.name}</div>
            <div class="wf-meta">${w.dept} • ${w.monthly} sheets/month</div>
          </div>
          <span class="badge ${badgeCls}">${badgeText}</span>
          <div class="wf-bar-wrap">
            <div class="wf-bar-label">Paper dependency</div>
            <div class="wf-bar-bg">
              <div class="wf-bar-fill ${fillCls}" style="width:${w.score}%"></div>
            </div>
          </div>
        </div>`;
    })
    .join("");
}

function initWorkflowForm() {
  const scanBtn = document.getElementById("scanBtn");
  const addBtn = document.getElementById("addWfBtn");
  if (!scanBtn || !addBtn) return;  // Elements don't exist for non-admin roles

  scanBtn.addEventListener("click", () => {
    showToast("Scanning institutional workflows...");
    setTimeout(() => showToast("Scan complete — workflows analyzed"), 1500);
  });

  addBtn.addEventListener("click", async () => {
    const name  = document.getElementById("wfName").value.trim();
    const dept  = document.getElementById("wfDept").value;
    const paper = document.getElementById("wfPaper").value;
    if (!name) { showToast("Please enter a workflow name"); return; }

    await Api.addWorkflow({ name, dept, monthly: parseInt(paper) || 100 });
    document.getElementById("wfName").value  = "";
    document.getElementById("wfPaper").value = "";
    showToast("Workflow added \u2705");
    loadWorkflows();
  });
}

// ─── Approvals ────────────────────────────────────────────────────────────────
let approvalDataMap = {};  // Cache for resubmit lookups

async function loadApprovals() {
  const session = requireSession();
  const isStudent = session && session.role === "student";

  try {
    if (isStudent) {
      const allRequests = await Api.getApprovals("");
      allRequests.forEach(a => { approvalDataMap[a.id] = a; });
      // Hide table view, show card tracker
      const tableWrap = document.getElementById("approvedTableWrap");
      if (tableWrap) tableWrap.style.display = "none";
      renderStudentTracker(allRequests);
    } else {
      const pending  = await Api.getApprovals("pending");
      const allItems = await Api.getApprovals("");
      const resolved = allItems.filter(a => a.status !== "pending");
      // Show table view, hide student tracker
      const tableWrap = document.getElementById("approvedTableWrap");
      if (tableWrap) tableWrap.style.display = "";
      const tracker = document.getElementById("studentTracker");
      if (tracker) tracker.innerHTML = "";
      renderPendingApprovals(pending);
      renderApprovedTable(resolved);
    }
  } catch (err) {
    console.error("Error loading approvals:", err);
    showToast("Error loading records: " + err.message, "danger");
  }
}

// ─── Student Card-Based Status Tracker ────────────────────────────────────────
function renderStudentTracker(items) {
  const container = document.getElementById("studentTracker");
  if (!container) return;

  if (items.length === 0) {
    container.innerHTML = `
      <div style="text-align:center; padding:3rem; color:var(--text-muted);">
        <div style="font-size:3rem; margin-bottom:1rem;">📭</div>
        <h3 style="margin:0 0 8px;">No requests yet</h3>
        <p style="margin:0;">Submit your first paperless request from the "New Request" tab!</p>
      </div>`;
    return;
  }

  container.innerHTML = items.map(a => {
    const isPending  = a.status === 'pending';
    const isApproved = a.status === 'approved';
    const isRejected = a.status === 'rejected';
    const isResolved = isApproved || isRejected;

    const borderColor = isApproved ? 'var(--primary)' : isPending ? '#e8a020' : '#dc3545';
    const badgeClass  = isApproved ? 'badge-done' : isPending ? 'badge-med' : 'badge-high';
    const badgeLabel  = a.status.charAt(0).toUpperCase() + a.status.slice(1);

    // Pipeline step styles
    const dotDone = `width:30px;height:30px;border-radius:50%;display:flex;align-items:center;justify-content:center;color:#fff;font-size:0.75rem;font-weight:700;`;
    const dotEmpty = dotDone + `background:var(--border);color:var(--text-muted);`;

    return `
    <div class="card" style="margin-bottom:1rem; border-left:4px solid ${borderColor}; animation: fadein 0.4s ease-out;">
      <!-- Header -->
      <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:0.8rem;">
        <div>
          <h3 style="margin:0 0 4px; font-size:1.05rem; font-weight:600;">${a.doc}</h3>
          <div style="color:var(--text-muted); font-size:0.82rem;">
            Approver: <strong>${a.dept}</strong> &bull; Submitted: ${a.submitted || '\u2014'}
          </div>
        </div>
        <span class="badge ${badgeClass}" style="font-size:0.78rem; padding:5px 14px; white-space:nowrap;">${badgeLabel}</span>
      </div>

      <!-- Status Pipeline -->
      <div style="display:flex; align-items:center; margin:1rem 0; padding:0.8rem 1rem; background:var(--surface2); border-radius:10px; gap:0;">
        <div style="display:flex; flex-direction:column; align-items:center; gap:4px; min-width:60px;">
          <div style="${dotDone}background:var(--primary);">\u2713</div>
          <span style="font-size:0.72rem; font-weight:600; color:var(--primary);">Submitted</span>
        </div>
        <div style="flex:1; height:3px; background:${isPending || isResolved ? 'var(--primary)' : 'var(--border)'}; border-radius:2px;"></div>
        <div style="display:flex; flex-direction:column; align-items:center; gap:4px; min-width:70px;">
          <div style="${isPending ? dotDone + 'background:#e8a020;' : isResolved ? dotDone + 'background:var(--primary);' : dotEmpty}">${isResolved ? '\u2713' : isPending ? '\u23F3' : ''}</div>
          <span style="font-size:0.72rem; font-weight:${isPending ? '700' : '500'}; color:${isPending ? '#e8a020' : 'var(--text-muted)'};">${isPending ? 'Under Review' : 'Reviewed'}</span>
        </div>
        <div style="flex:1; height:3px; background:${isApproved ? 'var(--primary)' : isRejected ? '#dc3545' : 'var(--border)'}; border-radius:2px;"></div>
        <div style="display:flex; flex-direction:column; align-items:center; gap:4px; min-width:60px;">
          <div style="${isApproved ? dotDone + 'background:var(--primary);' : isRejected ? dotDone + 'background:#dc3545;' : dotEmpty}">${isApproved ? '\u2713' : isRejected ? '\u2717' : ''}</div>
          <span style="font-size:0.72rem; font-weight:${isResolved ? '700' : '500'}; color:${isApproved ? 'var(--primary)' : isRejected ? '#dc3545' : 'var(--text-muted)'};">${isApproved ? 'Approved' : isRejected ? 'Rejected' : 'Decision'}</span>
        </div>
      </div>

      <!-- Details -->
      <div style="display:flex; flex-wrap:wrap; gap:0.6rem 1.5rem; font-size:0.88rem; color:var(--text-muted);">
        ${a.remarks ? `<div><strong>Remarks:</strong> ${a.remarks}</div>` : ''}
        ${a.attachment ? `<div><a href="/static/uploads/approvals/${a.attachment}" target="_blank" style="color:var(--primary); text-decoration:none; font-weight:500;">\uD83D\uDCCE View Attachment</a></div>` : ''}
        ${a.resolved_at ? `<div><strong>Resolved:</strong> ${a.resolved_at}</div>` : ''}
      </div>

      ${isRejected && a.rejection_reason ? `
      <!-- Rejection Reason -->
      <div style="margin-top:1rem; padding:0.9rem 1rem; background:#fef2f2; border-radius:10px; border-left:4px solid #dc3545;">
        <div style="font-weight:600; color:#dc3545; margin-bottom:4px; font-size:0.88rem;">\u274C Reason for Rejection</div>
        <div style="color:#7f1d1d; font-size:0.88rem; line-height:1.5;">${a.rejection_reason}</div>
      </div>` : ''}

      ${isRejected ? `
      <!-- Resubmit Button -->
      <div style="margin-top:1rem; display:flex; justify-content:flex-end;">
        <button class="btn btn-primary btn-sm" onclick="openResubmitForm('${a.id}')" style="padding:8px 18px;">
          \u270F\uFE0F Edit & Resubmit
        </button>
      </div>` : ''}
    </div>`;
  }).join('');
}

// ─── Staff: Pending Queue ─────────────────────────────────────────────────────
function renderPendingApprovals(items) {
  const container = document.getElementById("approvalQueue");
  if (!container) return;

  if (items.length === 0) {
    container.innerHTML = `<div style="text-align:center;padding:2rem;color:var(--text-muted)">No pending approvals \uD83C\uDF89</div>`;
    return;
  }

  container.innerHTML = items
    .map(
      (a) => `
      <div class="approval-item" id="approval-${a.id}">
        <div class="avatar">${a.initials}</div>
        <div class="approval-body">
          <div class="approval-title">${a.doc}</div>
          <div class="approval-meta">
            ${a.name} \u2022 ${a.dept}
            ${a.urgent ? ' \u2022 <span style="color:var(--danger);font-weight:600">Urgent</span>' : ""}
          </div>
          ${a.remarks ? `<div class="approval-remarks" style="margin-top:8px; padding:8px; background:var(--bg-alt); border-radius:6px; font-size:0.85rem; border-left:3px solid var(--accent);">${a.remarks}</div>` : ""}
          ${a.attachment ? `<div style="margin-top:6px;"><a href="/static/uploads/approvals/${a.attachment}" target="_blank" style="color:var(--primary); font-size:0.85rem; text-decoration:none;">\uD83D\uDCCE Attachment</a></div>` : ""}
        </div>
        <div class="approval-actions" id="actions-${a.id}">
          <button class="btn-approve" onclick="handleApproval('${a.id}', 'approve')">Approve \u2713</button>
          <button class="btn-reject"  onclick="showRejectDialog('${a.id}')">Reject \u2717</button>
        </div>
      </div>`
    )
    .join("");
}

// ─── Staff: Approved/Rejected Table ───────────────────────────────────────────
function renderApprovedTable(items) {
  const tbody = document.getElementById("approvedTable");
  if (!tbody) return;

  if (items.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;padding:2rem;color:var(--text-muted)">No requests found.</td></tr>`;
    return;
  }

  tbody.innerHTML = items
    .map(
      (a) => `
      <tr>
        <td>${a.doc}</td>
        <td>${a.name}</td>
        <td>${a.dept}</td>
        <td>${a.resolved_at || a.submitted}</td>
        <td>
          <span class="badge ${a.status === 'approved' ? 'badge-done' : a.status === 'pending' ? 'badge-med' : 'badge-high'}">
            ${a.status.charAt(0).toUpperCase() + a.status.slice(1)}
          </span>
        </td>
      </tr>`
    )
    .join("");
}

// ─── Approve (direct) ─────────────────────────────────────────────────────────
async function handleApproval(id, action) {
  await Api.updateApproval(id, action);
  const el = document.getElementById("approval-" + id);
  if (el) { el.style.opacity = "0.35"; el.style.pointerEvents = "none"; }
  showToast(action === 'approve' ? "\u2705 Approved digitally — no paper needed!" : "\u274c Request rejected.");
  setTimeout(() => loadApprovals(), 600);
}

// ─── Reject with Reason Dialog ────────────────────────────────────────────────
function showRejectDialog(id) {
  const actionsDiv = document.getElementById("actions-" + id);
  if (!actionsDiv) return;

  actionsDiv.innerHTML = `
    <div style="display:flex; flex-direction:column; gap:8px; width:100%; min-width:220px;">
      <textarea id="reject-reason-${id}" rows="2" placeholder="Reason for rejection (required)..."
        style="width:100%; padding:8px 10px; border:1px solid var(--border); border-radius:8px; font-size:0.85rem; resize:vertical; font-family:inherit;"></textarea>
      <div style="display:flex; gap:8px; justify-content:flex-end;">
        <button class="btn btn-sm" style="background:var(--surface2); color:var(--text); border:1px solid var(--border);"
          onclick="loadApprovals()">Cancel</button>
        <button class="btn-reject" style="padding:6px 14px; font-size:0.85rem;"
          onclick="confirmReject('${id}')">Confirm Reject</button>
      </div>
    </div>`;
}

async function confirmReject(id) {
  const reason = document.getElementById(`reject-reason-${id}`)?.value.trim();
  if (!reason) {
    showToast("Please provide a reason for rejection.", "danger");
    return;
  }
  await Api.updateApproval(id, "reject", reason);
  const el = document.getElementById("approval-" + id);
  if (el) { el.style.opacity = "0.35"; el.style.pointerEvents = "none"; }
  showToast("Request rejected with reason.");
  setTimeout(() => loadApprovals(), 600);
}

// ─── Submit Request (with file upload) ────────────────────────────────────────
async function emergencySubmitRequest() {
  const btn = document.getElementById("submitApprovalBtn");
  if (btn.disabled) return;

  const resubmitId  = document.getElementById("resubmitId")?.value || "";
  const submittedBy = document.getElementById("submittedBy")?.value.trim();
  const docType     = document.getElementById("docType")?.value;
  const dept        = document.getElementById("approverSelect")?.value;
  const remarks     = document.getElementById("docRemarks")?.value;
  const fileInput   = document.getElementById("approvalFileInput");
  const file        = fileInput?.files[0] || null;

  if (!submittedBy) {
    showToast("Please enter your name", "danger");
    return;
  }

  try {
    btn.disabled = true;
    btn.textContent = resubmitId ? "Resubmitting..." : "Submitting...";

    const formData = new FormData();
    formData.append("submitted_by", submittedBy);
    formData.append("doc_type", docType);
    formData.append("dept", dept);
    formData.append("remarks", remarks || "");
    if (file) formData.append("attachment", file);

    if (resubmitId) {
      // Resubmit rejected request
      await Api.resubmitApproval(resubmitId, formData);
      showToast("Request resubmitted for approval \u2705");
    } else {
      // New submission
      await Api.submitApprovalForm(formData);
      showToast("Request submitted for approval \u2705");
    }

    // Reset form
    document.getElementById("submittedBy").value = "";
    document.getElementById("docRemarks").value  = "";
    document.getElementById("resubmitId").value  = "";
    if (fileInput) fileInput.value = "";
    document.getElementById("fileUploadLabel").textContent = "\uD83D\uDCCE Click to attach a file (PDF, Image, Doc)";
    document.getElementById("newReqTitle").textContent = "Submit for Approval";
    btn.textContent = "Submit Request";

    loadApprovals();

    // Switch to My Approvals tab
    const myApprovalsBtn = document.querySelector('.tab-btn[data-tab="approved"]');
    if (myApprovalsBtn) myApprovalsBtn.click();
  } catch (err) {
    console.error("Submission error:", err);
    showToast("Submission failed: " + err.message, "danger");
  } finally {
    btn.disabled = false;
    if (!document.getElementById("resubmitId")?.value) {
      btn.textContent = "Submit Request";
    }
  }
}

// ─── Resubmit Flow ────────────────────────────────────────────────────────────
function openResubmitForm(id) {
  const a = approvalDataMap[id];
  if (!a) { showToast("Could not find request data."); return; }

  // Pre-fill the New Request form with existing data
  document.getElementById("docType").value      = a.doc;
  document.getElementById("submittedBy").value   = a.name;
  document.getElementById("approverSelect").value = a.dept;
  document.getElementById("docRemarks").value    = a.remarks || "";
  document.getElementById("resubmitId").value    = a.id;

  // Update form title and button
  document.getElementById("newReqTitle").textContent = "\u270F\uFE0F Edit & Resubmit Request";
  const btn = document.getElementById("submitApprovalBtn");
  btn.textContent = "Resubmit Request";

  // Update file label if there's an existing attachment
  if (a.attachment) {
    document.getElementById("fileUploadLabel").innerHTML =
      `\uD83D\uDCCE Current: <strong>${a.attachment.substring(9)}</strong> (select new file to replace)`;
  }

  // Switch to New Request tab
  const newReqBtn = document.querySelector('.tab-btn[data-tab="newreq"]');
  if (newReqBtn) newReqBtn.click();

  // Scroll to form
  document.getElementById("newRequestCard")?.scrollIntoView({ behavior: "smooth", block: "start" });
}

function initApprovalForm() {
  // File upload label update
  const fileInput = document.getElementById("approvalFileInput");
  if (fileInput) {
    fileInput.addEventListener("change", () => {
      const label = document.getElementById("fileUploadLabel");
      if (fileInput.files[0]) {
        const name = fileInput.files[0].name;
        const size = (fileInput.files[0].size / 1024 / 1024).toFixed(1);
        label.innerHTML = `\uD83D\uDCCE <strong>${name}</strong> (${size} MB) &mdash; <span style="color:var(--primary); cursor:pointer;">Change</span>`;
      } else {
        label.textContent = "\uD83D\uDCCE Click to attach a file (PDF, Image, Doc)";
      }
    });
  }
}

// ─── Documents ────────────────────────────────────────────────────────────────
async function loadDocuments(q = "", cat = "") {
  const docs = await Api.getDocuments(q, cat);
  renderDocGrid(docs);
}

function renderDocGrid(docs) {
  const iconMap = { PDF: "📄", XLSX: "📊", DOCX: "📝", CSV: "📋" };
  const container = document.getElementById("docGrid");
  if (docs.length === 0) {
    container.innerHTML = `<div style="color:var(--text-muted);font-size:0.85rem;padding:1rem">No documents found.</div>`;
    return;
  }
  container.innerHTML = docs
    .map(
      (d) => `
      <div class="doc-card" onclick="showToast('Opening ${d.name}...')">
        <div class="doc-icon">${iconMap[d.type] || "📄"}</div>
        <div class="doc-name">${d.name}</div>
        <div class="doc-meta">${d.category} • ${d.type} • ${d.size}</div>
        <div class="doc-meta" style="margin-top:4px">${d.date}</div>
      </div>`
    )
    .join("");
}

function initDocumentSearch() {
  const search = document.getElementById("docSearch");
  const filter = document.getElementById("docFilter");

  search.addEventListener("input",  () => loadDocuments(search.value, filter.value));
  filter.addEventListener("change", () => loadDocuments(search.value, filter.value));
  document.getElementById("uploadDocBtn").addEventListener("click", () => showToast("File upload — connect to backend storage"));
}

// ─── Analytics ────────────────────────────────────────────────────────────────
async function loadAnalytics() {
  const container = document.getElementById("deptChart");
  if (!container) return;
  const data = await Api.getAnalytics();

  renderBarChart("deptChart",  data.dept_labels,    data.dept_usage,    "var(--primary-lt)");
  renderBarChart("weekChart",  data.weekly_labels,  data.weekly_usage,  "var(--accent)");

  const pct = data.digitization_pct;
  const circumference = 314;
  const offset = circumference - (pct / 100) * circumference;
  const arc = document.getElementById("donutArc");
  if (arc) arc.setAttribute("stroke-dashoffset", offset.toFixed(1));
  const pctEl = document.getElementById("donutPct");
  if (pctEl) pctEl.textContent = pct + "%";
}

// ─── Recommendations ──────────────────────────────────────────────────────────
async function loadRecommendations(priority = "") {
  const container = document.getElementById("recList");
  if (!container) return;
  const recs = await Api.getRecommendations(priority);
  renderRecommendations(recs);
}

function renderRecommendations(recs) {
  const container = document.getElementById("recList");
  container.innerHTML = recs
    .map(
      (r, i) => `
      <div class="rec-item ${r.priority}">
        <div class="rec-num">0${i + 1}</div>
        <div class="rec-body">
          <div style="display:flex; align-items:center; gap:10px; margin-bottom:4px">
            <div class="rec-title">${r.title}</div>
            <span class="badge ${r.priority === "high" ? "badge-high" : r.priority === "med" ? "badge-med" : "badge-low"}">
              ${r.priority === "high" ? "High Impact" : r.priority === "med" ? "Medium" : "Low"}
            </span>
          </div>
          <div class="rec-desc">${r.desc}</div>
          <div class="rec-impact">Estimated savings: <span>${r.impact}</span></div>
        </div>
      </div>`
    )
    .join("");
}

function initRecommendationFilters() {
  document.querySelectorAll(".filter-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".filter-btn").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      loadRecommendations(btn.dataset.priority);
    });
  });
}

// ─── Leaderboard ──────────────────────────────────────────────────────────────
async function loadLeaderboard() {
  const data = await Api.getLeaderboard();
  
  const tbody = document.getElementById("leaderboardTable");
  if (tbody) {
    if (data.leaderboard.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;color:var(--text-muted)">No students on the leaderboard yet.</td></tr>`;
    } else {
      tbody.innerHTML = data.leaderboard.map(s => `
        <tr>
          <td><strong>#${s.rank}</strong></td>
          <td><div style="font-weight:600;">${s.name}</div></td>
          <td><span class="badge badge-sm" style="background:var(--surface2); color:var(--text);">${s.department}</span></td>
          <td><span style="color:var(--primary); font-weight:700;">${s.points || 0}</span></td>
          <td>🔥 ${s.streak} Days</td>
          <td><span style="font-size:0.85rem; font-weight:600;">${s.badge}</span></td>
        </tr>
      `).join("");
    }
  }

  // Render the Performance Graph for Top 5 Students
  if (data.leaderboard && data.leaderboard.length > 0) {
    const topStudents = data.leaderboard.slice(0, 5);
    const labels = topStudents.map(s => s.name.split(" ")[0]);
    const values = topStudents.map(s => parseInt(s.points) || 0);
    renderBarChart("leaderboardChart", labels, values, "var(--accent)");
  } else {
    const chartContainer = document.getElementById("leaderboardChart");
    if (chartContainer) {
      chartContainer.innerHTML = `<div style="text-align:center; padding:2rem; width:100%; color:var(--text-muted)">No data available for chart.</div>`;
    }
  }

  const aiBox = document.getElementById("aiSuggestionBox");
  if (aiBox) {
    aiBox.innerHTML = `<p style="font-weight: 500; line-height: 1.6; color: var(--text); margin:0;">${data.ai_suggestion}</p>`;
  }

  // Dept Ranking for HOD
  const deptRankingBox = document.getElementById("deptPointsRanking");
  if (deptRankingBox && data.dept_ranking) {
    if (data.dept_ranking.length === 0) {
      deptRankingBox.innerHTML = `<p style="color:var(--text-muted); font-size:0.85rem;">No department data available.</p>`;
    } else {
      deptRankingBox.innerHTML = data.dept_ranking.map((d, i) => `
        <div style="display:flex; justify-content:space-between; align-items:center; padding: 10px; background:var(--surface2); border-radius:8px;">
          <div style="display:flex; align-items:center; gap:10px;">
            <span style="font-weight:bold; color:var(--text-muted);">#${i+1}</span>
            <span style="font-weight:600;">${d.department}</span>
          </div>
          <div style="text-align:right;">
            <div style="font-weight:bold; color:var(--primary);">${d.total_points} Pts</div>
            <div style="font-size:0.75rem; color:var(--text-muted);">Avg: ${d.avg_per_student} pts/stu</div>
          </div>
        </div>
      `).join("");
    }
  }
}

// ─── Exams & Anti-Cheat ────────────────────────────────────────────────────────
let isTakingExam  = false;
let activeExamData = null; // holds the OnlineExam object during a session

async function loadExams() {
  // --- Score board ---
  const sDept = document.getElementById("scoreBoardDept")?.value || "";
  const sYear = document.getElementById("scoreBoardYear")?.value || "";
  const scoreData = await Api.getExamResults(sDept, sYear);
  const tbody = document.getElementById("examScoreBoard");
  if (tbody && scoreData.results) {
    if (scoreData.results.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;color:var(--text-muted)">No matching exam records found.</td></tr>`;
    } else {
      tbody.innerHTML = scoreData.results.map(r => `
        <tr>
          <td><div style="font-weight:600;">${r.student_name}</div></td>
          <td><span class="badge badge-sm" style="background:#eee;color:#444;">${r.dept || 'N/A'}</span></td>
          <td>${r.year || '—'}</td>
          <td>${r.exam_name}</td>
          <td><strong style="color:var(--primary);">${r.score}%</strong></td>
          <td><span class="badge ${r.status.includes('Cheating') ? 'badge-danger' : 'badge-success'}">${r.status}</span></td>
        </tr>
      `).join("");
    }
  }

  // --- Available exams for students (dept + year scoped) ---
  const startCard  = document.getElementById("exam-start-card");
  const takingUi   = document.getElementById("exam-taking-ui");
  const lockedCard = document.getElementById("exam-locked-card");

  if (scoreData.is_locked) {
    if (startCard)  startCard.style.display  = "none";
    if (takingUi)   takingUi.style.display   = "none";
    if (lockedCard) lockedCard.style.display = "block";
    return;
  }

  if (startCard) {
    try {
      const exams = await Api.getOnlineExams();
      if (exams.length === 0) {
        startCard.innerHTML = `
          <h2 style="margin-bottom:1rem;">Available Exams</h2>
          <div style="padding:2rem; text-align:center; background:var(--surface2); border-radius:12px; border:1px solid var(--border);">
            <div style="font-size:2rem; margin-bottom:10px;">📭</div>
            <p style="color:var(--text-muted);">No exams scheduled for your department and year right now.</p>
          </div>
        `;
      } else {
        startCard.innerHTML = `
          <h2 style="margin-bottom:1rem;">Available Exams</h2>
          <div style="display:flex; flex-direction:column; gap:12px;">
            ${exams.map(exam => `
              <div class="workflow-item" style="background:var(--surface2); border:1px solid var(--border);">
                <div class="wf-icon green">📝</div>
                <div class="wf-body">
                  <div class="wf-title">${exam.title}</div>
                  <div class="wf-meta">
                    <span class="badge badge-sm" style="background:rgba(var(--primary-rgb),0.1); color:var(--primary);">${exam.dept}</span>
                    ${exam.year ? `<span class="badge badge-sm">Year ${exam.year}</span>` : `<span class="badge badge-sm">All Years</span>`}
                    <span>⏱️ ${exam.duration} mins</span>
                    <span>❓ ${exam.questions.length} Qs</span>
                  </div>
                </div>
                <button class="btn btn-primary btn-sm" onclick="startOnlineExam(${JSON.stringify(exam).replace(/"/g, '&quot;')})">
                  Start Exam
                </button>
              </div>
            `).join("")}
          </div>
        `;
      }
    } catch(e) {
      console.warn("Could not load online exams:", e.message);
    }
  }

  // Initial load for admin/hod filters
  filterPublishedExams();
}

async function filterPublishedExams() {
  const publishedList = document.getElementById("publishedExamsList");
  if (!publishedList) return;

  const dept = document.getElementById("filterExamDept")?.value || "";
  const year = document.getElementById("filterExamYear")?.value || "";

  try {
    const allExams = await Api.getOnlineExams(dept, year);
    if (allExams.length === 0) {
      publishedList.innerHTML = `
        <div style="padding:1.5rem; text-align:center; border:1px dashed var(--border); border-radius:12px;">
          <p style="color:var(--text-muted); font-size:0.9rem; margin:0;">No exams found matching these filters.</p>
        </div>`;
    } else {
      publishedList.innerHTML = allExams.map(exam => `
        <div class="workflow-item" style="border:1px solid var(--border); border-radius:12px; padding:12px; margin-bottom:10px; background:var(--surface);">
          <div class="wf-icon" style="background:rgba(var(--primary-rgb),0.1); color:var(--primary);">📋</div>
          <div class="wf-body">
            <div class="wf-title">${exam.title}</div>
            <div class="wf-meta">
              <strong>${exam.dept}</strong> • 
              ${exam.year ? `Year ${exam.year}` : "All Years"} • 
              ${exam.duration} mins • 
              ${exam.questions.length} Qs • 
              <span style="color:var(--text-muted);">by ${exam.created_by}</span>
            </div>
          </div>
          <button class="btn btn-sm" style="color:var(--danger); background:transparent; border:none; padding:4px 8px;" onclick="deletePublishedExam('${exam.id}')">
            🗑 Delete
          </button>
        </div>
      `).join("");
    }
  } catch(e) {
    console.error("Filter error:", e);
  }
}

async function deletePublishedExam(id) {
  if (!confirm("Delete this exam? Students will no longer see it.")) return;
  await Api.deleteOnlineExam(id);
  showToast("Exam deleted.");
  loadExams();
}

function startOnlineExam(exam) {
  activeExamData = exam;
  const takingUi = document.getElementById("exam-taking-ui");
  const startCard = document.getElementById("exam-start-card");
  if (!takingUi) return;

  // Build the question UI dynamically
  const questionsHtml = exam.questions.map((q, idx) => {
    const opts = (q.options || []).map((opt, oIdx) => `
      <label style="display:flex; align-items:center; gap:10px; margin:6px 0; cursor:pointer;">
        <input type="radio" name="live_q${idx}" value="${oIdx}">
        <span>${opt}</span>
      </label>
    `).join("");
    return `
      <div style="margin-bottom:1.5rem; padding:1rem; border:1px solid var(--border); border-radius:10px; background:var(--surface2);">
        <p style="font-weight:600; margin-bottom:10px;">Q${idx+1}: ${q.text}</p>
        ${opts}
      </div>
    `;
  }).join("");

  // Countdown timer
  const totalSecs = (exam.duration || 30) * 60;
  let remaining = totalSecs;
  const timerId = setInterval(() => {
    if (!isTakingExam) { clearInterval(timerId); return; }
    remaining--;
    const m = Math.floor(remaining / 60).toString().padStart(2, "0");
    const s = (remaining % 60).toString().padStart(2, "0");
    const el = document.getElementById("examTimer");
    if (el) el.textContent = `⏱ ${m}:${s} remaining`;
    if (remaining <= 0) { clearInterval(timerId); finishExam("Completed"); }
  }, 1000);

  takingUi.innerHTML = `
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem;">
      <h2>In Progress: ${exam.title}</h2>
      <span id="examTimer" style="color:var(--danger); font-weight:700; font-size:1.1rem;">⏱ ${exam.duration}:00 remaining</span>
    </div>
    <p style="color:var(--danger); font-weight:600; margin-bottom:1.5rem;">⚠️ Do not switch tabs or minimize this window. Doing so will auto-submit your exam with a cheating penalty!</p>
    <div id="liveQuestionsContainer">${questionsHtml}</div>
    <button class="btn btn-primary" id="submitExamBtn" style="margin-top:1rem;">Submit Exam</button>
  `;

  document.getElementById("submitExamBtn").addEventListener("click", () => {
    clearInterval(timerId);
    finishExam("Completed");
  });

  if (startCard) startCard.style.display = "none";
  takingUi.style.display = "block";
  isTakingExam = true;
}

document.addEventListener("DOMContentLoaded", () => {
  // ── Exam-taking buttons (static, for legacy hardcoded exam) ──
  const startExamBtn = document.getElementById("startExamBtn");
  if(startExamBtn) {
    startExamBtn.addEventListener("click", () => {
      document.getElementById("exam-start-card").style.display = "none";
      document.getElementById("exam-taking-ui").style.display = "block";
      isTakingExam = true;
    });
  }

  const submitExamBtn = document.getElementById("submitExamBtn");
  if(submitExamBtn) {
    submitExamBtn.addEventListener("click", () => {
      if(!isTakingExam) return;
      finishExam("Completed");
    });
  }
  
  // ── Create Exam: Add Question button ──
  const addQuestionBtn = document.getElementById("addQuestionBtn");
  let questionCount = 1;
  if(addQuestionBtn) {
    addQuestionBtn.addEventListener("click", () => {
      questionCount++;
      const container = document.getElementById("questionsContainer");
      const block = document.createElement("div");
      block.className = "question-block";
      block.style.cssText = "padding: 1.5rem; border: 1px solid var(--border); border-radius: 12px; background: var(--surface2); animation: fadein 0.3s ease-out;";
      block.innerHTML = `
        <div style="display:flex; justify-content:space-between; margin-bottom: 1rem;">
          <h4 style="margin: 0; color: var(--primary);">Question ${questionCount}</h4>
          <button class="btn btn-sm" onclick="this.closest('.question-block').remove()" style="color:var(--danger); background:transparent; padding:0;">Remove</button>
        </div>
        <input type="text" placeholder="Enter your question here..." class="ecoflow-login__input q-text" style="margin-bottom: 1rem; font-weight: 500;">
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
          <div style="display:flex; align-items:center; gap:10px;">
            <input type="radio" name="q${questionCount}_correct" value="0" checked>
            <input type="text" placeholder="Option A (correct)" class="ecoflow-login__input q-opt" style="flex:1;">
          </div>
          <div style="display:flex; align-items:center; gap:10px;">
            <input type="radio" name="q${questionCount}_correct" value="1">
            <input type="text" placeholder="Option B" class="ecoflow-login__input q-opt" style="flex:1;">
          </div>
          <div style="display:flex; align-items:center; gap:10px;">
            <input type="radio" name="q${questionCount}_correct" value="2">
            <input type="text" placeholder="Option C" class="ecoflow-login__input q-opt" style="flex:1;">
          </div>
          <div style="display:flex; align-items:center; gap:10px;">
            <input type="radio" name="q${questionCount}_correct" value="3">
            <input type="text" placeholder="Option D" class="ecoflow-login__input q-opt" style="flex:1;">
          </div>
        </div>
      `;
      container.appendChild(block);
    });
  }

  // ── Create Exam: Publish button ──
  const publishBtn = document.getElementById("publishExamBtn");
  if (publishBtn) {
    publishBtn.addEventListener("click", async () => {
      const title    = document.getElementById("createExamTitle").value.trim();
      const dept     = document.getElementById("createExamDept").value.trim();
      const duration = parseInt(document.getElementById("createExamDuration").value) || 30;
      const year     = document.getElementById("createExamYear").value;

      if (!title) { showToast("Please enter an exam title."); return; }
      if (!dept)  { showToast("Please enter a department."); return; }

      // Harvest questions from the DOM
      const blocks = document.querySelectorAll(".question-block");
      if (blocks.length === 0) { showToast("Add at least one question."); return; }

      const questions = [];
      let valid = true;
      blocks.forEach((block, idx) => {
        const text    = block.querySelector(".q-text")?.value.trim();
        const optEls  = block.querySelectorAll(".q-opt");
        const options = Array.from(optEls).map(el => el.value.trim()).filter(Boolean);
        const radioChecked = block.querySelector(`input[type=radio]:checked`);
        const correctIndex = radioChecked ? parseInt(radioChecked.value) : 0;

        if (!text || options.length < 2) {
          showToast(`Question ${idx+1}: please fill in the question and at least 2 options.`);
          valid = false; return;
        }
        questions.push({ text, options, correct: correctIndex });
      });

      if (!valid) return;

      try {
        publishBtn.disabled = true;
        publishBtn.textContent = "Publishing...";
        await Api.createOnlineExam({ title, dept, duration, questions, year });
        showToast(`✅ "${title}" published successfully!`, "success");
        // Reset form
        document.getElementById("createExamTitle").value = "";
        document.getElementById("createExamDuration").value = "";
        document.getElementById("questionsContainer").innerHTML = "";
        // Keep dept and year as they might create multiple exams for same class
        filterPublishedExams(); 
      } catch(e) {
        // error already shown by apiFetch
      } finally {
        publishBtn.disabled = false;
        publishBtn.textContent = "🚀 Create & Publish Exam";
      }
    });
  }
});

// Anti-cheat mechanisms
document.addEventListener('visibilitychange', () => {
  if (document.hidden && isTakingExam) {
     handleCheatDetected("Tab switch / Minimized window detected!");
  }
});

window.addEventListener('blur', () => {
  if (isTakingExam) {
     handleCheatDetected("Lost focus (possible secondary window active)!");
  }
});

function handleCheatDetected(reason) {
  if (!isTakingExam) return;
  alert(`CHEATING DETECTED: ${reason}\nYour exam has automatically ended and your access is locked.`);
  finishExam("Cheating Detected");
}

async function finishExam(status) {
  isTakingExam = false;
  const takingUi = document.getElementById("exam-taking-ui");
  if (takingUi) takingUi.style.display = "none";

  let score = 0;
  const examName = activeExamData ? activeExamData.title : "Midterm Assessment";

  if (status === "Completed" && activeExamData && activeExamData.questions) {
    // Score against dynamically created exam questions
    const questions = activeExamData.questions;
    const perQ = questions.length > 0 ? Math.round(100 / questions.length) : 0;
    questions.forEach((q, idx) => {
      const checked = document.querySelector(`input[name="live_q${idx}"]:checked`);
      if (checked && parseInt(checked.value) === q.correct) {
        score += perQ;
      }
    });
    score = Math.min(score, 100); // cap at 100
  } else if (status === "Completed") {
    // Legacy fallback for hardcoded demo exam
    const p1 = document.querySelector('input[name="q1"]:checked')?.value;
    const p2 = document.querySelector('input[name="q2"]:checked')?.value;
    if (p1 === "correct") score += 50;
    if (p2 === "correct") score += 50;
  }

  // Show result card
  const startCard = document.getElementById("exam-start-card");
  if (startCard && status === "Completed") {
    startCard.innerHTML = `
      <h2>✅ Exam Submitted!</h2>
      <div style="margin-top:1rem; padding:1.5rem; background:var(--surface2); border-radius:12px; text-align:center;">
        <div style="font-size:3rem; font-weight:700; color:${score >= 60 ? 'var(--primary)' : 'var(--danger)'};">${score}%</div>
        <div style="color:var(--text-muted); margin-top:8px;">${examName}</div>
        <div style="margin-top:12px; color:${score >= 60 ? 'var(--primary)' : 'var(--danger)'}; font-weight:600;">
          ${score >= 60 ? '🎉 Passed!' : '❌ Failed — Better luck next time!'}
        </div>
      </div>
    `;
    startCard.style.display = "block";
  }

  try {
    await Api.submitExam({ exam_name: examName, score, status });
    showToast(status === "Completed" ? `Exam submitted! Score: ${score}%` : "Exam ended due to rule violation.");
    loadExams();
  } catch (err) {
    showToast("Failed to submit exam.");
  }

  activeExamData = null;
}


// ─── Document Upload ────────────────────────────────────────────────────────────
function initDocumentUpload() {
  const fileInput = document.getElementById("docUploadInput");
  const dropZone  = document.getElementById("docUploadDropZone");
  const resultView = document.getElementById("uploadResultView");
  const uploadLabel = document.getElementById("docUploadLabel");

  if (!fileInput || !dropZone) return;

  fileInput.addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (file) handleDocumentUpload(file);
  });

  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.style.borderColor = "var(--primary)";
    dropZone.style.background = "var(--surface)";
  });

  dropZone.addEventListener("dragleave", (e) => {
    e.preventDefault();
    dropZone.style.borderColor = "var(--border)";
    dropZone.style.background = "var(--surface2)";
  });

  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.style.borderColor = "var(--border)";
    dropZone.style.background = "var(--surface2)";
    const file = e.dataTransfer.files[0];
    if (file) handleDocumentUpload(file);
  });

  async function handleDocumentUpload(file) {
    if (file.size > 20 * 1024 * 1024) {
      showToast("File is too large (max 20MB)", "danger");
      return;
    }

    const category = document.getElementById("uploadCategorySelect")?.value || "General";
    const formData = new FormData();
    formData.append("file", file);
    formData.append("category", category);

    showToast("Uploading document...", "info");
    dropZone.style.pointerEvents = "none";
    const originalContent = dropZone.innerHTML;
    dropZone.innerHTML = `<div class="loader-ring"></div><p>Uploading ${file.name}...</p>`;

    try {
      const res = await Api.uploadDocument(formData);
      showToast("Document Uploaded Successfully!", "success");
      
      if (resultView) {
        resultView.innerHTML = `✅ <strong>${file.name}</strong> successfully uploaded to the digital library and sent to HOD for review (${category}).`;
        resultView.style.display = "block";
      }
      
    } catch (err) {
      showToast("Upload Error: " + err.message, "danger");
    } finally {
      dropZone.innerHTML = originalContent;
      dropZone.style.pointerEvents = "all";
      fileInput.value = ""; // Clear for re-upload
    }
  }
}

// ─── Uploads Page ──────────────────────────────────────────────────────────────
function initUploadsPage() {
  const fileInput = document.getElementById("uploadFileInput");
  const dropZone  = document.getElementById("uploadDropZone");
  const dropLabel = document.getElementById("uploadDropLabel");
  if (!fileInput) return;

  fileInput.addEventListener("change", () => {
    const f = fileInput.files[0];
    if (f && dropLabel) dropLabel.textContent = "📎 " + f.name + " — ready to submit";
  });

  if (dropZone) {
    dropZone.addEventListener("dragover", (e) => {
      e.preventDefault();
      dropZone.style.borderColor = "var(--primary)";
      dropZone.style.background  = "var(--surface)";
    });
    dropZone.addEventListener("dragleave", () => {
      dropZone.style.borderColor = "var(--border)";
      dropZone.style.background  = "var(--surface2)";
    });
    dropZone.addEventListener("drop", (e) => {
      e.preventDefault();
      dropZone.style.borderColor = "var(--border)";
      dropZone.style.background  = "var(--surface2)";
      const f = e.dataTransfer.files[0];
      if (f) {
        const dt = new DataTransfer();
        dt.items.add(f);
        fileInput.files = dt.files;
        if (dropLabel) dropLabel.textContent = "📎 " + f.name + " — ready to submit";
      }
    });
  }
}

async function submitStudentUpload() {
  const fileInput = document.getElementById("uploadFileInput");
  const file      = fileInput?.files[0];
  const category  = document.getElementById("uploadCategory")?.value || "Assignment";
  const remarks   = document.getElementById("uploadRemarks")?.value || "";
  const btn       = document.getElementById("submitUploadBtn");

  if (!file) { showToast("Please select a file first.", "danger"); return; }

  const allowed = [".pdf", ".doc", ".docx", ".ppt", ".pptx", ".jpg", ".jpeg", ".png", ".txt"];
  const ext = "." + file.name.split(".").pop().toLowerCase();
  if (!allowed.includes(ext)) {
    showToast("File type not allowed. Use PDF, Word, PPT, Image, or TXT.", "danger");
    return;
  }
  if (file.size > 20 * 1024 * 1024) {
    showToast("File too large (max 20 MB).", "danger");
    return;
  }

  const formData = new FormData();
  formData.append("file", file);
  formData.append("category", category);
  formData.append("remarks", remarks);

  btn.disabled    = true;
  btn.textContent = "Submitting...";
  try {
    const res = await fetch("/api/uploads", { method: "POST", body: formData, credentials: "include" });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || "Server error " + res.status);
    }
    showToast("Submitted for HOD review!", "success");
    const successMsg = document.getElementById("uploadSuccessMsg");
    if (successMsg) successMsg.style.display = "block";
    fileInput.value = "";
    const dropLabel = document.getElementById("uploadDropLabel");
    if (dropLabel) dropLabel.textContent = "Drag & drop your file here, or click to browse";
    const remarksEl = document.getElementById("uploadRemarks");
    if (remarksEl) remarksEl.value = "";
    loadUploads();
  } catch(e) {
    showToast("Upload failed: " + e.message, "danger");
  } finally {
    btn.disabled    = false;
    btn.textContent = "Submit for Review";
  }
}

async function loadUploads() {
  const cat    = document.getElementById("uploadFilterCat")?.value   || "";
  const status = document.getElementById("uploadFilterStatus")?.value || "";
  const list   = document.getElementById("uploadsList");
  if (!list) return;

  list.innerHTML = `<div style="text-align:center; padding:2rem; color:var(--text-muted);">Loading...</div>`;
  try {
    let url = `/api/uploads?`;
    if (cat)    url += `category=${encodeURIComponent(cat)}&`;
    if (status) url += `status=${encodeURIComponent(status)}&`;
    const data = await fetch(url, { credentials: "include" }).then(r => r.json());

    if (!data.length) {
      list.innerHTML = `<div style="text-align:center; padding:3rem; color:var(--text-muted);">No submissions found.</div>`;
      return;
    }

    const session = requireSession();
    const isReviewer = session && session.role !== "student";

    list.innerHTML = data.map(u => {
      const statusBadge = u.status === "approved"
        ? `<span class="badge badge-done">Approved</span>`
        : u.status === "rejected"
        ? `<span class="badge badge-high">Rejected</span>`
        : `<span class="badge badge-med">Pending</span>`;

      const attachBtn = u.attachment
        ? `<a href="/uploads/files/${u.attachment}" target="_blank" class="btn btn-sm btn-outline" style="font-size:0.8rem;">📎 View File</a>`
        : "";

      const reviewBtns = isReviewer && u.status === "pending" ? `
        <div style="display:flex; gap:8px; margin-top:12px;">
          <button class="btn btn-primary btn-sm" onclick="handleApproval('${u.id}','approve')">✅ Approve</button>
          <button class="btn btn-sm" style="background:var(--danger); color:#fff;" onclick="showRejectDialog('${u.id}')">✗ Reject</button>
        </div>
        <div id="actions-${u.id}"></div>` : "";

      return `<div class="card" id="approval-${u.id}" style="margin-bottom:1rem; border-left:4px solid ${u.status==='approved'?'var(--primary)':u.status==='rejected'?'var(--danger)':'var(--amber)'};">
        <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:8px;">
          <div>
            <div style="font-weight:600; font-size:1rem;">${u.doc} — <span style="color:var(--text-muted); font-weight:400;">${u.name}</span></div>
            <div style="font-size:0.83rem; color:var(--text-muted); margin-top:4px;">📅 ${u.submitted} &nbsp;|&nbsp; 🏛️ ${u.dept}</div>
            ${u.remarks ? `<div style="margin-top:6px; font-size:0.88rem; color:var(--text);">💬 ${u.remarks}</div>` : ""}
            ${u.rejection_reason ? `<div style="margin-top:6px; font-size:0.85rem; color:var(--danger);">Reason: ${u.rejection_reason}</div>` : ""}
          </div>
          <div style="display:flex; flex-direction:column; align-items:flex-end; gap:6px;">
            ${statusBadge}
            ${attachBtn}
          </div>
        </div>
        ${reviewBtns}
      </div>`;
    }).join("");
  } catch(e) {
    list.innerHTML = `<div style="color:var(--danger); padding:1rem;">Failed to load uploads.</div>`;
  }
}

// ─── Init ─────────────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  const session = requireSession();
  if (!session) return;

  initLogout();
  startClock();
  initNavigation();
  initTabs();
  initWorkflowForm();
  initApprovalForm();
  initDocumentSearch();
  initRecommendationFilters();
  initDocumentUpload();
  initUploadsPage();
  applyRoleUI(session);

  // Initial data load is role-driven by applyRoleUI() via setActivePage().
  // Still prefetch documents for both roles (fast and useful).
  loadDocuments();
  if (session.role !== "student") {
    loadRecommendations();
  }
});
