# Basecamp
[[toc]]

## Todo

Pour bc-watch, bc-hq et bc-annex:
- [x] adresses IP fixes
- [x] bc-annex: service "bc_TTS", avec API REST basique: texte unicode -> fichier wav téléchargeable en HTTP, reboot-proof, avec purge des wav régulièrement (schéma nommage avec TS) et une page "alive"
- [ ] bc-hq: service "zmq_forwarder" qui crée les forwarder pour pub/sub UPDATES & ORDERS, reboot-proof via supervisord.- [ ] Sur chaque machine, mettre les logs (quand il y en a) dans /var/log/basecamp.log (tournants). Installer supervisord, et lancer run_fw d'abord (en root), puis operator (en nio), avec un décalage dans le temps (attendre 5 sec par exemple).
- [ ] bc-ui: service "speaker" qui va surveiller ORDERS pour demander à la demande un wav à bc_TTS et le jouer sur l'UI pour faire une annonce
- [ ] bc-ui: service "time_announce" qui va annoncer les heures en TTS en utilisant speaker
- [ ] bc-hq: deplacer operator.py & dependances & le cabler sur le nouveau "zmq_forwarder".
- [ ] presence: installer bc-concierge avec le service "concierge" qui va gérer la présence et faire des annonces et fonction des évènements
- [ ] développer le watchdog: tester le ping des machines, puis le PUB/SUB ZMQ, et ensuite faire un ping de chaque service, tester aussi influxdb et grafana (http). Ajouter le monitoring du secteur avec désactivation du watchdog quand le secteur est perdu & réactivation après tempo quand il revient. Notifications par SMS si problème secteur, par pushover si problème watchdog.
- [ ] chauffage: mettre une alerte/info si confort pendant la nuit (oubli force_confort?) ou mettre durée d'application du force_confort!
- [ ] tester snowboy & la reconnaissance de hotword/word hotspotting
- [ ] mettre url_pushover & pushover restart notif sur TTS
- [ ] bug: veilleuse exits if cannot request influxdb => should raise alarm in logbook, but go on

## Machines
Many services are set on many machines. Interactions between them are done using time-series database (influxdb), and/or a ZMQ pub/sub messaging facility.

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
  
  * `bc-power` (Debian Jessi on CHIP, ssh chip@bc-power.local, UP) is the module located near the house heater and main power metering unit, that will:
  + control the heater command (via a latching relay)
  + receive the main power monitoring info provided by the main power metering unit (via the UART interface)
    * bonjour: bc-power.local
    * fixed IP: 192.168.1.51
  
**supervisord** is used to monitor/start/stop modules on each machine.
<br>**Bonjour/avahi** is used on machine to allow easy access using the **_\<hostname>.local_** syntax.

**Xubuntu** and **Windows 7** machines can be remotely accessed on the LAN using **NoMachine**'s protocol and client/server.

## ZMQ messaging

A single PUB/SUB messaging pattern is used for exchanging:
* orders, requests, actions that needs to be performed
* answers, reports, information or events

Only information and commands that could/should be shared among multiple services are passing through this communication mechanism.
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

## Services

### [rules for every service]
Each service will be automatically started by **supervisord** (unless for windows OSes where the task scheduler will handle that).
**Logs and configurations** are handled locally, and source code is managed using a single github basecamp project.

Each machine should send a notification to the LogBook service stating that **the machine has rebooted**.
Each service automatically (re)started by supervisord should also send a notification using the same mechanism.

### pushover_operator
+ purpose: send pushover notifications
+ machine: bc-watch
+ interface: HTTP, port:8080
  + http://192.168.1.54:8080/send_pushover_notification?text=héhé => OK
  + http://192.168.1.54:8080/alive => OK

### TTS
+ purpose: generate wav from text message using TTS
+ machine: bc-annex.local (192.168.1.55)
+ interface: HTTP, port 8080
  + http://192.168.1.55:8080/TTS?text=héhé => URL for wav file
  + http://192.168.1.55:8080/alive => OK
+ TODO:
  + sox in out contrast
  + sox 

### logbook
+ purpose: keep a trace of all minor events (major problems are notified in realtime using pushover/SMS) into a centralized log file.
+ machine: bc-watch
+ interface: HTTP, port:8082
  + http://192.168.1.54:8082/add_to_logbook?text=héhé => OK
  + http://192.168.1.54:8082/get_logbook => get the logfile as text
    + using a rotating logfile with a low size, we are returning the current logfile through this request
  + http://192.168.1.54:8082/alive => OK

### SMS_operator
+ purpose: send SMS notifications + receive SMS from outside
+ machine: bc-watch
+ interface: HTTP, port:8081
  + http://192.168.1.54:8080/send_SMS?text=héhé => OK
  + http://192.168.1.54:8080/alive => OK
+ if an incoming SMS is detected, its content is broadcasted on Basecamp's PUB ZMQ channel with the topic _basecamp.SMS.incoming_

### veilleuse
+ purpose: turn ON/OFF some night lights based on the outdoor light level, as measured by MUTA scout units
+ machine: bc-presence
+ when the outdoor light level rises/falls above/under a light threshold, a latching relay is activated to turn OFF/ON night lights.

### heater
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

### power_monitoring
+ purpose: monitors the main power supply and send an alert by SMS when there's a power shortage
+ 

### internet monitoring
purpose: monitors the internet access availability, and send a pushover notification when it is not available

### watchdog

### presence

### interphone
+ purpose: makes TTS anouncements based on presence events or on demand of other services. Future versions will use hotword detection (snowboy) and lightbox.
+ machine: bc-ui.local (i.e. _basecamp-hq.local_ right now)
+ interface: ZMQ SUB
  + topic: basecamp.interphone.announce params: [unicode_text]
+ every 1/4 of hour, the time will be announced too, according to time and presence status.

## cam2cam

rtsp://192.168.1.95/11<br>
rtsp://192.168.1.95/12

