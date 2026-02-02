window.CSRF_TOKEN =document.querySelector('meta[name="csrf-token"]')?.getAttribute("content");

if (!window.CSRF_TOKEN) {
  console.log("CSRF token not found in DOM");
}


document.addEventListener("DOMContentLoaded", function () {
    bindEditButtons();
    bindDeleteButtons();
});


function bindDeleteButtons(){
    document.querySelectorAll(".delete-folder-form").forEach(form => {
            form.addEventListener("submit", function (e) {
                const confirmed = confirm(
                    "Delete this folder?\n\nThis action cannot be undone."
                );
                if (!confirmed) {
                    e.preventDefault();
                }
            });
    });
}


// Bind all edit buttons - have event handler for each one to open the edit form.
function bindEditButtons() {
    let editButtons = document.getElementsByClassName("edit-folder-btn");

    for (let btn of editButtons) {
        btn.onclick = function (event) {
            event.preventDefault();
            openEditForm(btn);
        };
    }
}

// Rebind the edit button after it has been pressed.
function rebindSingleEditButton(folderId) {
    let btn = document.querySelector(`#folder-card-${folderId} .edit-folder-btn`);
    btn.onclick = function (event) {
        event.preventDefault();
        openEditForm(btn);
    };
}

// Opens the edit form when button is clicked.
function openEditForm(button) {

    let folderId = button.value;
    let card = document.getElementById("folder-card-" + folderId);
    let folderName = document.getElementById("folder-name-" + folderId).value;

    // Store original HTML 
    let originalHTML = card.innerHTML;
    card.innerHTML = "";

    // Wrapper
    let wrapper = document.createElement("div");
    wrapper.className = "form-box";

    // Heading
    let heading = document.createElement("h3");
    heading.textContent = "Edit Folder";
    wrapper.appendChild(heading);

    // Label
    let label = document.createElement("label");
    label.setAttribute("for", `edit-name-${folderId}`);
    label.textContent = "Folder name";
    wrapper.appendChild(label);

    // Input
    let input = document.createElement("input");
    input.type = "text";
    input.id = `edit-name-${folderId}`;
    input.value = folderName;   
    wrapper.appendChild(input);

    // Buttons container
    let actions = document.createElement("div");
    actions.className = "action-row";

    // Save button
    let saveBtn = document.createElement("button");
    saveBtn.classList = "secondary-btn view-btn";
    saveBtn.id = `save-${folderId}`;
    saveBtn.textContent = "Save";
    actions.appendChild(saveBtn);

    // Cancel button
    let cancelBtn = document.createElement("button");
    cancelBtn.classList = "secondary-btn delete-btn";
    cancelBtn.id = `cancel-${folderId}`;
    cancelBtn.textContent = "Cancel";
    actions.appendChild(cancelBtn);

    wrapper.appendChild(actions);
    card.appendChild(wrapper);

    // Bind SAVE + CANCEL buttons
    document.getElementById("save-" +folderId).onclick = function () {
        saveFolder(folderId, originalHTML);
    };

    document.getElementById("cancel-" +folderId).onclick = function () {
        cancelEdit(folderId, originalHTML);
    };
}

// Cancel edit - restores the old HTML
function cancelEdit(folderId, originalHTML) {
    let card = document.getElementById("folder-card-" + folderId);
    card.innerHTML = originalHTML;
    rebindSingleEditButton(folderId);
    bindDeleteButtons();
}

// Save edit using AJAX
function saveFolder(folderId, originalHTML) {

    let newName = document.getElementById("edit-name-" +folderId).value;
    let card = document.getElementById("folder-card-" + folderId);

    $.ajax({
        url: "/editfolder",
        type: "POST",
        headers: { "X-CSRFToken": window.CSRF_TOKEN },
        data: { 
            folderid: folderId,
            newname: newName
        },

        success: function (response) {
            // restore original HTML
            card.innerHTML = originalHTML;

            // re-bind edit button
            rebindSingleEditButton(folderId);
            bindDeleteButtons();

            // update visible folder name
            let title = card.querySelector(".folder-title h3");
            if (title) title.textContent = newName;

            // update hidden input
            let hidden = document.getElementById("folder-name-" + folderId);
            if (hidden) hidden.value = newName;
        },
        error: function(xhr) {
            alert("Error updating folder: " + xhr.responseText);
        }
    });
}