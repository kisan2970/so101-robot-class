const storageKey = "so101-class-progress";

const leaderInput = document.querySelector("#leaderPort");
const followerInput = document.querySelector("#followerPort");
const templateCodes = [...document.querySelectorAll("code[data-template]")];

function updateTemplates() {
  const leader = (leaderInput?.value || "COM10").trim().toUpperCase();
  const follower = (followerInput?.value || "COM11").trim().toUpperCase();
  templateCodes.forEach((code) => {
    if (!code.dataset.source) code.dataset.source = code.textContent;
    code.textContent = code.dataset.source.replaceAll("{{LEADER}}", leader).replaceAll("{{FOLLOWER}}", follower);
  });
}

leaderInput?.addEventListener("input", updateTemplates);
followerInput?.addEventListener("input", updateTemplates);
updateTemplates();

function copyText(text, button) {
  navigator.clipboard.writeText(text.trim()).then(() => {
    const label = button.querySelector("span");
    if (!label) return;
    const previous = label.textContent;
    label.textContent = "복사됨";
    setTimeout(() => { label.textContent = previous; }, 1200);
  });
}

document.querySelectorAll(".copy-button").forEach((button) => {
  button.addEventListener("click", () => copyText(button.closest("pre").querySelector("code").textContent, button));
});

document.querySelector("#copyPrompt")?.addEventListener("click", (event) => {
  copyText(document.querySelector("#promptText").textContent, event.currentTarget);
});

function activateTab(name) {
  document.querySelectorAll(".tab").forEach((tab) => tab.classList.toggle("active", tab.dataset.tab === name));
  document.querySelectorAll(".tab-panel").forEach((panel) => panel.classList.toggle("active", panel.dataset.panel === name));
  window.scrollTo({ top: document.querySelector(".tabs").offsetTop - 64, behavior: "smooth" });
}

document.querySelectorAll("[data-tab]").forEach((tab) => tab.addEventListener("click", () => activateTab(tab.dataset.tab)));
document.querySelectorAll("[data-tab-target]").forEach((button) => button.addEventListener("click", () => activateTab(button.dataset.tabTarget)));

const progressInputs = [...document.querySelectorAll("[data-progress]")];

function saveProgress() {
  const completed = progressInputs.filter((input) => input.checked).map((input) => input.dataset.progress);
  localStorage.setItem(storageKey, JSON.stringify(completed));
  document.querySelector("#progressLabel").textContent = `${completed.length} / ${progressInputs.length} 완료`;
}

function loadProgress() {
  let completed = [];
  try { completed = JSON.parse(localStorage.getItem(storageKey) || "[]"); } catch { completed = []; }
  progressInputs.forEach((input) => { input.checked = completed.includes(input.dataset.progress); });
  saveProgress();
}

progressInputs.forEach((input) => input.addEventListener("change", saveProgress));
document.querySelector("#resetProgress")?.addEventListener("click", () => {
  progressInputs.forEach((input) => { input.checked = false; });
  saveProgress();
});
loadProgress();

const navLinks = [...document.querySelectorAll(".step-nav a")];
const steps = [...document.querySelectorAll("article.step")];
const observer = new IntersectionObserver((entries) => {
  const visible = entries.filter((entry) => entry.isIntersecting).sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
  if (!visible) return;
  navLinks.forEach((link) => link.classList.toggle("current", link.getAttribute("href") === `#${visible.target.id}`));
}, { rootMargin: "-20% 0px -65%", threshold: [0.05, 0.2, 0.5] });
steps.forEach((step) => observer.observe(step));

window.addEventListener("DOMContentLoaded", () => {
  if (window.lucide) window.lucide.createIcons();
});
