(() => {
  "use strict";

  /* ── Utilities ──────────────────────────────────────────────────────────── */
  const $  = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  function setText(el, text) { if (el) el.textContent = text ?? ""; }

  function setHelper(el, text, type = "") {
    if (!el) return;
    el.className = "ecoflow-login__helper" + (type ? ` is-${type}` : "");
    el.textContent = text ?? "";
  }

  function clearFieldError(wrap) {
    if (!wrap) return;
    wrap.classList.remove("has-error");
    const err = $(".ecoflow-login__error", wrap);
    if (err) err.textContent = "";
  }

  function setFieldError(wrap, msg) {
    if (!wrap) return;
    wrap.classList.add("has-error");
    const err = $(".ecoflow-login__error", wrap);
    if (err) err.textContent = msg;
  }

  function shake(el) {
    if (!el) return;
    el.classList.remove("is-shaking");
    void el.offsetWidth;
    el.classList.add("is-shaking");
    setTimeout(() => el.classList.remove("is-shaking"), 500);
  }

  function setLoading(btn, loading) {
    btn.classList.toggle("is-loading", loading);
    btn.disabled = loading;
  }

  /* ── Mode switching (Sign In ↔ Sign Up) ─────────────────────────────────── */
  function switchMode(root, mode) {
    root.dataset.mode = mode;

    $$(".ecoflow-auth__tab").forEach(btn => {
      const active = btn.dataset.mode === mode;
      btn.classList.toggle("is-active", active);
      btn.setAttribute("aria-selected", active ? "true" : "false");
    });

    const loginForm  = $("#loginForm");
    const signupForm = $("#signupForm");

    if (mode === "signup") {
      loginForm.style.display  = "none";
      signupForm.style.display = "";
      signupForm.style.animation = "form-in 0.35s ease both";
      // focus first field
      const first = signupForm.querySelector("input");
      if (first) setTimeout(() => first.focus(), 50);
    } else {
      signupForm.style.display = "none";
      loginForm.style.display  = "";
      loginForm.style.animation = "form-in 0.35s ease both";
      const first = loginForm.querySelector("input");
      if (first) setTimeout(() => first.focus(), 50);
    }
  }

  /* ── Show/hide student-only fields ─────────────────────────────────────── */
  function toggleStudentFields(roleSelect) {
    const extras = $("#student_extras");
    if (!extras) return;
    extras.style.display = roleSelect.value === "student" ? "" : "none";
  }

  /* ── API helper ─────────────────────────────────────────────────────────── */
  async function apiPost(url, payload) {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "same-origin",
      body: JSON.stringify(payload),
    });
    const data = await res.json().catch(() => ({}));
    return { ok: res.ok, status: res.status, data };
  }

  /* ── Sign In ────────────────────────────────────────────────────────────── */
  function initSignIn(root, card) {
    const form        = $("#loginForm");
    if (!form) return;

    const identWrap = $('[data-field="login_identifier"]', form);
    const pwWrap    = $('[data-field="login_password"]',   form);
    const identIn   = $("#login_identifier");
    const pwIn      = $("#login_password");
    const helper    = $("#loginHelper");
    const submitBtn = form.querySelector(".ecoflow-login__submit");
    const forgot    = $("#forgotPassword");

    if (identIn) identIn.addEventListener("input", () => clearFieldError(identWrap));
    if (pwIn)    pwIn.addEventListener("input",    () => clearFieldError(pwWrap));

    if (forgot) {
      forgot.addEventListener("click", e => {
        e.preventDefault();
        setHelper(helper, "Password reset: contact your college admin.", "");
      });
    }

    form.addEventListener("submit", async e => {
      e.preventDefault();

      clearFieldError(identWrap);
      clearFieldError(pwWrap);
      setHelper(helper, "");

      const username = (identIn?.value ?? "").trim();
      const password = (pwIn?.value ?? "").trim();

      let valid = true;
      if (!username) { setFieldError(identWrap, "Please enter your username."); valid = false; }
      if (!password) { setFieldError(pwWrap,    "Please enter your password."); valid = false; }
      if (!valid)    { shake(card); return; }

      setLoading(submitBtn, true);
      setHelper(helper, "Signing in…");

      try {
        const { ok, data } = await apiPost("/api/login", { username, password, remember: true });
        // AFTER
if (ok) {
  const u = data.user || {};
  localStorage.setItem("ecoflow.session", JSON.stringify({
    name: u.full_name || u.username || username,
    role: u.role || "student",
    dept: u.department || "",
    id:   u.id || null,
  }));
  setHelper(helper, `Welcome back, ${u.full_name || username}! Redirecting…`, "success");
  setTimeout(() => { window.location.href = "/dashboard"; }, 600);
        } else {
          setHelper(helper, data.error || "Invalid credentials.", "error");
          shake(card);
          setLoading(submitBtn, false);
        }
      } catch {
        setHelper(helper, "Network error. Please try again.", "error");
        shake(card);
        setLoading(submitBtn, false);
      }
    });
  }

  /* ── Sign Up ────────────────────────────────────────────────────────────── */
  function initSignUp(root, card) {
    const form = $("#signupForm");
    if (!form) return;

    const helper    = $("#signupHelper");
    const submitBtn = form.querySelector(".ecoflow-login__submit");
    const roleSelect = $("#signup_role");

    if (roleSelect) {
      roleSelect.addEventListener("change", () => toggleStudentFields(roleSelect));
      toggleStudentFields(roleSelect); // set initial state
    }

    // clear errors on input
    form.querySelectorAll("input, select").forEach(input => {
      const fieldWrap = input.closest("[data-field]");
      if (fieldWrap) input.addEventListener("input", () => clearFieldError(fieldWrap));
    });

    form.addEventListener("submit", async e => {
      e.preventDefault();

      // Clear all errors
      $$("[data-field]", form).forEach(f => clearFieldError(f));
      setHelper(helper, "");

      const username  = $("#signup_username")?.value.trim() ?? "";
      const email     = $("#signup_email")?.value.trim()    ?? "";
      const fullName  = $("#signup_fullname")?.value.trim() ?? "";
      const password  = $("#signup_password")?.value.trim() ?? "";
      const role      = $("#signup_role")?.value             ?? "student";
      const dept      = $("#signup_dept")?.value             ?? "CSE";
      const year      = $("#signup_year")?.value             ?? null;
      const usn       = $("#signup_usn")?.value.trim()       ?? "";

      // Validation
      let valid = true;
      const validate = (fieldName, value, check, msg) => {
        if (!check) {
          setFieldError($(`[data-field="${fieldName}"]`, form), msg);
          valid = false;
        }
      };

      validate("signup_username", username, username.length >= 3,           "Username must be ≥ 3 characters.");
      validate("signup_email",    email,    /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email), "Enter a valid email address.");
      validate("signup_fullname", fullName, fullName.length >= 2,           "Full name is required.");
      validate("signup_password", password, password.length >= 8,           "Password must be ≥ 8 characters.");

      if (!valid) { shake(card); return; }

      const payload = { username, email, full_name: fullName, password, role, department: dept };
      if (role === "student") {
        if (year) payload.year = parseInt(year, 10);
        if (usn)  payload.usn  = usn;
      }

      setLoading(submitBtn, true);
      setHelper(helper, "Creating your account…");

      try {
        const { ok, data } = await apiPost("/api/register", payload);
        if (ok) {
          setHelper(helper, "Account created! Signing you in…", "success");
          // Auto-login after signup
          const { ok: lok, data: ld } = await apiPost("/api/login", { username, password });
          // AFTER
if (ok) {
  const u = data.user || {};
  localStorage.setItem("ecoflow.session", JSON.stringify({
    name: u.full_name || u.username || username,
    role: u.role || "student",
    dept: u.department || "",
    id:   u.id || null,
  }));
  setHelper(helper, `Welcome back, ${u.full_name || username}! Redirecting…`, "success");
  setTimeout(() => { window.location.href = "/dashboard"; }, 600);
            
          } else {
            setHelper(helper, "Account created! Please sign in.", "success");
            setLoading(submitBtn, false);
            // Switch to sign-in tab
            const root = $(".ecoflow-login");
            if (root) {
              setTimeout(() => switchMode(root, "signin"), 1200);
            }
          }
        } else {
          setHelper(helper, data.error || "Registration failed.", "error");
          shake(card);
          setLoading(submitBtn, false);
        }
      } catch {
        setHelper(helper, "Network error. Please try again.", "error");
        shake(card);
        setLoading(submitBtn, false);
      }
    });
  }

  /* ── Bootstrap ──────────────────────────────────────────────────────────── */
  document.addEventListener("DOMContentLoaded", () => {
    const root = $(".ecoflow-login");
    if (!root) return;

    const card = $(".ecoflow-login__card", root);

    // Tab switching
    root.addEventListener("click", e => {
      const tab = e.target?.closest?.(".ecoflow-auth__tab");
      if (!tab) return;
      const mode = tab.dataset.mode === "signup" ? "signup" : "signin";
      switchMode(root, mode);
    });

    // Init both forms
    initSignIn(root, card);
    initSignUp(root, card);

    // Set initial mode
    switchMode(root, "signin");
  });
})();
