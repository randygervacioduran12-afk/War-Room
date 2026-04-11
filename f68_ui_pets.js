const DEFAULT_PETS = [
  { key: "general_of_the_army", name: "Claude Core", avatar: "CL", xp: 0, level: 1 },
  { key: "general_of_engineering", name: "Engineer Wing", avatar: "EN", xp: 0, level: 1 },
  { key: "general_of_intelligence", name: "Intel Wing", avatar: "IN", xp: 0, level: 1 },
  { key: "general_of_the_archive", name: "Archive Wing", avatar: "AR", xp: 0, level: 1 },
];

function loadPets() {
  try {
    const raw = localStorage.getItem("warroom_pets");
    if (!raw) return DEFAULT_PETS;
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) && parsed.length ? parsed : DEFAULT_PETS;
  } catch {
    return DEFAULT_PETS;
  }
}

function savePets(pets) {
  localStorage.setItem("warroom_pets", JSON.stringify(pets));
}

export function getPets() {
  return loadPets();
}

export function awardPetXp(generalKey, amount = 10) {
  const pets = loadPets();
  const pet = pets.find((p) => p.key === generalKey);
  if (!pet) return pets;

  pet.xp += amount;
  pet.level = Math.max(1, Math.floor(pet.xp / 100) + 1);
  savePets(pets);
  return pets;
}

export function renderPets(el, pets) {
  if (!el) return;

  el.innerHTML = pets
    .map((pet) => {
      const progress = pet.xp % 100;
      return `
        <div class="pet-card">
          <div class="pet-avatar">${pet.avatar}</div>
          <div>
            <div class="pet-name">${pet.name}</div>
            <div class="pet-stats">level ${pet.level} · ${pet.xp} xp</div>
            <div class="progress"><span style="width:${progress}%"></span></div>
          </div>
        </div>
      `;
    })
    .join("");
}