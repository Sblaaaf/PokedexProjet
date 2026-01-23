from django.shortcuts import render, redirect
import requests
import random

API_URL = "https://pokeapi.co/api/v2/pokemon/"
SPECIES_URL = "https://pokeapi.co/api/v2/pokemon-species/"

# Fonction pour récupérer les données propres d'un Pokémon
def get_pk_data(id_or_name):
    try:
        # On utilise le nom ou l'ID
        res = requests.get(f"{API_URL}{str(id_or_name).lower()}")
        if res.status_code == 200:
            data = res.json()
            stats = {s['stat']['name']: s['base_stat'] for s in data['stats']}
            
            # On récupère l'ID depuis l'objet pour être sûr (utile si on cherche par nom)
            pk_id = data['id']

            return {
                'id': pk_id,
                'name': data['name'],
                'image': data['sprites']['other']['official-artwork']['front_default'],
                'image_front': data['sprites']['other']['official-artwork']['front_default'],
                'image_back': data['sprites']['other']['official-artwork']['front_default'],
                'hp': stats.get('hp', 0),
                'hp_max': stats.get('hp', 0),
                'attack': stats.get('attack', 0),
                'defense': stats.get('defense', 0),
                'speed': stats.get('speed', 0),
                'types': [t['type']['name'] for t in data['types']],
                # Important pour récupérer les évolutions ensuite
                'species_url': data['species']['url'] 
            }
    except:
        return None

# Nouvelle fonction pour gérer la chaîne d'évolution
def get_evolutions(species_url):
    evo_list = []
    try:
        # 1. Récupérer les infos de l'espèce pour avoir l'URL de la chaine
        species_res = requests.get(species_url)
        if species_res.status_code != 200: return []
        
        evo_chain_url = species_res.json()['evolution_chain']['url']
        
        # 2. Récupérer la chaine d'évolution
        chain_res = requests.get(evo_chain_url)
        if chain_res.status_code != 200: return []
        
        chain_data = chain_res.json()['chain']
        
        # 3. Fonction récursive pour parcourir l'arbre d'évolution
        def parse_chain(chain_node):
            species_name = chain_node['species']['name']
            # Extraction de l'ID depuis l'URL de l'espèce (ex: .../species/25/ -> 25)
            species_id = chain_node['species']['url'].rstrip('/').split('/')[-1]
            
            # Construction manuelle de l'URL image pour éviter un appel API supplémentaire lent
            img_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{species_id}.png"

            evo_list.append({
                'id': int(species_id),
                'name': species_name,
                'image': img_url
            })

            # S'il y a des évolutions suivantes, on continue
            for next_node in chain_node['evolves_to']:
                parse_chain(next_node)

        parse_chain(chain_data)
        
    except Exception as e:
        print(f"Erreur évolution: {e}")
        
    return evo_list

def index(request):
    current_search = request.POST.get('pokemon_name') or request.GET.get('pokemon_name', '1')
    
    # Stock team
    if 'team' not in request.session:
        request.session['team'] = []
    team = request.session['team']
    
    context = {'team': team}
    
    # Pokémon principal
    current_pk = get_pk_data(current_search)

    if current_pk:
        # Limite à 251
        if current_pk['id'] > 251:
            context['error'] = "Limited to the first 251 Pokémon."
        else:
            prev_id = current_pk['id'] - 1 if current_pk['id'] > 1 else None
            next_id = current_pk['id'] + 1 if current_pk['id'] < 251 else None
            
            # Evolutions
            current_pk['evolutions'] = get_evolutions(current_pk['species_url'])

            context.update({
                'current_pk': current_pk,
                'prev_pk': get_pk_data(str(prev_id)) if prev_id else None,
                'next_pk': get_pk_data(str(next_id)) if next_id else None,
            })
    else:
        context['error'] = "Pokémon not found!"

    return render(request, 'pokedex/index.html', context)

def add_to_team(request, pokemon_id):
    team = request.session.get('team', [])
    if len(team) < 5:
        # Doublons ?
        if not any(p['id'] == int(pokemon_id) for p in team):
            new_pk = get_pk_data(str(pokemon_id))
            if new_pk:
                team.append(new_pk)
                request.session['team'] = team
                request.session.modified = True
    return redirect(f'/?pokemon_name={pokemon_id}')

def remove_team_member(request, member_index):
    team = request.session.get('team', [])
    if 0 <= member_index < len(team):
        del team[member_index]
        request.session['team'] = team
        request.session.modified = True
    return redirect('index') # Redirige vers index plutôt que referer pour éviter des soucis de POST

def clear_team(request):
    request.session['team'] = []
    return redirect('index')

# --- LOGIQUE DE COMBAT (Inchangée) ---

def combat(request):
    player_team = request.session.get('team', [])
    if len(player_team) == 0:
        return redirect('index')

    # Vérifier si le combat a déjà été initié
    battle_started = request.session.get('battle_started', False)
    
    if not battle_started:
        # Écran de sélection du Pokémon initial
        context = {
            'player_team': player_team,
            'battle_started': False,
        }
        return render(request, 'pokedex/combat.html', context)
    
    # Sinon, le combat est déjà en cours
    if 'ai_team' not in request.session:
        ai_team = [get_pk_data(random.randint(1, 251)) for _ in range(5)]
        request.session['ai_team'] = ai_team
        request.session['player_active_idx'] = 0
        request.session['ai_active_idx'] = 0
        request.session['battle_log'] = "A challenger appears!"

    p_idx = request.session.get('player_active_idx', 0)
    a_idx = request.session.get('ai_active_idx', 0)
    ai_team = request.session['ai_team']
    
    # Protection index hors limite
    if p_idx >= len(player_team): 
        p_idx = 0
        request.session['player_active_idx'] = p_idx
    
    # Si tous les Pokémon adverses sont KO ou si tous les Pokémon du joueur sont KO
    if a_idx >= 5:
        # Utiliser le dernier Pokémon adverse pour l'affichage
        a_idx = 4
    
    context = {
        'player_pk': player_team[p_idx],
        'ai_pk': ai_team[a_idx],
        'player_team': player_team,
        'ai_team': ai_team,
        'battle_log': request.session.get('battle_log'),
        'p_idx': p_idx, 
        'a_idx': request.session.get('ai_active_idx', 0),  # Utiliser la vraie valeur pour la condition de victoire
        'battle_started': True,
    }
    return render(request, 'pokedex/combat.html', context)

def start_combat(request, pokemon_idx):
    """Démarre le combat avec le Pokémon choisi"""
    player_team = request.session.get('team', [])
    
    # Vérifier que l'index est valide et que le Pokémon a des HP
    if pokemon_idx < 0 or pokemon_idx >= len(player_team) or player_team[pokemon_idx]['hp'] <= 0:
        return redirect('combat')
    
    # Initialiser le combat
    ai_team = [get_pk_data(random.randint(1, 251)) for _ in range(5)]
    request.session['ai_team'] = ai_team
    request.session['player_active_idx'] = pokemon_idx
    request.session['ai_active_idx'] = 0
    request.session['battle_log'] = f"Go {player_team[pokemon_idx]['name']}!"
    request.session['battle_started'] = True
    request.session.modified = True
    
    return redirect('combat')

def attack_turn(request):
    player_team = request.session.get('team')
    ai_team = request.session.get('ai_team')
    p_idx = request.session.get('player_active_idx', 0)
    a_idx = request.session.get('ai_active_idx', 0)
    
    p_pk = player_team[p_idx]
    ai_pk = ai_team[a_idx]

    damage = max(10, p_pk['attack'] - (ai_pk['defense'] // 2))
    ai_pk['hp'] -= damage
    log = f"{p_pk['name']} deals {damage} damage."

    if ai_pk['hp'] <= 0:
        ai_pk['hp'] = 0
        request.session['ai_active_idx'] = a_idx + 1
        log = f"{ai_pk['name']} is KO!"
    else:
        ai_damage = max(10, ai_pk['attack'] - (p_pk['defense'] // 2))
        p_pk['hp'] -= ai_damage
        log += f" | Enemy deals {ai_damage}."
        if p_pk['hp'] <= 0:
            p_pk['hp'] = 0

    request.session['team'] = player_team
    request.session['ai_team'] = ai_team
    request.session['battle_log'] = log
    return redirect('combat')

def switch_pokemon(request, index):
    request.session['player_active_idx'] = index
    team = request.session.get('team', [])
    if index < len(team):
        name = team[index]['name']
        request.session['battle_log'] = f"Go {name}!"
    return redirect('combat')

def reset_combat(request):
    keys = ['ai_team', 'player_active_idx', 'ai_active_idx', 'battle_log']
    for k in keys:
        if k in request.session: del request.session[k]
    
    team = request.session.get('team', [])
    for p in team: p['hp'] = p['hp_max']
    request.session['team'] = team
    request.session.modified = True
    return redirect('combat')

def stop_combat(request):
    """Arrête le combat et nettoie le cache"""
    keys = ['ai_team', 'player_active_idx', 'ai_active_idx', 'battle_log']
    for k in keys:
        if k in request.session: del request.session[k]
    
    # Réinitialise la vie des Pokémon du joueur
    team = request.session.get('team', [])
    for p in team: 
        p['hp'] = p['hp_max']
    request.session['team'] = team
    request.session.modified = True
    return redirect('index')