# finance_core.py

import json
import random
from datetime import datetime, timedelta
import re
import os

USER_DATA_FILE = "user_data.json"

SPEND_KEYWORDS = ["payé", "payee", "payer", "acheté", "achat", "dépensé", "coûté", "facture", "sorti", "utilisé", "débit", "abonnement"]
INCOME_KEYWORDS = ["reçu", "gagné", "gain", "touché", "salaire", "rentré", "remboursé", "remboursement", "prime"]
FINANCIAL_RULES = [
    ("Règle 50/30/20", "50% pour les besoins essentiels, 30% pour le plaisir, 20% pour l'épargne. Plus tu mets dans la case 20%, plus ton matelas grossit."),
    ("Fonds d'urgence", "Objectif : 3 à 6 mois de dépenses fixes sur un livret. Commence petit (1 mois) puis augmente."),
    ("Automatisation", "Fais partir l'épargne dès que le salaire tombe. Ce qui n'arrive pas sur ton compte courant ne sera pas dépensé."),
    ("Méthode des enveloppes", "Donne une enveloppe (physique ou virtuelle) à chaque poste variable (courses, restos...). Quand elle est vide, stop jusqu'au mois suivant."),
    ("Négociation annuelle", "Loyers, assurances, abonnements : mets un rappel annuel pour comparer et renégocier — c'est là que les grosses économies se cachent.")
]

_EXPENSE_SYNONYM_GROUPS = {
    "loyer": ["loyer", "logement", "rent", "hypothèque", "hypotheque", "crédit immo", "credit immo", "pret immo", "prêt immo", "pret immobilier", "crédit immobilier"],
    "transport": ["transport", "bus", "métro", "metro", "train", "navigo", "uber", "taxi", "voiture", "essence", "carburant", "parking", "stationnement"],
    "abonnements": ["abonnement", "abonnements", "abo", "netflix", "spotify", "disney", "prime", "canal", "paramount", "gym", "muscu", "salle", "logiciel", "saas"],
    "courses": ["courses", "course", "bouffe", "nourriture", "alimentation", "épicerie", "epicerie", "supermarché", "supermarche"],
    "energie": ["électricité", "electricite", "gaz", "energie", "énergie", "chauffage", "edf"],
    "internet": ["internet", "fibre", "box", "wifi", "free", "orange", "bouygues"],
    "assurance": ["assurance", "mutuelle", "santé", "sante", "assurance auto", "assurance habitation"],
    "loisirs": ["loisir", "loisirs", "sortie", "ciné", "cinema", "jeux", "shopping", "voyage"],
}

CANONICAL_EXPENSE_LOOKUP = {
    synonym.lower(): canonical
    for canonical, synonyms in _EXPENSE_SYNONYM_GROUPS.items()
    for synonym in set([canonical] + synonyms)
}

FIXED_CATEGORIES = {"loyer", "transport", "energie", "internet", "assurance"}


class FinanceCore:
    def __init__(self):
        self.user = {
            "balance": None,
            "income": None,
            "expenses": {},   # dict of poste:montant
            "transactions": [],  # list of {"date","amount","desc","category"}
            "projects": []
        }

    # ---------- persistence ----------
    def load_user(self):
        if os.path.exists(USER_DATA_FILE):
            try:
                with open(USER_DATA_FILE, "r", encoding="utf-8") as f:
                    self.user = json.load(f)
                    # ensure types
                    if "transactions" not in self.user:
                        self.user["transactions"] = []
                print("Profil chargé.")
            except Exception:
                print("Impossible de charger le profil, démarrage d'un profil vierge.")
        else:
            print("Aucun profil trouvé — on va créer le tien. Dis 'profil' pour voir l'état.")

    def save_user(self):
        with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.user, f, ensure_ascii=False, indent=2)
        print("Profil sauvegardé.")

    def reset_user(self):
        self.user = {
            "balance": None,
            "income": None,
            "expenses": {},
            "transactions": [],
            "projects": []
        }
        self.save_user()

    # ---------- setters ----------
    def set_balance(self, amount: float):
        self.user["balance"] = float(amount)
        self.save_user()

    def set_income(self, amount: float):
        self.user["income"] = float(amount)
        self.save_user()

    def set_expenses(self, expenses: dict):
        # expenses: {"loyer":700, "bouffe":200}
        cleaned = {}
        for k,v in expenses.items():
            try:
                cleaned[k] = float(v)
            except:
                pass
        self.user["expenses"] = cleaned
        self.save_user()

    def add_transaction(self, amount: float, desc: str, date: str = None, category: str = "autres"):
        d = date if date else datetime.now().isoformat()
        tx = {"date": d, "amount": float(amount), "desc": desc, "category": category}
        self.user.setdefault("transactions", []).append(tx)
        # update balance if known
        if self.user.get("balance") is not None:
            self.user["balance"] += float(amount)
        self.save_user()

    # ---------- helpers ----------
    def has_balance(self):
        return self.user.get("balance") is not None

    def has_income(self):
        return self.user.get("income") is not None

    def is_setup_complete(self):
        return self.has_balance() and self.has_income() and bool(self.user.get("expenses"))

    def pretty(self, amount: float) -> str:
        try:
            a = float(amount)
            # format french style
            s = f"{a:,.2f} €".replace(",", " ").replace(".", ",")
            return s
        except:
            return str(amount)

    # ---------- reports ----------
    def show_profile(self) -> str:
        lines = []
        b = self.user.get("balance")
        lines.append("Profil financier — version cosy :")
        lines.append(f"- Solde : {self.pretty(b) if b is not None else 'non défini'} (c'est ce qu'on garde à l'œil)")
        inc = self.user.get("income")
        lines.append(f"- Revenu mensuel : {self.pretty(inc) if inc is not None else 'non défini'} (net, pas de chichis)")
        lines.append("- Postes de dépenses principaux :")
        if self.user.get("expenses"):
            for k,v in self.user["expenses"].items():
                lines.append(f"   • {k} : {self.pretty(v)}")
        else:
            lines.append("   • On n'a encore rien listé. Tu peux me dire 'loyer:700, bouffe:250' etc.")
        lines.append(f"- Transactions mémorisées : {len(self.user.get('transactions',[]))}")
        if self.user.get("projects"):
            lines.append(f"- Projets d'épargne actifs : {len(self.user['projects'])}")
        return "\n".join(lines)

    def show_expenses(self) -> str:
        if not self.user.get("expenses"):
            return "Aucun poste enregistré."
        return "\n".join([f"{k} : {self.pretty(v)}" for k,v in self.user["expenses"].items()])

    def monthly_report(self) -> str:
        # somme des dépenses négatives sur 30 jours par catégorie heuristique
        cutoff = datetime.now() - timedelta(days=30)
        cats = {}
        for tx in self.user.get("transactions", []):
            try:
                amt = float(tx["amount"])
                if amt < 0:
                    date_str = tx.get("date")
                    if date_str:
                        try:
                            tx_date = datetime.fromisoformat(date_str)
                            if tx_date < cutoff:
                                continue
                        except Exception:
                            pass  # keep transaction if date is unusable
                    cat = tx.get("category") or "autres"
                    cats[cat] = cats.get(cat, 0.0) + (-amt)
            except:
                pass
        lines = ["Bilan 30 derniers jours :"]
        if not cats:
            lines.append("Rien à signaler, soit tu es sobre niveau dépenses, soit tu ne m'as rien raconté.")
        else:
            for c,v in cats.items():
                lines.append(f"- {c} : {self.pretty(v)}")
        # compare to budgets if available
        if self.user.get("expenses"):
            lines.append("\nComparaison avec tes postes :")
            for k,v in self.user["expenses"].items():
                spent = cats.get(k, 0.0)
                if v > 0:
                    ratio = spent / v
                    if ratio > 1.2:
                        lines.append(f"  • {k} : explosé ({self.pretty(spent)} vs {self.pretty(v)}) — on calme le jeu.")
                    elif ratio > 0.85:
                        lines.append(f"  • {k} : proche ({self.pretty(spent)} / {self.pretty(v)}) — surveille.")
                    else:
                        lines.append(f"  • {k} : OK ({self.pretty(spent)} / {self.pretty(v)}) — cool.")
        lines.append("\nBesoin d'ajuster ? Balance de nouvelles transactions ou dis 'projet'.")
        lines.append(random.choice([
            "On garde le cap ou on sort la calculette ?",
            "Je suis chaud pour passer tes dépenses au shaker si tu veux.",
            "Quand tu veux pour rejouer la partie budget, je suis là."
        ]))
        return "\n".join(lines)

    def quick_advice(self) -> str:
        """Return conversational advice based on actual profile data."""
        inc = self.user.get("income") or 0.0
        expenses = self.user.get("expenses", {})
        total_expenses = sum(expenses.values())
        fixed_total = sum(v for k,v in expenses.items() if self._is_fixed_category(k))
        variable_total = total_expenses - fixed_total

        sections = []

        overview = []
        if inc and total_expenses:
            ratio = (total_expenses / inc) * 100
            overview.append(f"Tu dépenses {self.pretty(total_expenses)} pour {self.pretty(inc)} de revenu ({ratio:.0f}% du salaire).")
            if ratio > 90:
                overview.append("⚠️ Niveau critique : il faut couper dans les dépenses variables immédiates.")
            elif ratio > 70:
                overview.append("Zone tendue : on cible un ou deux postes pour libérer 5-10% du revenu.")
            else:
                overview.append("Ton ratio reste contenu. On renforce l'épargne et on sécurise un matelas.")
        elif inc and not total_expenses:
            overview.append("J'ai ton revenu mais pas tes postes. Ajoute-les pour que je les analyse.")
        else:
            overview.append("Donne-moi ton revenu pour que je calcule tes ratios (50/30/20, fonds d'urgence...).")

        if fixed_total:
            msg = f"Charges fixes (loyer, énergie, internet...) : {self.pretty(fixed_total)}"
            if inc:
                msg += f" ({(fixed_total/inc)*100:.0f}% du revenu)."
            overview.append(msg)
        if variable_total > 0:
            msg = f"Dépenses variables (courses, loisirs, extras) : {self.pretty(variable_total)}"
            if inc:
                msg += f" ({(variable_total/inc)*100:.0f}% du revenu)."
            overview.append(msg)

        sections.append("SYNTHÈSE\n" + "\n".join(f"• {line}" for line in overview))

        if expenses:
            sections.append("\nPOSTES À SURVEILLER\n" + "\n".join(self._expense_focus_lines(expenses, inc)))
        else:
            sections.append("\nPOSTES À SURVEILLER\n• Ajoute tes dépenses principales afin que je pointe les leviers.")

        sections.append("\nPLAN D'ACTION\n" + "\n".join(self.build_savings_playbook(inc, expenses, fixed_total, variable_total)))

        sections.append("\nBASES FINANCIÈRES\n" + "\n".join([f"• {title} : {desc}" for title, desc in FINANCIAL_RULES]))

        sections.append("\nMÉTHODES À ACTIVER\n" + "\n".join(self._savings_methods(inc, expenses, fixed_total, variable_total)))

        return "\n".join(sections)

    def build_savings_playbook(self, inc: float, expenses: dict, fixed_total: float, variable_total: float):
        """Provide actionable multi-step savings advice."""
        steps = []
        step_num = 1
        if inc:
            target = max(inc * 0.2, inc - (fixed_total + variable_total))
            steps.append(f"{step_num}. Automatise {self.pretty(min(target, inc*0.3))} dès réception du salaire (objectif 20% du revenu).")
            step_num += 1
        target_var = self._largest_variable_category(expenses)
        if target_var:
            cat, amount = target_var
            steps.append(f"{step_num}. Sur '{cat}', fixe un plafond hebdo ({self.pretty(amount/4)}). Arrêt des dépenses dès que c'est atteint.")
            step_num += 1
        elif expenses:
            cat, amount = max(expenses.items(), key=lambda x: x[1])
            steps.append(f"{step_num}. '{cat}' est ton plus gros poste : vise -10% ({self.pretty(amount*0.9)}).")
            step_num += 1
        if fixed_total:
            steps.append(f"{step_num}. Compare loyer/assurances/énergie pour gratter {self.pretty(min(fixed_total*0.05, 150))} dans les 30 jours.")
            step_num += 1
        if variable_total > 0:
            steps.append(f"{step_num}. Bloque un budget plaisir de {self.pretty(variable_total*0.5)}. Une fois dépensé, pause jusqu'au mois prochain.")
            step_num += 1
        steps.append(f"{step_num}. Chaque nouvelle dépense ou projet ? Informe-moi pour ajuster le plan en temps réel.")
        return steps

    def _savings_methods(self, inc: float, expenses: dict, fixed_total: float, variable_total: float):
        methods = []
        if inc:
            methods.append(f"• ⚡ Méthode avalanche : ordonne tes dettes de la plus chère à la moins chère et surpaye la première. Utilise {self.pretty(max(inc*0.1, 50))} / mois pour ça.")
            methods.append("• 📦 Méthode boîte à glaçons : vire immédiatement une petite somme vers un sous-compte inaccessible pendant 30 jours.")
        if variable_total > 0:
            methods.append("• 🧾 Méthode cashback: paie tes achats variables avec une carte/cashback dédié, transfère les gains directement sur l'épargne.")
        methods.append("• 📅 Méthode 24h: pour tout achat > 50€, attends 24h. Si l'envie reste, valide; sinon, mets l'argent de côté.")
        methods.append("• 🔁 Audit trimestriel: tous les 3 mois, passe en revue les abonnements/assurances et supprime ceux dormants.")
        return methods

    def _expense_focus_lines(self, expenses: dict, income: float):
        if not expenses:
            return []
        lines = []
        sorted_exp = sorted(expenses.items(), key=lambda x: x[1], reverse=True)[:3]
        for cat, amount in sorted_exp:
            label = "charge fixe" if self._is_fixed_category(cat) else "dépense variable"
            share = (amount / income * 100) if income else None
            if share and share > 35:
                comment = f"pèse {share:.0f}% de ton revenu — priorité pour retrouver de la marge."
            elif not self._is_fixed_category(cat):
                comment = "facile à ajuster : fixe un plafond hebdo ou passe en mode cash envelope."
            else:
                comment = "renégocie / mets en concurrence pour gratter quelques euros."
            lines.append(f"• {cat} ({label}) : {self.pretty(amount)} — {comment}")
        return lines

    def _largest_variable_category(self, expenses: dict):
        candidates = [(k,v) for k,v in expenses.items() if not self._is_fixed_category(k)]
        if not candidates:
            return None
        return max(candidates, key=lambda x: x[1])
    # ---------- projects ----------
    def create_project_plan(self, name: str, amount: float, months: int) -> str:
        # compute required monthly saving and check feasibility
        amount = float(amount)
        months = max(1, int(months))
        monthly = amount / months
        suggestion = ""
        inc = self.user.get("income") or 0.0
        # feasibility rule: can't exceed 30% of income
        feasible = (inc == 0) or (monthly <= 0.3 * inc)
        if inc == 0:
            suggestion = "Je n'ai pas ton revenu. Si tu veux, dis 'profil' puis renseigne ton revenu pour une analyse plus précise."
        else:
            if feasible:
                suggestion = f"C'est faisable : il te faut {self.pretty(monthly)} par mois, soit {int((monthly/inc)*100)}% de ton revenu."
            else:
                suggestion = f"Cela représente {int((monthly/inc)*100)}% de ton revenu. Trop ambitieux sans ajustements."
        # save project
        p = {
            "name": name,
            "target": amount,
            "months": months,
            "monthly": monthly,
            "created": datetime.now().isoformat()
        }
        self.user.setdefault("projects", []).append(p)
        self.save_user()
        return f"Projet '{name}': cible {self.pretty(amount)} en {months} mois -> {self.pretty(monthly)}/mois.\n{suggestion}"

    # ---------- parsing free text transaction ----------
    def try_parse_transaction(self, text: str):
        # recherche d'un montant dans le texte
        m = re.search(r"(-?\d+[ ,]?\d*(?:[.,]\d{1,2})?)\s*(€|euros?)?", text)
        if m:
            num = m.group(1)
            num = num.replace(" ", "").replace(",", ".")
            try:
                amt = float(num)
                context = text[max(m.start()-40, 0): m.end()+40]
                amt = self._apply_contextual_sign(context, amt)
                # description: take words after the amount if any
                after = text[m.end():].strip()
                before = text[:m.start()].strip().split()
                history = " ".join(before[-4:])
                desc = after
                desc = re.sub(r"^(pour|de|chez)\s+", "", desc, flags=re.IGNORECASE).strip()
                if not desc:
                    desc = re.sub(r"(?:j'ai|jai|je|on)\s+", "", history, flags=re.IGNORECASE).strip()
                return amt, desc if desc else history or "Transaction"
            except:
                return None
        return None

    def try_parse_transactions_in_text(self, text: str):
        """Parse multiple amounts from storytelling sentences."""
        chunks = re.split(r"(?:,|\bet\b|\bpuis\b|\bensuite\b|\.|\n)", text, flags=re.IGNORECASE)
        parsed = []
        for chunk in chunks:
            chunk = chunk.strip()
            if not chunk:
                continue
            res = self.try_parse_transaction(chunk)
            if res:
                parsed.append(res)
        return parsed

    def extract_amount(self, text: str):
        """Parse a standalone float from text without logging a transaction."""
        m = re.search(r"(-?\d+[ ,]?\d*(?:[.,]\d{1,2})?)", text)
        if m:
            try:
                return float(m.group(1).replace(" ", "").replace(",", "."))
            except:
                return None
        return None

    def parse_expenses_input(self, text: str):
        """Parse 'poste:montant, poste2:montant' blobs or natural phrases."""
        parsed = {}
        normalized = text.replace(";", ",")
        candidates = [p.strip() for p in normalized.split(",") if p.strip()]
        for p in candidates:
            if ":" in p:
                key, val = p.split(":", 1)
                key_clean = self._clean_expense_key(key)
                try:
                    parsed[key_clean] = float(val.replace(" ", "").replace(",", "."))
                    continue
                except:
                    # try parsing the tail if it still contains more items (ex: "dépenses: loyer 900")
                    nested = self.parse_expenses_input(val)
                    parsed.update(nested)
                    continue
            # fallback pattern "loyer 900" or "loyer est 900"
            m = re.search(r"([a-zA-Zéèêûàç' ]+?)(?:\s*(?:est|=|à|coûte|coute|revient à)?\s*)(-?\d+[ ,.]?\d*)(?:\s*(€|euros?))?$", p, re.IGNORECASE)
            if m:
                key = self._clean_expense_key(m.group(1))
                if not key:
                    continue
                try:
                    parsed[key] = float(m.group(2).replace(" ", "").replace(",", "."))
                except:
                    pass
        # sentences like "je dépense 80€ en abonnements"
        sentence_pattern = re.compile(r"(?:je|j')\s*dépense(?:s)?[^\d]{0,40}(?P<amount>-?\d+[ ,.]?\d*)(?:\s*(?:€|euros?))?(?P<tail>[^.,;\n]*)", re.IGNORECASE)
        for match in sentence_pattern.finditer(text):
            tail = match.group("tail") or ""
            cat_match = re.search(r"(?:en|pour)\s+([a-zA-Zéèêûàç' ]{2,40})", tail, re.IGNORECASE)
            if not cat_match:
                continue
            key = self._clean_expense_key(cat_match.group(1))
            if not key:
                continue
            try:
                parsed[key] = float(match.group("amount").replace(" ", "").replace(",", "."))
            except:
                continue

        # scan full text for additional pairs
        for match in re.finditer(r"([a-zA-Zéèêûàç' ]{2,40})\s*(?:[:=]|est|=|à|coûte|coute|revient à)?\s*(-?\d+[ ,.]?\d*)", text, re.IGNORECASE):
            key = self._clean_expense_key(match.group(1))
            if not key or key in parsed:
                continue
            try:
                parsed[key] = float(match.group(2).replace(" ", "").replace(",", "."))
            except:
                continue
        return parsed

    def _apply_contextual_sign(self, context: str, amount: float) -> float:
        lower = context.lower()
        if any(word in lower for word in INCOME_KEYWORDS):
            return abs(amount)
        if any(word in lower for word in SPEND_KEYWORDS):
            return -abs(amount)
        return amount

    def _clean_expense_key(self, key: str) -> str:
        key = key.strip(" :")
        key = re.sub(r"^(et|plus)\s+", "", key, flags=re.IGNORECASE)
        key = re.sub(r"^(mes|mon|ma)\s+", "", key, flags=re.IGNORECASE)
        key = re.sub(r"^(dépenses?|postes?|charges?)\s+", "", key, flags=re.IGNORECASE)
        key = key.strip()
        if not key:
            return ""
        lowered = key.lower()
        if lowered.startswith(("je ", "j'", "hier", "aujourd")) or "j'ai" in lowered:
            return ""
        parts = lowered.split()
        if len(parts) > 2:
            lowered = " ".join(parts[-2:])
        lowered = lowered.strip()
        return self._canonicalize_expense_key(lowered)

    def _canonicalize_expense_key(self, key: str) -> str:
        key = key.strip()
        if not key:
            return ""
        if key in CANONICAL_EXPENSE_LOOKUP:
            return CANONICAL_EXPENSE_LOOKUP[key]
        for synonym, canonical in CANONICAL_EXPENSE_LOOKUP.items():
            if synonym in key:
                return canonical
        return key

    def _is_fixed_category(self, key: str) -> bool:
        base = self._canonicalize_expense_key(key)
        return base in FIXED_CATEGORIES
