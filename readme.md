# Basecamp

## Todo

Pour bc-watch, bc-hq et bc-annex:
- [ ] A) modif format logbook (python+shell) + B) service_name & machine_name auto pour chaque service & pour restart machine! + C)revoir restart+events+errors -> log+logbook. + D) modif log: stdout/stderr en copie de log applicatif (pour retrouver dans supervisor). E) file log: DEBUG, console log: ERROR
    + REFACTORING DES SERVICES:
      + quand une action ESSENTIELLE foire, écrire dans le log, notifier logbook (au moins essayer), et quitter avec un code d'erreur pour que supervisor relance?
      + si action PAS ESSENTIELLE, on peut continuer après écriture log+logbook
      + @start: info logbook
  - [x] bc-power: power, heater
  - [x] bc-presence: veilleuse
  - [x] bc-watch: logbook, SMS_operator, pushover_operator
  - [x] bc-hq: scheduler, zmq_fw, MUTA_operator
  - [ ] bc-ui: interphone
- [x] bc-presence/veilleuse: implémenter la solution proposée par l'auteur de CHIP_IO sur github pour contourner le problème de GPIO déjà configuré (qui oblige à rebooter sinon)
- [x] bc-presence/veilleuse: [bug] veilleuse exits if cannot request influxdb => should raise alarm in logbook, but go on
- [ ] Ajouter le monitoring du secteur avec désactivation du watchdog quand le secteur est perdu & réactivation après tempo quand il revient. Notifications par SMS si problème secteur, par pushover si problème watchdog (mais limiter le nombre de message pour ne pas flooder / boucles)
- [ ] envisager de remonter automatiquement la consommation en utilisant python/scheduler
- [ ] chauffage: mettre une alerte/info si confort pendant la nuit (oubli force_confort?) ou mettre durée d'application du force_confort!
- [x] voir comment organiser la reco vocale + lightbox / présence (reprendre notes)
- [ ] tester snowboy & la reconnaissance de hotword/word hotspotting
- [ ] coupler avec la lightbox, qui devra être installée derrière l'écran
- [ ] watchdog => implement a watchod service testing that regularly pings every machine+service using ping/http-alive/zmq-alive, alert if any problem, offers detailed results via HTTP + logbook agreggation on dedicated page.
- [ ] bug: si perte secteur (plus d'ethernet ni internet) et que secteur revient => bc-watch n'est plus accessible par réseau!?!
- [ ] améliorer monitoring: sur l'UI, avoir une interface vers les logs applicatifs de n'importe quel service, en plus des infos données par le _watchdog-master_. + prévoir des infos d'espace disque de chaque machine (df -h avec % important) => watchdog avec notif

## Basecamp UI

### Services/applications/machines Monitoring

Basic page with iframes to:
+ watchdog_master status
+ logbook output
+ supervisor http UIs of each machines

=> allows to easily start/stop programs and see program logs

## Services

### [rules for every service] **[DONE]**
Each service will be automatically started by **supervisord** (unless for windows OSes where the task scheduler will handle that).
To enable supervisord http server access (and also xml-rpc API), use the following in supervisor.conf:
```
[inet_http_server]
port=*:9001
```
Example of entry for a program in supervisor.conf:
```
[program:operator]
command=/usr/bin/python ./operator.py
directory=/home/nio/MUTA_interface
user=nio
redirect_stderr=true
startsecs=10
startretries=3
autorestart=true
```
program logs should then be available through the supervisor http UI.

**Logs and configurations** are handled locally, and source code is managed using a single github basecamp project.

Each machine should send a notification to the LogBook service stating that **the machine has rebooted**. We'll be using a basic shell script put into the `/etc/network/if-up.d/` directory, to send a notification to the logbook when the network is up (see `if-up/` in sources).
Each service automatically (re)started by supervisord should also send a notification to the logbook.

### pushover_operator **[DONE]**
+ purpose: send pushover notifications
+ machine: bc-watch
+ interface: HTTP, port:8080
  + http://192.168.1.54:8080/send_pushover_notification?text=héhé => OK
  + http://192.168.1.54:8080/alive => OK

### TTS **[DONE]**
+ purpose: generate wav from text message using TTS
+ machine: bc-annex.local (192.168.1.55)
+ interface: HTTP, port 8080
  + http://192.168.1.55:8080/TTS?text=héhé => URL for wav file
  + http://192.168.1.55:8080/alive => OK
+ TODO:
  + sox in out contrast
  + sox

### logbook **[DONE]**
+ purpose: keep a trace of all minor events (major problems are notified in realtime using pushover/SMS) into a centralized log file.
+ machine: bc-watch
+ interface: HTTP, port:8082
  + http://192.168.1.54:8082/add_to_logbook?machine=...&service=...&message=... => message as unicode is fine
  + http://192.168.1.54:8082/get_logbook => get the logfile as text
    + using a rotating logfile with a low size, we are returning the current logfile through this request
  + http://192.168.1.54:8082/alive => OK

### SMS_operator **[DONE]**
+ purpose: send SMS notifications + receive SMS from outside
+ machine: bc-watch
+ interface: HTTP, port:8081
  + http://192.168.1.54:8081/send_SMS?msisdn=%2B33607080910&text=héhé => OK
  + http://192.168.1.54:8081/alive => OK
+ if an incoming SMS is detected, its content is broadcasted on Basecamp's PUB ZMQ channel with the topic _basecamp.SMS.incoming_

### veilleuse **[DONE]**
+ purpose: turn ON/OFF some night lights based on the outdoor light level, as measured by MUTA scout units
+ machine: bc-presence
+ when the outdoor light level rises/falls above/under a light threshold, a latching relay is activated to turn OFF/ON night lights.

### heater **[DONE]**
+ purpose: monitors temperature, and depending on heating profiles, commands the heater latching relay to start/stop heating
+ interface: ZMQ SUB
  + topic: basecamp.muta.update
  + monitors basecamp.muta.update events to get fresh information about selected temperature sensors
+ interface: HTTP, port:8080
  + http://192.168.1.51:8080/alive
  + http://192.168.1.51:8080/status
  + http://192.168.1.51:8080/set_profile?profile=force_eco
+ reads profiles list from configuration
+ reads locally heating schedules for certain profiles
+ turn on/off latching relay when needed
+ has failsafe procedure if temperature has not been updated for a long time, while the heater is turned on => turn it off to be safe
+ exports regularly (+at every modification) variables to influxdb for recording the goal temperature + the latching relay state (0/1)
+ machine: bc-power

### power_monitoring **[DONE]**
+ purpose: monitors the power consumption and send metrics to influxdb
+ machine: bc-power

### watchdog (watchdog_master, watchdog_client)
purpose: Detect any problem on a machine/service, and if so, reboot/restart it, then report.
+ Check regularly every machine/server/service and report on a dedicated HTTP page plus send pushover notifications or sms notifications if needed. Must handle flooding prevention on pushover/sms channels.
+ checking a service consists of testing it, and also testing the supervisord API/server to get the status and uptime. This is done using supervisor's XML RPC API (http://supervisord.org/api.html#xml-rpc). For each machine, supervisord's status should also be check beforehand.
+ begins by checking every service on a given machine, then send an OK/KO message to this machine's _watchdog_client_. If the message is KO, the machine will reboot (and the service will be restarted).
+ To able to restart a machine that has lost network connections, _watchdog_clients_ are installed on each machine. If the _watchdog_client_ hasn't received a watchdog_master signal for a given time (10mn?), then the watchdog_client will also reboot the machine.
+ If the problem is encountered with a docker container service, we should also docker/stop/rm and start again the services, instead of just rebooting, to re-create the containers. A dedicated script should be used (see `watchdog/docker_scripts` in sources).
+ monitors also the main power supply and sends an alert by SMS
+ monitors the internet access availability, and send a pushover notification when it is not available
+ à vérifier: suite à coupure secteur, on ne peut plus atteindre bc-watch? si bc-watch n'arrive plus à atteindre la passerelle/routeur, envoi SMS d'info + faire un reboot de bc-watch. Suffisant?
+ machine for _watchdog_master_: bc-watch
+ interface: HTTP, port:8083
  + http://192.168.1.54:8083/watch_report => report services & machines status, by machine (JSON)
  + http://192.168.1.54:8083/alive => OK

### presence

### interphone **[DONE]**
+ purpose: makes TTS anouncements based on presence events or on demand of other services. Future versions will use hotword detection (snowboy) and lightbox.
+ machine: bc-ui.local (i.e. _basecamp-hq.local_ right now)
+ interface: ZMQ SUB
  + topic: basecamp.interphone.announce params: [unicode_text]

### lightbox

### scheduler **[DONE]**
every 1/4 of hour, the time will be announced through interphone, according to time and presence status.


## cam2cam

rtsp://192.168.1.95/11<br>
rtsp://192.168.1.95/12

## Machines
Many services are set on many machines. Complex interactions between them are done using time-series database (influxdb), and/or a ZMQ pub/sub messaging facility. Simple interactions are done using basic HTTP requests and servers.

* `bc-ui` (Xubuntu on an old Intel NUC, remote desktop/Nomachine & ssh nio@bc-hq.local, TO BE INSTALLED) is the main basecamp UI, to interact with guests. A 24" touch-enabled LCD is used to browse the web server UI (using _firefox_ in fullscreen), a loudspeaker is used to make announcements (using the **interphone** service), and a **lightpack** USB module is used to bring a visual feedback, if needed. Located in the main room, it is powered by an old **Intel NUC**, under **Xubuntu**.
  * bonjour: bc-ui.local, basecamp.local (old)
  * fixed IP: 192.168.1.52

* `bc-hq` (Xubuntu on recent Intel NUC, remote desktop/Nomachine & ssh nio@bc-hq.local, UP) is the main backend. It's hosting the time-series database **influxdb** and it's graphing module **graphana**, the main UI web server powered by **bottle**, and the interface to the wireless field units via the USB connected **operator** unit. It is powered by a recent **Intel NUC**, under **Xubuntu**.
  * bonjour: bc-hq.local
  * fixed IP: 192.168.1.50

* `bc-annex` (win7 on old Atom, remote desktop/Nomachine bc-watch.local, UP) mainly hosts the windows-based SAPI5 synthesis, and the **interphone** server module. It also host some periodical scraping / transcoding tasks (video feeds), and some scraping about the weather forecast. It is powered by an old **Atom** motherboard, under **windows 7**.
  * bonjour: bc-annex.local
  * fixed IP: 192.168.1.55

* `bc-watch` (Debian Jessi on CHIP, ssh chip@bc-watch.local, UP) is the watchdog module, EPS backed, able to detect any power outage, and equipped with an USB 3G/4G modem to sens/receive SMS. It's also in charge of configuring the router's port forwarding via UPnP to temporarily allow external access to the basecamp UI, of monitoring presence, and of handling pushover notifications in parallel of SMS dialogs. It is powered by a headless C.H.I.P., with a powered hub (required for powering the USB modem), and an USB ethernet adapter (_because I use wifi only if I can't use ethernet_).
  * bonjour: bc-watch.local
  * fixed IP: 192.168.1.54

* `bc-presence` (Debian Jessi on CHIP, ssh chip@bc-presence.local, UP) is the presence module, located near the bc-ui unit, that will:
  + detect any nearby presence using PIR sensors, and then wake up the bc-ui from screensaver, to let the user see the dashboard slideshow/clock (+ update the presence if required, or set an alarm if _lockout_ state)
  + monitor the outdoor luminosity to turn on/off the night led lights in the living room
  + scan regularly via bluetooth to check if the Galaxy A5 is detected nearby, and set the presence variable accordingly (disable _lockout_, greets & report)
    * bonjour: bc-presence.local
    * fixed IP: 192.168.1.53
  
* `bc-power` (Raspbian on RPi1, ssh nio@bc-power.local, UP) is the module located near the house heater and main power metering unit, that will:
   + control the heater command (via a latching relay)
   + receive the main power monitoring info provided by the main power metering unit (via the UART interface)
     * bonjour: bc-power.local
     * fixed IP: 192.168.1.51
  
**supervisord** is used to monitor/start/stop modules on each machine.
<br>**Bonjour/avahi** is used on machine to allow easy access using the **_\<hostname>.local_** syntax (_only to ease development, not to be used in production/resolution is very slow sometimes through python HTTP modules, use static IPs in that case_).

**Xubuntu** and **Windows 7** machines can be remotely accessed on the LAN using **NoMachine**'s protocol and client/server.

### logbook notification on restart
use a dedicated script in `/etc/network/if-up.d` to send a logbook notification for every machine restart.
<br>_or in /etc/rc.local on rpi for example, since the above doesn't work, they broke the if-up.d mechanism on the last raspbian..._


## ZMQ messaging

A single PUB/SUB messaging pattern is used for exchanging:
* orders, requests, actions that needs to be performed
* answers, reports, information or events

Only information and commands that should be shared among multiple services are passing through this communication mechanism.
Other peer2peer-like commands would be done using basic REST commands, that are easier to implement/debug.

Each basecamp module can then PUB/SUB on any topic, to send/receive orders, or events across the machines/network.

Forwarder is hosted on `basecamp_hq`, and binds PUB/SUB to `basecamp_hq`'s local TCP ports:
`.bind("tcp://*:%s" % port)`.
Module can then connect to the forwarders PUB or SUB ports using `.connect("tcp://basecamp_hq:%s" % port)`

ZMQ PUB/SUB topics are used to filter messages.

Topics:
* bc.muta(.order/.update)
* basecamp.interphone.client (play message requests from interphone server)
* basecamp.interphone.server (annoucement requests from other modules)
* basecamp.operator (orders sent to field units)
* basecamp.concierge (presence declaration/manual mode)

* basecamp.watchdog (PING answers sent periodically by every module to the watchdog)
* basecamp.operator (reports received from field units)
* basecamp.concierge (update presence)
