document.addEventListener("DOMContentLoaded", () => {
  JF.topbar("login");
  const form = document.getElementById("login");
  const err = document.getElementById("err");
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    err.classList.add("hidden");
    const data = Object.fromEntries(new FormData(form));
    try {
      await JF.api("/api/auth/login", { method: "POST", body: data, allow401: true });
      const next = new URLSearchParams(location.search).get("next");
      location.href = next && next.startsWith("/app") ? next : "/app";
    } catch (ex) {
      err.textContent = ex.message;
      err.classList.remove("hidden");
    }
  });
});
