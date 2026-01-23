from django.shortcuts import render, redirect
import requests
import random

API_URL = "https://pokeapi.co/api/v2/pokemon/"
SPECIES_URL = "https://pokeapi.co/api/v2/pokemon-species/"

def get_pk_data(id_or_name):
    # interroge API pour choper les données
    try:
        res = requests.get(f"{API_URL}{str(id_or_name).lower()}")
        if res.status_code == 200:
            data = res.json()
            stats = {s['stat']['name']: s['base_stat'] for s in data['stats']}
            pk_id = data['id']

            return {
                'id': pk_id,
                'name': data['name'],
                'image': data['sprites']['other']['official-artwork']['front_default'],
                'hp': stats.get('hp', 0),
                'hp_max': stats.get('hp', 0),
                'attack': stats.get('attack', 0),
                'defense': stats.get('defense', 0),
                'speed': stats.get('speed', 0),
                'types': [t['type']['name'] for t in data['types']],
                'species_url': data['species']['url'] 
            }
    except:
        return None

def get_evolutions(species_url):
    # SPEICIES_URL + id pour évolution
    evo_list = []
    try:
        species_res = requests.get(species_url)
        if species_res.status_code != 200: 
            return []
        
        evo_chain_url = species_res.json()['evolution_chain']['url']
        chain_res = requests.get(evo_chain_url)
        if chain_res.status_code != 200: 
            return []
        
        chain_data = chain_res.json()['chain']
        
        def parse_chain(chain_node):
            species_name = chain_node['species']['name']
            species_id = chain_node['species']['url'].rstrip('/').split('/')[-1]
            img_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/{species_id}.png"

            evo_list.append({
                'id': int(species_id),
                'name': species_name,
                'image': img_url
            })

            for next_node in chain_node['evolves_to']:
                parse_chain(next_node)

        parse_chain(chain_data)
    except Exception as e:
        print(f"Erreur évolution: {e}")
        
    return evo_list

def index(request):
    # Pokémon + équipe.
    current_search = request.POST.get('pokemon_name') or request.GET.get('pokemon_name', '1')
    
    if 'team' not in request.session:
        request.session['team'] = []
    team = request.session['team']
    
    context = {'team': team}
    current_pk = get_pk_data(current_search)

    if current_pk:
        if current_pk['id'] > 251:
            context['error'] = "Limited to the first 251 Pokémon."
        else:
            prev_id = current_pk['id'] - 1 if current_pk['id'] > 1 else None
            next_id = current_pk['id'] + 1 if current_pk['id'] < 251 else None
            
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
    # Ajoute un Pokémon à team
    team = request.session.get('team', [])
    if len(team) < 5: # max 5
        new_pk = get_pk_data(str(pokemon_id))
        if new_pk:
            team.append(new_pk)
            request.session['team'] = team
            request.session.modified = True
    return redirect(f'/?pokemon_name={pokemon_id}')

def remove_team_member(request, member_index):
  # Supprime de team
    team = request.session.get('team', [])
    if 0 <= member_index < len(team):
        del team[member_index]
        request.session['team'] = team
        request.session.modified = True
    return redirect('index')

def clear_team(request):
   # reset l'équipe
    request.session['team'] = []
    return redirect('index')

def combat(request):
   # Affiche combat
    player_team = request.session.get('team', [])
    if len(player_team) == 0:
        return redirect('index')

    battle_started = request.session.get('battle_started', False)
    # Init
    if not battle_started:
        first_available = next((i for i, p in enumerate(player_team) if p['hp'] > 0), 0)
        request.session['battle_started'] = True
        request.session['player_active_idx'] = first_available
        request.session.modified = True
    # equipe adverse
    if 'ai_team' not in request.session:
        ai_team = [get_pk_data(random.randint(1, 251)) for _ in range(5)]
        request.session['ai_team'] = ai_team
        request.session['player_active_idx'] = 0
        request.session['ai_active_idx'] = 0
    # Affichage
    p_idx = request.session.get('player_active_idx', 0)
    a_idx = request.session.get('ai_active_idx', 0)
    ai_team = request.session['ai_team']
    # Vérif KO
    if p_idx >= len(player_team):
        next_idx = next((i for i in range(len(player_team)) if player_team[i]['hp'] > 0), None)
        # Cherche le next 
        if next_idx is not None:
            p_idx = next_idx
            request.session['player_active_idx'] = p_idx
    # Limite
    if a_idx >= 5:
        a_idx = 4
    
    context = {
        'player_pk': player_team[p_idx] if p_idx < len(player_team) else None,
        'ai_pk': ai_team[a_idx],
        'player_team': player_team,
        'ai_team': ai_team,
        'p_idx': p_idx, 
        'a_idx': request.session.get('ai_active_idx', 0),
        'battle_started': True,
    }
    return render(request, 'pokedex/combat.html', context)

# Démarre le combat
def start_combat(request, pokemon_idx):
    # Init le combat avec le Pokémon choisi
    player_team = request.session.get('team', [])
    
    if pokemon_idx < 0 or pokemon_idx >= len(player_team) or player_team[pokemon_idx]['hp'] <= 0:
        return redirect('combat')
    
    ai_team = [get_pk_data(random.randint(1, 251)) for _ in range(5)]
    request.session['ai_team'] = ai_team
    request.session['player_active_idx'] = pokemon_idx
    request.session['ai_active_idx'] = 0
    request.session['battle_started'] = True
    request.session.modified = True
    
    return redirect('combat')

# fitht turn
def attack_turn(request):
  # étapes : attaque joueur, vérif KO, attaque IA, vérif KO
    player_team = request.session.get('team')
    ai_team = request.session.get('ai_team')
    p_idx = request.session.get('player_active_idx', 0)
    a_idx = request.session.get('ai_active_idx', 0)
    # actif
    p_pk = player_team[p_idx]
    ai_pk = ai_team[a_idx]
    # attaque joueur
    damage = max(10, p_pk['attack'] - (ai_pk['defense'] // 2))
    ai_pk['hp'] -= damage

    if ai_pk['hp'] <= 0:
        ai_pk['hp'] = 0
        request.session['ai_active_idx'] = a_idx + 1
    else:
        # attaque IA
        ai_damage = max(10, ai_pk['attack'] - (p_pk['defense'] // 2))
        p_pk['hp'] -= ai_damage
        if p_pk['hp'] <= 0:
            p_pk['hp'] = 0
            next_idx = next((i for i in range(p_idx + 1, len(player_team)) if player_team[i]['hp'] > 0), None)
            if next_idx is not None:
                request.session['player_active_idx'] = next_idx
            else:
                request.session['player_active_idx'] = len(player_team)

    request.session['team'] = player_team
    request.session['ai_team'] = ai_team
    return redirect('combat')

def switch_pokemon(request, index):
# switch 
    request.session['player_active_idx'] = index
    return redirect('combat')

def reset_combat(request):
    # Reset le combat + vie
    keys = ['ai_team', 'player_active_idx', 'ai_active_idx', 'battle_log', 'battle_started']
    for k in keys:
        if k in request.session: 
            del request.session[k]
    
    team = request.session.get('team', [])
    for p in team: 
        p['hp'] = p['hp_max']
    request.session['team'] = team
    request.session.modified = True
    return redirect('combat')

def stop_combat(request):
    # Termine le combat et retourne au Pokédex.
    keys = ['ai_team', 'player_active_idx', 'ai_active_idx', 'battle_log', 'battle_started']
    for k in keys:
        if k in request.session: 
            del request.session[k]
    
    team = request.session.get('team', [])
    for p in team: 
        p['hp'] = p['hp_max']
    request.session['team'] = team
    request.session.modified = True
    return redirect('index')

def new_opponent(request):
    # Nouvelle équipe adverse
    keys = ['ai_team', 'player_active_idx', 'ai_active_idx', 'battle_log', 'battle_started']
    for k in keys:
        if k in request.session: 
            del request.session[k]
    # Reinitialise la vie
    team = request.session.get('team', [])
    for p in team: 
        p['hp'] = p['hp_max']
    request.session['team'] = team
    request.session.modified = True
    return redirect('combat')