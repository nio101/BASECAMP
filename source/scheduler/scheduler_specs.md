# scheduler_specs

+ on gère un status spécial pour savoir si on est en vacances ou pas, en se basant sur le profil de chauffage! :)
http://bc-power.local:8080/status
si base_profile == "semaine_vacances", alors on est en vacances, sinon on est au boulot!

+ pour chaque jour, on définit des lancement de jobs régulier sur les différentes plages

    # lundi, mardi, jeudi: réveil (6h45 - 7h45) départ (8h00-8h15) nicolas (8h30-8h45), nicolas - départ (9h), normal (9h15-22h00)
    # mercredi: réveil (9h00 - 9h15), travail maison (9h30-18h), normal (18h15-22h00)
    # vendredi: réveil (6h45 - 7h45) départ (8h00-8h15) nicolas (8h30-9h15), travail maison (9h30-18h), normal (18h15-22h00)
    # samedi-dimanche: (9h00 - 9h45) (hello, week-end), week-end normal (10h00 - 22h00)

on peut faire un job générique qui prend en paramètre hour+mn+la liste des templates en cas de vacances et en cas de boulot.
si on est hors période (appel à 6h45 en vacances, qui commence à 9h30) alors on ne fait rien...

+ on peut ajouter un lien avec le calendrier outlook pour détecter les tags basecamp & jouer des reminders pour les poubelles par exemple... :)

