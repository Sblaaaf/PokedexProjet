# Projet Pokédex Python (Django)

Ce projet est un Pokédex interactif réalisé en Python avec le framework Django.
Il utilise l'API publique PokeApi pour récupérer les données.

## Fonctionnalités
1.  **Recherche** : Recherche de Pokémon par nom ou numéro (gestion des 150 premiers et plus).
2.  **Navigation** : Boutons Suivant/Précédent pour parcourir le Pokédex.
3.  **Gestion d'équipe** : Possibilité de constituer une équipe de 5 Pokémon.
4.  **Système de Combat** : Affrontement entre l'équipe du joueur et une IA générée aléatoirement basé sur la "force" (expérience de base) des Pokémon.

## Choix Techniques
* **Langage** : Python 3
* **Framework Web** : Django (pour sa robustesse et sa gestion facile des templates).
* **Interface** : HTML/CSS (Fichiers statiques Django).
* **Données** : 
    * Récupération via `requests` sur https://pokeapi.co/
    * Pas de base de données SQL persistante pour les équipes : utilisation des **Sessions Django** pour stocker l'équipe temporairement le temps de la visite de l'utilisateur.

## Installation et Lancement (Mac/Linux)

1.  **Cloner ou télécharger le dossier du projet.**
2.  **Ouvrir un terminal** dans le dossier du projet.
3.  **Créer un environnement virtuel** (recommandé) :
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```
4.  **Installer les dépendances** :
    ```bash
    pip install django requests pillow
    ```
5.  **Lancer le serveur** :
    ```bash
    python manage.py runserver
    ```
6.  **Ouvrir le navigateur** à l'adresse : `http://127.0.0.1:8000/`

## Comment jouer ?
1.  Tapez le nom d'un Pokémon (ex: "pikachu") ou naviguez avec les flèches.
2.  Cliquez sur "Capturer !" pour l'ajouter à votre équipe.
3.  Une fois 5 Pokémon capturés, un bouton "COMBATTRE" apparaît.
4.  Affrontez l'IA et tentez de gagner !# PokedexProjet
