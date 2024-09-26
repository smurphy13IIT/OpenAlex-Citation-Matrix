import json
from dictionaries import journal_counts, journal_titles, pub_year_ranges, journals_master
from functions import cited_by_per_decade, references_per_decade

## TO DO: - Create a function to collect data on references by a given journal's articles per time period
##        - Feed citation data to the journals_master dictionary
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

    for key, value in pub_year_ranges.items():
        print("Gathering citation data for the " + str(key))
        cited_per_decade = cited_by_per_decade(base_url, endpoint, value, source, journal_counts, journal_titles)
        i['cited_by'][key] = cited_per_decade

        references_list = references_per_decade(base_url, endpoint, value, source, journal_counts, journal_titles)
        i['references'][key] = references_list

    journal_path = i['title']

    with open(journal_path, 'w') as journal_file:
        json.dump(i, journal_file, indent=4)


file_path = "master_citation_data.json"

with open(file_path, 'w') as json_file:
    json.dump(journals_master, json_file, indent=4)

