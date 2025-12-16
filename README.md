# Gestion de Stock des Équipements Inwi

## Description
Cette application desktop permet de gérer le **stock des équipements télécoms** pour l’opérateur Inwi.  
Elle est développée en **Python** avec **Tkinter** pour l’interface graphique et **MySQL** pour la base de données.  

L’application peut :
- Importer des fichiers Excel contenant des périphériques.
- Convertir automatiquement les fichiers Excel en CSV.
- Mettre à jour le stock existant ou ajouter de nouveaux périphériques.
- Suivre l’état des équipements (**Fonctionnel / Non fonctionnel**).
- Ajouter, modifier ou supprimer des périphériques manuellement.
- Afficher tous les équipements dans une interface intuitive.

---

## Fonctionnalités

1. **Import Excel**  
   - Le fichier Excel peut contenir des périphériques déjà existants.  
   - Si un périphérique est déjà présent dans la base, la **quantité est mise à jour automatiquement**.  
   - Si un périphérique est nouveau, il est ajouté à la base.

2. **Gestion du stock**  
   - Ajouter un périphérique manuellement.  
   - Modifier les informations ou la quantité d’un périphérique.  
   - Supprimer un périphérique.

3. **Suivi du statut**  
   - Chaque périphérique a un **statut** : `Fonctionnel` ou `Non fonctionnel`.

4. **Interface graphique avec Tkinter**  
   - Formulaire pour saisir/modifier les périphériques.  
   - Tableau (`Treeview`) pour afficher le stock complet.  
   - Boutons pour ajouter, modifier, supprimer et importer Excel.

---

## Technologies utilisées
- **Python 3**
- **Tkinter** pour l’interface graphique
- **MySQL** pour la base de données
- **Pandas** pour la lecture des fichiers Excel et CSV
- **mysql-connector-python** pour la connexion à la base de données

---

## Structure de la base de données MySQL

**Table : `equipements`**

| Colonne     | Type       | Description                  |
|------------|-----------|------------------------------|
| id         | INT       | Identifiant unique           |
| nom        | VARCHAR   | Nom du périphérique          |
| type       | VARCHAR   | Type de périphérique         |
| quantite   | INT       | Quantité en stock            |
| fournisseur| VARCHAR   | Fournisseur / marque         |
| remarque   | TEXT      | Remarques supplémentaires    |
| statut     | VARCHAR   | Fonctionnel / Non fonctionnel|

---


