# wack google code from their docs

import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/documents.readonly', 'https://www.googleapis.com/auth/spreadsheets.readonly']

def get_credentials():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return creds

def read_paragraph_element(element):
    text_run = element.get('textRun')
    if not text_run:
        return ''
    return text_run.get('content')


def read_structural_elements(elements):
    text = ''
    for value in elements:
        if 'paragraph' in value:
            elements = value.get('paragraph').get('elements')
            for elem in elements:
                text += read_paragraph_element(elem)
        elif 'table' in value:
            table = value.get('table')
            for row in table.get('tableRows'):
                cells = row.get('tableCells')
                for cell in cells:
                    text += read_structural_elements(cell.get('content'))
        elif 'tableOfContents' in value:
            toc = value.get('tableOfContents')
            text += read_structural_elements(toc.get('content'))
    return text

# extraction code

import re
import csv
import json
import toml
from slugify import slugify

id_regex = re.compile(r"(?:id=(.+)$)|\/document\/d\/(.+?)(?:$|\/)")

docs_service = build('docs', 'v1', credentials=get_credentials())
sheets_service = build('sheets', 'v4', credentials=get_credentials())

def download_seasons():
    seasons = []
    transcripts_sheet = sheets_service.spreadsheets().get(spreadsheetId="1KZHwlSBvHtWStN4vTxOTrpv4Dp9WQrulwMCRocXeYcQ", includeGridData=True).execute()

    for sheet in transcripts_sheet["sheets"]:
        sheet_title = sheet["properties"]["title"]
        # skip overview sheet
        if sheet_title == "OVERVIEW":
            continue

        rows = sheet["data"][0]["rowData"]

        episodes = []

        for row in rows:
            if "values" in row and len(row["values"]) >= 3:
                title = row["values"][0].get("formattedValue", None)
                url = row["values"][2].get("formattedValue", None)
                if title and url:
                    res = id_regex.search(url)
                    if res:
                        id_ = res.group(1) or res.group(2)
                        episodes.append({"id": id_, "title": title})
        
        seasons.append({
            "title": sheet_title,
            "slug": slugify(sheet_title),
            "episodes": episodes
        })

    with open("seasons-metadata.json", "w") as seasonsf:
        json.dump(seasons, seasonsf, indent=4, ensure_ascii=False)

    return seasons

def get_seasons():
    if os.path.exists("seasons-metadata.json"):
        with open("seasons-metadata.json") as f:
            return json.load(f)
    else:
        return download_seasons()

def doc_text(id):
    doc = docs_service.documents().get(documentId=id).execute()
    doc_content = doc.get('body').get('content')
    return read_structural_elements(doc_content)

seasons = get_seasons()
for season in seasons:
    print(f"downloading transcripts for {season['title']}")
    # os.makedirs(season["slug"], exist_ok=True)
    episodes = []

    for i,episode in enumerate(season["episodes"]):
        print(f"#{i} - {episode['title']}")
        # with open(os.path.join(season["slug"], f"{episode['id']}.txt"), "w") as episodef:
            # episodef.write(doc_text(episode["id"]))
        episodes.append({
            "path": f"{episode['id']}.txt",
            "url": episode['id'],
            "title": episode["title"]
        })
    
    with open(f"seasons/{season['slug']}.toml", "w") as f:
        toml.dump({
            "input": {
                "base_directory": os.path.join("transcripts", season['slug']),
                "url_prefix": "https://docs.google.com/document/d/",
                "files": episodes,
                "stemming": "None"
            }
        }, f)