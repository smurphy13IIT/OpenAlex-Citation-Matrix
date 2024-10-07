import json
import requests
from dictionaries import journal_counts, journal_titles, pub_year_ranges, journals_master
from functions import fetch_all_articles_cursor, cited_by_per_decade, references_per_decade, json_to_csv

##        - Use Pandas to populate csv files with the data in the journals_master dicitonary

# Set the base URL for OpenAlex API
base_url = "https://api.openalex.org/"

# Set the endpoint for a specific entity (e.g., works, authors, concepts, venues, institutions)
# This example fetches works by a specific author ID
endpoint = "works"
type_limiter = ',type:article'

cited_by_dict = {}

# Collect "cited by" data - the number of journals that have cited one of a list of journals in a given timeframe
for i in journals_master:
    source = i['oaid']
    print("Gathering Citation Matrix data for " + i['title'] + "\n")
    for key, value in pub_year_ranges.items():
        works_url = f"{base_url}{endpoint}?filter=publication_year:{value},primary_location.source.id:{source}{type_limiter}&per_page=100&mailto=smurphy13@iit.edu"
        response = requests.get(works_url)

        if response.status_code == 200:
            all_articles = fetch_all_articles_cursor(works_url)
            print(f"{len(all_articles)} total articles published during the {key}")

            #Export data about all the articles to a CSV file
            article_data = []
            item_data = {
                'source_journal': '',
                'work_title': '',
                'work_oaid': '',
                'DOI': '',
                'pub_year': '',
                'work_type': '',
                'all_cited_by_count': '',
            }

            for j in all_articles:
                temp_item_data = item_data.copy()
                temp_item_data['source_journal'] = j['primary_location']['source']['display_name']
                temp_item_data['work_title'] = j['title']
                temp_item_data['work_oaid'] = j['ids']['openalex']

                try:
                    temp_item_data['DOI'] = j['ids']['doi']

                except:
                    temp_item_data['DOI'] = "None"

                temp_item_data['pub_year'] = j['publication_year']
                temp_item_data['work_type'] = j['type']
                temp_item_data['all_cited_by_count'] = j['cited_by_count']
                article_data.append(temp_item_data)

            csv_filename = f"{i['title']}-{key}-all-articles-articles_only"

            if not article_data:
                article_data = [
                    {
                    'source_journal': 'NONE',
                    'work_title': 'NONE',
                    'work_oaid': 'NONE',
                    'DOI': 'NONE',
                    'pub_year': 'NONE',
                    'work_type': 'NONE',
                    'all_cited_by_count': 'NONE'
                    }
                ]

            json_to_csv(article_data, csv_filename)

            ## Gather citation and reference counts for each journal
            print(f"Gathering citation data for {i["title"]} during the {key}")
            citation_counts = journal_counts.copy()
            all_cited_by, cited_per_decade = cited_by_per_decade(all_articles, value, type_limiter, citation_counts, journal_titles)
            i['cited_by'][key] = cited_per_decade

            all_cited_by_list = []
            cited_by_data_template = {
                'cites_article_in': '',
                'source_journal': '',
                'work_title': '',
                'work_oaid': '',
                'DOI': '',
                'pub_year': '',
                'work_type': '',
            }

            for k in all_cited_by:
                cited_by_item_data = cited_by_data_template.copy()
                cited_by_item_data['cites_article_in'] = i['title']
                cited_by_item_data['source_journal'] = k['primary_location']['source']['display_name']
                cited_by_item_data['work_title'] = k['title']
                cited_by_item_data['work_oaid'] = k['ids']['openalex']

                try:
                    cited_by_item_data['DOI'] = k['ids']['doi']

                except:
                    cited_by_item_data['DOI'] = "None"

                cited_by_item_data['pub_year'] = k['publication_year']
                cited_by_item_data['work_type'] = k['type']
                all_cited_by_list.append(cited_by_item_data)

            citing_csv_filename = f"{i['title']}-{key}-citing_articles-articles_only"

            if not all_cited_by_list:
                all_cited_by_list = [
                    {'cites_article_in': 'NONE',
                     'source_journal': 'NONE',
                     'work_title': 'NONE',
                     'work_oaid': 'NONE',
                     'DOI': 'NONE',
                     'pub_year': 'NONE',
                     'work_type': 'NONE', }
                ]

            json_to_csv(all_cited_by_list, citing_csv_filename)

            # print(f"Gathering reference data for {i["title"]} during the {key}")
            # reference_counts = journal_counts.copy()
            # references_list = references_per_decade(all_articles, value, type_limiter, reference_counts, journal_titles)
            # i['references'][key] = references_list

        else:
            print(f"Error: {response.status_code}")

    journal_path = str(i['title']) + ".json"

    with open(journal_path, 'w') as journal_file:
        json.dump(i, journal_file, indent=4)

file_path = "master_citation_data.json"

with open(file_path, 'w') as json_file:
    json.dump(journals_master, json_file, indent=4)
