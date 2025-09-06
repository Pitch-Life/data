import json
import string
import urllib.request

limited_sets = [
    'WTR',
    'ARC',
    'MON',
    'ELE',
    'UPR',
    'OUT',
    'EVO',
    'HVY',
    'MST',
    'ROS',
    'HNT',
    'SEA',
    'MPG',
    'SUP',
]

boxed_sets = [
    'DVR',
    'TCC',
    'SMP',
]

def merge(item1, item2):
    return {
        **item1,
        'types': sorted(list(set(item1['types'] + item2['types'])), key=str.lower),
        'formats': sorted(list(set(item1['formats'] + item2['formats'])), key=str.lower),
    }

def formats(item):
    formats = []
    if item['blitz_legal'] and not item['blitz_living_legend'] and not item['blitz_banned'] and not item['blitz_suspended']:
        formats.append('blitz')
    if item['cc_legal'] and not item['cc_living_legend'] and not item['cc_banned'] and not item['cc_suspended']:
        formats.append('cc')
    if ('Young' in item['types'] or 'Adjudicator' in item['types'] or 'Pit-Fighter' in item['types']) and not item['upf_banned']:
        formats.append('upf')
    if item['ll_legal'] and not item['ll_banned']:
        formats.append('ll')
    if item['commoner_legal'] and not item['commoner_banned']:
        formats.append('commoner')

    if ('Young' in item['types'] or 'Pit-Fighter' in item['types']) and item['rarity'] not in ['V', 'L']:
        if item['set_id'] in limited_sets:
            formats.append(f'Limited:{item['set_id']}')
        
        if item['set_id'] in boxed_sets:
            formats.append(f'Boxed:{item['set_id']}')

    # Fixup some known data issues
    if normalize_hero_id(item) == 'rhinar' and ('Boxed:DVR' not in formats):
        formats.append('Boxed:DVR')

    if normalize_hero_id(item) == 'valda-brightaxe' and ('Limited:MPG' not in formats):
        formats.append('Limited:MPG')
    
    return formats

def normalize_hero_id(item):
    hero_id = item['name'].translate(str.maketrans("","", string.punctuation)).replace(' ', '-').lower().encode('ascii', 'ignore').decode('ascii')
    return hero_id

def process(item):
    hero_id = normalize_hero_id(item)
    return {
        'id': hero_id,
        'name': item['name'],
        'health': int(item['health']) if item['health'].isnumeric() else 0,
        'types': item['types'],
        'formats': formats(item),
        'image_url': f'https://pitch-life.github.io/images/{hero_id}.heic'
    }

branch = 'super-slam'
url = f'https://raw.githubusercontent.com/the-fab-cube/flesh-and-blood-cards/refs/heads/{branch}/json/english/card-flattened.json'
data = None

with urllib.request.urlopen(url) as content:
    data = json.load(content)

processed = [process(x) for x in data]
filtered = [x for x in processed if 'Hero' in x['types']]

mapping = {}
for card in filtered:
    other = mapping.get(card['id'])
    if other is not None:
        mapping[card['id']] = merge(other, card)
    else:
        mapping[card['id']] = card

uniqued = list(mapping.values())

with open('../heroes.json', 'w') as file:
    json.dump(uniqued, file, indent=4)

