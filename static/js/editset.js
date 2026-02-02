
let csrfToken = null;

document.addEventListener("DOMContentLoaded", function () {

    csrfToken = document.querySelector('input[name="csrf_token"]')?.value;

    if (!csrfToken) {
    console.log("CSRF token not found in DOM");
    }
    bindEditSetButtons();
    bindDeleteButtons();
});

function bindDeleteButtons(){
    // Delete Set confirm
    document.querySelectorAll(".delete-set-form").forEach(form => {
        form.addEventListener("submit", function (e) {
        const ok = confirm("Delete this Q&A set?\n\nThis will delete all questions inside it.");
        if (!ok) e.preventDefault();
        });
    });
}

// Bind edit set questions to event handlers.
function bindEditSetButtons() {
    let editButtons = document.getElementsByClassName("edit-set-btn");

    for (let btn of editButtons) {
        btn.onclick = function (event) {
            event.preventDefault();
            openSetEditForm(btn);
        };
    }
}

// Open edit form to show new fields to fill in
function openSetEditForm(button) {

    let setId = button.value;
    let card = document.getElementById("set-card-" + setId);
    let setName = document.getElementById("set-name-" + setId).value;
    let isPrivate = document.getElementById("set-private-" + setId).value === "1";

    // Save original HTML
    let originalHTML = card.innerHTML;

    card.innerHTML = "";

    // Wrapper
    let wrapper = document.createElement("div");
    wrapper.className = "form-box";

    // Heading
    let heading = document.createElement("h3");
    heading.textContent = "Edit Q&A Set";
    wrapper.appendChild(heading);

    // Label (name)
    let labelName = document.createElement("label");
    labelName.setAttribute("for", `edit-set-name-${setId}`);
    labelName.textContent = "Name";
    wrapper.appendChild(labelName);

    // Input (name)
    let inputName = document.createElement("input");
    inputName.type = "text";
    inputName.id = `edit-set-name-${setId}`;
    inputName.className = "input-text";
    inputName.value = setName;   // SAFE
    wrapper.appendChild(inputName);

    // Privacy label
    let privacyLabel = document.createElement("label");
    privacyLabel.style.marginTop = "10px";

    // Checkbox
    let checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.id = `edit-set-private-${setId}`;
    checkbox.checked = isPrivate;

    privacyLabel.appendChild(checkbox);
    privacyLabel.appendChild(document.createTextNode(" Private"));
    wrapper.appendChild(privacyLabel);

    // Actions
    let actions = document.createElement("div");
    actions.className = "action-row";

    // Save button
    let saveBtn = document.createElement("button");
    saveBtn.classList = "secondary-btn view-btn";
    saveBtn.id = `save-set-${setId}`;
    saveBtn.textContent = "Save";
    actions.appendChild(saveBtn);

    // Cancel button
    let cancelBtn = document.createElement("button");
    cancelBtn.classList = "secondary-btn delete-btn";
    cancelBtn.id = `cancel-set-${setId}`;
    cancelBtn.textContent = "Cancel";
    actions.appendChild(cancelBtn);

    wrapper.appendChild(actions);
    card.appendChild(wrapper);


    // Bind save/cancel
    document.getElementById("save-set-" + setId).onclick = function () {
        saveSet(setId, originalHTML);
    };
    document.getElementById("cancel-set-" + setId).onclick = function () {
        cancelSetEdit(setId, originalHTML);
    };
}

// Cancel edit restores original HTML
function cancelSetEdit(setId, originalHTML) {
    let card = document.getElementById("set-card-" + setId);
    card.innerHTML = originalHTML;
    bindEditSetButtons();
    bindDeleteButtons();
}

// Save edit using AJAX
function saveSet(setId, originalHTML) {

    let newName = document.getElementById("edit-set-name-" + setId).value;
    let newPrivate = document.getElementById("edit-set-private-" + setId).checked ? 1 : 0;

    let card = document.getElementById("set-card-" + setId);

    $.ajax({
        url: "/editset",
        type: "POST",
        headers: { "X-CSRFToken": csrfToken },
        data: {
            setid: setId,
            newname: newName,
            newprivate: newPrivate
        },

        success: function (response) {
            // Restore normal view
            card.innerHTML = originalHTML;

            // Rebind edit buttons
            bindEditSetButtons();
            bindDeleteButtons();

            // Update displayed name
            let title = card.querySelector(".card-title");
            if (title) title.textContent = newName;
            let privacyDiv = card.querySelector(".set-privacy");
            if (privacyDiv) {
                privacyDiv.textContent = (newPrivate === 1 ? "Private" : "Public"); // Set the privacy label text based on whether the set is marked as private or public
            }           

            // Update hidden inputs
            document.getElementById("set-name-" + setId).value = newName;
            document.getElementById("set-private-" + setId).value = newPrivate;
        },
        error: function(xhr) {
            alert("Error updating set: " + xhr.responseText);
        }
    });
}