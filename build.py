import json
import toml
import chevron 
import subprocess
import os

os.makedirs('seasons', exist_ok=True)
os.makedirs('stork-configs', exist_ok=True)
os.makedirs('indexes', exist_ok=True)


def build_index(season):
    index = {
        'base_directory': 'data',
        'url_prefix': "https://docs.google.com/document/d/",
        'files': []
    }

    for episode in season['episodes']:
        if 'download' not in episode:
            continue
        index['files'].append({
            'title': episode['title'],
            'url': episode['docs_id'],
            'path': episode['download']['plain']
        })
    
    with open(f"stork-configs/{season['id']}.toml", "w") as season_config:
        toml.dump({'input': index}, season_config)
    
    subprocess.run(["stork", "build", "--input", f"stork-configs/{season['id']}.toml", "--output", f"indexes/{season['id']}.st"])
    

seasons = json.load(open("data/seasons.json"))

categories_ids = {
    'divine': ['counterweight','twilight-mirage','road-to-partizan', 'partizan','road-to-palisade', 'palisade'],
    'hieron': ['autumn-in-hieron', 'marielda', 'winter-in-hieron', 'spring-in-hieron'],
    'longfielle': ['sangfielle'],
    'patreon': ['patreon-games', 'patreon-other'],
    'extras': ['extras', 'media-club-plus'],
    'others': []
}

categories = {
    'divine': [],
    'hieron': [],
    'longfielle': [],
    'patreon': [],
    'extras': [],
    'others': []
}

for name,season in seasons.items():
    has_category = False
    for cat,vals in categories_ids.items():
        if name in vals:
            categories[cat].append(season)
            has_category = True
            break

    if not has_category:
        categories['others'].append(season)

    with open(f"seasons/{season['id']}.html", "w") as season_out, open("season-page-template.html") as season_template:
        season_out.write(chevron.render(season_template, season))

    build_index(season)

with open("index.html", "w") as index_out, open("index-template.html") as index_template:
    index_out.write(chevron.render(index_template, categories))