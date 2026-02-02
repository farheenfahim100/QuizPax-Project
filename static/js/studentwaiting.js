
document.addEventListener("DOMContentLoaded", () => {
    const socket = io();

    const pinEl = document.getElementById("waiting-pin");
    if (!pinEl) {
        console.error("waiting-pin element not found");
        return;
    }

    const pin = pinEl.textContent.trim();
    console.log("Student joining lobby room:", pin);

    socket.emit("student_join_lobby", { pin: pin });

    const countdownBox = document.getElementById("student-countdown");
    const countdownNumber = document.getElementById("student-countdown-number");


    // Teacher starts the game - countdown on student screen
    socket.on("game_starting", (data) => {
        if (data.pin !== pin) return;

        console.log("Game starting in...", data.countdown);
        const status = document.getElementById("status");
        status.hidden = true;
        let remaining = data.countdown || 5;

        countdownBox.hidden = false;
        countdownNumber.textContent = remaining;

        const interval = setInterval(() => {
            remaining -= 1;

            if (remaining <= 0) {
                clearInterval(interval);
                window.location.href = `/play_game?pin=${pin}`;
            } else {
                countdownNumber.textContent = remaining;
            }
        }, 1000);
    });


    socket.on("game_closed", function(data) {
        console.log("Game was closed by teacher:", data);
        alert("The teacher has closed the game or left the lobby.");
        window.location.href = "/entercode";
    });

    socket.on("game_started", () => {
        console.log("Game started (instant redirect)");
        window.location.href = `/play_game?pin=${pin}`;
    });

});