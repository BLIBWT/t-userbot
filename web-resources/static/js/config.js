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

function setModulesSettings(elem) {
  'use strict';
  const moduleNumber = elem.dataset.modulenum - 1;
  const configKey = elem.dataset.configkey;
  fetch("/setModulesSettings", {method: "PUT", body: JSON.stringify({mid: moduleNumber, key: configKey,
    value: elem.value}), credentials: "include"})
  .then(function(response) {
    if (!response.ok) {
      console.log(response);
      setModulesSettingsFailed(elem);
    } else {
      setModulesSettingsDone(elem);
    }
  })
  .catch(function(response) {
    console.log(response);
    setModulesSettingsFailed(elem);
  });
}

function setModulesSettingsFailed(elem) {
  'use strict';
  elem.value = elem.dataset.currentvalue;
  document.getElementById("snackbar").MaterialSnackbar.showSnackbar({
      message: "Setting configuration value failed",
      timeout: 2000});
}

function setModulesSettingsDone(elem) {
  'use strict';
  if (elem.value === "") {
    elem.value = elem.dataset.defaultvalue;
    elem.parentElement.className += " is-dirty";
  }
  elem.dataset.currentvalue = elem.value;
  document.getElementById("snackbar").MaterialSnackbar.showSnackbar({
      message: "Configuration value set",
      timeout: 2000});
}

