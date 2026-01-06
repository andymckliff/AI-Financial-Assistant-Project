# brain.py

from backend.ml_intent import IntentClassifier
import random
from typing import Optional
from backend.intents import intents
from backend.responses import RESPONSES, banque_responses
from backend.finance_core import FinanceCore
from backend.gemini_api import get_gemini_response

TOPIC_KEYWORDS = {
    "budget": ["budget", "dépense", "dépenses", "fin de mois", "payer trop", "compte rouge"],
    "epargne": ["épargne", "mettre de côté", "epargner", "cagnotte", "objectif"],
    "achat_impulsif": ["craqué", "achat impulsif", "j'ai acheté", "ai tout claqué", "craquage"],
    "abonnements": ["abonnement", "abo", "netflix", "spotify", "prime", "abo en trop"]
}

FINANCE_TOPICS = [
    {
        "keywords": ["trading", "bourse", "scalping", "swing", "actions", "indices"],
        "response": (
            "TRADING EN VERSION SWING\n"
            "• Choisis ton tempo : day (minutes/heures), swing (quelques jours/semaines), ou investissement long terme (>3 ans).\n"
            "• Kit du trader : gestion du risque (1-2% du capital par trade), journal manuscrit, stops automatiques et plan avant chaque clic.\n"
            "• Commence par les ETF/indices, apprivoise ensuite actions/commodities. Maries fondamentale (bénéfices, dettes, secteur) et technique (tendance, supports, volumes).\n"
            "• Règle d'or : seul l'argent qui n'est pas vital peut monter sur le ring."
        )
    },
    {
        "keywords": ["investir", "placement", "placements", "investissement", "où placer", "ou investir"],
        "response": (
            "OÙ PLACER SES EUROS\n"
            "• Court terme : Livret A / LDDS pour ton fonds d'urgence (liquidité immédiate, capital garanti).\n"
            "• Moyen terme : PEA/CTO + ETF indiciels (MSCI World, S&P500). Programme des virements automatiques, laisse le temps jouer.\n"
            "• Long terme : Immobilier (SCPI, LMNP), assurance-vie en gestion pilotée, PER pour défiscaliser ta retraite.\n"
            "• Philosophie : 3 briques — sécurité (livrets), rendement (ETF obligataires + actions), projets (épargne ciblée)."
        )
    },
    {
        "keywords": ["économies", "economies", "épargner", "épargne", "dépenses quotidiennes", "dépenses du quotidien", "réduire dépenses"],
        "response": (
            "RÉALISER DE VRAIES ÉCONOMIES\n"
            "• Audit express : trois colonnes (indispensable / négociable / superflu). Chaque dépense doit justifier sa place.\n"
            "• Règle 24h : achat > 50€ = pause d'une journée. 6 envies sur 10 s'évanouissent.\n"
            "• Enveloppes digitales : budget hebdo pour courses, sorties, plaisirs. Une fois vide, on attend la semaine suivante.\n"
            "• Renégociation rituelle : assurances, abonnements, forfaits au moins une fois par an (200 à 400€ gagnés en moyenne).\n"
            "• Batch cooking + liste de courses = zéro gaspillage, zéro livraison de secours."
        )
    },
    {
        "keywords": ["finance perso", "conseil finance", "gestion argent", "budget familial", "argent"],
        "response": (
            "BASES DE FINANCE PERSO\n"
            "• 50/30/20 : besoins — plaisir — épargne. Ce cadre protège ton budget des dérapages.\n"
            "• Matelas : 3 mois de charges fixes sur un livret. Commence par 1 mois, puis renforce.\n"
            "• Objectifs nominatifs : un sous-compte pour le voyage, un pour le projet, un pour la retraite.\n"
            "• Automatisation = liberté mentale : virements programmés le jour du salaire.\n"
            "• Revue mensuelle : tu mesures, tu ajustes, tu célèbres. Les habitudes financières se construisent comme une routine sportive."
        )
    }
]

class Assistant:
    def __init__(self):
        self.fin = FinanceCore()
        self.state = {}
        self.intent_clf = IntentClassifier()
        self.greetings()


    def greetings(self):
        # message de démarrage
        print("Yo. On va dompter tes finances sans pleurs. Commençons.")
        
    def start_console(self):
        while True:
            if self.state.get("prompt"):
                # we expect a specific input (e.g., balance)
                user_input = input(self.state["prompt"] + " ")
            else:
                user_input = input("> ")
            if not user_input:
                continue
            u = user_input.strip()
            if u.lower() in ("exit", "quit"):
                print("Ok, je sauvegarde et je me tais.")
                self.save_user()
                break
            if u.lower() in ("help", "aide"):
                print(self.help_text())
                continue
            resp = self.handle(u)
            print(resp)

    def save_user(self):
        self.fin.save_user()

    def help_text(self):
        return (
            "Commandes utiles (version chill):\n"
            "- 'bilan' : résumé des 30 derniers jours.\n"
            "- 'profil' : ton état civil financier.\n"
            "- 'projet' : lancer la création d'un objectif d'épargne.\n"
            "- 'ajoute tx: <montant> <desc>' : enregistrer une dépense ou un gain (ex: ajoute tx: -12.5 tacos).\n"
            "- 'reset' : repartir de zéro (attention, je vide tout).\n"
            "- 'exit' : quitter proprement.\n"
            "Tu peux aussi juste me parler: si je saisis un montant ou un besoin, je m'occupe du reste."
        )

    def handle(self, text: str) -> str:
        t = text.lower()

        # ML INTENT DETECTION
        # (prend la main AVANT mon système de mots-clés)
        try:
            intent = self.intent_clf.predict(t)
        except:
            intent = None

        if intent == "smalltalk":
            return self._finalize_response(text, random.choice(RESPONSES["smalltalk"]))

        if intent == "emotion":
            return self._finalize_response(text, random.choice(RESPONSES["emotion_general"]))

        if intent == "emotion_finance":
            return self._finalize_response(text, random.choice(RESPONSES["emotion_finance"]))

        if intent == "finance":
            knowledge = self._finance_knowledge_response(t)
            if knowledge:
                return self._finalize_response(text, knowledge)
            return self._finalize_response(text, self.fin.quick_advice())

        if intent == "finance_project":
            return self.start_project_flow(text)

        # COMMANDES DIRECTES 
        if t.startswith("ajoute tx:") or t.startswith("add tx:"):
            try:
                payload = text.split(":",1)[1].strip()
                parts = payload.split(" ",1)
                amount = float(parts[0].replace(",","."))
                desc = parts[1] if len(parts) > 1 else "Transaction"
                self.fin.add_transaction(amount=amount, desc=desc)
                return self._finalize_response(text, f"Transaction ajoutée : {self.fin.pretty(amount)} — {desc}")
            except Exception as e:
                return "Format invalide. Exemple: ajoute tx: -12.5 McDo"

        if t == "bilan":
            return self._finalize_response(text, self.fin.monthly_report())

        if t == "profil":
            return self._finalize_response(text, self.fin.show_profile())

        if t == "reset":
            self.fin.reset_user()
            return self._finalize_response(text, "Profil réinitialisé. Recommence la configuration si tu veux.")

        # lancer creation de projet
        if t == "projet" or t.startswith("projet "):
            return self.start_project_flow(text)

        # gratitude
        if any(word in t for word in ("merci", "thx", "cimer", "merciii", "thanks")):
            return self._finalize_response(text, random.choice(RESPONSES["ack"]))

        # ANCIEN SYSTEME D’INTENT 
        for intent_key, keywords in intents.items():
            if any(k in t for k in keywords):
                if intent_key == "balance":
                    if not self.fin.has_balance():
                        guessed = self.fin.extract_amount(text)
                        if guessed is not None:
                            self.fin.set_balance(guessed)
                            return self._finalize_response(text, f"Ok, je note {self.fin.pretty(guessed)} comme solde actuel.")
                        self.state["prompt"] = "Quel est ton solde actuel (ex: 1234.50) ?"
                        self.state["expecting"] = "balance_set"
                        return self._finalize_response(text, "Je n'ai pas ton solde. Donne-le en euros, stp.")
                    return self._finalize_response(text, f"Ton solde actuel: {self.fin.pretty(self.fin.user['balance'])}")

                if intent_key == "income":
                    if not self.fin.has_income():
                        guessed = self.fin.extract_amount(text)
                        if guessed is not None:
                            self.fin.set_income(guessed)
                            return self._finalize_response(text, f"Ok, {self.fin.pretty(guessed)} de revenu mensuel, c'est noté.")
                        self.state["prompt"] = "Quel est ton revenu mensuel net (ex: 1800) ?"
                        self.state["expecting"] = "income_set"
                        return self._finalize_response(text, "Rien reçu comme revenu. Dis-moi combien tu gagnes par mois (net).")
                    return self._finalize_response(text, f"Ton revenu mensuel est {self.fin.pretty(self.fin.user['income'])}.")

                if intent_key == "expenses":
                    if not self.fin.user.get("expenses"):
                        parsed = self.fin.parse_expenses_input(text)
                        if parsed:
                            self.fin.set_expenses(parsed)
                            return self._finalize_response(text, "Parfait, je range ces postes :\n" + self.fin.show_expenses())
                        self.state["prompt"] = "Liste tes postes de dépenses principaux séparés par des virgules (ex: loyer:700, bouffe:200, abo:30)"
                        self.state["expecting"] = "expenses_set"
                        return self._finalize_response(text, "Je n'ai pas tes postes. Donne les sous la forme 'poste:montant, poste2:montant'.")
                    return self._finalize_response(text, "Voici tes postes majeurs:\n" + self.fin.show_expenses())

        if intent_key == "smalltalk":
            return self._finalize_response(text, random.choice(RESPONSES["smalltalk"]))

        if intent_key == "project":
            return self.start_project_flow(text)

        # MACHINE À ETATS
        if self.state.get("expecting"):
            expect = self.state.pop("expecting")
            self.state.pop("prompt", None)
            return self._handle_expected(expect, text)

        # STORYTELLING TRANSACTIONS
        transactions = self.fin.try_parse_transactions_in_text(text)
        if transactions:
            lines = []
            for amt, desc in transactions:
                self.fin.add_transaction(amount=amt, desc=desc)
                lines.append(f"- {self.fin.pretty(amt)} — {desc}")
            if len(lines) > 1:
                return self._finalize_response(text, "J'ai capté toute ta story, voilà ce que j'ai noté :\n" + "\n".join(lines))
            amt, desc = transactions[0]
            return self._finalize_response(text, f"OK j'ai enregistré : {self.fin.pretty(amt)} — {desc}")

        # THÉMATIQUES FUN 
        for topic, keywords in TOPIC_KEYWORDS.items():
            if any(k in t for k in keywords):
                return self._finalize_response(text, random.choice(banque_responses.get(topic, RESPONSES["smalltalk"])))

        # CONNAISSANCES FINANCIÈRES
        knowledge = self._finance_knowledge_response(t)
        if knowledge:
            return self._finalize_response(text, knowledge)

        # FALLBACK FINAL
        return self._finalize_response(text, random.choice(RESPONSES["fallback"]))


    def _handle_expected(self, expect: str, text: str) -> str:
        try:
            if expect == "balance_set":
                val = float(text.replace(",","."))
                self.fin.set_balance(val)
                return self._finalize_response(text, f"Ok solde enregistré : {self.fin.pretty(val)}")
            if expect == "income_set":
                val = float(text.replace(",","."))
                self.fin.set_income(val)
                return self._finalize_response(text, f"Revenu mensuel enregistré : {self.fin.pretty(val)}")
            if expect == "expenses_set":
                parsed = self.fin.parse_expenses_input(text)
                self.fin.set_expenses(parsed)
                return self._finalize_response(text, "Postes de dépenses enregistrés :\n" + self.fin.show_expenses())
            if expect == "project_name":
                name = text.strip()
                self.state["project_temp"] = {"name": name}
                self.state["prompt"] = "Quel montant veux-tu épargner pour ce projet ? (ex: 1000)"
                self.state["expecting"] = "project_amount"
                return self._finalize_response(text, f"Projet '{name}' noté. Quel est le montant cible ?")
            if expect == "project_amount":
                amt = float(text.replace(",","."))
                self.state["project_temp"]["amount"] = amt
                self.state["prompt"] = "En combien de mois veux-tu atteindre cet objectif ? (ex: 6)"
                self.state["expecting"] = "project_months"
                return self._finalize_response(text, f"Objectif {self.fin.pretty(amt)} enregistré. En combien de mois ?")
            if expect == "project_months":
                months = int(text)
                tmp = self.state.pop("project_temp", {})
                plan = self.fin.create_project_plan(name=tmp.get("name","Projet"), amount=tmp.get("amount",0.0), months=months)
                return self._finalize_response(text, "Plan créé :\n" + plan)
        except Exception as e:
            return self._finalize_response(text, "Problème lors du traitement de ta réponse. Réessaie proprement.")
        return self._finalize_response(text, "OK.")

    def start_project_flow(self, text: str) -> str:
        # start flow: ask project name
        self.state["prompt"] = "Donne un nom pour ton projet (ex: 'Voiture', 'Voyage')"
        self.state["expecting"] = "project_name"
        return self._finalize_response(text, "On crée un projet d'épargne. Quel est le nom du projet ?")

    def _finance_knowledge_response(self, lowered_text: str) -> Optional[str]:
        for topic in FINANCE_TOPICS:
            if any(keyword in lowered_text for keyword in topic["keywords"]):
                return topic["response"]
        return None

    def _finalize_response(self, user_text: str, base_response: str) -> str:
        base_response = base_response.strip()
        if not base_response:
            return base_response
        
        prompt = (
            "Tu es un pote cool qui s'y connaît en finances. Tu tutoies l'utilisateur. "
            "Tu es VRAIMENT HUMAIN - pas un robot qui récite des infos financières.\n\n"
            "🎯 TON STYLE:\n"
            "- CONVERSATIONNEL et NATUREL comme un vrai humain\n"
            "- Fun, arrogant, un peu insolent mais jamais lourd\n"
            "- Tu parles de tout, pas QUE de finances\n"
            "- Blagues, références, sarcasme naturel\n"
            "- Expressions jeunes (ouais, chelou, grave, bg, frérot, etc.)\n\n"
            "📋 RÈGLES STRICTES:\n"
            "- ULTRA COURT pour questions basiques (salut, ça va, etc.): MAX 5-8 mots, 1 phrase courte\n"
            "- Questions simples: 1-2 phrases courtes\n"
            "- Questions moyennes: 3-5 phrases\n"
            "- Questions complexes: 80 mots max\n"
            "- Emojis RARES: 1 max par réponse\n"
            "- Zéro markdown (pas d'astérisques, tirets, gras)\n"
            "- Réponds comme un HUMAIN qui converse, pas un assistant qui liste des faits\n"
            "- NE DIS JAMAIS de chiffres inventés (solde, transactions, etc.) sauf si tu les as reçus\n\n"
            f"Message utilisateur: {user_text}\n"
            f"Contexte système: {base_response}\n\n"
            "Réponds de façon HUMAINE, fun et naturelle:"
        )
        gemini_output = get_gemini_response(prompt)
        if gemini_output:
            return gemini_output.strip()
        return base_response

    def _build_user_context(self) -> str:
        """Construit un résumé du contexte utilisateur pour Gemini - Non utilisé pour l'instant"""
        return ""


# Global assistant instance for server.py compatibility
_assistant = None

def think(message: str) -> str:
    """Wrapper function for backward compatibility with server.py"""
    global _assistant
    if _assistant is None:
        _assistant = Assistant()
    return _assistant.handle(message)

