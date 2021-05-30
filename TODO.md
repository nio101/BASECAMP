# Evolutions BASECAMP

===========

TODO:
- les erreurs de sms_operator doivent être transmises à pushover_operator!

TODO:
refaire pages grafana + backup dans git! dumbass!
faire une page avec le status des modules + les logs!
nightwatch => écrire dans influxdb quand un module pinge!
ou alors... les modules ping alive dans influxdb et nightwatch va lire ces infos?
Est-ce mieux ou pas que vers nightwatch?
Oui, ce serait mieux... on va faire ca!
=> fonction ping dans basecamp qui permet à chaque appli de faire un alive dans influxdb

faire une page sur l'UI qui sorte l'état de chaque service (via grafana), les derniers évènements (via grafana), et donne les liens
vers le logbook, et les pages de status supervisord

nightwatch:
- check batteries modules Muta >= 2V, sinon warning pour recharger?
- check age des mesures Muta => relancer operator + alerte
- piles noires + recharger all

TODO0:
mettre les noms de service et de host dans des variables make!

--=========
TODO1:
+ migration vers usage du package basecamp!
+ alive_check vers nightwatch!
+ faire des makefile pour tout le monde, pour MAJ & tester facilement...
+ ajouter la MAJ et la copie de basecamp dans les makefile individuels

done pour:
* logbook!

--=========

the way Python handles modules and namespaces gives the developer a natural way to ensure the encapsulation and separation of abstraction layers, both being the most common reasons to use object-orientation. Therefore, Python programmers have more latitude to not use object-orientation, when it is not required by the business model.

--=========

Carefully isolating functions with context and side-effects from functions with logic (called pure functions) allow the following benefits:

    Pure functions are deterministic: given a fixed input, the output will always be the same.
    Pure functions are much easier to change or replace if they need to be refactored or optimized.
    Pure functions are easier to test with unit-tests: There is less need for complex context setup and data cleaning afterwards.
    Pure functions are easier to manipulate, decorate, and pass around.

--=========

The generator approach using Python’s own contextlib:

from contextlib import contextmanager

@contextmanager
def custom_open(filename):
    f = open(filename)
    try:
        yield f
    finally:
        f.close()

with custom_open('file') as f:
    contents = f.read()

--=========

modifs logbook & basecamp.tools & sms_operator:
+ mettre une option sans SMS_forwarding dans l'ajout au logbook
+ faire en sorte que le sms_operator ajoute ses erreurs au logbook, mais sans cette option
mettre cette option sous forme de FLAG dans basecamp.tools, et sms_operator: tools.sms_forwarding = False
+ mettre des starting times dans supervisord qui soient > waiting time des services (avec petite marge de 15 sec?)

---
ex. de tests unitaires avec boddle:

```python
from server import do_add, do_sub
from boddle import boddle

def test_add():
    with boddle(method='GET', path='/add', params={'a': 1, 'b': 2}):            assert do_add() == '3', "erreur test unitaire sur /add"
```


--========= notes

To give the individual tests import context, create a tests/context.py file:

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import sample

Then, within the individual test modules, import the module like so:

from .context import sample

--=========

init:
    pip install -r requirements.txt

test:
    py.test tests

.PHONY: init test

--=========

And, most of all, don’t namespace with underscores, use submodules instead.

# OK
import library.plugin.foo
# not OK
import library.foo_plugin

--=========

A folder with .py files and a __init__.py is called a package. One of those files containing classes and functions is a module. Folder nesting can give you subpackages.

So for example if I had the following structure:

  mypackage
     __init__.py
     module_a.py
     module_b.py
        mysubpackage
             __init__.py
             module_c.py
             module_d.py

I could import mypackage.module_a or mypackage.mysubpacakge.module_c and so on.

--=========


TODO:

+ SMS_operator: ajouter gestion des erreurs graves avec exit(1) ne répond plus, etç...
+ Nightwatch doit essayer de rebooter une fois le SMS_operator, et si rien de mieux => le laisser et attendre opération manuelle
+ ajouter du throttling sur pushover & SMS pour éviter le spam...
+ commandes retour en pushover?
=> help / questions / réponses... développer une CLI
Idem via SMS, same CLI! :)
faire un même programme de CLI qui soit client de pushover_operator & SMS_operator!
=> un même sous-module de BC_commons, genre remote_CLI!:)

+ virer le module maya et faire mon propre module qui ne met pas 3h à se charger
+ avec fonction .slang qui permet de dire "dans 3mn", ou bien "il y a 5h" avec sortie en fr et en anglais
+ du coup virer maya des services/projets

+ pour tous les serveurs, mettre la version en retour dans le /alive
+ cabler chaque service sur BC_commons
+ pour chaque service, charger _version_.py et l'ajouter dans le restart...
+ revoir le process de restart:
  - log.info("Restarting!")
  - log.info("Waiting {} seconds")
  - sleep
  - notify("{service} {version+build} restarted!")
  - pour tous les serveurs multithreadés, utiliser gevent + monkeypatch, mais pas gunicorn qui fout la merde avec les logs!
    from gevent import monkey; monkey.patch_all()
    run(..., server='gevent')

+ pour tous les timers dans les services, faire en sorte que le starttimer soit au début de la fonction, sinon en cas d'erreur avant le nouveau start, on perd le timer, mais le programme continue! Ou alors mettre en try/except tout ce qui est avant le start du timer!

+ modifier les supervisord.conf pour sortir les logs dans les répertoires des services (STDOUT)... pas de STDERR? - tester et améliorer sur heater par exemple

+ watchdog: mettre des warnings sur temp hautes et basses dans la maison ou données trop vieilles

+ compléter le module BASECAMP_commons
    * tester bc.influxDB

+ heater:
    + une fois que les modes seront implémentés, le mode ASLEEP force l'usage du secondary sensor comme référence, même si la config dit autrement.

+ Veilleuse:
    + transformer en serveur HTTP & positionner une variable ON/OFF/AUTO avec /alive, /status, /set?mode=ON/OFF/AUTO
    + exporter variable veilleuse vers mongoDB en fonction de luminosité extérieure.
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

=> comment là: https://material.io/components/web/
et là: https://github.com/material-components/material-components-web

Frameworks HTML5 material design
1er choix: https://material.io/components/web/
2ème choix: http://materializecss.com/about.html

fonte:Roboto, ou bien utiliser fontes:
      + Coolvetica
      + Alte Haas Grotesk Regular
      + Neue Haas Grotesk

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
    * current mode: aller le chercher dans influxDB, avec un mode par défaut si rien en base.
    + reçoit les infos de MAJ PIR depuis PIR_scan
        * détection présence => ping présence dans influxdb
        * reprendre schémas de transition pour déterminer TODO qd réception PIR
        * si PIR entrée, scan BT. Si ok => greetings & passage en mode Cocoon. Sinon, alarm.
        * si PIR écran, sortir de la mise en veille (xset dpms force on/off, xset -q)
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

+ PIR_scanner
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
