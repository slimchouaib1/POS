import re

with open('src/pages/AnomaliesPage.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

replacements = [
    (r"Détection d'Anomalies", "Anomaly Detection"),
    (r"alertes • Seuil:", "alerts • Threshold:"),
    (r"Total alertes", "Total alerts"),
    (r"Critiques", "Critical"),
    (r"Alertes", "Alerts"),
    (r"toFixed\(0\) \+ '%'", r"toFixed(1) + '%'"),
    (r"<th>Commande</th>", "<th>Order</th>"),
    (r"<th>Risque</th>", "<th>Risk</th>"),
    (r"<th>Type</th>", "<th>Type</th>"),
    (r"<th>Statut</th>", "<th>Status</th>"),
    (r"Alerte #", "Alert #"),
    (r"Score de risque", "Risk score"),
    (r"💡 Explication", "💡 Explanation"),
    (r">Chargement...<", ">Loading...<"),
    (r">Voir détails de la commande<", ">View order details<"),
    (r"Changer le statut:", "Change status:"),
    (r"Historique:", "History:"),
    (r"Commande #", "Order #"),
    (r"Données historiques extraites de la base analytique", "Historical data from analytical database"),
    (r"📋 Informations de la commande", "📋 Order Information"),
    (r"N° Commande", "Order No."),
    (r"Date & Heure", "Date & Time"),
    (r"Paiement", "Payment"),
    (r"Catégorie principale", "Main category"),
    (r">Oui<", ">Yes<"),
    (r">Non<", ">No<"),
    (r": 'Non'", ": 'No'"),
    (r"💰 Montants & Prix", "💰 Amounts & Prices"),
    (r"Montant total", "Total amount"),
    (r"Prix moyen / article", "Avg price / item"),
    (r"Prix max", "Max price"),
    (r"Prix min", "Min price"),
    (r"Ligne max", "Max line total"),
    (r"Ligne min", "Min line total"),
    (r"Déviation prix moy.", "Avg price deviation"),
    (r"🛒 Panier", "🛒 Basket"),
    (r"Taille du panier", "Basket size"),
    (r"} articles", "} items"),
    (r"Articles uniques", "Unique items"),
    (r"Catégories uniques", "Unique categories"),
    (r"Ratio articles uniques", "Unique items ratio"),
    (r"Montant moyen / article", "Avg amount / item"),
    (r"🏷️ Remises & Annulations", "🏷️ Discounts & Voids"),
    (r"Remise appliquée", "Discount applied"),
    (r"Taux remise moyen", "Avg discount rate"),
    (r"Taux remise max", "Max discount rate"),
    (r"Lignes avec remise", "Discounted lines"),
    (r"Montant remise estimé", "Est. discount amount"),
    (r"Commande annulée", "Voided order"),
    (r"Lignes annulées", "Voided lines"),
    (r"👤 Profil Caissier", "👤 Cashier Profile"),
    (r"Total commandes", "Total orders"),
    (r"Montant moyen", "Avg amount"),
    (r"Taux d'annulation", "Void rate"),
    (r"Taux de remises", "Discount rate"),
    (r"Z-Score montant", "Amount Z-Score"),
    (r"Signalé", "Flagged"),
    (r"🧑 Profil Client", "🧑 Customer Profile"),
    (r"Anonyme", "Anonymous"),
    (r"Panier moyen", "Avg basket size"),
    (r"Archétype", "Archetype"),
    (r"Segment prix", "Price tier"),
    (r"🔍 Description de l'anomalie", "🔍 Anomaly description")
]

for pattern, repl in replacements:
    content = re.sub(pattern, repl, content)

with open('src/pages/AnomaliesPage.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

print("Translated AnomaliesPage.tsx successfully.")
