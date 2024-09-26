import requests
import math


def fetch_all_articles(url):
    page_num = 1
    all_results = []

    while True:
        # Perform the GET request
        response = requests.get(url + "&page=" + str(page_num))

        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            all_results.extend(data['results'])  # Add current page's results to list

            # Check if there are more pages
            current_page = data['meta']['page']
            total_pages = math.ceil(data['meta']['count'] / 100)

            if current_page < total_pages:
                page_num += 1  # Move to the next page
                print("Fetching page " + str(page_num))

            else:
                break  # Stop if all pages are fetched
        else:
            print(f"Error: {response.status_code}")
            break

    return all_results

def cited_by_per_decade(base_url, endpoint, pub_year, source_id, journal_counts, journal_titles):

    # Perform the initial GET request to retrieve 100 articles published in the given journal in a given year
    works_url = f"{base_url}{endpoint}?filter=publication_year:{pub_year},primary_location.source.id:{source_id}&per_page=100&mailto=smurphy13@iit.edu"

    response = requests.get(works_url)

    # Check if the request was successful
    if response.status_code == 200:
        all_articles = fetch_all_articles(works_url)

        print(str(len(all_articles)) + " total articles published in this time frame")

        cited_by = []

        for i in all_articles:
            cited_by.append(i['cited_by_api_url'])

        all_cited_by = []

        citation_counter = 0

        for j in cited_by:
            all_cited_by.extend(fetch_all_articles(j + ",publication_year:" + pub_year + "&per_page=100&mailto=smurphy13@iit.edu"))
            citation_counter += len(all_cited_by)
            if citation_counter % 50 == 0:
                print("Added " + str(citation_counter) + " citations to the master citations list...")

        print(str(len(all_cited_by)) + " articles cited this journal in this time frame\n"
                                       "Searching for citations from journals in the list.")

        for k in all_cited_by:
            try:
                article_source = k['primary_location']['source']['id']

                if article_source in journal_titles:
                    print("Citation " + str(article_source) + " matched to journal, adding to list")
                    journal = journal_titles[article_source]
                    journal_counts[journal] += 1

            except:
                pass

        return journal_counts


    else:
        print(f"Error: {response.status_code}")

def references_per_decade(base_url, endpoint, pub_year, source_id, journal_counts, journal_titles):

    # Perform the initial GET request to retrieve 100 articles published in the given journal in a given year
    works_url = f"{base_url}{endpoint}?filter=publication_year:{pub_year},primary_location.source.id:{source_id}&per_page=100&mailto=smurphy13@iit.edu"

    response = requests.get(works_url)

    # Check if the request was successful
    if response.status_code == 200:
        all_articles = fetch_all_articles(works_url)

        print(str(len(all_articles)) + " total articles published in this time frame.\n"
                                       "Searching for references in the journals list.")

        references = []

        for i in all_articles:
            for j in i['referenced_works']:
                j_api = j[:8] + 'api.' + j[8:]
                references.append(j_api)

        print(str(len(references)) + " total articles referenced in this time frame")

        reference_count = 0

        for k in references:
            ref_response = requests.get(k)

            if ref_response.status_code == 200:

                reference_data = ref_response.json()

                try:
                    reference_source = reference_data['primary_location']['source']['id']

                    if reference_source in journal_titles:
                        journal = journal_titles[reference_source]
                        reference_count += 1
                        journal_counts[journal] += 1
                        if reference_count % 10 == 0:
                            print("Added " + str(reference_count) + " references to the master citations list...")

                except:
                    pass

        return journal_counts


    else:
        print(f"Error: {response.status_code}")

# def journal_title_replace(decade_dict, journal_titles):
#     decade = {}
#     for key, value in decade_dict.items():
#         if key in journal_titles:
#             for key2, value2 in journal_titles.items():
#                 if key2 == key:
#                     decade[value2] = key
#     return decade

# def create_csv_from_dict(my_dict, source, decade, csv_name):
#     df = pd.DataFrame({
#         'Cited Journal': source,
#         'Decade': decade,
#         'Citing Journal': my_dict.keys(),
#         'Citations': my_dict.values()
#     })
#     csv_file = "/cited_by/" + csv_name + ".csv"
#
#     df.to_csv(csv_file, index=False)
#
#     print(f"Citation data recorded to {csv_file}")