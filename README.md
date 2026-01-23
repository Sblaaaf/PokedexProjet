# Pokédex Django - Système de Combat

Application web interactive pour explorer et combattre avec des Pokémon, réalisée en Django et utilisant l'API PokeAPI.
Par souci d'homogénéité, l'application est en anglais car les données sont plus facile à récupérer en anglais qu'en francias.

## Vue d'ensemble

Ce projet propose un Pokédex complet où tu peux:
- Rechercher et explorer les 251 premiers Pokémon
- Constituer une équipe personnalisée de 5 Pokémon maximum
- Combattre contre des équipes d'IA générées aléatoirement

## Fonctionnalités principales

- **Pokédex interactif**: Recherche par nom ou numéro, navigation avant/arrière
- **Gestion d'équipe**: Ajouter/retirer des Pokémon à l'équipe (max 5)
- **Système de combat**: Affrontement au tour par tour avec calcul de dégâts basé sur Attaque/Défense
- **Intelligence artificielle**: Équipes adverses générées aléatoirement
- **Gestion de victoire/défaite**: Détection automatique et messages appropriés
- **Interface fluide**: Démarrage automatique du combat avec le premier Pokémon vivant
- **Dynamique de combat**: Option de "switch" pour changer de Pokémon pendant le combat

## Technologies

- **Framework**: Django 4.2.27
- **Langage**: Python 3.9.6
- **Frontend**: HTML5, CSS3
- **API**: PokeAPI v2 pour les données Pokémon
- **Stockage d'état**: Sessions Django (pas de base de données persistante)

## Installation

1. Cloner le projet
2. Créer un environnement virtuel:
   ```
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Installer les dépendances:
   ```
   pip install django requests pillow
   ```
4. Lancer le serveur:
   ```
   python manage.py runserver
   ```
5. Accéder à `http://127.0.0.1:8000/`

## Comment jouer

1. Navigue dans le Pokédex ou recherche un Pokémon spécifique
2. Ajoute jusqu'à 5 Pokémon à ton équipe avec le bouton "Capture"
3. Clique sur "Combat" pour affronter une équipe adverse
4. Utilise le bouton ATTACK pour combattre
5. Gère ton équipe en changeant de Pokémon si le tien s'affaiblit
6. Utilise "Restart Battle" pour relancer contre la même équipe
7. Utilise "New Opponent" pour générer une nouvelle équipe adverse

## Améliorations récentes

- Démarrage automatique du combat avec le premier Pokémon disponible
- Affichage des stats d'attaque/défense dans les sidebars
- Affichage des types dans l'arène avec badges colorés
- Correction de la détection de défaite (affichage correct de "DEFEAT")