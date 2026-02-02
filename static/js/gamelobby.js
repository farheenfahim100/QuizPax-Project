
document.addEventListener("DOMContentLoaded", () => {

    // const socket = io();
    const socket = io({
        transports: ["websocket"],
        upgrade: false,
        });
    const pinElement = document.getElementById("game-pin");
    const pin = pinElement.textContent.trim();
    const teamSelectContainer = document.getElementById("team-select-container");
    const teamSelect = document.getElementById("team-count-select");
    const isTeamMode = !!teamSelectContainer;
    const cancelBtn = document.getElementById("cancel-game-button");

    if (!pinElement) {
        console.error("ERROR: game-pin element not found.");
        return;
    }

    if (cancelBtn) {
        cancelBtn.addEventListener("click", () => {
            const confirmed = confirm(
                "Are you sure you want to cancel this game?\n\nAll players will be removed from the lobby and you will be redirected to your dashboard."
            );

            if (!confirmed) return;

            console.log("Teacher cancelled game:", pin);

            socket.emit("cancel_game", { pin });

            cancelBtn.disabled = true;
            if (startBtn) startBtn.disabled = true;
            
            window.location.href = "/dashboard";
        });
    }

    console.log("Teacher joining lobby room:", pin);

    // Ensure teacher joins the room. 
    socket.emit("teacher_join_lobby", { pin: pin });

    const playerList = document.getElementById("player-list");
    const startBtn = document.getElementById("start-game-button");
    const countdownEl = document.getElementById("countdown");

    /** Count how many players are shown */
    function countPlayers() {
        return playerList.querySelectorAll("li.player").length;
    }

    /** Enable/disable start button based on number of players in lobby */
    function updateStartButtonState() {
        if (!startBtn) return;
        if (isTeamMode) {
            startBtn.disabled = countPlayers() < 3;
        } else {
            startBtn.disabled = countPlayers() < 2;
        }
    }

    updateStartButtonState();
    updatePlayerCount();
    updateTeamNumSelector();


    function updatePlayerCount() {
        const countEl = document.getElementById("player-count");
        if (!countEl) return;
        const count = countPlayers()
        countEl.textContent = `Players connected: ${count}`;
    }



    // ------- PLAYER EVENTS -------

    socket.on("player_joined", function (data) {
        // Add player name to list of players in the lobby
        console.log("Player joined:", data);

        const { student_id, name } = data;
        if (!student_id) return;

        let li = playerList.querySelector(`li[data-student-id="${student_id}"]`);
        if (!li) {
            li = document.createElement("li");
            li.classList.add("player");
            li.dataset.studentId = student_id;
            playerList.appendChild(li);
        }
        // If they have reconnected, remove the class "player-disconnected" from the element and remove "(disconnected)" from the text of the html.  
        li.classList.remove("player-disconnected");
        li.textContent = name;

        updateStartButtonState();
        updatePlayerCount();
        updateTeamNumSelector();
    });


    socket.on("player_disconnected", function (data) {
        // Remove player name from list of players in the lobby
        console.log("Player disconnected:", data);

        const { student_id } = data;

        if (!student_id) return;

        const li = playerList.querySelector(`li[data-student-id="${student_id}"]`);
        if (li){
            li.remove();
        }

        updateStartButtonState();
        updatePlayerCount();
        updateTeamNumSelector();
    });



    // Bind start button event listener:
    if (startBtn) {
        startBtn.addEventListener("click", () => {
            const payload = {};
            payload.pin = pin;
            if (isTeamMode && !teamSelectContainer.classList.contains("hidden") && teamSelect.options.length > 0) {
                num_teams = parseInt(teamSelect.value);
                if (!num_teams || isNaN(num_teams)){
                    alert("Please select the number of teams before starting the game.")
                    return
                }
                payload.num_teams = num_teams;
            }
            
            console.log("Teacher starting game:", pin);
            startBtn.disabled = true;
            socket.emit("start_game", payload);
        });
    }

    // Server says "no" to starting game
    socket.on("start_denied", (data) => {
        console.log("Start denied:", data);
        alert("Can't start game yet: " + data.reason);
        updateStartButtonState();
    });


    // Game starting countdown
    socket.on("game_starting", (data) => {
        if (data.pin !== pin) return;

        console.log("Game starting with countdown:", data);

        let remaining = 5;

        const countdownBox = document.getElementById("countdown");
        const countdownNumber = countdownBox.querySelector(".countdown-number");

        countdownBox.hidden = false;
        countdownNumber.textContent = remaining;
        const interval = setInterval(() => { // setInterval is a JS function that runs the function given every 1 second, so remaining decrements every second. 
            remaining -= 1;

            if (remaining <= 0) { // Countdown reached 0 so redirect everyone. 
                clearInterval(interval); // Cancel the interval - stop running the setInterval function.
                pinURI = encodeURIComponent(pinElement.textContent.trim());
                window.location.href = `/teacher_game?pin=${pinURI}`;
            } else { // Countdown has not yet reached 0 so update countdown. 
                countdownNumber.textContent = remaining;
            }

        }, 1000); // 1000 milliseconds = 1 second intervals
    });

    function updateTeamNumSelector() {
        if (!teamSelectContainer) return;

        const playerCount = countPlayers();
        console.log("playercount")
        console.log(playerCount)

        if (playerCount < 4) {
            teamSelectContainer.classList.add("hidden");
            return;
        }

        const minTeams = 2;
        const maxTeams = Math.floor(playerCount / 2);

        teamSelect.textContent = "";

        for (let i = minTeams; i <= maxTeams; i++) {
            const opt = document.createElement("option");
            opt.value = i;
            opt.textContent = `${i} teams`;
            teamSelect.appendChild(opt);
        }

        teamSelectContainer.classList.remove("hidden");
    }

});