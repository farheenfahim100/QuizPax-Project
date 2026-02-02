let csrfToken = null;



document.addEventListener("DOMContentLoaded", function () {
    csrfToken = document.querySelector('input[name="csrf_token"]')?.value;

    if (!csrfToken) {
        console.error("CSRF token not found in DOM");
    }

    bindEditQuestionButtons();
    bindDeleteQuestionButtons();

});

// Delete Question confirm:
function bindDeleteQuestionButtons() {
    document.querySelectorAll(".delete-question-form").forEach(form => {
        form.addEventListener("submit", function (e) {
        const ok = confirm("Delete this question?\n\nThis action cannot be undone.");
        if (!ok) e.preventDefault();
        });
    });

}


// Bind edit question buttons to event handlers
function bindEditQuestionButtons() {
    let editButtons = document.getElementsByClassName("edit-question-btn");

    for (let btn of editButtons) {
        btn.onclick = function (event) {
            event.preventDefault();
            openQuestionEditForm(btn);
        };
    }
}

// Opens the edit question form to show new fields to fill in
function openQuestionEditForm(button) {

    let qid = button.value;
    let card = document.getElementById("question-card-" + qid);

    let qtext = document.getElementById("q-question-" + qid).value;
    let ans = document.getElementById("q-answer-" + qid).value;
    let f1 = document.getElementById("q-f1-" + qid).value;
    let f2 = document.getElementById("q-f2-" + qid).value;
    let f3 = document.getElementById("q-f3-" + qid).value;

    let originalHTML = card.innerHTML;

    card.innerHTML = "";
    
    // Outer wrapper
    let wrapper = document.createElement("div");
    wrapper.className = "form-box";

    // Heading
    let heading = document.createElement("h3");
    heading.textContent = "Edit Question";
    wrapper.appendChild(heading);

    // Label + input: Question
    let labelQ = document.createElement("label");
    labelQ.setAttribute("for", `edit-q-${qid}`);
    labelQ.textContent = "Question:";
    wrapper.appendChild(labelQ);

    let inputQ = document.createElement("input");
    inputQ.type = "text";
    inputQ.id = `edit-q-${qid}`;
    inputQ.className = "input-text";
    inputQ.value = qtext;
    wrapper.appendChild(inputQ);

    // Label + input: Correct Answer
    let labelA = document.createElement("label");
    labelA.setAttribute("for", `edit-a-${qid}`);
    labelA.textContent = "Correct Answer:";
    wrapper.appendChild(labelA);

    let inputA = document.createElement("input");
    inputA.type = "text";
    inputA.id = `edit-a-${qid}`;
    inputA.className = "input-text";
    inputA.value = ans;
    wrapper.appendChild(inputA);

    // Label + input: Fake Answer 1
    let labelF1 = document.createElement("label");
    labelF1.setAttribute("for", `edit-f1-${qid}`);
    labelF1.textContent = "Fake Answer 1:";
    wrapper.appendChild(labelF1);

    let inputF1 = document.createElement("input");
    inputF1.type = "text";
    inputF1.id = `edit-f1-${qid}`;
    inputF1.className = "input-text";
    inputF1.value = f1;
    wrapper.appendChild(inputF1);

    // Label + input: Fake Answer 2
    let labelF2 = document.createElement("label");
    labelF2.setAttribute("for", `edit-f2-${qid}`);
    labelF2.textContent = "Fake Answer 2:";
    wrapper.appendChild(labelF2);

    let inputF2 = document.createElement("input");
    inputF2.type = "text";
    inputF2.id = `edit-f2-${qid}`;
    inputF2.className = "input-text";
    inputF2.value = f2;
    wrapper.appendChild(inputF2);

    // Label + input: Fake Answer 3
    let labelF3 = document.createElement("label");
    labelF3.setAttribute("for", `edit-f3-${qid}`);
    labelF3.textContent = "Fake Answer 3:";
    wrapper.appendChild(labelF3);

    let inputF3 = document.createElement("input");
    inputF3.type = "text";
    inputF3.id = `edit-f3-${qid}`;
    inputF3.className = "input-text";
    inputF3.value = f3;
    wrapper.appendChild(inputF3);

    // Action buttons container
    let actions = document.createElement("div");
    actions.className = "folder-actions";
    actions.style.marginTop = "15px";

    // Save button
    let saveBtn = document.createElement("button");
    saveBtn.classList = "secondary-btn view-btn";
    saveBtn.id = `save-q-${qid}`;
    saveBtn.textContent = "Save";
    actions.appendChild(saveBtn);

    // Cancel button
    let cancelBtn = document.createElement("button");
    cancelBtn.classList = "secondary-btn delete-btn";
    cancelBtn.id = `cancel-q-${qid}`;
    cancelBtn.textContent = "Cancel";
    actions.appendChild(cancelBtn);

    // Assemble
    wrapper.appendChild(actions);
    card.appendChild(wrapper);
    // Bind Save + Cancel buttons
    document.getElementById("save-q-" + qid).onclick = function () {
        saveQuestion(qid, originalHTML);
    };

    document.getElementById("cancel-q-" + qid).onclick = function () {
        cancelQuestionEdit(qid, originalHTML);
    };
}

// Cancell restores original HTML
function cancelQuestionEdit(qid, originalHTML) {
    let card = document.getElementById("question-card-" + qid);
    card.innerHTML = originalHTML;
    bindEditQuestionButtons();
    bindDeleteQuestionButtons();
}

// Save edited question using AJAX
function saveQuestion(qid, originalHTML) {

    let newQ = document.getElementById("edit-q-" + qid).value;
    let newA = document.getElementById("edit-a-" + qid).value;
    let f1 = document.getElementById("edit-f1-" + qid).value;
    let f2 = document.getElementById("edit-f2-" + qid).value;
    let f3 = document.getElementById("edit-f3-" + qid).value;

    let card = document.getElementById("question-card-" + qid);

    $.ajax({
        url: "/editquestion",
        type: "POST",
        headers: { "X-CSRFToken": csrfToken },
        data: {
            qid: qid,
            question: newQ,
            answer: newA,
            fakeans1: f1,
            fakeans2: f2,
            fakeans3: f3
        },

        success: function (response) {
            // Restore card layout
            card.innerHTML = originalHTML;

            // Rebind button
            bindEditQuestionButtons();
            bindDeleteQuestionButtons();

            // Update visible text
            card.querySelector(".question-text").textContent = newQ;
            card.querySelector(".answer-value").textContent = newA;
            let fakePara = card.querySelector("p:nth-of-type(2)");
            fakePara.textContent = `Fake Answers: ${f1}, ${f2}, ${f3}`;

            // Update hidden fields
            document.getElementById("q-question-" + qid).value = newQ;
            document.getElementById("q-answer-" + qid).value = newA;
            document.getElementById("q-f1-" + qid).value = f1;
            document.getElementById("q-f2-" + qid).value = f2;
            document.getElementById("q-f3-" + qid).value = f3;
        },
        error: function(xhr) {
            alert("Error updating question: " + xhr.responseText);
        }
    });
}