(function () {
  function byId(id) {
    return document.getElementById(id);
  }

  function showErr(msg) {
    var err = byId("login-error");
    if (!err) return;
    err.hidden = false;
    err.textContent = msg;
  }

  function unlock() {
    var gate = byId("gate");
    var app = byId("app");
    if (gate) {
      gate.hidden = true;
      gate.setAttribute("hidden", "hidden");
      gate.style.display = "none";
    }
    if (app) {
      app.hidden = false;
      app.removeAttribute("hidden");
      app.removeAttribute("inert");
      app.inert = false;
      app.style.display = "grid";
    }
    try {
      document.dispatchEvent(new Event("dashboard-ready"));
    } catch (error) {
      var ev = document.createEvent("Event");
      ev.initEvent("dashboard-ready", true, true);
      document.dispatchEvent(ev);
    }
  }

  function trimmed(value) {
    return String(value || "").replace(/^\s+|\s+$/g, "");
  }

  function ok(password) {
    return trimmed(password) === "Risk2026";
  }

  function submit(event) {
    if (event) {
      if (event.preventDefault) event.preventDefault();
      if (event.stopPropagation) event.stopPropagation();
    }
    var input = byId("password");
    if (ok(input && input.value)) {
      unlock();
    } else {
      showErr("รหัสผ่านไม่ถูกต้อง");
    }
    return false;
  }

  var form = byId("login-form");
  var btn = byId("login-btn");
  var input = byId("password");
  if (!form || !btn) return;
  form.onsubmit = submit;
  if (form.addEventListener) form.addEventListener("submit", submit, false);
  btn.onclick = submit;
  if (btn.addEventListener) btn.addEventListener("click", submit, false);
  if (input && input.addEventListener) {
    input.addEventListener("keydown", function (event) {
      var key = event.key || event.keyCode;
      if (key === "Enter" || key === 13) submit(event);
    });
  }
})();
