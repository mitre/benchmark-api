import requests
import re
import json
import uuid
from bs4 import BeautifulSoup
from difflib import SequenceMatcher

url = "https://public.cyber.mil/stigs/downloads/"

headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Max-Age': '3600',
    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'
}

req = requests.get(url, headers)
soup = BeautifulSoup(req.content, 'html.parser')
table = soup.find_all('table')[0] # Grab the first table

row_marker = 0
stigs = []

versionRegex = r'V\dR\d(\d)?(\d)?'

existingStigs = []

# Load existing stigs
with open('stigs.json', 'r') as f:
    existingStigs = json.load(f)

def cleanText(inputText):
    return re.sub(' +', ' ', inputText.replace('\r', ' ').replace('\u200b', '').replace('\n', ' ').split('\t')[0].strip()).strip()

for row in table.find_all('tr'):
    try:
        columns = row.find_all('td')
        href = ""
        name = ""
        size = ""
        for idx, column in enumerate(columns):
            if idx == 2:
                size = column.get_text().strip()
            if idx == 1:
                href = column.find('a')['href']
                name = cleanText(column.get_text())
        if (href != "" and name != "" and size != "" and ('stig' in name.lower() or 'benchmark' in name.lower() or 'stig' in href.lower() or 'benchmark' in href.lower()) and "viewer" not in name.lower() and "srg" not in href.lower()):
            # If we have a zip file
            filename = href.split('/')[-1]
            if (href.lower().endswith('.zip')):
                versionMatches = re.search(versionRegex, filename.upper())
                if versionMatches is not None:
                    versionString = versionMatches.group(0)
                    versionNumber, releaseNumber = re.findall(r'\d+', versionString)
                    # Check if we have a stig with a smiliar name
                    similarStig = None
                    currentSimilarity = 0.0
                    for stig in existingStigs:
                        similarity = SequenceMatcher(None, stig['name'], name).ratio()
                        if similarity > 0.85 and similarity > currentSimilarity:
                            currentSimilarity = similarity
                            similarStig = stig
                    if similarStig is not None:
                        stigs.append({
                            'id': similarStig['id'],
                            'name': name,
                            'version': int(versionNumber),
                            'release': int(releaseNumber),
                            'size': size,
                            'url': href
                        })
                    else:
                        stigs.append({
                            'id': str(uuid.uuid4()),
                            'name': name,
                            'href': href,
                            'size': size,
                            'version': int(versionNumber),
                            'release': int(releaseNumber)
                        })
                else:
                    print(f"Could not find version in {filename}")
    except:
        print("Error parsing row: ")

with open('stigs.json', 'w') as outfile:
    json.dump(stigs, outfile, indent=2)