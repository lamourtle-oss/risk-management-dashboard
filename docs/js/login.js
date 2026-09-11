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

  function trimmed(value) {
    return String(value || "").replace(/^\s+|\s+$/g, "");
  }

  function ok(password) {
    return trimmed(password) === "Risk2026";
  }

  function submit(event) {
    var input = byId("password");
    if (ok(input && input.value)) {
      window.location.href = "home.html";
      return true;
    }
    if (event) {
      if (event.preventDefault) event.preventDefault();
      if (event.stopPropagation) event.stopPropagation();
    }
    showErr("รหัสผ่านไม่ถูกต้อง");
    return false;
  }

  var form = byId("login-form");
  var btn = byId("login-btn");
  if (!form || !btn) return;
  form.onsubmit = submit;
  if (form.addEventListener) form.addEventListener("submit", submit, false);
  btn.onclick = function (event) {
    return submit(event);
  };
})();
