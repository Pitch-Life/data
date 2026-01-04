import json
import string
import argparse
import dataclasses
import urllib.request
from typing import List

limited_sets = {
    'WTR': 'WTR',
    'ARC': 'ARC',
    'MON': 'MON',
    'ELE': 'ELE',
    'UPR': 'UPR',
    'OUT': 'OUT',
    'EVO': 'EVO',
    'HVY': 'HVY',
    'MST': 'MST',
    'ROS': 'ROS',
    'HNT': 'HNT',
    'SEA': 'SEA',
    'MPG': 'MPG',
    'SUP': 'SUP',
}

# This is mostly just to map the two halves of Rhinar v Dorinthea to the same "box" format
boxed_sets = {
    'DVR': 'DVR',
    'RVD': 'DVR',
    'TCC': 'TCC',
    'SMP': 'SMP',
}

'''
Manual fixups

1. Legal formats for Hala
2. Legal formats for Ruudi
3. Legal formats for Brutus
'''

fixes = [
    ('ruudi-gem-keeper', { 'formats': [] }),
    ('hala-bladesaint-of-the-vow', { 'formats': ['cc', 'll' ] }),
    ('brutus-summa-rudis', { 'formats': ['upf']})
]

def merge(item1, item2):
    return {
        **item1,
        'types': sorted(list(set(item1['types'] + item2['types'])), key=str.lower),
        'formats': sorted(list(set(item1['formats'] + item2['formats'])), key=str.lower),
    }

def is_blitz_legal(item):
    return item['blitz_legal'] and not item['blitz_banned'] and not item['blitz_suspended'] #  and not item['blitz_living_legend']:

def is_cc_legal(item):
    return item['cc_legal'] and not item['cc_living_legend'] and not item['cc_banned'] and not item['cc_suspended']

def is_upf_legal(item):
    return ('Young' in item['types'] or 'Adjudicator' in item['types'] or 'Pit-Fighter' in item['types']) and not item['upf_banned']

def is_ll_legal(item):
    return item['ll_legal'] and not item['ll_banned']

def is_commoner_legal(item):
    return item['commoner_legal'] and not item['commoner_banned']

def is_sage_legal(item):
    return item['silver_age_legal'] and not item['silver_age_banned']

def is_limited_legal(item):
    return ('Young' in item['types'] or 'Pit-Fighter' in item['types']) and item['rarity'] not in ['V', 'L']

def is_hero_card(item):
    return 'Hero' in item['types']

def formats(item):
    formats = []

    # Blitz
    if is_blitz_legal(item):
        formats.append('blitz')

    # CC
    if is_cc_legal(item):
        formats.append('cc')

    # UPF
    if is_upf_legal(item):
        formats.append('upf')

    # LL
    if is_ll_legal(item):
        formats.append('ll')

    # Commoner
    if is_commoner_legal(item):
        formats.append('commoner')

    # Silver Age
    if is_sage_legal(item):
        formats.append('sage')

    # Limited
    if is_limited_legal(item):
        limited = limited_sets.get(item['set_id'], None)
        if limited:
            formats.append(f'Limited:{limited}')
        
        boxed = boxed_sets.get(item['set_id'], None)
        if boxed:
            formats.append(f'Boxed:{boxed}')
    
    return formats

def normalize_hero_id(item):
    hero_id = item['name'].translate(str.maketrans("","", string.punctuation)).replace(' ', '-').lower().encode('ascii', 'ignore').decode('ascii')
    overrides = {
        'kayo-strongarm': 'kayo-strong-arm'
    }
    return overrides.get(hero_id, hero_id)

def process_card(item):
    hero_id = normalize_hero_id(item)
    return {
        'id': hero_id,
        'name': item['name'],
        'health': int(item['health']) if item['health'].isnumeric() else 0,
        'types': item['types'],
        'formats': formats(item),
        'image_url': f'https://pitch-life.github.io/images/{hero_id}.heic'
    }

def get_card_data(branch:str = 'main'):
    url = f'https://raw.githubusercontent.com/the-fab-cube/flesh-and-blood-cards/refs/heads/{branch}/json/english/card-flattened.json'
    data = None
    with urllib.request.urlopen(url) as content:
        data = json.load(content)

    with open('../res/card-flattened.json', 'w') as f:
        json.dump(data, f, indent=4)

    return data

def load_card_data():
    with open('../res/card-flattened.json', 'r') as f:
        return json.load(f)

def process(data):
    processed = [process_card(x) for x in data]
    filtered = [x for x in processed if is_hero_card(x)]

    mapping = {}
    for card in filtered:
        other = mapping.get(card['id'])
        if other is not None:
            mapping[card['id']] = merge(other, card)
        else:
            mapping[card['id']] = card


    for fix in fixes:
        id = fix[0]
        change = fix[1]
        item = mapping.get(fix[0])
        if not item: continue
        
        mapping[id] = {
            **item, **change
        }
    uniqued = list(mapping.values())

    return uniqued

def main():
    parser = argparse.ArgumentParser(description="")
    parser.add_argument(
        "-b", "--branch",
        default='develop',
        help="Specify a specific branch for loading card data."
    )
    parser.add_argument(
        "-c", "--use-cache",
        action="store_true",
        help="Use the cached card information instead of downloading it again."
    )
    args = parser.parse_args()

    data = None
    if args.use_cache:
        data = load_card_data()
    else:
        data = get_card_data(branch=args.branch)

    heroes = process(data)

    with open('../heroes.json', 'w') as file:
        json.dump(heroes, file, indent=4)

if __name__ == "__main__":
    main()
