const THEMES = [
{
name: “sanctuary”,
label: “Sanctuary”,
bg: “radial-gradient(ellipse 80% 60% at 50% 50%, rgba(210,118,78,0.09) 0%, transparent 55%), radial-gradient(ellipse 65% 55% at 75% 25%, rgba(124,85,248,0.11) 0%, transparent 50%), radial-gradient(ellipse 55% 45% at 20% 70%, rgba(0,180,255,0.07) 0%, transparent 50%), linear-gradient(155deg, #030409 0%, #060812 45%, #030409 100%)”,
orange: “#d97b55”, cyan: “#00d4ff”,
},
{
name: “neon-city”,
label: “Neon City”,
bg: “radial-gradient(ellipse 60% 50% at 12% 0%, rgba(0,197,255,0.15) 0%, transparent 55%), radial-gradient(ellipse 50% 40% at 88% 8%, rgba(255,55,155,0.11) 0%, transparent 50%), radial-gradient(ellipse 40% 40% at 50% 85%, rgba(124,85,248,0.08) 0%, transparent 50%), linear-gradient(155deg, #04060d 0%, #06091a 45%, #030508 100%)”,
orange: “#00c8ff”, cyan: “#ff3ca0”,
},
{
name: “amber-core”,
label: “Amber Core”,
bg: “radial-gradient(ellipse 65% 50% at 15% 5%, rgba(230,180,70,0.13) 0%, transparent 55%), radial-gradient(ellipse 45% 35% at 82% 15%, rgba(210,95,80,0.10) 0%, transparent 50%), linear-gradient(155deg, #080709 0%, #120e0d 45%, #080709 100%)”,
orange: “#e8b450”, cyan: “#f09050”,
},
{
name: “planet-ice”,
label: “Planet Ice”,
bg: “radial-gradient(ellipse 60% 50% at 15% 5%, rgba(88,208,255,0.13) 0%, transparent 55%), radial-gradient(ellipse 45% 38% at 85% 12%, rgba(128,148,255,0.12) 0%, transparent 50%), linear-gradient(155deg, #060e18 0%, #08101c 45%, #050b12 100%)”,
orange: “#58d2ff”, cyan: “#a0b8ff”,
},
{
name: “destiny”,
label: “Destiny HUD”,
bg: “radial-gradient(ellipse 55% 45% at 10% 0%, rgba(255,188,55,0.11) 0%, transparent 55%), radial-gradient(ellipse 40% 35% at 90% 10%, rgba(178,128,48,0.09) 0%, transparent 50%), linear-gradient(155deg, #080700 0%, #100d03 45%, #070600 100%)”,
orange: “#f5bb40”, cyan: “#c8a838”,
},
{
name: “void-noir”,
label: “Void Noir”,
bg: “radial-gradient(ellipse 70% 55% at 5% -5%, rgba(124,85,248,0.15) 0%, transparent 60%), radial-gradient(ellipse 60% 45% at 95% 105%, rgba(210,118,78,0.12) 0%, transparent 55%), radial-gradient(ellipse 40% 35% at 100% 30%, rgba(0,180,255,0.065) 0%, transparent 50%), linear-gradient(155deg, #030409 0%, #050820 45%, #03040a 100%)”,
orange: “#d97b55”, cyan: “#00d4ff”,
},
];

let idx = 0;

export function applyTheme(i = 0) {
idx = ((i % THEMES.length) + THEMES.length) % THEMES.length;
const t = THEMES[idx];
document.body.style.background = t.bg;
document.documentElement.style.setProperty(”-orange”, t.orange);
document.documentElement.style.setProperty(”-amber”,  t.orange === “#d97b55” ? “#e9a355” : t.orange);
document.documentElement.style.setProperty(”-cyan”,   t.cyan);
localStorage.setItem(“warroom_theme”, String(idx));
}

export function cycleTheme() {
applyTheme(idx + 1);
return THEMES[idx].label;
}

export function bootTheme() {
const saved = parseInt(localStorage.getItem(“warroom_theme”) || “0”, 10);
applyTheme(isNaN(saved) ? 0 : saved);
}

export function getThemes()       { return THEMES; }
export function getCurrentTheme() { return THEMES[idx]; }