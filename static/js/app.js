document.addEventListener("DOMContentLoaded", () => {
  const dateLabel = document.getElementById("today-label");
  if (dateLabel) dateLabel.textContent = new Intl.DateTimeFormat(undefined, {weekday:"short", month:"short", day:"numeric"}).format(new Date());

  const localDate = (date) => {
    const d = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
    return d.toISOString().slice(0, 10);
  };
  const today = localDate(new Date());
  ["due-date-input", "reminder-date-input"].forEach(id => {
    const input = document.getElementById(id);
    if (input) {
      input.min = today;
      if (!input.value) input.value = today;
    }
  });

  document.querySelectorAll(".flash-close").forEach(btn => btn.addEventListener("click", () => btn.closest(".flash").remove()));
  document.querySelectorAll(".filter-pill").forEach(btn => btn.addEventListener("click", () => {
    document.querySelectorAll(".filter-pill").forEach(x => x.classList.remove("selected"));
    btn.classList.add("selected");
    let count = 0;
    document.querySelectorAll(".task-item").forEach(item => {
      const show = btn.dataset.filter === "all" || item.dataset.status === btn.dataset.filter;
      item.hidden = !show;
      if (show) count++;
    });
    const target = document.getElementById("visible-count");
    if (target) target.textContent = count;
  }));
  document.querySelectorAll(".delete-form").forEach(form => form.addEventListener("submit", e => {
    if (!window.confirm(form.dataset.confirm || "Are you sure?")) e.preventDefault();
  }));

  // Normalize typed 24-hour time as HH:MM while preserving keyboard entry.
  document.querySelectorAll('input[name="due_time"], input[name="reminder_time"], input[name="daily_time"]').forEach(input => {
    input.addEventListener("input", () => {
      input.setCustomValidity("");
    });
    input.addEventListener("invalid", () => {
      input.setCustomValidity("Enter time in 24-hour HH:MM format, for example 09:30.");
    });
  });

  // Theme preference persists across page navigation and browser sessions.
  const themeToggle = document.getElementById("theme-toggle");
  const themeMeta = document.getElementById("theme-color-meta");
  const applyTheme = (theme) => {
    const dark = theme === "dark";
    document.body.classList.toggle("dark-theme", dark);
    if (themeToggle) {
      themeToggle.setAttribute("aria-label", dark ? "Switch to light theme" : "Switch to dark theme");
      themeToggle.setAttribute("title", dark ? "Switch to light theme" : "Switch to dark theme");
      const icon = themeToggle.querySelector(".theme-icon");
      const label = themeToggle.querySelector(".theme-toggle-label");
      if (icon) icon.textContent = dark ? "☀" : "☾";
      if (label) label.textContent = dark ? "Light mode" : "Dark mode";
    }
    if (themeMeta) themeMeta.setAttribute("content", dark ? "#171624" : "#f7f7fb");
  };
  let savedTheme = "light";
  try { savedTheme = localStorage.getItem("taskSchedulerTheme") || "light"; } catch (_) {}
  applyTheme(savedTheme);
  if (themeToggle) themeToggle.addEventListener("click", () => {
    const nextTheme = document.body.classList.contains("dark-theme") ? "light" : "dark";
    applyTheme(nextTheme);
    try { localStorage.setItem("taskSchedulerTheme", nextTheme); } catch (_) {}
  });

  // Mobile left navigation drawer.
  const appShell = document.getElementById("app-shell");
  const navToggle = document.getElementById("mobile-nav-toggle");
  const navBackdrop = document.getElementById("mobile-nav-backdrop");
  const closeMobileNav = () => {
    if (appShell) appShell.classList.remove("mobile-nav-open");
    if (navBackdrop) navBackdrop.hidden = true;
    if (navToggle) {
      navToggle.setAttribute("aria-expanded", "false");
      navToggle.setAttribute("aria-label", "Open navigation menu");
    }
    document.body.classList.remove("nav-drawer-open");
  };
  if (navToggle) navToggle.addEventListener("click", () => {
    const opening = !(appShell && appShell.classList.contains("mobile-nav-open"));
    if (appShell) appShell.classList.toggle("mobile-nav-open", opening);
    if (navBackdrop) navBackdrop.hidden = !opening;
    navToggle.setAttribute("aria-expanded", String(opening));
    navToggle.setAttribute("aria-label", opening ? "Close navigation menu" : "Open navigation menu");
    document.body.classList.toggle("nav-drawer-open", opening);
  });
  if (navBackdrop) navBackdrop.addEventListener("click", closeMobileNav);
  document.querySelectorAll(".sidebar .nav-link").forEach(link => link.addEventListener("click", closeMobileNav));
  document.addEventListener("keydown", event => { if (event.key === "Escape") closeMobileNav(); });

  // Time inputs use a normal text keyboard and provide clear validation feedback.
  document.querySelectorAll('input[name="due_time"], input[name="reminder_time"], input[name="daily_time"]').forEach(input => {
    input.setAttribute("inputmode", "text");
    input.addEventListener("input", () => {
      input.setCustomValidity("");
      const value = input.value.trim();
      if (value && value.length === 5 && !/^([01]\d|2[0-3]):[0-5]\d$/.test(value)) {
        input.setCustomValidity("Use 24-hour HH:MM time, such as 09:30 or 18:45.");
      }
    });
    input.addEventListener("invalid", () => {
      input.setCustomValidity("Use 24-hour HH:MM time, such as 09:30 or 18:45.");
    });
    input.addEventListener("blur", () => {
      const value = input.value.trim();
      if (value && !/^([01]\d|2[0-3]):[0-5]\d$/.test(value)) {
        input.setCustomValidity("Use 24-hour HH:MM time, such as 09:30 or 18:45.");
      } else {
        input.setCustomValidity("");
      }
    });
  });

});
