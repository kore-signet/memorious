import json
import chevron

with open("seasons-metadata.json") as seasonsf:
    seasons = json.load(seasonsf)

with open("season-page-template.html") as templatef:
    base_template = templatef.read()

for season in seasons:
    with open(f"seasons-pages/{season['slug']}.html", "w") as outf:
        outf.write(chevron.render(base_template, season))