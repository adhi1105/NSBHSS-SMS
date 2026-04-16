/**
 * Eduplex Admin — Run Action Button Injector
 * Injects a branded "Run Action" button next to Django admin's action dropdown.
 * Works regardless of theme overrides (Unfold etc.).
 */
(function () {
  "use strict";

  function injectRunButton() {
    // The action <select> dropdown in Django admin
    const actionSelect = document.querySelector('select[name="action"]');
    if (!actionSelect) return;

    // Prevent double-injection
    if (document.querySelector(".eduplex-run-btn")) return;

    const btn = document.createElement("button");
    btn.type = "submit";
    btn.className = "eduplex-run-btn";
    btn.innerHTML = `<span style="font-size:0.8em;">▶</span>&nbsp;Run Action`;

    // Insert immediately after the <select>
    actionSelect.insertAdjacentElement("afterend", btn);

    btn.addEventListener("click", function (e) {
      const selectedAction = actionSelect.value;
      if (!selectedAction) {
        e.preventDefault();
        btn.textContent = "⚠️ Pick an action first";
        btn.style.background = "#b45309";
        btn.style.borderColor = "#fbbf24";
        setTimeout(() => {
          btn.innerHTML = `<span style="font-size:0.8em;">▶</span>&nbsp;Run Action`;
          btn.style.background = "";
          btn.style.borderColor = "";
        }, 2000);
      }
    });
  }

  // Run on DOM ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", injectRunButton);
  } else {
    injectRunButton();
  }
})();
