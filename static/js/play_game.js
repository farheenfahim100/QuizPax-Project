document.addEventListener("DOMContentLoaded", () => {
    const socket = io();

    const pin = document.getElementById("game-pin").textContent.trim();
    const studentId = document.getElementById("student-id").textContent.trim();
    let gameEnded = false;
    

    socket.emit("student_join_game", { pin, student_id: studentId });

    console.log("Student joined game room:", pin);

    const questionBox = document.getElementById("question-box");
    const feedbackBox = document.getElementById("feedback");
    const scoreBox = document.getElementById("current-score");
    const flagBtn = document.getElementById("flag-question-btn");

    const choiceButtons = [
        document.getElementById("choice1"),
        document.getElementById("choice2"),
        document.getElementById("choice3"),
        document.getElementById("choice4")
    ];

    choiceButtons.forEach(btn => btn.disabled = true);

    let pendingNextQuestion = null;
    let answeringLocked = false;
    let currentQuestionId = null;
    let hasFlaggedCurrentQuestion = false;

    

    // Receive a new question - get rid of feedback overlay, and change buttons and questions text.
    socket.on("new_question", (data) => {
        console.log("new question arrival")
        answeringLocked = false;
        currentQuestionId = data.question_id;
        // Reset flag button for the new question
        hasFlaggedCurrentQuestion = false;
        if (flagBtn) flagBtn.disabled = false;
        questionBox.textContent = data.question;
        console.log("done adding question text")
        const overlay = document.getElementById("feedback-overlay");
        overlay.classList.add("hidden");

        // Fill buttons with possible answers
        data.choices.forEach((choice, index) => {
            const btn = choiceButtons[index];

            btn.disabled = false;
            btn.removeAttribute("aria-hidden");
            // btn.style.display = "inline-block";
            btn.textContent = choice;
            // btn.setAttribute("aria-label", choice);

            btn.onclick = () => {
                if (answeringLocked) return;
                answeringLocked = true;
                socket.emit("answer_submitted", {
                    pin,
                    student_id: studentId,
                    question_id: currentQuestionId,
                    answer: choice
                });
            };
        });

        // Hide unused buttons (if fewer than 4 choices)
        //for (let i = data.choices.length; i < 4; i++) {
        //    choiceButtons[i].style.display = "none";
        //}
    });

    // Score updates - change HTML element's text.
    socket.on("update_score", (data) => {
        if (data.student_id == studentId) {
            scoreBox.textContent = data.score;
        }
    });

    // Show feedback for question attempt. Longer delay for incorrect answer.
    socket.on("answer_feedback", (data) => {
        console.log("FEEDBACK:", data);
        const overlay = document.getElementById("feedback-overlay");
        const textBox = document.getElementById("feedback-text");


        overlay.classList.remove("hidden", "correct", "wrong");

        let delay;

        if (data.correct) {
            overlay.classList.add("correct");
            textBox.textContent = "Correct!";
            delay = 500;
        } else {
            overlay.classList.add("wrong");
            textBox.textContent = "Incorrect! Correct answer: " + data.correct_answer;
            delay = 3000;
        }

        overlay.classList.remove("hidden");

        // Add delay for showing the feedback
        setTimeout(() => {
            if (gameEnded) return;
            overlay.classList.add("hidden");

            // Request next question
            socket.emit("request_next_question", {
                pin,
                student_id: studentId
            });

        }, delay);
    });

    // Game over - display the overlay and disable buttons
    socket.on("game_over", (data) => {
        console.log("GAME OVER received: ", data);
        gameEnded = true;
        // Disable ALL answering permanently
        choiceButtons.forEach(btn => {
            btn.disabled = true;
            btn.style.display = "none";
            btn.setAttribute("aria-hidden", "true");
        });
        flagBtn.disabled = true;
        questionBox.textContent = "Game Over!";
        feedbackBox.textContent = "";

        // Show overlay
        const overlay = document.getElementById("feedback-overlay");
        const textBox = document.getElementById("feedback-text");

        // Clear previous content safely
        while (textBox.firstChild) {
            textBox.removeChild(textBox.firstChild);
        }

        overlay.classList.remove("correct", "wrong");
        if (!data || data.position === undefined) {
            const msg = document.createElement("p");
            msg.textContent = "GAME OVER!";
            textBox.appendChild(msg);
        }
        else {
            // Game over title
            const title = document.createElement("h5");
            title.textContent = "Game Over - Your Results:";

            // Final score
            const score = document.createElement("p");
            score.textContent = `Final Score: ${data.score}`;

            // Final position
            const position = document.createElement("p");
            position.textContent = `Final Position: ${data.position} / ${data.total_players}`;

            // Highest streak
            const streak = document.createElement("p");
            streak.textContent = `Highest Streak: ${data.highest_streak}`;

            // Return to dashboard button
            const link = document.createElement("a");
            link.href = "/dashboard";
            link.className = "primary-btn has-arrow";
            link.style.padding = "5px 5px";
            // Label span (for text)
            const label = document.createElement("span");
            label.className = "label";
            label.textContent = "Return to Dashboard";
            // Arrow span (for ->)
            const arrow = document.createElement("span");
            arrow.className = "arrow";
            arrow.textContent = "→";

            link.appendChild(label);
            link.appendChild(arrow);


            // Append to overlay
            textBox.appendChild(title);
            textBox.appendChild(score);
            textBox.appendChild(position);
            textBox.appendChild(streak);
            textBox.appendChild(link);

        }
        overlay.classList.remove("hidden");

    });

    socket.on("team_info", (data) => {
        const el = document.getElementById("teacher-status");
        if (!el) return;

        el.textContent = `You are on ${data.team_name}`;
        setTimeout(() => el.textContent = "", 5000);
    });

    // React to teacher disconnect/reconnect
    socket.on("teacher_disconnected", () => {
        console.log("Teacher disconnected from the game");
        const ts = document.getElementById("teacher-status");
        if (ts) {
            ts.textContent = "The teacher has temporarily disconnected. Please wait...";
        }
    });

    socket.on("teacher_reconnected_game", () => {
        console.log("Teacher reconnected");
        const ts = document.getElementById("teacher-status");
        if (ts) {
            ts.textContent = "";
        }
    });

    if (flagBtn) {
        flagBtn.addEventListener("click", () => {
            if (hasFlaggedCurrentQuestion || !currentQuestionId) return;

            socket.emit("flag_question", {pin,student_id: studentId,question_id: currentQuestionId});

            hasFlaggedCurrentQuestion = true;
            flagBtn.disabled = true;
        });
    }

});