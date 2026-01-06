# ml_intent.py

class IntentClassifier:
    """
    Classifieur léger basé sur des mots-clés pour éviter les dépendances lourdes.
    """

    def __init__(self):
        self.intent_keywords = {
            "finance_project": ["objectif d'épargne", "projet d'épargne", "plan d'épargne", "objectif financier"],
            "finance": [
                "budget", "argent", "finance", "investir", "investissement", "épargne",
                "épargner", "dépenses", "loyer", "salaire", "revenu", "trading", "bourse"
            ],
            "emotion_finance": ["angoisse financière", "peur de l'argent", "stress financier", "galère d'argent"],
            "emotion": ["triste", "stressé", "fatigué", "démotivé"],
            "smalltalk": ["salut", "bonjour", "yo", "ça va", "hello"]
        }

    def predict(self, text: str):
        text = text.lower()
        for intent, keywords in self.intent_keywords.items():
            if any(keyword in text for keyword in keywords):
                return intent
        return "unknown"
