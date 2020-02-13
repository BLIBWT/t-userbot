//    Copyright (C) 2020 BLIBWT

//    This program is free software: you can redistribute it and/or modify
//    it under the terms of the GNU Affero General Public License as published by
//    the Free Software Foundation, either version 3 of the License, or
//    (at your option) any later version.

//    This program is distributed in the hope that it will be useful,
//    but WITHOUT ANY WARRANTY; without even the implied warranty of
//    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//    GNU Affero General Public License for more details.

//    You should have received a copy of the GNU Affero General Public License
//    along with this program.  If not, see <https://www.gnu.org/licenses/>.

/* Deployment */
var deployment = (document.getElementById("deployment")) ? document.getElementById("deployment") : null;
if (deployment !== null) {
  deployment_form = (deployment.getElementById("botConfiguration")) ? deployment.getElementById("botConfiguration") : null;
  if (deployment_form !== null) {
    deployment_form_submit = (deployment_form.getElementById("botInstall")) ? deployment_form.getElementById("botInstall") : null;

    if (deployment_form_submit !== null) {
      deployment_form_submit.addEventListener('click', function(e) {
        'use strict';
        e.preventDefault();

        var telegram_api_id = (deployment_form.getElementById("api_id")) ? deployment_form.getElementById("api_id") : null;
        var telegram_api_hash = (deployment_form.getElementById("api_hash")) ? deployment_form.getElementById("api_hash") : null;
        var telegram_phone = (deployment_form.getElementById("phone")) ? deployment_form.getElementById("phone") : null;
        var heroku_api_key = (deployment_form.getElementById("api_key")) ? deployment_form.getElementById("api_key") : null;
        if (telegram_api_id !== null && telegram_api_hash !== null && telegram_phone !== null && heroku_api_key !== null) {
/* Parameters */
          var is_ok = true;
          var error = [];
/* Check Telegram API ID */
          if (!(/[0-9]+/g.test(telegram_api_id.value))) {
            telegram_api_id.classList.add("is-invalid");
            telegram_api_id.addEventListener("click", function(e) {e.target.classList.remove("is-invalid")});
            telegram_api_id.addEventListener("focus", function(e) {e.target.classList.remove("is-invalid")});
            error.push("Invalid Telegram API ID.")
            is_ok = false;
          }
/* Check Telegram API Hash */
          if (!(/[0-9a-f]{32}/g.test(telegram_api_hash.value))) {
            telegram_api_id.classList.add("is-invalid");
            telegram_api_id.addEventListener("click", function(e) {e.target.classList.remove("is-invalid")});
            telegram_api_id.addEventListener("focus", function(e) {e.target.classList.remove("is-invalid")});
            error.push("Invalid Telegram API Hash.")
            is_ok = false;
          }
/* Check Telegram phone number */
          if (!(/\+[0-9]{6,}/g.test(telegram_phone.value))) {
            telegram_api_id.classList.add("is-invalid");
            telegram_api_id.addEventListener("click", function(e) {e.target.classList.remove("is-invalid")});
            telegram_api_id.addEventListener("focus", function(e) {e.target.classList.remove("is-invalid")});
            error.push("Invalid Telegram phone number.")
            is_ok = false;
          }
/* Check Heroku API Key */
          if (!(/[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}/g.test(heroku_api_key.value))) {
            heroku_api_key.classList.add("is-invalid");
            heroku_api_key.addEventListener("click", function(e) {e.target.classList.remove("is-invalid")});
            heroku_api_key.addEventListener("focus", function(e) {e.target.classList.remove("is-invalid")});
            error.push("Invalid Heroku API Key.")
            is_ok = false;
          }
/* Configure and send Telegram code */
          if (is_ok) {
            fetch("/setConfiguration", {
              method: "POST", 
              body: telegram_api_id.value + "\n" + telegram_api_hash.value + "\n" + telegram_phone.value + "\n" + heroku_api_key.value,
              credentials: "include"
            })
            .then(function(response) {
              if (!response.ok) {
                /* An error as occured */
              } 
              else {
                response.text()
                .then(function(data) {
                  if (data.length > 0) {

                  }
                  else {
                    showTelegramCodeModal(telegram_phone.value);
                  }
                })
              }
            });
          }
          else {
            displayError(deployment_form, error);
          }
        }
        else {
          /* One or more input not found in form */
        }
      });
    }
    else {
      /* For submit button not found in form */
    }
  }
  else {
    /* Deployement form not found */
  }
}

function showTelegramCodeModal(telegram_phone) {
  'use strict'
  if (telegram_phone !== null && /\+[0-9]{6,}/g.test(telegram_phone)) {
    telegram_modal = (document.getElementById("telegramCodeModal")) ? document.getElementById("telegramCodeModal") : null;
    if (telegram_modal !== null) {
      var telegram_modal_form = (telegram_modal.getElementById("telegramCodeForm")) ? telegram_modal.getElementById("telegramCodeForm") : null;
      if (telegram_modal_form !== null) {
        var telegram_modal_submit = (telegram_modal_form.getElementById("telegramCodeSubmit")) ? telegram_modal_form.getElementById("telegramCodeSubmit") : null;
        if (telegram_modal_submit !== null) {
  /* Open modal */
          $("#telegramCodeModal").modal("show");
  /* Code sent by user */
          telegram_modal_submit.addEventListener('click', function(e) {
            'use strict';
            e.preventDefault();

            var telegram_modal_code = (telegram_modal_form.getElementById("telegramCode")) ? telegram_modal_form.getElementById("telegramCode") : null;
            if (telegram_modal_code !== null) {
  /* Parameters */
              var is_ok = true;
              var error = [];
/* Check Telegram Modal code */
              if (!(/[0-9]+/g.test(telegram_modal_code.value))) {
                telegram_modal_code.classList.add("is-invalid");
                telegram_modal_code.addEventListener("click", function(e) {e.target.classList.remove("is-invalid")});
                telegram_modal_code.addEventListener("focus", function(e) {e.target.classList.remove("is-invalid")});
                error.push("Invalid Code.")
                is_ok = false; 
              }
  /* Verify if code correspond to code sent at Telegram Account*/
              if (is_ok) {
                fetch("/verifyTelegramCode", {
                  method: "POST", 
                  body: telegram_modal_code.value + "\n" + telegram_phone,
                  credentials: "include"
                })
                .then(function(response) {
                  if (!response.ok) {
                    if (response.status == 401) {
                      /* 2FA Enabled - Open Telegram password modal*/
                      $("#telegramCodeModal").modal("hide");
                      showTelegramPasswordModal(telegram_phone);
                    }
                    else if (response.status == 403) {
                      /* Code invalid */
                      error.push("The code you entered is incorrect. Please try again.")
                      displayError(telegram_modal_form, error);
                    }
                    else if (response.status == 404) {
                      /* Code expired - Close modal */
                      error.push("Code expired. Please close this popup and click again on <span class=\"font-weight-bold\">Confirm</span> button to receive a new code.")
                      displayError(telegram_modal_form, error);
                    }
                    else if (response.status == 421) {
                      /* Flood Wait Error */
                      response.text()
                      .then(function(data) {
                        if (data.length > 0) {
                          error.push("Flood Wait Error. A wait of " + data + " seconds is required.")
                          displayError(telegram_modal_form, error);
                        }
                        else {
                          /* No data returned */
                        }
                      });
                    }
                  } 
                  else {
                    response.text()
                    .then(function(data) {
                      if (data.length > 0) {
                        document.cookie = "secret=" + data;
                        deploy();
                      }
                      else {
                        /* No data returned */
                      }
                    })
                  }
                });
              }
              else {
                displayError(telegram_modal_form, error);
              }
            }
            else {
              /* Telegram modal code input not found */
            }
          });
        }
        else {
          /* Modal submit button not found */
        }
      }
      else {
        /* Telegram modal form not found */
      }
    }
    else {
      /* Telegram code modal not found */
    }
  }
  else {
    /* Telegram phone number empty or wrong */
  }
}

function showTelegramPasswordModal(telegram_phone) {
  'use strict'
  if (telegram_phone !== null && /\+[0-9]{6,}/g.test(telegram_phone)) {
    telegram_modal = (document.getElementById("telegramPasswordModal")) ? document.getElementById("telegramPasswordModal") : null;
    if (telegram_modal !== null) {
      var telegram_modal_form = (telegram_modal.getElementById("telegramPasswordForm")) ? telegram_modal.getElementById("telegramPasswordForm") : null;
      if (telegram_modal_form !== null) {
        var telegram_modal_submit = (telegram_modal_form.getElementById("telegramPasswordSubmit")) ? telegram_modal_form.getElementById("telegramPasswordSubmit") : null;
        if (telegram_modal_submit !== null) {
  /* Open modal */
          $("#telegramPasswordModal").modal("show");
  /* Password sent by user */
          telegram_modal_submit.addEventListener('click', function(e) {
            'use strict';
            e.preventDefault();

            var telegram_modal_password = (telegram_modal_form.getElementById("telegramPassword")) ? telegram_modal_form.getElementById("telegramPassword") : null;
            if (telegram_modal_password !== null) {
  /* Parameters */
              var is_ok = true;
              var error = [];
/* Check Telegram Modal password */
              if (!(/[0-9]+/g.test(telegram_modal_password.value))) {
                telegram_modal_password.classList.add("is-invalid");
                telegram_modal_password.addEventListener("click", function(e) {e.target.classList.remove("is-invalid")});
                telegram_modal_password.addEventListener("focus", function(e) {e.target.classList.remove("is-invalid")});
                error.push("Invalid password.")
                is_ok = false; 
              }
  /* Verify if password correspond to password of Telegram Account*/
              if (is_ok) {
                fetch("/verifyTelegramPassword", {
                  method: "POST", 
                  body: telegram_modal_password.value + "\n" + telegram_phone,
                  credentials: "include"
                })
                .then(function(response) {
                  if (!response.ok) {
                    if (response.status == 400) {
                      /* Error with data sent */
                    }
                    else if (response.status == 403) {
                      /* Password invalid */
                      error.push("The password you entered is incorrect. Please try again.")
                      displayError(telegram_modal_form, error);
                    }
                    else if (response.status == 421) {
                      /* Flood Wait Error */
                      response.text()
                      .then(function(data) {
                        if (data.length > 0) {
                          error.push("Flood Wait Error. A wait of " + data + " seconds is required.")
                          displayError(telegram_modal_form, error);
                        }
                        else {
                          /* No data returned */
                        }
                      });
                    }
                  } 
                  else {
                    response.text()
                    .then(function(data) {
                      if (data.length > 0) {
                        document.cookie = "secret=" + data;
                        deploy();
                      }
                      else {
                        /* No data returned */
                      }
                    })
                  }
                });
              }
              else {
                displayError(telegram_modal_form, error);
              }
            }
            else {
              /* Telegram modal password input not found */
            }
          });
        }
        else {
          /* Modal submit button not found */
        }
      }
      else {
        /* Telegram modal form not found */
      }
    }
    else {
      /* Telegram password modal not found */
    }
  }
  else {
    /* Telegram phone number empty or wrong */
  }
}

function deploy() {
  'use strict';
/* Parameters */
  error = [];
/* Deploy */
  fetch("/deploy", { 
    method: "POST",
    body: "deploy",
    credentials: "include" 
  })
  .then(function(response) {
    if (!response.ok) {
      /* Deploy problem */
      if (deployment_form !== null) {
        error.push("An error as occured. Please try again.");
        displayError(deployment_form, error);
      }
      else {
        /* Deployment form not found */
      }
    }
    else {
      window.location.reload(true);
    }
  })
}

function displayError(el = null, error = null) {
  if (el !== null && (el.tagName == "DIV" || el.tagName == "FORM") && error !== null && Array.isArray(error)) {
    var error_div = document.createElement("div");
    error_div.className = "col alert alert-danger";
    error_div.innerHTML = "⚠ Warning :";
    var error_ul = document.createElement("ul");
    error.forEach(function(el) {
      var error_li = document.createElement("li");
      error_li.innerHTML = el;
      error_ul.appendChild(error_li);
    });
    error_div.appendChild(error_ul);
    el.insertBefore(error_div, el.firstChild);
/* Delete warning div */
    var buttons = document.querySelectorAll("btn");
    Array.prototype.forEach.call(buttons, function(button) {
      button.removeEventListener('click', removeError, false);
      button.addEventListener('click', removeError, false);
    });
  }
}

function removeError() {
  var error_div = (document.getElementById("alert")) ? document.getElementById("alert") : null;
  if (error_div !== null) {
    document.removeChild(error_div);
  }
  else {
    /* No error div */
  }
}