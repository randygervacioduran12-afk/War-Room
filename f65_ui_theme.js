const THEMES = [
{
name: “void-noir”,
label: “Void Noir”,
// Reflect cosmic void + Control brutalist dark
bg: “radial-gradient(ellipse 70% 55% at 5% -5%, rgba(124,92,252,0.16) 0%, transparent 60%), radial-gradient(ellipse 60% 45% at 95% 105%, rgba(215,122,84,0.13) 0%, transparent 55%), radial-gradient(ellipse 40% 35% at 100% 30%, rgba(0,224,255,0.07) 0%, transparent 50%), linear-gradient(168deg, #03040b 0%, #05081f 35%, #060a1e 65%, #03040a 100%)”,
orange: “#d97b55”, cyan: “#00e0ff”,
},
{
name: “neon-city”,
label: “Neon City”,
// Cyberpunk 2077 skyline — cyan + magenta neon
bg: “radial-gradient(ellipse 55% 50% at 12% 0%, rgba(0,197,255,0.16) 0%, transparent 55%), radial-gradient(ellipse 50% 40% at 88% 8%, rgba(255,60,160,0.12) 0%, transparent 50%), radial-gradient(ellipse 40% 40% at 50% 85%, rgba(124,92,252,0.09) 0%, transparent 50%), linear-gradient(168deg, #04060d 0%, #070a19 35%, #060919 65%, #030508 100%)”,
orange: “#00c5ff”, cyan: “#ff3ca0”,
},
{
name: “amber-core”,
label: “Amber Core”,
// Capi Finance + ZeroTrust gold luxury
bg: “radial-gradient(ellipse 60% 50% at 12% 5%, rgba(232,185,80,0.14) 0%, transparent 55%), radial-gradient(ellipse 45% 35% at 82% 15%, rgba(215,100,84,0.11) 0%, transparent 50%), linear-gradient(168deg, #080709 0%, #130f0e 35%, #110d0d 65%, #080709 100%)”,
orange: “#e8b950”, cyan: “#f09050”,
},
{
name: “planet-ice”,
label: “Planet Ice”,
// AIAF grid + finance dashboard cool blue
bg: “radial-gradient(ellipse 60% 50% at 15% 5%, rgba(89,210,255,0.14) 0%, transparent 55%), radial-gradient(ellipse 45% 38% at 85% 12%, rgba(130,150,255,0.12) 0%, transparent 50%), linear-gradient(168deg, #060e18 0%, #080f1c 35%, #06101b 65%, #050b12 100%)”,
orange: “#59d2ff”, cyan: “#a0b8ff”,
},
{
name: “destiny-hud”,
label: “Destiny HUD”,
// Destiny gameplay + military operations UI
bg: “radial-gradient(ellipse 55% 45% at 10% 0%, rgba(255,190,60,0.12) 0%, transparent 55%), radial-gradient(ellipse 40% 35% at 90% 10%, rgba(180,130,50,0.10) 0%, transparent 50%), linear-gradient(168deg, #080700 0%, #100e03 35%, #0e0c03 65%, #070600 100%)”,
orange: “#f5bc42”, cyan: “#c8a83c”,
},
{
name: “sanctuary”,
label: “Sanctuary”,
// Deep purple + Agentrooms warm dark — Randy’s default aura
bg: “radial-gradient(ellipse 65% 55% at 8% -5%, rgba(180,100,255,0.15) 0%, transparent 58%), radial-gradient(ellipse 55% 45% at 92% 105%, rgba(255,100,160,0.12) 0%, transparent 55%), radial-gradient(ellipse 35% 30% at 50% 45%, rgba(215,122,84,0.07) 0%, transparent 50%), linear-gradient(168deg, #04030d 0%, #080518 35%, #07061a 65%, #030310 100%)”,
orange: “#d97b55”, cyan: “#c878ff”,
},
];

let currentIndex = 0;

export function applyTheme(i = 0) {
currentIndex = ((i % THEMES.length) + THEMES.length) % THEMES.length;
const t = THEMES[currentIndex];
document.body.style.background = t.bg;
document.documentElement.style.setProperty(”–orange”, t.orange);
document.documentElement.style.setProperty(”–amber”,  t.orange === “#d97b55” ? “#f0a753” : t.orange);
document.documentElement.style.setProperty(”–cyan”,   t.cyan);
localStorage.setItem(“warroom_theme”, String(currentIndex));
}

export function cycleTheme() {
applyTheme(currentIndex + 1);
return THEMES[currentIndex].label;
}

export function bootTheme() {
const saved = parseInt(localStorage.getItem(“warroom_theme”) || “0”, 10);
applyTheme(isNaN(saved) ? 0 : saved);
}

export function getThemes()      { return THEMES; }
export function getCurrentTheme(){ return THEMES[currentIndex]; }