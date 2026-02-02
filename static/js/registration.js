// no labels checked for wcag yet since unused


let one_time_passcode = document.getElementById("One-time-passcode");
let register_button = document.getElementById("Register");
let added_form = false;
let added_paragraph = false;
let added_password_error = false;
let otpWrapper = document.getElementById("OTP-wrapper"); 

// Get CSRF token rendered by Flask-WTF
const csrfToken = document.querySelector('input[name="csrf_token"]')?.value;

if (!csrfToken) {
  console.log("CSRF token not found in DOM");
}

const form = document.getElementById('registration-form');

form.addEventListener("submit", (event)=>{
    event.preventDefault();
    let name = document.getElementById("name").value;
    let email_address = document.getElementById("email").value;
    let password = document.getElementById("password").value;
    let teacher_student = document.getElementById("teacherorstudent").value;
    

    $.ajax({
        url: "/registration",
        type: "POST",
        // data: {"email":email_address, "name":name,"password":password, "teacherorstudent":teacher_student},
        headers: {"X-CSRFToken": csrfToken},
        data: {"email":email_address,"password": password},
        success: (response) =>{
            let paragraph = document.createElement("p");
            if (response == "otp sent to email" && added_form==false){
                lockRegistrationForm();
                otpWrapper.style.display = "block";
                if (added_paragraph==true){
                    one_time_passcode.textContent = "";
                    added_paragraph=false;
                }
                if (added_password_error==true){
                    let password_error_message_p = document.getElementById("password-reject-error");
                    if (password_error_message_p) {
                        password_error_message_p.textContent = "";}
                    added_password_error = false;
                }
                
                let newForm = document.createElement("form");
                newForm.setAttribute("method", "POST");
                newForm.setAttribute("action", "/registration-check");

                let csrfInput = document.createElement("input");
                csrfInput.type = "hidden";
                csrfInput.name = "csrf_token";
                csrfInput.value = csrfToken;
                newForm.appendChild(csrfInput);
                
                let text = document.createElement("p");
                text.textContent = "An email has been sent to your account. Please input the one-time passcode here.";
                let textBox = document.createElement("input");
                textBox.type = "number";
                textBox.className = "no-spinner";
                textBox.id = "OTPsubmission";
                textBox.name = "OTPsubmission"
                newForm.appendChild(textBox);

                const otpLabel = document.createElement("label");
                otpLabel.setAttribute("for", "OTPsubmission");
                otpLabel.textContent = "One-time passcode";
                newForm.appendChild(otpLabel);
                newForm.appendChild(textBox);

                let hiddenName = document.createElement("input");
                hiddenName.type = "hidden";
                hiddenName.name = "name";
                hiddenName.value = name;
                newForm.appendChild(hiddenName);

                let hiddenEmail = document.createElement("input");
                hiddenEmail.type = "hidden";
                hiddenEmail.name = "email";
                hiddenEmail.value = email_address;
                newForm.appendChild(hiddenEmail);

                let hiddenTeacherStudent = document.createElement("input");
                hiddenTeacherStudent.type = "hidden";
                hiddenTeacherStudent.name = "teacherorstudent";
                hiddenTeacherStudent.value = teacher_student;
                newForm.appendChild(hiddenTeacherStudent);

                let hiddenPassword = document.createElement("input");
                hiddenPassword.type = "hidden";
                hiddenPassword.name = "password";
                hiddenPassword.value = password;
                newForm.appendChild(hiddenPassword);
            

                let submitOTP = document.createElement("input");
                submitOTP.type = "submit";
                submitOTP.className = "primary-btn";
                submitOTP.value = "Submit";

                newForm.appendChild(submitOTP);
                one_time_passcode.appendChild(text);
                one_time_passcode.appendChild(newForm);
                added_form = true;

            }
            else if (response =="otp sent to email"){
                if (added_form == true){
                    one_time_passcode.textContent = "";
                    added_form = false;
                    added_paragraph = false;}
                if(added_form==false){
                    paragraph.textContent = (response);
                    if(added_paragraph==false){
                        one_time_passcode.appendChild(paragraph);
                        added_paragraph = true;
                    }
                }
            }
        },
        error: (xhr) => {
            // PASSWORD ERRORS:
            if (added_password_error == false){
                otpWrapper.style.display = "block";
                one_time_passcode.textContent = "";
                added_password_error = true;
                const p = document.createElement("p");
                
                p.id = "password-reject-error";
                p.textContent = xhr.responseText; // text sent from backend: "password must be ..."
                p.style.color = "red";
                p.style.fontWeight = "500";
                p.setAttribute("role", "alert");
                p.setAttribute("aria-live", "assertive");
                one_time_passcode.appendChild(p);
            }
        }
    });
    return false;
});

function lockRegistrationForm() {
    document.getElementById("name").disabled = true;
    document.getElementById("email").disabled = true;
    document.getElementById("password").disabled = true;
    document.getElementById("teacherorstudent").disabled = true;
    register_button.disabled = true;
    register_button.setAttribute("aria-disabled", "true");
}
