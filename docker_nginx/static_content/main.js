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

function httpGetJSONAsync(theUrl, callback_OK, callback_ERROR)
{
    var xmlHttp = new XMLHttpRequest();
    xmlHttp.overrideMimeType("application/json");
    xmlHttp.onreadystatechange = function() { 
        if (xmlHttp.readyState == 4 && xmlHttp.status == 200)
            callback_OK(JSON.parse(xmlHttp.responseText));
        else if (xmlHttp.readyState == 4)
            callback_ERROR(JSON.parse(xmlHttp.responseText));
    }
    xmlHttp.open("GET", theUrl, true); // true for asynchronous 
    xmlHttp.send(null);
}

function httpGetAsync(theUrl, callback_OK, callback_ERROR)
{
    var xmlHttp = new XMLHttpRequest();
    xmlHttp.onreadystatechange = function() { 
        if (xmlHttp.readyState == 4 && xmlHttp.status == 200)
            callback_OK(xmlHttp.responseText);
        else if (xmlHttp.readyState == 4)
            callback_ERROR(xmlHttp.responseText);
    }
    xmlHttp.open("GET", theUrl, true); // true for asynchronous 
    xmlHttp.send(null);
}

function switch_announces_clicked() {
    document.getElementById("radio_progressbar").style.display = "inline-block";
    document.getElementById("switch_announces").disabled = true;
    if (document.getElementById("switch_announces").checked)
        httpGetAsync("http://bc-hq.local/service/interphone/enable_announces",
        function(response) {
            // do something with response in case of SUCCESS
            console.log("OK");
            console.log(response);
            get_interphone_status();
        },
        function(response) {
            // do something with response in case of ERROR
            console.log("ERROR!");
            console.log(response);
            // show an error message or something?!?
        })        
    else
        httpGetAsync("http://bc-hq.local/service/interphone/disable_announces",
        function(response) {
            // do something with response in case of SUCCESS
            console.log("OK");
            console.log(response);
            get_interphone_status();
        },
        function(response) {
            // do something with response in case of ERROR
            console.log("ERROR!");
            console.log(response);
            // show an error message or something?!?
        })
}

function get_interphone_status() {
    console.log("querying interphone status...");
    document.getElementById("radio_progressbar").style.display = "inline-block";
    document.getElementById("switch_announces").disabled = true;
    httpGetJSONAsync("http://bc-hq.local/service/interphone/status",
        function(response) {
            // do something with response in case of SUCCESS
            document.getElementById("radio_progressbar").style.display = "none";
            console.log(response);
            console.log(response["announces_enabled"]);
            document.getElementById("switch_announces").checked = response.announces_enabled;
            document.getElementById("switch_announces").disabled = false;
        },
        function(response) {
            // do something with response in case of ERROR
            document.getElementById("radio_progressbar").style.display = "none";
            console.log(response);
            document.getElementById("switch_announces").disabled = true;
            // show an error message or something?!?
        })
}

function InitPage() {
    moment.locale('fr');
    DisplayTime();
    get_interphone_status();
}

window.onload=InitPage;
