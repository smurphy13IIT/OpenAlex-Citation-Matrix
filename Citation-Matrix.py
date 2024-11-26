from itertools import chain
from datetime import datetime
from pyalex import config, Works
from dictionaries import journal_oaids, timeframe, article_data_template, citation_data_template
from functions import json_to_csv, scrub

## config.email = "smurphy13@iit.edu"
config.max_retries = 5
config.retry_backoff_factor = 0.5
config.retry_http_codes = [429, 500, 503]

keys_to_check = ['source_journal', 'work_title', 'primary_author', 'pub_year', 'volume', 'issue']
ref_keys_to_check = ['source_journal', 'work_title', 'primary_author', 'pub_year', 'volume', 'issue']

new_year_months = [1, 12]

for journal_name, journal_oaid in journal_oaids.items():
    articles = []
    print(f"Gathering articles published in {journal_name}...")
    results = chain(*Works().filter(primary_location={"source": {"id": journal_oaid}},
                             publication_year=timeframe['recent_history'],
                             type="article",
                             indexed_in="crossref").paginate(per_page=200, n_max=None))

    print("API Call Successful")
    for record in results:
        match = False
        article_data = article_data_template.copy()
        article_data['source_journal'] = record['primary_location']['source']['display_name']
        article_data['work_title'] = record['title']
        article_data['work_oaid'] = record['ids']['openalex']

        if record['authorships']:
            article_data['primary_author'] = record['authorships'][0]['author']['display_name']

        article_data['volume'] = record['biblio']['volume']
        article_data['issue'] = record['biblio']['issue']
        if record['ids']['doi']:
            article_data['DOI'] = record['ids']['doi']

        article_data['pub_year'] = record['publication_year']
        article_data['pub_date'] = record['publication_date']
        article_data['work_type'] = record['type']
        article_data['unique_reference_count'] = record['referenced_works_count']
        article_data['all_cited_by_count'] = record['cited_by_count']
        article_data['duplicate_count'] = 0

        if len(articles) >= 1:
            for existing_article in articles:
                metadata_match_count = sum(1 for key in keys_to_check if scrub(str(existing_article.get(key))) == scrub(str(article_data.get(key))))

                existing_pub_date = datetime.strptime(existing_article['pub_date'], "%Y-%m-%d")
                article_pub_date = datetime.strptime(article_data['pub_date'], "%Y-%m-%d")

                if metadata_match_count == 5 and abs((existing_pub_date - article_pub_date).days) <= 62:
                    metadata_match_count += 1

                if metadata_match_count == 6:
                    match = True
                    print("Matching article found: " + existing_article['work_oaid'])

                    if existing_article['duplicate_count'] >= 1:
                        existing_article['merged_from_duplicate'] += f", {article_data['work_oaid']}"

                    elif existing_article['duplicate_count'] == 0:
                        existing_article['merged_from_duplicate'] = article_data['work_oaid']

                    existing_article['duplicate_count'] += 1

                    ## Combine the reference counts for the duplicate articles
                    existing_refs = Works()[existing_article['work_oaid']]['referenced_works']
                    dup_refs = record['referenced_works']

                    ## Retain only unique references
                    merged_refs = list(set(existing_refs + dup_refs))

                    ## de-duplicate references
                    unique_refs = []

                    for reference in merged_refs:
                        ref_match = False

                        try:
                            reference_metadata = Works()[reference]

                        except:
                            continue

                        reference_data = {}

                        try:
                            reference_data['source_journal'] = reference_metadata['primary_location']['source'][
                                'display_name']

                        except:
                            reference_data['source_journal'] = ''

                        reference_data['work_title'] = reference_metadata['title']

                        if reference_metadata.get('authorships'):
                            reference_data['primary_author'] = reference_metadata['authorships'][0]['author'][
                                'display_name']

                        reference_data['work_oaid'] = reference_metadata['ids']['openalex']

                        if reference_metadata.get('ids', {}).get('doi'):
                            reference_data['DOI'] = reference_metadata['ids']['doi']

                        reference_data['pub_year'] = reference_metadata['publication_year']
                        reference_data['pub_date'] = reference_metadata['publication_date']

                        if reference_metadata.get('biblio', {}).get('volume'):
                            reference_data['volume'] = reference_metadata['biblio']['volume']

                        reference_data['work_type'] = reference_metadata['type']

                        if len(unique_refs) >= 1:
                            for existing_reference in unique_refs:
                                if reference_data['work_type'] == 'article':
                                    ref_metadata_match_count = sum(1 for key in keys_to_check if
                                                               scrub(str(existing_reference.get(key))) == scrub(
                                                                   str(reference_data.get(key))))

                                    existing_ref_pub_date = datetime.strptime(existing_reference['pub_date'], "%Y-%m-%d")
                                    reference_pub_date = datetime.strptime(reference_data['pub_date'], "%Y-%m-%d")

                                    if ref_metadata_match_count == 5 and abs((existing_ref_pub_date - reference_pub_date).days) <= 62:
                                        ref_metadata_match_count += 1

                                    if ref_metadata_match_count == 6:
                                        ref_match = True

                                else:
                                    new_keys = ['work_title', 'primary_author', 'pub_year']

                                    ref_metadata_match_count = sum(1 for key in new_keys if
                                                               scrub(str(existing_reference.get(key))) == scrub(
                                                                   str(reference_data.get(key))))

                                    if ref_metadata_match_count == 3:
                                        ref_match = True

                            if ref_match == False:
                                unique_refs.append(reference_data)

                        else:
                            unique_refs.append(reference_data)

                    existing_article['raw_reference_count'] = len(merged_refs)
                    existing_article['unique_reference_count'] = len(unique_refs)


                    # ## Combine the citation counts for the duplicate articles
                    # existing_work_id = existing_article['work_oaid']
                    # existing_cites_results = chain(*Works().filter(cites=existing_work_id).paginate(per_page=200, n_max=None))
                    # existing_cites = []
                    #
                    # for existing_citation in existing_cites_results:
                    #     existing_cites.append(existing_citation['id'])
                    #
                    # dup_work_id = article_data['work_oaid']
                    # dup_cites_results = chain(*Works().filter(cites=dup_work_id).paginate(per_page=200, n_max=None))
                    # dup_cites = []
                    #
                    # for dup_citation in dup_cites_results:
                    #     dup_cites.append(dup_citation['id'])
                    #
                    # ## Combine the existing and duplicate citation lists, retaining only the unique articles
                    # merged_cites = list(set(existing_cites + dup_cites))
                    # duplicate_citation_output = f"# Existing Articles: {len(existing_cites)} | # Duplicate Articles: {len(dup_cites)} | # Merged Articles: {len(merged_cites)}"
                    # print(f"Duplicate Citation Data: {duplicate_citation_output}\n")
                    # existing_article['all_cited_by_count'] = len(merged_cites)
                    # existing_article['duplicate_citation_data'] = duplicate_citation_output

            if match == False:
                articles.append(article_data)

        else:
            articles.append(article_data)


    print(f"Total articles published in {journal_name} during this period: {len(articles)}")
    csv_filename = f"{journal_name}-nineties-to-present-duplicates_removed"

    json_to_csv(articles, csv_filename)
    print("\n")