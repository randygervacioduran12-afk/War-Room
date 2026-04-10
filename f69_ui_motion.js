export function bootReveal() {
  const els = Array.from(document.querySelectorAll(".reveal"));
  const observer = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) entry.target.classList.add("in");
      }
    },
    { threshold: 0.12 }
  );
  els.forEach((el) => observer.observe(el));
}

export function bootParallax() {
  const hero = document.querySelector(".hero");
  if (!hero) return;

  hero.addEventListener("pointermove", (e) => {
    const rect = hero.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width - 0.5;
    const y = (e.clientY - rect.top) / rect.height - 0.5;

    const orbit = hero.querySelector(".hero-orbit");
    if (orbit) {
      orbit.style.transform = `translate(${x * 8}px, ${y * 8}px)`;
    }
  });

  hero.addEventListener("pointerleave", () => {
    const orbit = hero.querySelector(".hero-orbit");
    if (orbit) orbit.style.transform = "translate(0, 0)";
  });
}