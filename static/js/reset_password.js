let forgotten_password = document.getElementById("forgottenPassword");
let sendOTP_button = document.getElementById("SendOTP");
let added_form = false;
let added_paragraph = false;
let otpWrapper = document.getElementById("OTP-wrapper");
let added_email_error = false;
const csrfToken = document.querySelector('input[name="csrf_token"]')?.value;

if (!csrfToken) {
  console.log("CSRF token not found in DOM");
}


sendOTP_button.addEventListener("click", (event)=>{
    event.preventDefault();
    let email_address = document.getElementById("email").value;
    
    $.ajax({
        url: "/reset-password",
        type: "POST",
        data: {"email":email_address},
        headers: {"X-CSRFToken": csrfToken},
        success: (response) =>{
            let paragraph = document.createElement("p");
            if (response == "otp sent to email" && added_form == false){
                otpWrapper.style.display = "block";
                lockResetPasswordForm();
                if(added_paragraph==true){
                    forgotten_password.removeChild(forgotten_password.children[0]);
                    added_paragraph=false;
                }

                if (added_email_error==true){
                    let email_error_message_p = document.getElementById("reset-reject-error");
                    if (email_error_message_p) {
                        email_error_message_p.textContent = "";}
                    added_email_error = false;
                }

                let newForm = document.createElement("form");
                newForm.setAttribute("method", "POST");
                newForm.setAttribute("action", "/resetp-check");

                let csrfInput = document.createElement("input");
                csrfInput.type = "hidden";
                csrfInput.name = "csrf_token";
                csrfInput.value = csrfToken;
                newForm.appendChild(csrfInput);

                let textBox = document.createElement("input");
                textBox.type = "number";
                textBox.className = "no-spinner";
                textBox.id = "OTPsubmission";
                textBox.name = "OTPsubmission"
                newForm.appendChild(textBox);
                newForm.appendChild(document.createElement("br"))

                let otpLabel = document.createElement("label");
                otpLabel.setAttribute("for", "OTPsubmission");
                otpLabel.textContent = "One-time passcode."
                newForm.appendChild(otpLabel);
                newForm.appendChild(document.createElement("br"))

                let hiddenEmail = document.createElement("input");
                hiddenEmail.type = "hidden";
                hiddenEmail.name = "email";
                hiddenEmail.value = email_address;
                newForm.appendChild(hiddenEmail);

                let passwordLabel = document.createElement("label");
                passwordLabel.textContent = "Enter new password:"
                newForm.appendChild(passwordLabel);
                newForm.appendChild(document.createElement("br"))

                let myPassword = document.createElement("input");
                myPassword.type = "password";
                myPassword.name = "password";
                myPassword.id = "password";
                myPassword.setAttribute("autocomplete", "new-password");
                newForm.appendChild(myPassword);
                newForm.appendChild(document.createElement("br"))

                let submitOTP = document.createElement("input");
                submitOTP.type = "submit";
                submitOTP.value = "Submit";
                submitOTP.className = "primary-btn";
                
                
                newForm.style.display = "flex";
                newForm.style.flexDirection = "column";
                newForm.style.gap = "12px";

                newForm.appendChild(submitOTP);
                forgotten_password.appendChild(newForm);
                added_form = true;
            }
            else if (response != "otp sent to email"){
                if(added_form==true){
                    forgotten_password.removeChild(forgotten_password.children[0]);
                    forgotten_password.removeChild(forgotten_password.children[0]);
                    added_form = false;
                }   
                else{
                    paragraph.textContent = ("Unable to send email to your account. Please try again");
                    if (added_paragraph == false){
                        forgotten_password.appendChild(paragraph);
                        added_paragraph = true;
                    }
                }
            }
        },
        error: (xhr) => {
            if (added_email_error == false){
                otpWrapper.style.display = "block";
                forgotten_password.textContent = "";
                added_email_error = true;

                const p = document.createElement("p");
                p.id = "reset-reject-error";
                p.textContent = xhr.responseText;
                p.style.color = "red";
                p.style.fontWeight = "500";
                p.setAttribute("role", "alert");
                p.setAttribute("aria-live", "assertive");
            

                forgotten_password.appendChild(p);
            }
        }
    });
    return false
});


function lockResetPasswordForm() {
    document.getElementById("email").disabled = true;
    sendOTP_button.disabled = true;
    sendOTP_button.setAttribute("aria-disabled", "true");
}