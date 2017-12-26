# Evolutions BASECAMP

+ heater:
    + ajouter *max_temp* dans heater.ini + liste de capteurs pour check sur les capteurs & stopper le chauffage tant que temp(un des capteurs) >= max_temp. Permet d'adresser le problème de la chambre qui ne chauffe pas alors qu'il fait 22°C au RDC si asservissement sur la chambre...

+ Veilleuse: exporter variable veilleuse vers mongoDB en fonction de luminosité extérieure.
    + récupérer éphéméride (librairie python?) & calculer heure de lever/coucher
    + si noir avant coucher => WARNING
    + si lumière avant lever => WARNING
    + positionner variable jour/nuit en fonction d'éphéméride

+ Interface:
    * serveur WEB de BASECAMP
    * Basic page with iframes to:
    * watchdog_master status
    * logbook output
    * supervisor http UIs of each machines
    => allows to easily start/stop programs and see program logs

Frameworks HTML5 material design
1er choix: https://material.io/components/web/
2ème choix: http://materializecss.com/about.html

fonte:Roboto, ou bien utiliser fontes:
      + Coolvetica
      + Alte Haas Grotesk Regular
      + Neue Haas Grotesk

+ Scheduler:
    * toutes les 5mn, aller grabber une image du flux vidéo des carpes ! :)
        - sera utilisé sur la page web d'accueil! :)
    + faire en sorte que scheduler puisse lire mon agenda et me rappeler les trucs pour lesquels j'ai mis un TAG spécifique genre "BASECAMP-1d", et du coup, il me rappelle le RV la veille au soir, à mon retour (ou par SMS, ou les deux). Ou bien "BASECAMP-3h" et il me rappelle le RV 3h avant... :)
        + mettre le calendrier des poubelles! :)
    + pour les annonces d'heure, ajouter des variantes marrantes, et aussi un commentaire... "et tout va bien ici..." ou bien "On a quelques soucis, ici, quand tu auras un moment... merci!". Scanner la présence BT par exemple pour varier en ajoutant les Alias (Nico, Natacha)...
    + conditionner les annonces vocales d'heure au mode cocoon exclusivement.
    + 

+ Music:
    + commande du/des ZipMini (de deezer devices en général) via l'API de Deezer
    + permet de mettre une playlist sur un deezer devices en standby

+ NightWatch Core/Sentry
    + Core sur watch
        + check connectivité/réseau interne avec machines (ping routeur + ping sur Sentry)
        + check Internet
        + check services OK via supervisord
        + UPNP + check adresse IP extérieure
            + au besoin, ouvrir un forward_port sur le routeur pour permettre l'accès extérieur, en générant un password temporaire sur bc-watch pour accès SSH. Le tout transmis par SMS ou pushover. Fermeture automatique du port et suppression du passwd au bout d'un certain temps.
            + PLUS forwarding de l'interface WEB sur bc-hq pour accès simple depuis extérieur (doit être très limité pour éviter scan & failles!). Par SMS: lien cliquable HTTP:// avec clé temporaire + réponse que si clé OK - permet d'éviter login/passwd :)
        + check secteur - boucle principale
            + gérer un état local MAINS avec POWER_OK et BLACKOUT
            + POWER_OK && lecture KO? => coupure de courant => alerte SMS + on arrête de scanner le reste, on scanne uniquement le secteur...
            + BLACKOUT && lecture OK => le courant est revenu => alerte SMS + on attend au moins 2mn avant de reprendre le scan normal.
            + POWER_OK && lecture OK => scan normal du reste...
        + check matin: si pas de créneau sans aucune dépense eau durant la nuit => fuite d'EAU! => SMS+vocal
        + check horaire => surveiller les dépenses d'eau & d'électricité & vérifier qu'on ne dépasse pas des valeurs max de sécurité => WARNING par SMS + annonce vocale.
        + si LOCKOUT && lumière pendant la nuit => WARNING SMS
    + Sentry sur chaque autre machine (sauf windows)
        + Si pas de ping depuis Core depuis un certain temps => reboot

+ Operator
    + reçoit les infos de MAJ PIR depuis PIR_scan
    + gère le lightpad
      + possibilité de pulser gentiment la couleur?
        + lockout => rouge/orange
        + asleep => bleu
        + Cocoon => blanc chaud
    + gère Snowboy
        + "Je pars/je m'absente/je m'en vais": "tu reviens quand?" "je ne sais pas/aucune idée/ce soir/ce midi/demain matin/demain midi/demain soir/dans x heures/dans x jours" "ok, je surveille en ton absence. Bonne matinée/journée/soirée"... => LOCKOUT + forcer le chauffage en ECO jusqu'à la prochaine échéance en COMFORT (en lisant le status, et en positionnant un profil exceptionnel en force_eco jusque là). Exemple du matin où je pars très tôt jusqu'au midi.
        + "Je m'absente":
        + "Je suis revenu":
        + "Je vais me coucher"
        + "Rapport complet":
        + "Chauffage": 
    + modes de gestion:
        + cocoon: présence
        + lockout: absence, tout est fermé/vérouillé
        + asleep: nuit, surveillance partielle
    + si LOCKOUT && retour indéterminé => on ne touche pas au chauffage
    + si LOCKOUT && retour précisé => force_eco jusqu'au retour (-1h), sauf si trop court.
    + 

+ BT_scan
    + depuis veilleuse (CHIP, ok pour bluez & scan BT)
    + mettre une API simple pour scanner / demander qui est là, et obtenir un RSSI et des prénoms en retour
    + /alive, /scan_all, /scan_alias?alias=nicolas

+ PIR_scan
    + depuis bc-ui, lit la sortie console du module TrinketM0 (mettre aussi son script python dans _circuitpython_), et MAJ la température du module dans InfluxDB (5mn? - utilisé par Nightwatch pour éventuel check problème chauffage), et surtout détecte et pousse la présence de passage pour chaque capteur PIR dans InfluxDB (PIR_entry, PIR_UI, PIR_indoor) + info poussée vers Operator pour éventuelle prise en compte.

+ passer tous les modules en python3, sauf ceux qui ne peuvent pas. (implique d'installer le dernier python3 & les requirements)
```
sudo apt update && sudo apt ugrade -y
sudo apt install python3 python3-dev python3-pip
sudo pip3 install bottle requests influxdb greenlet gevent gunicorn
```

REFACTORING:
+ mettre en python3 tout ceux qui peuvent l'être
+ rendre multithread les serveurs web qui peuvent l'être... exemple logbook!
+ laisser SMS en monothread par contre...

+ mettre des timeouts dans TOUS les requests!!! par défaut, ils bloquent indéfiniment!
`requests.get(...., timeout=5)`

+ mettre des try/except dans tous les requests! et toutes les requêtes extérieures
  + except pass si c'est pour le logbook, ou les SMS/pushover
  + except "add_to_logbook" en error sinon!

+ revoir la logbook notification on restart sur les machines (ajouter le log_type pour que ca fonctionne)

## Idées

+ _web\_server_ interface web: hostée sur hq, en javascript avec des encarts divers (frames ou équivalents?).
  + état des modules
  + métriques
  + commandes / modifications
  + utiliser un NGINX en reverse proxy sur hq pour contourner le problème du same-origin policy de puis les clients web. Derrière, on pointera vers les modules et les exports grafana.

+ _interphone_: mélanger la synthèse avec des bruits de radio (avec sox) pour rendre l'ensemble moins "clean", ou utiliser des filtres passe-bande, passe-haut?

+ _veilleuse_: gère une variable jour/nuit automatiquement, mappée sur l'état des veilleuses (simple).

+ _scheduler_: toutes les semaines, faire un pruning de la BDD pour ne garder que les données les plus récentes (moins de 1 an? 6 mois? 3 mois?)

+ _hello_: module d'accueil et interface utilisant la synthèse et la reconnaissance vocale / hotword basé sur snowboy qui permet un échange guidé. "Hello?" "Hello! Que puis-je faire pour vous?"
  + "Je vais me coucher"
  + "Je m'en vais"
  + "chauffage"
    + "semaine de travail"
    + "semaine de vacances"
    + "force le mode confort"
    + "force le mode éco"
  + "Rapport" - "quelques problèmes rencontrés... blablabla"
  + "silence" "le mode silence est activé" "désactiver" "le mode silence est désactivé"
Prévoir un mode "silence" (activé par défaut en mode sommeil) qui permet de désactiver l'interface de synthèse, mais autorise toujours l'activation par dialogue vocal.
Le module gère la présence et positionne des variables en conséquence (présent, absent, sommeil).
Une interface physique (trinket CircuitPython) permet de détecter la présence d'un humain devant la console de controle et activera l'écran au besoin / déclenchera un rapport ou un dialogue au besoin.

+ _pir_: sur _bc-veilleuse_, le module pir va détecter la présence d'humains (ou d'animaux) par détection PIR => activité dans la cuisine et le salon. Tout changement de détection sera tracé dans la BDD, et l'info transmise à _hello_ pour une éventuelle MAJ de la présence, ou une alerte au besoin (intrusion?).

+ _BT\_track_: scanne régulièrement la présence de devices BT connus (téléphone nio, natacha...) & transmets l'info à _hello_ pour prise en compte + trace tout changement dans la BDD. On va l'héberger sur _bc-hq_ ? ou le distribuer sur plusieurs machines?
  + Faire des tests de détection sur plusieurs machines, avec mon mobile, pour voir ce qui est le plus efficace...

+ _lightpack_: gère le module lightpack sur bc-ui. Lockable pour un usage limité dans le temps (typiquement, par _hello_ lors des dialogues vocaux). En dehors, la lumière reflète:
  + le mode de présence (présent+chauffage confort, présent+chauffage éco, absent, sommeil) - lu directement dans la BDD
  Avec en tâche de fond l'indication potentielle d'un problème rencontré sur le système:
  + le fait qu'un problème ait été rencontré (orange), mais qu'il a disparu, ou pas majeur.
  + le fait qu'un problème majeur ait été rencontré (rouge).
  c'est _nightwatch_ qui gèrerait çà? à étudier...
  
  + _nightwatch_: fait office de watchdog pour l'ensemble du système. hébergé sur _bc-watch_ pour être opérationnel en cas de coupure de courant + au plus près de l'envoi de SMS.
  + on installe des _nightwatch-cli_ sur les autres machines, pour détecter une éventuelle perte de connectivité, et les redémarrer si c'est le cas.
s
+ _sms\_operator_ & _pushover_ : imaginer des dialogues & possibilité de remontée d'infos/alertes/rapports réguliers + commandes.

+ offrir la possibilité à Natacha de m'envoyer des messages par SMS qui seront vocalisés par _hello_ si je suis présent (ou stockés et reproduit quand j'arrive - gérer une liste).

+ éclairage automatique du kiosque commandé par bc-presence: installer l'éclairage, et le commande avec un module CHIP par exemple _bc-kiosque_ (+ relais bistable 3V).

+ mettre un CHIP à l'entrée pour gérer la sonnette + un capteur de passage/présence PIR _bc-entry_.
  
  + SMS_operator => ajouter des dialogues par SMS! :)

+ remonter qques métriques système dans influxdb (%CPU, %disques, %MEM) pour chaque machine => prévenir failure

+ régler la réception SIM du modem au max à l'étage + ajouter une métrique remontée régulièrement qui indique la qualité de réception.
