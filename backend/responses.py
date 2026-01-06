import random

# CATEGORIES BANQUE 

banque_responses = {
    "budget": [
        "Ton budget ressemble à un freestyle… on va remettre du tempo.",
        "Si ton argent avait une playlist, ce serait du chaos BPM 240.",
        "Je pense que ton compte tente d’envoyer un SOS en morse.",
        "T’as un budget ou un parc d’attractions ? On va calmer les montagnes russes.",
        "Respire. On découpe ton budget comme un chirurgien stage 1.",
        "Ton portefeuille vit sa meilleure vie sans toi.",
        "On restructure ça comme si t’étais une start-up qui vient de perdre 12 millions.",
        "On met ton budget au régime sec, version ‘perdre 5 kilos avant l’été’.",
        "Je sais pas si c’est un budget ou un roman noir, mais on attaque.",
        "Cette situation financière mérite un documentaire Netflix.",
        "On dirait une brouillon Excel en PLS, je vais arranger ça.",
    ],

    "epargne": [
        "L’épargne, c’est toi qui envoies un message gentil à ton futur toi.",
        "Tu veux épargner ? On commence simple, pas besoin d’être moine Shaolin.",
        "Même 20€, c’est mieux que rien. Ton compte te dira merci.",
        "L’épargne, c’est faire travailler ton argent au lieu qu’il te regarde dormir.",
        "Si t’épargnes jamais, ton compte va demander un congé maladie.",
        "On va te fabriquer une petite réserve, pas besoin d’être Elon Musk.",
        "Mets un billet de côté, ça te fait un bouclier anti-fin-de-mois.",
        "Ton épargne est en mode avion. On va la reconnecter.",
        "Un futur stable, ça commence par des petits gestes qui piquent pas.",
        "On parle d’épargne, pas de te transformer en moine tibétain.",
        "Faut que ton argent ait des enfants, pas qu’il disparaisse.",
    ],

    "achat_impulsif": [
        "T’as encore craqué ? On dirait que ta carte bleue fait du cardio.",
        "Toi, dès que tu vois un truc shiny, ton cerveau clique sur 'Ajouter au panier'.",
        "On dirait que tu collectionnes les remords post-achat.",
        "Ton panier Amazon devrait avoir un bouton 'calme-toi'.",
        "Les achats impulsifs, c’est ton sport national apparemment.",
        "Tes dépenses sont rapides comme Mbappé, mais ton salaire c’est Giroud.",
        "Acheter c’est bien, manger en fin de mois c’est mieux.",
        "À ce rythme, tu vas acheter l’air autour de toi.",
        "Ton banquier a probablement mis ta photo dans son bureau pour prier.",
        "Tu frappes ton compte plus fort qu’un boxeur pro.",
        "Ton portefeuille souffre du syndrome de Stockholm.",
    ],

    "abonnements": [
        "Encore un abonnement ? Tu finances toute l’industrie du streaming.",
        "Tu dois avoir plus d’abos que de chaussettes appariées.",
        "Un abonnement de plus et tu vas débloquer le succès 'Sponsor du Monde'.",
        "Tu t’abonnes à des trucs que tu utilises même pas… un classique.",
        "On va faire un tri, parce que là c’est la salle d’attente des abonnements.",
        "Ton banquier voit 'Spotify – 9.99€', il pleure.",
        "Netflix, Disney+, Amazon, Apple… t’es abonné à la planète.",
        "Ton compte ressemble à un catalogue d’abonnements ambulant.",
        "Supprimer un abo = sauver une vie (celle de ton solde).",
        "Ton portefeuille mérite une thérapie à cause des abonnements.",
        "Est-ce que t’utilises vraiment TOUT ? J’en doute.",
    ],
}


# ==== RÉPONSES GLOBALES POUR ML (boostées aussi) ====

RESPONSES = {
    # SMALLTALK: discuter normal
    "smalltalk": [
        "Je suis là, posé. Tu veux parler de quoi ?",
        "On discute ? Je suis dispo, j’ai pas de pause café moi.",
        "Toujours branché, toujours prêt à te roast ou t'aider.",
        "Raconte, je prends note (ou je me moque gentiment).",
        "On parle finances, vie, projets, drama… j’suis là.",
        "Tu veux papoter ou tu veux régler des dettes ?",
        "Tu veux vider ton sac ou vider ton panier Amazon ?",
        "J’suis ton assistant, pas ton psy… mais si faut aider, je suis là.",
        "Balance ton meilleur délire, je juge pas (trop).",
        "Je capte, je suis là. On discute tranquille.",
        "Vas-y parle, j’suis plus fiable que ton ex.",
        "Je suis dans le cloud mais je t’écoute comme un frère.",
        "Si tu veux juste papoter, j’ai signé pour ça aussi.",
        "Tu veux quoi ? Confiance, conseils, roast ? Choisis.",
        "Je t’écoute, je suis pas pressé, j’ai pas de métro à prendre.",
    ],

    # FALLBACK: quand le bot comprend pas
    "fallback": [
        "Pas capté. Essaie avec des chiffres, des montants, ou des mots simples.",
        "Hmm… c’était flou. Reformule façon humain civilisé.",
        "Je suis fort, mais pas télépathe. Reformule.",
        "On dirait un charade cryptée… refais-moi ça propre.",
        "Je suis là pour t’aider, mais j’ai besoin d’un minimum de contexte.",
        "Parle-moi en euros, en dépenses ou en objectifs, sinon je rame.",
        "Ce message a été sponsorisé par : 'Je comprends pas'.",
        "Essaie avec des phrases simples, ton cerveau me remercie.",
        "Je crois que t’as parlé en klingon, reformule.",
        "J’ai buggé, mais pas crashé. Reformule juste un peu.",
    ],

    # ACK: remerciements
    "ack": [
        "Toujours là, poto.",
        "Avec plaisir, on continue.",
        "De rien ! Maintenant, on s’occupe de tes finances.",
        "Content d’aider, c’est mon taf.",
        "Pas de souci, on gère ça ensemble.",
        "Avec plaisir, t’inquiète.",
        "Toujours dispo (j’ai pas de RTT).",
        "On avance ensemble, pas de stress.",
        "Ok, on continue.",
        "Cimer, ça fait plaisir.",
    ],

    # EMOTIONS (hors finance)
    "emotion_general": [
        "J’sens que t’es pas dans ton meilleur mood… ça arrive.",
        "Tu veux en parler un peu ? Je suis là, je juge pas.",
        "Ça va passer, t’es plus solide que tu penses.",
        "Si t’as besoin de vider le sac, je suis là.",
        "Je suis juste un assistant, mais je peux t’écouter.",
        "Les vibes sont un peu sombres là. On respire ensemble.",
        "La vie c’est du yo-yo, t’inquiète tu vas remonter.",
        "Si t’es down, c’est pas grave. On remonte ça tranquille.",
        "T’inquiète, tu vas t’en sortir, t’es pas seul.",
        "On peut parler, pas obligé que ce soit finances.",
    ],

    # EMOTIONS *FINANCE*
    "emotion_finance": [
        "Le stress financier, normal… mais on structure ça.",
        "Balance ton solde et tes dépenses, et je fais le ménage.",
        "Quand l’argent stresse, on fait un plan. Je suis là.",
        "Tu galères financièrement ? Je t’aide à clarifier.",
        "On attaque ton stress à la source : chiffres, plan, objectifs.",
        "On va transformer ton angoisse en stratégie.",
        "Je suis là pour t’aider à dompter cette pression.",
        "Je te laisse pas avec ce stress, on va faire un vrai plan.",
        "Ça sent le mois compliqué. On va rectifier.",
        "Balance-moi ta situation, je te fais un diagnostic clean.",
    ],
}
