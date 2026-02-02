document.addEventListener("DOMContentLoaded", () => {
  const detailBoxes = document.querySelectorAll(".details-inner");

  const SHOW = 0.20; // threshold at which element becomes visible
  const HIDE = 0.05; // threshold at which elements hide (less than show to prevent flicker on edge of screen)

  const state = new WeakMap(); // track visibility per element: element -> boolean

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      const wasVisible = state.get(entry.target) === true; // check if this element was previously visible
      const ratio = entry.intersectionRatio; // See how much of element is in view

      if (!wasVisible && ratio >= SHOW) { // Case 1: if not visible before and most is in view, then show
        entry.target.classList.add("is-visible");
        state.set(entry.target, true); 
      } else if (wasVisible && ratio <= HIDE) { // Case 2: if visible before and most is out of view, then hide
        entry.target.classList.remove("is-visible");
        state.set(entry.target, false);
      }
    });
  }, {
    threshold: [HIDE, SHOW] // Function runs only when cars is in view enough to show, and out of view enough to hide
  });

  detailBoxes.forEach(box => observer.observe(box));
});