import json
import requests
from dictionaries import journal_counts, journal_titles, jom_complete_history, journals_master
from functions import fetch_all_articles_cursor, cited_by_per_decade, references_per_decade


base_url = "https://api.openalex.org/"
endpoint = "works"
time_range = jom_complete_history
source = "https://openalex.org/S142990027"

url = f"{base_url}{endpoint}?filter=publication_year:{time_range},primary_location.source.id:{source}&per_page=100&mailto=smurphy13@iit.edu"

complete_data = journals_master[0].copy()

all_articles = fetch_all_articles_cursor(url)
print("Retrieved " + str(len(all_articles)) + " articles.")

print(f"Gathering citation data")
citation_counts = journal_counts.copy()
cited_per_decade = cited_by_per_decade(all_articles, time_range, citation_counts, journal_titles)
complete_data['cited_by'] = cited_per_decade

print(f"Gathering reference data")
reference_counts = journal_counts.copy()
references_list = references_per_decade(all_articles, time_range, reference_counts, journal_titles)
complete_data['references'] = references_list

journal_path = "complete_jom_citations.json"

with open(journal_path, 'w') as journal_file:
    json.dump(i, journal_file, indent=4)


