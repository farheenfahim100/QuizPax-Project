




document.addEventListener("DOMContentLoaded", () => {
    const pageContent = document.getElementById("page-content");
    const modal = document.getElementById("game-modal");
    const overlay = document.getElementById("game-modal-overlay");
    const closeBtn = document.getElementById("close-game-modal");
    const createGameBtn = document.getElementById("game-create-submit");

    let lastFocusedElement = null;

    // Open the modal when clicking the big button
    document.getElementById("create-game-btn").onclick = openGameModal;


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
        loadSetsIntoPopup();
        
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

    // AJAX: Load folders and sets in popup for teacher to choose a set for the game
    function loadSetsIntoPopup() {
        $("#folder-set-list").html("Loading...");

        $.ajax({
            url: "/get_teacher_sets",
            method: "GET",
            success: function(response) {
                renderFolderList(response.folders);
            }
        });
    }

    function renderFolderList(folders) {
        const container = document.getElementById("folder-set-list");
         container.innerHTML = "";

        folders.forEach(folder => {
            const folderBlock = document.createElement("div");
            folderBlock.className = "folder-block";

            const title = document.createElement("h3");
            title.className = "folder-title";
            title.textContent = `${folder.name}`;
            folderBlock.appendChild(title);

            folder.sets.forEach(set => {
                const option = document.createElement("div");
                option.className = "set-option";

                const input = document.createElement("input");
                input.type = "radio";
                input.id = `set-${set.id}`;
                input.name = "chosenSet";
                input.value = set.id;

                const label = document.createElement("label");
                label.setAttribute("for", input.id);
                label.textContent = set.name;

                option.appendChild(input);
                option.appendChild(label);
                folderBlock.appendChild(option);
            });

            container.appendChild(folderBlock);
        });
    }

    // Create Game using AJAX
    createGameBtn.onclick = function() {
        let selectedSet = document.querySelector("input[name='chosenSet']:checked");
        if (!selectedSet) {
            alert("Please select a Q&A set.");
            return;
        }
        let gamemode = document.querySelector("input[name='gamemode']:checked").value;
        let timelimit = document.getElementById("game-length").value;
        $.ajax({
            url: "/creategame",
            method: "POST",
            headers: { "X-CSRFToken": window.CSRF_TOKEN },
            data: {
                setid: selectedSet.value,
                mode: gamemode,
                timelimit: timelimit
            },
            success: function(response) {
                closeGameModal();
                // showGamePinScreen(response.pin);
                window.location.href = "/game_lobby?pin=" + encodeURIComponent(response.pin);
            },
            error: function(xhr){
                alert("Error updating folder: " + xhr.responseText);
            }
        });
    };

});

// Show final PIN popup (removed this, but useful for checking generated code)
function showGamePinScreen(pin) {
    alert("Your game PIN is: " + pin + "\n(This will later open the WebSocket room)");
}