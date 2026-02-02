

document.addEventListener("DOMContentLoaded", () => {

    const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute("content");

    if (!csrfToken) {
    console.error("CSRF token not found");
    }

    const modal = document.getElementById("game-modal");
    const overlay = document.getElementById("game-modal-overlay");
    const closeBtn = document.getElementById("close-game-modal");
    const openBtn = document.getElementById("use-public-set-btn");
    const createGameBtn = document.getElementById("game-create-submit");
    const setid = openBtn.dataset.setid;
    const pageContent = document.getElementById("page-content");
    let lastFocusedElement = null;

    if (!modal || !openBtn || !createGameBtn) {
        console.error("Public set modal elements missing");
        return;
    }

    // ---------- MODAL OPEN / CLOSE ----------

    openBtn.onclick = openGameModal;

    closeBtn.onclick = closeGameModal;
    overlay.onclick = closeGameModal;

    function openGameModal() {
        lastFocusedElement = document.activeElement;
        modal.classList.add("show");
        overlay.classList.add("show");
        pageContent.setAttribute("inert", "");
        modal.removeAttribute("inert");
        // move focus into modal
        modal.querySelector("button, input, [tabindex]:not([tabindex='-1'])")?.focus();

    }

    function closeGameModal() {
        modal.classList.add("fade-out");
        overlay.classList.add("fade-out");
        modal.setAttribute("inert", "");
        pageContent.removeAttribute("inert");

        lastFocusedElement?.focus();

        setTimeout(() => {
            modal.classList.remove("show", "fade-out");
            overlay.classList.remove("show", "fade-out");
        }, 250);
    }

    // ---------- CREATE GAME ----------
    createGameBtn.onclick = function () {
        const gamemodeEl = document.querySelector("input[name='gamemode']:checked");
        const timelimitEl = document.getElementById("game-length");

        if (!gamemodeEl) {
            alert("Please select a game mode.");
            return;
        }

        const gamemode = gamemodeEl.value;
        const timelimit = parseInt(timelimitEl.value);

        if (isNaN(timelimit) || timelimit < 1 || timelimit > 10) {
            alert("Game length must be between 1 and 10 minutes.");
            return;
        }

        $.ajax({
            url: "/creategame",
            method: "POST",
            headers: { "X-CSRFToken": csrfToken },
            data: {
                setid: setid,
                mode: gamemode,
                timelimit: timelimit
            },
            success: function (response) {
                closeGameModal();
                window.location.href = "/game_lobby?pin=" + response.pin;
            },
            error: function (xhr) {
                alert("Error creating game: " + xhr.responseText);
            }
        });
    };

});