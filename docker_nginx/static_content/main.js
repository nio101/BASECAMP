/*!
 * radio.js
 */

/*moment().format('MMMM Do YYYY, h:mm:ss a');*/

function DisplayTime() {
    document.getElementById("datetime").innerHTML =
        moment().format("dddd Do MMMM HH:mm");
        moment().format("LLLL");
    setTimeout("DisplayTime()",3000);
}

function InitPage() {
    moment.locale('fr');
    DisplayTime();

    console.log("start")
      document.getElementById("radio_progressbar").style.display = "inherit";
      console.log("show progressbar & wait 5s")
      setTimeout(function () {
        document.getElementById("switch_announces").checked = true;
        console.log("hides progressbar")
        document.getElementById("radio_progressbar").style.display = "none";
      }, 5000);
}

window.onload=InitPage;
