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

## Machines
Many services are set on many machines. Interactions between them are done using time-series database (influxdb), and/or a ZMQ pub/sub messaging facility.

* `bc-ui` (Xubuntu on an old Intel NUC, remote desktop/Nomachine & ssh nio@bc-hq.local, TO BE INSTALLED) is the main basecamp UI, to interact with guests. A 24" touch-enabled LCD is used to browse the web server UI (using _firefox_ in fullscreen), a loudspeaker is used to make announcements (using the **interphone** service), and a **lightpack** USB module is used to bring a visual feedback, if needed. Located in the main room, it is powered by an old **Intel NUC**, under **Xubuntu**.

* `bc-hq` (Xubuntu on recent Intel NUC, remote desktop/Nomachine & ssh nio@bc-hq.local, UP) is the main backend. It's hosting the time-series database **influxdb** and it's graphing module **graphana**, the main UI web server powered by **bottle**, and the interface to the wireless field units via the USB connected **operator** unit. It is powered by a recent **Intel NUC**, under **Xubuntu**.

* `bc-annex` (win7 on old Atom, remote desktop/Nomachine bc-watch.local, UP) mainly hosts the windows-based SAPI5 synthesis, and the **interphone** server module. It also host some periodical scraping / transcoding tasks (video feeds), and some scraping about the weather forecast. It is powered by an old **Atom** motherboard, under **windows 7**.

* `bc-watch` (Debian Jessi on CHIP, ssh chip@bc-watch.local, UP) is the watchdog module, EPS backed, able to detect any power outage, and equipped with an USB 3G/4G modem to sens/receive SMS. It's also in charge of configuring the router's port forwarding via UPnP to temporarily allow external access to the basecamp UI, of monitoring presence, and of handling pushover notifications in parallel of SMS dialogs. It is powered by a headless C.H.I.P., with a powered hub (required for powering the USB modem), and an USB ethernet adapter (_because I use wifi only if I can't use ethernet_).

* `bc-presence` (Debian Jessi on CHIP, ssh chip@bc-presence.local, UP) is the presence module, located near the bc-ui unit, that will:
  + detect any nearby presence using PIR sensors, and then wake up the bc-ui from screensaver, to let the user see the dashboard slideshow/clock (+ update the presence if required, or set an alarm if _lockout_ state)
  + monitor the outdoor luminosity to turn on/off the night led lights in the living room
  + scan regularly via bluetooth to check if the Galaxy A5 is detected nearby, and set the presence variable accordingly (disable _lockout_, greets & report)

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
* 

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
  + http://bc-watch.local:8080/send_pushover_notification?text=héhé => OK
  + http://bc-watch.local:8080/alive => OK

### TTS
+ purpose: generate wav from text message using TTS
+ machine: bc-annex
+ interface: HTTP, port 8080
  + http://bc-annex.local:8080/TTS?text=héhé => URL for wav file
  + http://bc-annex.local:8080/alive => OK

### logbook
+ purpose: keep a trace of all minor events (major problems are notified in realtime using pushover/SMS) into a centralized log file.
+ machine: bc-hq
+ interface: HTTP, port:8080
  + http://bc-hq.local:8080/add_to_logbook?text=héhé => OK
  + http://bc-hq.local:8080/get_logbook => get the logfile as text
    + using a rotating logfile with a low size, we are returning the current logfile through this request
  + http://bc-hq.local:8080/alive => OK

### SMS_operator

### watchdog

### presence

## cam2cam

rtsp://192.168.1.95/11<br>
rtsp://192.168.1.95/12

