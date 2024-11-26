from itertools import chain
import string
from datetime import datetime
import os
import pandas as pd
from pyalex import config, Works
from dictionaries import journal_oaids, timeframe, citation_data_template
from functions import json_to_csv, scrub

config.email = "smurphy13@iit.edu"
config.max_retries = 0
config.retry_backoff_factor = 0.5
config.retry_http_codes = [429, 500, 503]

filesize_threshold = 100000000
csv_file_counter = 1

keys_to_check = ['source_journal', 'work_title', 'primary_author', 'pub_year', 'volume']

journal_list = []
for key, value in journal_oaids.items():
    journal_list.append(value)

journal_search_query = "|".join(journal_list)

for journal_title, journal_oaid in journal_oaids.items():
    print(f"Gathering citation data for {journal_title}")
    article_counter = 0

    article_csv_filename = rf"{journal_title}-nineties-to-present-duplicates_removed"
    citing_csv_filename = f"{journal_title}-citing_articles-all_types_all_sources - File {csv_file_counter}"

    all_cited_by_list = []
    all_cited_by_list.append(citation_data_template)
    json_to_csv(all_cited_by_list, citing_csv_filename)

    articles_csv = pd.read_csv(article_csv_filename + ".csv", dtype=str, low_memory=False)

    for j, row in articles_csv.iterrows():
        if os.path.exists(citing_csv_filename + ".csv") and os.path.getsize(citing_csv_filename + ".csv") >= filesize_threshold:
            csv_file_counter += 1
            citing_csv_filename = f"{journal_title}-citing_articles-all_types - File {csv_file_counter}"
            all_cited_by_list = []
            all_cited_by_list.append(citation_data_template)
            json_to_csv(all_cited_by_list, citing_csv_filename)
            print(citing_csv_filename)

        citations_csv = pd.read_csv(citing_csv_filename + ".csv", dtype=str, low_memory=False)
        article_counter += 1
        if article_counter % 100 == 0:
            print(f"Proccessed citations for {str(article_counter)} {journal_title} articles")

        unique_citation_list = []

        duplicate_works = str(row['merged_from_duplicate']).split(", ")

        if duplicate_works[0] != "nan":
            citation_search_query = f"{row['work_oaid']}|{"|".join(duplicate_works)}"

        else:
            citation_search_query = row['work_oaid']

        existing_cites_results = chain(*Works().filter(cites=citation_search_query,
                                                       publication_year=timeframe['recent_history']
                                                       ).paginate(per_page=200, n_max=None))

        for record in existing_cites_results:
            match = False
            print(record['id'])
            citation_data = citation_data_template.copy()

            citation_data['cites_article_in'] = journal_title
            citation_data['cites_article'] = row['work_oaid']

            try:
                citation_data['source_type'] = record['primary_location']['source']['type']

            except:
                citation_data['source_type'] = ''

            try:
                citation_data['source_journal'] = record['primary_location']['source']['display_name']

            except:
                citation_data['source_journal'] = ''

            citation_data['work_title'] = record['title']

            if record.get('authorships', {}):
                citation_data['primary_author'] = record['authorships'][0]['author']['display_name']

            citation_data['work_oaid'] = record['ids']['openalex']

            if record.get('ids', {}).get('doi'):
                citation_data['DOI'] = record['ids']['doi']

            citation_data['pub_year'] = record['publication_year']
            citation_data['pub_date'] = record['publication_date']

            if record.get('biblio', {}).get('volume'):
                citation_data['volume'] = record['biblio']['volume']

            citation_data['work_type'] = record['type']

            if len(unique_citation_list) >= 1:
                for existing_citation in unique_citation_list:

                    if citation_data['work_type'] == 'article':
                        metadata_match_count = sum(1 for key in keys_to_check if
                                                   scrub(str(existing_citation.get(key))) == scrub(str(citation_data.get(key))))

                        existing_pub_date = datetime.strptime(existing_citation['pub_date'], "%Y-%m-%d")
                        article_pub_date = datetime.strptime(citation_data['pub_date'], "%Y-%m-%d")

                        if metadata_match_count == 4 and abs((existing_pub_date - article_pub_date).days) <= 62:
                            metadata_match_count += 1

                            if metadata_match_count == 5:
                                match = True

                    else:
                        new_keys = keys_to_check.copy()
                        new_keys.remove('volume')
                        new_keys.remove('source_journal')

                        metadata_match_count = sum(1 for key in new_keys if
                                                   scrub(str(existing_citation.get(key))) == scrub(str(citation_data.get(key))))

                        existing_pub_date = datetime.strptime(existing_citation['pub_date'], "%Y-%m-%d")
                        article_pub_date = datetime.strptime(citation_data['pub_date'], "%Y-%m-%d")

                        if metadata_match_count == 2 and abs((existing_pub_date - article_pub_date).days) <= 62:
                            metadata_match_count += 1

                            if metadata_match_count == 3:
                                match = True

                if match == False:
                    unique_citation_list.append(citation_data)

            else:
                unique_citation_list.append(citation_data)

        citations_df = pd.DataFrame(unique_citation_list)

        citations_update = pd.concat([citations_csv, citations_df], ignore_index=True)
        citations_update.to_csv(citing_csv_filename + ".csv", index=False)