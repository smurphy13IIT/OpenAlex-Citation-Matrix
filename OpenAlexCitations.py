import json
import requests
from dictionaries import journal_counts, journal_titles, pub_year_ranges, journals_master
from functions import fetch_all_articles, cited_by_per_decade, references_per_decade

##        - Use Pandas to populate csv files with the data in the journals_master dicitonary

# Set the base URL for OpenAlex API
base_url = "https://api.openalex.org/"

# Set the endpoint for a specific entity (e.g., works, authors, concepts, venues, institutions)
# This example fetches works by a specific author ID
endpoint = "works"

cited_by_dict = {}

# Collect "cited by" data - the number of journals that have cited one of a list of journals in a given timeframe
for i in journals_master:
    source = i['oaid']
    print("Gathering Citation Matrix data for " + i['title'] + "\n")

    for key, value in pub_year_ranges.items():
        works_url = f"{base_url}{endpoint}?filter=publication_year:{value},primary_location.source.id:{source}&per_page=100&mailto=smurphy13@iit.edu"
        response = requests.get(works_url)

        if response.status_code == 200:
            all_articles = fetch_all_articles(works_url)
            print(f"{len(all_articles)} total articles published during the {key}")

            print(f"Gathering citation data for {i["title"]} during the {key}")
            citation_counts = journal_counts.copy()
            cited_per_decade = cited_by_per_decade(all_articles, value, citation_counts, journal_titles)
            i['cited_by'][key] = cited_per_decade

            print(f"Gathering reference data for {i["title"]} during the {key}")
            reference_counts = journal_counts.copy()
            references_list = references_per_decade(all_articles, value, reference_counts, journal_titles)
            i['references'][key] = references_list

        else:
            print(f"Error: {response.status_code}")

    journal_path = str(i['title']) + ".json"

    with open(journal_path, 'w') as journal_file:
        json.dump(i, journal_file, indent=4)


file_path = "master_citation_data.json"

with open(file_path, 'w') as json_file:
    json.dump(journals_master, json_file, indent=4)

