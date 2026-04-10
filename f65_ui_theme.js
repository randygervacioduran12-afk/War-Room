const THEMES = [
  {
    name: "void",
    bg: "radial-gradient(circle at top, rgba(95,76,255,0.18), transparent 30%), radial-gradient(circle at 80% 20%, rgba(255,79,180,0.12), transparent 28%), linear-gradient(180deg, #050711 0%, #090d19 36%, #050711 100%)",
  },
  {
    name: "neon-city",
    bg: "radial-gradient(circle at 20% 20%, rgba(0,197,255,0.18), transparent 22%), radial-gradient(circle at 80% 10%, rgba(255,70,160,0.12), transparent 26%), linear-gradient(180deg, #05060d 0%, #0b0f1b 35%, #06070c 100%)",
  },
  {
    name: "amber-core",
    bg: "radial-gradient(circle at 20% 20%, rgba(255,184,92,0.17), transparent 22%), radial-gradient(circle at 78% 18%, rgba(255,79,180,0.08), transparent 24%), linear-gradient(180deg, #08070a 0%, #121018 38%, #08070b 100%)",
  },
  {
    name: "planet-ice",
    bg: "radial-gradient(circle at 25% 20%, rgba(89,227,255,0.14), transparent 28%), radial-gradient(circle at 80% 15%, rgba(130,160,255,0.14), transparent 26%), linear-gradient(180deg, #07111a 0%, #08131c 40%, #050711 100%)",
  },
];

let index = 0;

export function applyTheme(i = 0) {
  index = i % THEMES.length;
  document.body.style.background = THEMES[index].bg;
  localStorage.setItem("warroom_theme_index", String(index));
}

export function cycleTheme() {
  applyTheme((index + 1) % THEMES.length);
}

export function bootTheme() {
  const saved = Number(localStorage.getItem("warroom_theme_index") || "0");
  applyTheme(Number.isFinite(saved) ? saved : 0);
}