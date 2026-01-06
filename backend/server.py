
import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from io import StringIO
import sys
from brain import think   # le code python

app = Flask(__name__)
CORS(app)


@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    message = data.get("message", "")
    profile = data.get("profile", {})
    user_data = data.get("userData", {})
    
    # Ajouter le profil au message si disponible
    if profile and (profile.get("income") or profile.get("expenses")):
        income = profile.get("income", 0)
        expenses = profile.get("expenses", 0)
        name = profile.get("name", "")
        
        context_info = []
        if name:
            context_info.append(f"Nom: {name}")
        if income:
            context_info.append(f"Revenu mensuel: {income}€")
        if expenses:
            context_info.append(f"Dépenses mensuelles: {expenses}")
        
        if context_info:
            # Préfixer le message avec le contexte utilisateur
            message = f"[PROFIL: {', '.join(context_info)}]\n{message}"
    
    # Contexte des données utilisateur
    if user_data:
        balance = user_data.get("balance", 0)
        transactions_count = len(user_data.get("transactions", []))
        message = f"[SOLDE ACTUEL: {balance}€ | {transactions_count} transactions]\n{message}"
    
    # Suppress console output from think()
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    
    response = think(message)
    
    sys.stdout = old_stdout
    
    # Détecter automatiquement les données à enregistrer
    detected_data = detect_financial_data(message, user_data.get("balance", 0))
    
    return jsonify({
        "response": response,
        "detectedData": detected_data
    })

def detect_financial_data(message, current_balance):
    """Utilise Gemini pour détecter automatiquement les données financières"""
    from gemini_api import get_gemini_response
    import json
    
    prompt = f"""
Tu es un extracteur de données financières. Analyse ce message et extrais UNIQUEMENT les informations financières explicites.

Message: "{message}"
Solde actuel: {current_balance}€

RÈGLES STRICTES:
1. BALANCE: Si l'utilisateur dit "J'ai X euros" ou "Mon solde est X" → retourne le montant exact
2. TRANSACTION: Si l'utilisateur dit "J'ai payé X euros pour Y" ou "J'ai dépensé X pour Y" → retourne montant négatif et description
3. TRANSACTION POSITIVE: Si "J'ai reçu X euros" ou "On m'a donné X" → retourne montant positif
4. OTHER: Toute autre info importante (objectif d'épargne, rappel, etc.)
5. Si AUCUNE donnée financière explicite → retourne null

Réponds UNIQUEMENT avec du JSON valide (pas de markdown):
{{
  "balance": 200 ou null,
  "transaction": {{"amount": -20, "description": "bouffe"}} ou null,
  "other": {{"title": "Objectif", "value": "Economiser 500€"}} ou null
}}
"""
    
    try:
        result = get_gemini_response(prompt)
        # Nettoyer le résultat (enlever markdown si présent)
        result = result.strip()
        if result.startswith('```json'):
            result = result[7:]
        if result.startswith('```'):
            result = result[3:]
        if result.endswith('```'):
            result = result[:-3]
        result = result.strip()
        
        parsed = json.loads(result)
        
        # Ne retourner que si au moins une donnée est présente
        if parsed.get("balance") is not None or parsed.get("transaction") is not None or parsed.get("other") is not None:
            return parsed
        return None
    except Exception as e:
        print(f"Erreur détection: {e}")
        return None

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5002))
    host = os.environ.get("HOST", "0.0.0.0")
    print(f"Server running on http://{host}:{port}")
    app.run(host=host, port=port)
