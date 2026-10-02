document.addEventListener("DOMContentLoaded", () => {
  const key = document.body.dataset.page || "home";
  JF.topbar(key).then((user) => {
    document.querySelectorAll("[data-when-signed-in]").forEach((el) => el.classList.toggle("hidden", !user));
    document.querySelectorAll("[data-when-signed-out]").forEach((el) => el.classList.toggle("hidden", !!user));
  });
});
