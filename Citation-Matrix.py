from itertools import chain
from datetime import datetime
from pyalex import config, Works
import crossref.restful as crossref
import pandas as pd
import os
import string
import html
from dictionaries import journal_oaids, timeframe, article_data_template, citation_data_template, reference_data_template
from functions import json_to_csv, scrub

## PyAlex Configuration Settings
config.email = "smurphy13@iit.edu"
config.max_retries = 5
config.retry_backoff_factor = 0.5
config.retry_http_codes = [429, 500, 503]

## Initialize Crossref Library
crossref_work = crossref.Works()

## Set up CSV filesize handling
filesize_threshold = 100000000
csv_file_counter = 1

## Metadata fields to check for de-duplification process
keys_to_check = ['source_journal', 'work_title', 'author_id', 'volume']
new_year_months = [1, 12]

## Define allowed string characters
allowed_chars = string.printable

## Loop to create CSV files of unique articles published in each journal
for journal_name, journal_oaid in journal_oaids.items():
    articles = []
    print(f"Gathering articles published in {journal_name}...")
    results = chain(*Works().filter(primary_location={"source": {"id": journal_oaid}},
                             publication_year=timeframe['recent_history'],
                             type="article").paginate(per_page=200, n_max=None))

    print("API Call Successful")
    for record in results:
        match = False
        if record['title'] == journal_name:
            continue

        article_data = article_data_template.copy()
        article_data['source_journal'] = record['primary_location']['source']['display_name']
        record_html_stripped = html.unescape(record.get('title') or '')
        record_title_cleaned = ''.join(c for c in record_html_stripped if c in allowed_chars)
        record_title_remove_semicolons = record_title_cleaned.replace(';', '')
        article_data['work_title'] = record_title_remove_semicolons
        article_data['work_oaid'] = record['ids']['openalex']

        if record['authorships']:
            article_data['primary_author'] = record['authorships'][0]['author']['display_name']
            article_data['author_id'] = record['authorships'][0]['author']['id']

        article_data['volume'] = record['biblio']['volume']
        article_data['issue'] = record['biblio']['issue']

        if not record.get('ids',{}).get('doi'):
            continue

            article_data['DOI'] = record['ids']['doi']
        article_data['pub_year'] = record['publication_year']
        article_data['pub_date'] = record['publication_date']
        article_data['work_type'] = record['type']

        try:
            article_data['unique_reference_count'] = crossref_work.doi(record['ids']['doi'])['reference-count']
            article_data['reference_count_source'] = 'crossref'

        except:
            article_data['unique_reference_count'] = record['referenced_works_count']
            article_data['reference_count_source'] = 'openalex'

        article_data['all_cited_by_count'] = record['cited_by_count']
        article_data['duplicate_count'] = 0

        if len(articles) >= 1:
            for existing_article in articles:
                metadata_match_count = sum(1 for key in keys_to_check if scrub(str(existing_article.get(key))) == scrub(str(article_data.get(key))))

                existing_pub_date = datetime.strptime(existing_article['pub_date'], "%Y-%m-%d")
                article_pub_date = datetime.strptime(article_data['pub_date'], "%Y-%m-%d")

                if metadata_match_count == len(keys_to_check) and existing_pub_date.year == article_pub_date.year:
                    metadata_match_count += 1

                elif metadata_match_count == len(keys_to_check) and abs((existing_pub_date - article_pub_date).days) <= 62:
                    metadata_match_count += 1

                final_match_count = metadata_match_count

                if final_match_count == (len(keys_to_check) + 1):
                    match = True
                    print("Matching article found: " + existing_article['work_oaid'])

                    if existing_article['duplicate_count'] >= 1:
                        existing_article['merged_from_duplicate'] += f", {article_data['work_oaid']}"

                    elif existing_article['duplicate_count'] == 0:
                        existing_article['merged_from_duplicate'] = article_data['work_oaid']

                    existing_article['duplicate_count'] += 1

                    ## Combine the reference counts for the duplicate articles
                    duplicate_list_oaids = [existing_article['work_oaid']]
                    for oaid in existing_article['merged_from_duplicate'].split(', '):
                        duplicate_list_oaids.append(oaid)
                    duplicate_list_oaids.append(article_data['work_oaid'])

                    duplicate_dois_list = []
                    for duplicate in duplicate_list_oaids:
                        duplicate_dois_list.append(Works()[duplicate]['ids']['doi'])

                    crossref_dup_data = []
                    for dup_doi in duplicate_dois_list:
                        try:
                            crossref_metadata = crossref_work.doi(dup_doi)
                            crossref_ref_count = crossref_metadata['reference-count']
                            crossref_deposit_date_list = crossref_metadata['deposited']['date-parts'][0]
                            crossref_deposit_date_string = f"{crossref_deposit_date_list[0]}-{crossref_deposit_date_list[1]}-{crossref_deposit_date_list[2]}"
                            crossref_deposit_date = datetime.strptime(crossref_deposit_date_string, "%Y-%m-%d")
                            crossref_dict = {
                                "doi": dup_doi,
                                "ref_count": crossref_ref_count,
                                "deposit_date": crossref_deposit_date
                            }
                            crossref_dup_data.append(crossref_dict)

                        except:
                            continue

                    unique_ref_values = set()

                    unique_ref_count = []

                    for d in crossref_dup_data:
                        value = d.get('ref_count')
                        if value not in unique_ref_values:
                            unique_ref_count.append(d)
                            unique_ref_values.add(value)

                    if len(unique_ref_count) == 1:
                        existing_article['unique_reference_count'] = unique_ref_count[0]['ref_count']

                    elif len(unique_ref_count) > 1:
                        temp_ref_list = []

                        for count in unique_ref_count:
                            count_value = count['ref_count']

                            if count_value > 0:
                                temp_ref_list.append(count)

                                if len(temp_ref_list) == 1:
                                    existing_article['unique_reference_count'] = temp_ref_list[0]["ref_count"]

                                elif len(temp_ref_list) == 0:
                                    existing_article['unique_reference_count'] = "no data"

                                elif len(temp_ref_list) > 1:
                                    date_key = "deposit_date"
                                    max_dict = max(temp_ref_list, key=lambda e: e[date_key])
                                    existing_article['unique_reference_count'] = max_dict["ref_count"]


            if match == False:
                articles.append(article_data)

        else:
            articles.append(article_data)


    print(f"Total articles published in {journal_name} during this period: {len(articles)}")
    csv_filename = f"{journal_name}-articles-nineties-to-present-duplicates_removed"

    json_to_csv(articles, csv_filename)
    print("\n")

## Code to retrieve lists of citations for each article in each journal
journal_list = []
for key, value in journal_oaids.items():
    journal_list.append(value)

journal_search_query = "|".join(journal_list)

for journal_title, journal_oaid in journal_oaids.items():
    print(f"Gathering citation data for {journal_title}")
    article_counter = 0

    article_csv_filename = rf"{journal_title}-articles-nineties-to-present-duplicates_removed"
    citing_csv_filename = f"{journal_title}-citing_articles-all_types - File {csv_file_counter}"

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
            citation_search_query = f"{row['work_oaid']}|{'|'.join(duplicate_works)}"

        else:
            citation_search_query = row['work_oaid']

        existing_cites_results = chain(*Works().filter(cites=citation_search_query,
                                                       publication_year=timeframe['recent_history'],
                                                       primary_location={"source": {"id": journal_search_query}}
                                                       ).paginate(per_page=200, n_max=None))

        for record in existing_cites_results:
            match = False
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

            citation_html_stripped = html.unescape(record.get('title') or '')
            citation_title_cleaned = ''.join(c for c in citation_html_stripped if c in allowed_chars)
            citation_title_remove_semicolons = citation_title_cleaned.replace(';', '')
            citation_data['work_title'] = citation_title_remove_semicolons

            if record.get('authorships', {}):
                citation_data['primary_author'] = record['authorships'][0]['author']['display_name']
                citation_data['author_id'] = record['authorships'][0]['author']['id']

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

                        if metadata_match_count == len(keys_to_check) and existing_pub_date.year == article_pub_date.year:
                            metadata_match_count += 1

                        elif metadata_match_count == len(keys_to_check) and abs((existing_pub_date - article_pub_date).days) <= 62:
                            metadata_match_count += 1

                        final_match_count = metadata_match_count

                        if final_match_count == (len(keys_to_check) + 1):
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
        citations_update.to_csv(citing_csv_filename + ".csv", index=False, sep=',', quotechar='"')
    csv_file_counter = 1

## Code to retrieve lists of references for each article in each journal
journal_list = []
for key, value in journal_oaids.items():
    journal_list.append(value)

journal_search_query = "|".join(journal_list)

for journal_title, journal_oaid in journal_oaids.items():
    print(f"Gathering reference data for {journal_title}")
    article_counter = 0

    ## Lists of articles per journal were manually cleaned to exclude non-peer-reviewed documents
    ## The resulting files were appended with the suffix "articles-nineties-to-present-cleaned"
    article_csv_filename = rf"{journal_title}-articles-nineties-to-present-cleaned"
    reference_csv_filename = f"{journal_title}-references - File {csv_file_counter}"

    all_reference_list = []
    all_reference_list.append(reference_data_template)
    json_to_csv(all_reference_list, reference_csv_filename)

    articles_csv = pd.read_csv(article_csv_filename + ".csv", dtype=str, low_memory=False)

    for j, row in articles_csv.iterrows():
        print(row['work_oaid'])
        if os.path.exists(reference_csv_filename + ".csv") and os.path.getsize(reference_csv_filename + ".csv") >= filesize_threshold:
            csv_file_counter += 1
            reference_csv_filename = f"{journal_title}-references - File {csv_file_counter}"
            all_reference_list = []
            all_reference_list.append(reference_data_template_data_template)
            json_to_csv(all_reference_list, reference_csv_filename_csv_filename)
            print(reference_csv_filename)

        if os.path.exists(reference_csv_filename + " - BACKUP.csv"):
            ref_df = pd.read_csv(reference_csv_filename + " - BACKUP.csv", dtype=str, low_memory=False)
            if row['work_oaid'] in ref_df['referencing_article'].values:
                continue

        reference_csv = pd.read_csv(reference_csv_filename + ".csv", dtype=str, low_memory=False)
        article_counter += 1
        if article_counter % 100 == 0:
            print(f"Proccessed references for {str(article_counter)} {journal_title} articles")

        print(f"Retrieving references for article '{row['work_title']}', {row['work_oaid']}")

        unique_reference_list = []

        duplicate_articles_list = [row['work_oaid']]

        duplicate_works = str(row['merged_from_duplicate']).split(", ")

        if duplicate_works[0] != "nan":
            duplicate_articles_list.extend(duplicate_works)


        all_references = []

        for article in duplicate_articles_list:

            try:
                article_result = Works()[article]
                article_references = article_result['referenced_works']

            except:
                continue

            for item in article_references:
                if item not in all_references:
                    all_references.append(item)

        for reference in all_references:

            match = False

            try:
                record = Works()[reference]

            except:
                continue

            reference_data = reference_data_template.copy()

            reference_data['referencing_article'] = row['work_oaid']

            try:
                reference_data['source_type'] = record['primary_location']['source']['type']

            except:
                reference_data['source_type'] = ''

            try:
                reference_data['source_journal'] = record['primary_location']['source']['display_name']

            except:
                reference_data['source_journal'] = ''

            reference_html_stripped = html.unescape(record.get('title') or '')
            reference_title_cleaned = ''.join(c for c in reference_html_stripped if c in allowed_chars)
            reference_title_remove_semicolons = reference_title_cleaned.replace(';', '')
            reference_data['work_title'] = reference_title_remove_semicolons

            if record.get('authorships', {}):
                reference_data['primary_author'] = record['authorships'][0]['author']['display_name']
                reference_data['author_id'] = record['authorships'][0]['author']['id']

            reference_data['work_oaid'] = record['ids']['openalex']

            if record.get('ids', {}).get('doi'):
                reference_data['DOI'] = record['ids']['doi']

            reference_data['pub_year'] = record['publication_year']
            reference_data['pub_date'] = record['publication_date']

            if record.get('biblio', {}).get('volume'):
                reference_data['volume'] = record['biblio']['volume']

            reference_data['work_type'] = record['type']

            if len(unique_reference_list) >= 1:
                for existing_reference in unique_reference_list:

                    if reference_data['work_type'] == 'article':
                        metadata_match_count = sum(1 for key in keys_to_check if
                                                   scrub(str(existing_reference.get(key))) == scrub(str(reference_data.get(key))))

                        existing_pub_date = datetime.strptime(existing_reference['pub_date'], "%Y-%m-%d")
                        article_pub_date = datetime.strptime(reference_data['pub_date'], "%Y-%m-%d")

                        if metadata_match_count == len(keys_to_check) and existing_pub_date.year == article_pub_date.year:
                            metadata_match_count += 1

                        elif metadata_match_count == len(keys_to_check) and abs((existing_pub_date - article_pub_date).days) <= 62:
                            metadata_match_count += 1

                        final_match_count = metadata_match_count

                        if final_match_count == (len(keys_to_check) + 1):
                            match = True

                    else:
                        new_keys = keys_to_check.copy()
                        new_keys.remove('volume')
                        new_keys.remove('source_journal')

                        metadata_match_count = sum(1 for key in new_keys if
                                                   scrub(str(existing_reference.get(key))) == scrub(str(reference_data.get(key))))

                        existing_pub_date = datetime.strptime(existing_reference['pub_date'], "%Y-%m-%d")
                        article_pub_date = datetime.strptime(reference_data['pub_date'], "%Y-%m-%d")

                        if metadata_match_count == 2 and abs((existing_pub_date - article_pub_date).days) <= 62:
                            metadata_match_count += 1

                            if metadata_match_count == 3:
                                match = True

                if match == False:
                    unique_reference_list.append(reference_data)

            else:
                unique_reference_list.append(reference_data)

        reference_df = pd.DataFrame(unique_reference_list)

        reference_update = pd.concat([reference_csv, reference_df], ignore_index=True)
        reference_update.to_csv(reference_csv_filename + ".csv", index=False, sep=',', quotechar='"')
    csv_file_counter = 1
