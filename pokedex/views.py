from django.shortcuts import render, redirect
import requests
import random

API_URL = "https://pokeapi.co/api/v2/pokemon/"

# Fonction pour récupérer les données propres d'un Pokémon (Artworks HD)
def get_pk_data(id_or_name):
    try:
        res = requests.get(f"{API_URL}{str(id_or_name).lower()}")
        if res.status_code == 200:
            data = res.json()
            stats = {s['stat']['name']: s['base_stat'] for s in data['stats']}
            return {
                'id': data['id'],
                'name': data['name'],
                # Image HD (non pixel)
                'image': data['sprites']['other']['official-artwork']['front_default'],
                # Image de DOS pour le combat
                'image_back': data['sprites']['back_default'],
                'hp': stats.get('hp', 0),
                'hp_max': stats.get('hp', 0),
                'attack': stats.get('attack', 0),
                'defense': stats.get('defense', 0),
                'speed': stats.get('speed', 0),
                'types': [t['type']['name'] for t in data['types']],
            }
    except:
        return None

def index(request):
    current_search = request.POST.get('pokemon_name') or request.GET.get('pokemon_name', '1')
    team = request.session.get('team', [])
    context = {'team': team}
    
    current_pk = get_pk_data(current_search)

    if current_pk:
        # Tâche 15 : Augmenter la limite à 251
        if current_pk['id'] > 251:
            context['error'] = "Limited to the first 251 Pokémon."
        else:
            prev_id = current_pk['id'] - 1 if current_pk['id'] > 1 else None
            next_id = current_pk['id'] + 1 if current_pk['id'] < 251 else None
            
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
        new_pk = get_pk_data(str(pokemon_id))
        if new_pk:
            team.append(new_pk)
            request.session['team'] = team
    return redirect(f'/?pokemon_name={pokemon_id}')

def remove_team_member(request, member_index):
    team = request.session.get('team', [])
    if 0 <= member_index < len(team):
        del team[member_index]
        request.session['team'] = team
    return redirect(request.META.get('HTTP_REFERER', 'index'))

def clear_team(request):
    if 'team' in request.session:
        del request.session['team']
    return redirect('index')

# --- LOGIQUE DE COMBAT ---

def combat(request):
    player_team = request.session.get('team', [])
    if len(player_team) < 5:
        return redirect('index')

    if 'ai_team' not in request.session:
        ai_team = [get_pk_data(random.randint(1, 251)) for _ in range(5)]
        request.session['ai_team'] = ai_team
        request.session['player_active_idx'] = 0
        request.session['ai_active_idx'] = 0
        request.session['battle_log'] = "A challenger appears!"

    p_idx = request.session.get('player_active_idx', 0)
    a_idx = request.session.get('ai_active_idx', 0)
    
    # Si l'IA n'a plus de Pokémon, on affiche la victoire
    if a_idx >= 5:
        return render(request, 'pokedex/combat.html', {'victory': True})

    context = {
        'player_pk': player_team[p_idx],
        'ai_pk': request.session['ai_team'][a_idx],
        'player_team': player_team,
        'ai_team': request.session['ai_team'],
        'battle_log': request.session.get('battle_log'),
        'p_idx': p_idx, 'a_idx': a_idx
    }
    return render(request, 'pokedex/combat.html', context)

def attack_turn(request):
    player_team = request.session.get('team')
    ai_team = request.session.get('ai_team')
    p_idx = request.session['player_active_idx']
    a_idx = request.session['ai_active_idx']
    
    p_pk, ai_pk = player_team[p_idx], ai_team[a_idx]

    # Dégâts simplifiés
    damage = max(10, p_pk['attack'] - (ai_pk['defense'] // 2))
    ai_pk['hp'] -= damage
    log = f"{p_pk['name']} deals {damage} damage."

    if ai_pk['hp'] <= 0:
        ai_pk['hp'] = 0
        request.session['ai_active_idx'] += 1
        log = f"{ai_pk['name']} is KO!"
    else:
        # Riposte de l'IA
        ai_damage = max(10, ai_pk['attack'] - (p_pk['defense'] // 2))
        p_pk['hp'] -= ai_damage
        log += f" | Enemy deals {ai_damage}."
        if p_pk['hp'] <= 0:
            p_pk['hp'] = 0

    request.session['team'], request.session['ai_team'] = player_team, ai_team
    request.session['battle_log'] = log
    return redirect('combat')

def switch_pokemon(request, index):
    request.session['player_active_idx'] = index
    request.session['battle_log'] = f"Go {request.session['team'][index]['name']}!"
    return redirect('combat')

# Tâche 5.2 : Fonction officielle pour réinitialiser
def reset_combat(request):
    keys = ['ai_team', 'player_active_idx', 'ai_active_idx', 'battle_log']
    for k in keys:
        if k in request.session: del request.session[k]
    # Soigner l'équipe
    team = request.session.get('team', [])
    for p in team: p['hp'] = p['hp_max']
    request.session['team'] = team
    return redirect('combat')