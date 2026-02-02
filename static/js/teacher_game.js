const activeAlerts = {}; // { question_id : alertData }
const flaggedQuestions = {}; // {}
let timerId = null;
let remaining = null;
let timerEl = null;
let socket = null;
let pin = null;

document.addEventListener("DOMContentLoaded", () => {
    socket = io();
    pin = document.getElementById("game-pin").textContent.trim();

    socket.emit("teacher_join_game", { pin });
    console.log("Teacher joined game room", pin);

    socket.on("update_score", (data) => {
        updateScoreRow(data.student_id, data.score);
        reorderLeaderboard();
    });

    //socket.on("player_reconnected", (data) => {
    //    markOnline(data.student_id);
    //});

    //socket.on("player_disconnected", (data) => {
    //    markOffline(data.student_id);
    //});

    socket.on("streak_update", (data) => {
        updateTopStreak(data.student_id, data.name, data.streak);
    });

    socket.on("question_alert", data => {
        console.log("RECEIVED Q ALERT" )
        const qid = data.question_id;
        activeAlerts[qid] = data; // save alert
        renderAlerts();           // update UI
    });

    socket.on("question_clear", data => {
        const qid = data.question_id;

        delete activeAlerts[qid];
        renderAlerts();
    });

    socket.on("update_team_score", (data) => {
        const container = document.getElementById("team-leaderboard");
        if (!container) return; // classic mode

        let card = container.querySelector(
            `.team-card[data-team-id="${data.team_id}"]`
        );

        // Create team card if it doesn't exist
        if (!card) {
            card = document.createElement("div");
            card.classList.add("team-card");
            card.dataset.teamId = data.team_id;

            const nameSpan = document.createElement("span");
            nameSpan.className = "team-name";
            nameSpan.textContent = data.name || "Team";

            const scoreSpan = document.createElement("span");
            scoreSpan.className = "team-score";
            scoreSpan.textContent = "0";

            card.appendChild(nameSpan);
            card.appendChild(scoreSpan);

            container.appendChild(card);
        }

        // Update score
        card.querySelector(".team-score").textContent = data.score;

        reorderTeams();
    });


    socket.on("game_over", () => {
        console.log("GAME OVER received on teacher screen");
        const banner = document.createElement("div");
        banner.id = "gameover-banner";
        banner.textContent = "GAME OVER — Final Scores Locked";
        banner.setAttribute("role", "alert");
        banner.setAttribute("aria-live", "assertive");
        const navbar = document.querySelector("nav");
        if (navbar) {
            navbar.insertAdjacentElement("afterend", banner);
        } else {
            // Fallback if navbar is missing for some reason
            document.body.prepend(banner);
        }
    });

    // Timer:
    timerEl = document.getElementById("timer-value");
    socket.on("timer_sync", (data) => {
        remaining = data.remaining;
        if (!timerEl) return;
        if (timerId) {
            clearInterval(timerId);
        }
        tick(); // render immediately
        timerId = setInterval(tick, 1000);
    });



    socket.on("question_flagged", data => {
        const qid = data.question_id;

        if (flaggedQuestions[qid]) {
            flaggedQuestions[qid].count += 1;
        } else {
            flaggedQuestions[qid] = {
                count: 1,
                question_text: data.question_text,
                choices: data.choices,
                correct_answer: data.correct_answer
            };
        }
        renderFlaggedQuestions();
    });


    socket.on("player_joined_game", data => {
        const container = document.getElementById("scoreboard-body");
        if (!container) return;

        // Avoid duplicates
        if (container.querySelector(`.player-card[data-student-id="${data.student_id}"]`)) {
            return;
        }
        
        const card = document.createElement("div");
        card.className = "player-card";
        card.dataset.studentId = data.student_id;

        // Position number
        const pos = document.createElement("div");
        pos.className = "position-number";

        // Player main wrapper
        const main = document.createElement("div");
        main.className = "player-main";

        const topRow = document.createElement("div");
        topRow.className = "top-row";

        const name = document.createElement("span");
        name.className = "player-name";
        name.textContent = data.name;

        const score = document.createElement("span");
        score.className = "player-score";
        score.textContent = data.score ?? 0;

        topRow.appendChild(name);
        topRow.appendChild(score);
        main.appendChild(topRow);

        card.appendChild(pos);
        card.appendChild(main);

        container.appendChild(card);
        reorderLeaderboard();
    });

        
    reorderLeaderboard();
});

function tick() {
    if (remaining <= 0) {
        remaining = 0;
        clearInterval(timerId);
    }

    const mins = Math.floor(remaining / 60);
    const secs = remaining % 60;

    timerEl.textContent = `${mins}:${secs.toString().padStart(2, "0")}`;
    remaining--;
}


function reorderLeaderboard() {
    const container = document.getElementById("scoreboard-body");
    if (!container) return;

    const cards = Array.from(container.querySelectorAll(".player-card"));

    // Sort by score desc
    cards.sort((a, b) => {
        const scoreA = parseInt(a.querySelector(".player-score").textContent, 10) || 0;
        const scoreB = parseInt(b.querySelector(".player-score").textContent, 10) || 0;
        return scoreB - scoreA;
    });

    // Reinsert + update visuals
    cards.forEach((card, index) => {
        const posNum = card.querySelector(".position-number");
        if (posNum) posNum.textContent = index + 1;

        card.classList.remove("leader", "second", "third");

        // Apply highlights to podiums
        if (index === 0) card.classList.add("leader");
        else if (index === 1) card.classList.add("second");
        else if (index === 2) card.classList.add("third");

        container.appendChild(card);
    });
}

function reorderTeams() {
    const container = document.getElementById("team-leaderboard");
    if (!container) return;

    const cards = Array.from(container.querySelectorAll(".team-card"));

    cards.sort((a, b) => {
        const scoreA = parseInt(a.querySelector(".team-score").textContent, 10) || 0;
        const scoreB = parseInt(b.querySelector(".team-score").textContent, 10) || 0;
        return scoreB - scoreA;
    });

    cards.forEach((card, index) => {
        // Highlight the leading team
        card.classList.toggle("leader", index === 0);
        // Reinsert in correct order
        container.appendChild(card);
    });
}



function updateScoreRow(student_id, newScore) {
    const card = document.querySelector(`.player-card[data-student-id="${student_id}"]`);
    if (!card) return;
    card.querySelector(".player-score").textContent = newScore;
    reorderLeaderboard();
}

//function markOnline(student_id) {
    //const card = document.querySelector(`.player-card[data-student-id="${student_id}"]`);
    //if (!card) return;
    //card.classList.remove("player-disconnected");
    //card.querySelector(".player-status").textContent = "Online";
//}

//function markOffline(student_id) {
    //const card = document.querySelector(`.player-card[data-student-id="${student_id}"]`);
    //if (!card) return;
    //card.classList.add("player-disconnected");
    //card.querySelector(".player-status").textContent = "Disconnected";
//}


// Top streak widget handling - update only if top streak was beaten, or is tied.
let topStreakValue = 0;
let topStreakLatestStudent = null;

function updateTopStreak(student_id, name, streak) {
    const widget = document.getElementById("streak-widget");
    if (!widget) return;

    const empty = widget.querySelector(".streak-empty");
    const details = widget.querySelector(".streak-details");

    // Determine if this student becomes the new displayed streak
    if (streak > topStreakValue) {
        topStreakValue = streak;
        topStreakLatestStudent = student_id;
    } else if (streak === topStreakValue) {
        // If tied, the newest person wins
        topStreakLatestStudent = student_id;
    } else {
        return; // Not a new top streak
    }

    // Update UI
    empty.style.display = "none";
    details.style.display = "block";

    details.querySelector(".streak-player-name").textContent = name;
    details.querySelector(".streak-value").textContent = streak;
}



function renderAlerts() {
    const list = document.getElementById("question-alerts");
    const noAlerts = document.getElementById("no-alerts");

    list.innerHTML = "";

    const keys = Object.keys(activeAlerts);
    if (keys.length === 0) {
        noAlerts.style.display = "block";
        return;
    }

    noAlerts.style.display = "none";

    keys.forEach(qid => {
        const data = activeAlerts[qid];

        const li = document.createElement("li");
        li.classList.add("alert-item");

        // Question text
        const strong = document.createElement("strong");
        strong.textContent = data.question_text;
        li.appendChild(strong);
        li.appendChild(document.createElement("br"));

        // Accuracy
        const acc = document.createElement("div");
        acc.textContent = `Accuracy: ${(data.accuracy * 100).toFixed(1)}%`;
        li.appendChild(acc);

        // Response rate
        const rate = document.createElement("div");
        rate.textContent = `Response rate: ${(data.response_rate * 100).toFixed(1)}%`;
        li.appendChild(rate);

        // Show answer button
        const btn = document.createElement("button");
        btn.classList.add("show-answer-btn", "secondary-btn");
        btn.dataset.qid = qid;
        btn.textContent = "Show Correct Answer";
        li.appendChild(btn);

        // Choices list
        const ul = document.createElement("ul");
        ul.className = "choices";

        data.choices.forEach(choice => {
            const c = document.createElement("li");
            c.className = "choice-box";
            c.dataset.choice = choice;
            c.textContent = choice;
            ul.appendChild(c);
        });

        li.appendChild(ul);
        list.appendChild(li);
    });

    // Attach button logic after creating elements
    document.querySelectorAll(".show-answer-btn").forEach(btn => {
        btn.addEventListener("focus", showCorrectAnswer);
        btn.addEventListener("blur", hideCorrectAnswer);
        btn.addEventListener("mouseenter", showCorrectAnswer);
        btn.addEventListener("mouseleave", hideCorrectAnswer);
    });
}


function renderFlaggedQuestions() {
    const list = document.getElementById("flagged-questions");
    const noFlagged = document.getElementById("no-flagged");

    list.innerHTML = "";

    const keys = Object.keys(flaggedQuestions);
    if (keys.length === 0) {
        noFlagged.style.display = "block";
        return;
    }

    noFlagged.style.display = "none";

    // Sort by frequency (descending)
    keys
        .sort((a, b) => flaggedQuestions[b].count - flaggedQuestions[a].count)
        .forEach(qid => {
            const data = flaggedQuestions[qid];

            const li = document.createElement("li");
            li.classList.add("alert-item");

            // Header
            const header = document.createElement("div");
            header.className = "alert-header";

            const strong = document.createElement("strong");
            strong.textContent = data.question_text;
            header.appendChild(strong);

            const dismiss = document.createElement("button");
            dismiss.classList.add("dismiss-flag-btn", "delete-btn");
            dismiss.dataset.qid = qid;
            dismiss.setAttribute("aria-label", "Dismiss flagged question");
            dismiss.textContent = "✖";
            header.appendChild(dismiss);

            li.appendChild(header);

            // Flag count
            const count = document.createElement("div");
            count.textContent = `Flag count: ${data.count}`;
            li.appendChild(count);
            li.appendChild(document.createElement("br"));

            // Show answer button
            const btn = document.createElement("button");
            btn.classList.add("show-answer-btn", "secondary-btn");
            btn.dataset.qid = qid;
            btn.textContent = "Show Correct Answer";
            li.appendChild(btn);

            // Choices
            const ul = document.createElement("ul");
            ul.className = "choices";

            data.choices.forEach(choice => {
                const c = document.createElement("li");
                c.className = "choice-box";
                c.dataset.choice = choice;
                c.textContent = choice;
                ul.appendChild(c);
            });

            li.appendChild(ul);
            list.appendChild(li);
        });

    document.querySelectorAll("#flagged-questions .show-answer-btn").forEach(btn => {
        btn.addEventListener("focus", showCorrectFlaggedAnswer);
        btn.addEventListener("blur", hideCorrectAnswer);
        btn.addEventListener("mouseenter", showCorrectFlaggedAnswer);
        btn.addEventListener("mouseleave", hideCorrectAnswer);
    });

    document.querySelectorAll(".dismiss-flag-btn").forEach(btn => {
    btn.addEventListener("click", e => {
        const qid = e.target.dataset.qid;

        // Tell server to delete it from DB
        socket.emit("dismiss_flagged_question", {
            pin: pin,
            question_id: qid
        });

        delete flaggedQuestions[qid];
        renderFlaggedQuestions();
    });
});
}


function showCorrectAnswer(e) {
    const qid = e.target.dataset.qid;
    const correct = activeAlerts[qid].correct_answer;

    const alertItem = e.target.closest(".alert-item")

    alertItem.querySelectorAll(".choice-box").forEach(box => {
        if (box.dataset.choice === correct) {
            if (!box.dataset.originalText) {
                box.dataset.originalText = box.textContent;
            }
            box.classList.add("correct-highlight");
            box.textContent = `${box.textContent} (Correct answer)`;
        }
    });
}

function showCorrectFlaggedAnswer(e) {
    const qid = e.target.dataset.qid;
    const correct = flaggedQuestions[qid].correct_answer;
    const alertItem = e.target.closest(".alert-item")
    alertItem.querySelectorAll(".choice-box").forEach(box => {
        if (box.dataset.choice === correct) {
            if (!box.dataset.originalText) {
                box.dataset.originalText = box.textContent;
            }
            box.classList.add("correct-highlight");
            box.textContent = `${box.textContent} (Correct answer)`;
        }
    });
}


function hideCorrectAnswer() {
    document.querySelectorAll(".choice-box").forEach(box => {
        box.classList.remove("correct-highlight");
        if (box.dataset.originalText) {
            box.textContent = box.dataset.originalText;
            delete box.dataset.originalText;
        }
    });
}