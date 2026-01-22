from django.shortcuts import render, redirect
import requests
import random

API_URL = "https://pokeapi.co/api/v2/pokemon/"
SPECIES_URL = "https://pokeapi.co/api/v2/pokemon-species/"

# extraire ID depuis URL
def get_id_from_url(url):
    return url.split('/')[-2]

# Récupérer les infos du Pokémon
def get_pokemon_basic(id_or_name):
    try:
        response = requests.get(f"{API_URL}{id_or_name}")
        if response.status_code == 200:
            data = response.json()
            return {
                'id': data['id'],
                'name': data['name'],
                'image': data['sprites']['other']['official-artwork']['front_default'] or data['sprites']['front_default'],
            }
    except:
        pass
    return None

# Récupérer toutes les infos du Pokémon
def get_full_pokemon_data(id_or_name):
    pk = get_pokemon_basic(id_or_name)
    if not pk:
        return None

    # 1 - Stats & Types
    response = requests.get(f"{API_URL}{id_or_name}")
    data = response.json()
    
    stats = {stat['stat']['name']: stat['base_stat'] for stat in data['stats']}
    types = [t['type']['name'] for t in data['types']]
    
    pk.update({
        'hp': stats.get('hp', 0),
        'attack': stats.get('attack', 0),
        'defense': stats.get('defense', 0),
        'types': types
    })

    # 2 - Evolutions
    # je cherche l'espèce pour avoir le lien de la chaine
    try:
        species_res = requests.get(f"{SPECIES_URL}{pk['id']}")
        if species_res.status_code == 200:
            species_data = species_res.json()
            evo_chain_url = species_data['evolution_chain']['url']
            
            # On récupère la chaine
            evo_res = requests.get(evo_chain_url)
            if evo_res.status_code == 200:
                evo_data = evo_res.json()
                chain = evo_data['chain']
                
                evolutions = []
                
                # Petite fonction récursive pour parcourir l'arbre des évolutions
                def parse_chain(node):
                    e_id = get_id_from_url(node['species']['url'])
                    evolutions.append({
                        'name': node['species']['name'],
                        'id': e_id,
                        # URL de l'image pour ne pas appeller API
                        'image': f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{e_id}.png"
                    })
                    for child in node['evolves_to']:
                        parse_chain(child)
                
                parse_chain(chain)
                pk['evolutions'] = evolutions
    except:
        pk['evolutions'] = []

    return pk

def index(request):
    current_search = '1' 

    if request.method == 'POST':
        current_search = request.POST.get('pokemon_name')
    elif request.GET.get('pokemon_name'):
        current_search = request.GET.get('pokemon_name')
    
    context = {'team': request.session.get('team', [])}

    if current_search: 
        current_search = current_search.lower()

    # Le Pokémon Central (Complet avec évolutions)
    current_pk = get_full_pokemon_data(current_search)

    if current_pk:
        # On limite la recherche aux 251 premiers Pokémon
        if current_pk['id'] > 251:
            context['error'] = "Limited search to Pokémon #1 to #251."
            return render(request, 'pokedex/index.html', context)

        current_id = current_pk['id']
        prev_id = current_id - 1 if current_id > 1 else None
        next_id = current_id + 1 if current_id < 251 else None
        
        # Pour les voisins, on ne prend que les infos de base (plus rapide)
        context.update({
            'current_pk': current_pk,
            'prev_pk': get_pokemon_basic(prev_id),
            'next_pk': get_pokemon_basic(next_id),
        })
    else:
        context['error'] = "Pokemon not found!"

    return render(request, 'pokedex/index.html', context)

# Ajouter un Pokémon à l'équipe
def add_to_team(request, pokemon_id):
    team = request.session.get('team', [])
    if len(team) < 5:
        # requete API
        res = requests.get(f"{API_URL}{pokemon_id}")
        if res.status_code == 200:
            data = res.json()
            stats = {s['stat']['name']: s['base_stat'] for s in data['stats']}
            
            pk_data = {
                'id': data['id'],
                'name': data['name'],
                'image_back': data['sprites']['back_default'],
                'image_front': data['sprites']['other']['official-artwork']['front_default'],
                'hp': stats.get('hp', 0),
                'hp_max': stats.get('hp', 0), # On garde le max pour la barre de vie
                'attack': stats.get('attack', 0),
                'defense': stats.get('defense', 0),
                'speed': stats.get('speed', 0),
                'types': [t['type']['name'] for t in data['types']]
            }
            team.append(pk_data)
            request.session['team'] = team
    
    return redirect(f'/?pokemon_name={pokemon_id}')

# Supprimer un membre (index)
def remove_team_member(request, member_index):
    team = request.session.get('team', [])
    
    if 0 <= member_index < len(team):
        del team[member_index]
        request.session['team'] = team
    
    return redirect(request.META.get('HTTP_REFERER', 'index'))

# Supprimer l'équipe
def clear_team(request):
    if 'team' in request.session:
        del request.session['team']
    return redirect('index')


# reset combat et équipe IA
def reset_combat(request):
    if 'ai_team' in request.session:
        del request.session['ai_team']
    return redirect('combat')

# COMBAT V2 - tour par tour + PV, attaques, types, speed

def combat(request):
    # récupère équipe min 5
    player_team = request.session.get('team', [])
    if len(player_team) < 5:
        return redirect('index')

    # équipe adverse (IA)
    if 'ai_team' not in request.session:
        ai_team = []
        for _ in range(5):
            rand_id = random.randint(1, 151)
            res = requests.get(f"{API_URL}{rand_id}")
            data = res.json()
            stats = {s['stat']['name']: s['base_stat'] for s in data['stats']}
            ai_team.append({
                'name': data['name'],
                'image_front': data['sprites']['front_default'],
                'hp': stats.get('hp', 0),
                'hp_max': stats.get('hp', 0),
                'attack': stats.get('attack', 0),
                'defense': stats.get('defense', 0),
                'speed': stats.get('speed', 0),
                'types': [t['type']['name'] for t in data['types']]
            })
        request.session['ai_team'] = ai_team
        # qui combat ? (index 0 au début)
        request.session['player_active_idx'] = 0
        request.session['ai_active_idx'] = 0
        request.session['battle_log'] = "A wild team appears! Prepare for battle!"

    # état actuel du combat (session stockée)
    ai_team = request.session['ai_team']
    p_idx = request.session.get('player_active_idx', 0)
    a_idx = request.session.get('ai_active_idx', 0)
    
    # Pokémon actuels
    p_pk = player_team[p_idx]
    a_pk = ai_team[a_idx]

    context = {
        'player_pk': p_pk,
        'ai_pk': a_pk,
        'player_team': player_team,
        'battle_log': request.session.get('battle_log'),
        'p_idx': p_idx,
        'a_idx': a_idx
    }
    return render(request, 'pokedex/combat_V1.html', context)

def attack_turn(request):
    # données
    player_team = request.session.get('team')
    ai_team = request.session.get('ai_team')
    p_idx = request.session['player_active_idx']
    a_idx = request.session['ai_active_idx']
    
    p_pk = player_team[p_idx]
    a_pk = ai_team[a_idx]

    # MULTIPLICATEURS DE TYPE
    multipliers = {
        "fire": {"grass": 2, "water": 0.5},
        "water": {"fire": 2, "grass": 0.5},
        "grass": {"water": 2, "fire": 0.5}
    }

    # Fonction pour calculer le multiplicateur
    def get_multiplier(p1_types, p2_types):
        m = 1
        for t1 in p1_types:
            for t2 in p2_types:
                if t1 in multipliers and t2 in multipliers[t1]:
                    m *= multipliers[t1][t2]
        return m

    # DÉROULEMENT DU TOUR
    log = []
    
    # speed ?
    if p_pk['speed'] >= a_pk['speed']:
        first, second = 'player', 'ai'
    else:
        first, second = 'ai', 'player'

    # Calcul attaque
    def hit(attacker, defender):
        mult = get_multiplier(attacker['types'], defender['types'])
        damage = max(5, (attacker['attack'] - (defender['defense'] / 2)) * mult)
        defender['hp'] -= int(damage)
        return f"{attacker['name']} deals {int(damage)} damage!"

    # Round 1
    if first == 'player':
        log.append(hit(p_pk, a_pk))
        if a_pk['hp'] > 0: # Si > 0 alors IA survit donc elle réplique
            log.append(hit(a_pk, p_pk))
    else:
        log.append(hit(a_pk, p_pk))
        if p_pk['hp'] > 0: # Si > 0 je réplique
            log.append(hit(p_pk, a_pk))

    # K.O. ?
    if a_pk['hp'] <= 0:
        a_pk['hp'] = 0
        log.append(f"{a_pk['name']} is KO!")
        request.session['ai_active_idx'] += 1 # L'IA passe au suivant
    
    if p_pk['hp'] <= 0:
        p_pk['hp'] = 0
        log.append(f"{p_pk['name']} is KO!")
        # SWITCH necessaire

    # Stock PV
    request.session['team'] = player_team
    request.session['ai_team'] = ai_team
    request.session['battle_log'] = " | ".join(log)

    return redirect('combat')

# Changer de Pokémon "actif"
def switch_pokemon(request, index):
    # modifie index
    request.session['player_active_idx'] = index
    request.session['battle_log'] = f"Go {request.session.get('team')[index]['name']}!"
    return redirect('combat')


    return render(request, 'pokedex/combat_V1.html', context)