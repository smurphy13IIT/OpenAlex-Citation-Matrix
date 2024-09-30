import requests
import math


## This function accepts an OpenAlex API url that should return a JSON of article data.
## The OpenAlex API can return a maximum of 100 results per call.
## It uses the pagination field to make several API calls and combine the results into a list object.

def fetch_all_articles_cursor(url):
    page_num = 1
    all_results = []
    response = requests.get(url + "&cursor=*")

    if response.status_code == 200:
        data = response.json()
        all_results.extend(data['results'])  # Add current page's results to list
        cursor = data['meta']['next_cursor']
        print(data['meta']['count'])

        while cursor != None:
            # Perform the GET request
            loop_response = requests.get(url + "&cursor=" + cursor)

            # Check if the request was successful
            if loop_response.status_code == 200:
                loop_data = loop_response.json()
                all_results.extend(loop_data['results'])  # Add current page's results to list
                page_num += 1
                # Save the new cursor for the next call
                cursor = loop_data['meta']['next_cursor']
                print("Retrieving page " + str(page_num) + " of results")

            else:
                print(f"Error: {response.status_code}")

                break

    return all_results

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

            else:
                break  # Stop if all pages are fetched
        else:
            print(f"Error: {response.status_code}")
            break

    return all_results

## This function's parameters include a list of articles in OpenAlex JSON format, a publication year or range of years,
## a dictionary of counters for a list of journals, and a dictionary of journal titles matched with OpenAlex URLs.
## It determines the number of times the list of articles were cited by the list of provided journals in the given time frame.
def cited_by_per_decade(all_articles, pub_year, journal_counts, journal_titles):

    all_work_ids = [] # Set up an empty list to hold work IDs only

    # scrub the URL prefix from each of the work IDs provided in the article list
    for i in all_articles:
        work_id_url = i["ids"]["openalex"]
        work_id = work_id_url.translate(str.maketrans('', '', "https://openalex.org/"))
        all_work_ids.append(work_id)

    # Combine the work IDs into groups of 50, then add the groups to a list object
    group_size = 50
    chunked_work_ids = ["|".join(all_work_ids[i:i + group_size]) for i in range(0, len(all_work_ids), group_size)]

    all_cited_by = [] # Set up an empty list to contain JSON data for all articles citing those in the provided list

    ## Make a series of API calls that return lists of articles that cited those provided, scoped to the publication date
    ## range and limited to the provided list of journals
    for j in chunked_work_ids:
        search_url_stem = "https://api.openalex.org/works?filter=cites:"
        all_cited_by.extend(fetch_all_articles(search_url_stem + j + ",publication_year:" + pub_year + ",primary_location.source.id:https://openalex.org/S142990027|https://openalex.org/S145429826|https://openalex.org/S119950638|https://openalex.org/S163534328|https://openalex.org/S163545350|https://openalex.org/S92522684|https://openalex.org/S11810700|https://openalex.org/S102896891|https://openalex.org/S89389284|https://openalex.org/S159120381|https://openalex.org/S31748134&per_page=100&mailto=smurphy13@iit.edu"))

    print(f"{len(all_cited_by)} articles cited this journal in this time frame")

    cited_journal_count = 0

    # Sort the list of citing articles by journal as listed in the journal_counts dictionary
    for k in all_cited_by:
        try:
            article_source = k['primary_location']['source']['id']

            if article_source in journal_titles:
                cited_journal_count += 1
                journal = journal_titles[article_source]
                journal_counts[journal] += 1

                if cited_journal_count % 100 == 0:
                    print(f"{cited_journal_count} citations identified from these journals...")

        except:
            pass

    print(f"Added {cited_journal_count} citations to the master citations list")

    return journal_counts

## This function takes a list of articles as its first parameter, as well as a publication year or range of years
## and two dictionaries containing journal data. It searches the list of articles for references and supplies a count
## of the number of times the articles cited other articles in the provided list of journals.
def references_per_decade(all_articles, pub_year, journal_counts, journal_titles):

    references = [] # Create an empty list to hold reference data

    # Collect all the OpenAlex IDs of articles referenced among the list of articles
    for i in all_articles:
        for j in i['referenced_works']:
            references.append(j)

    print(f"{len(references)} total articles referenced in this time frame")

    # Group the reference IDs into sets of 50, then gather the sets into a list object
    group_size = 50
    chunked_references = ["|".join(references[i:i + group_size]) for i in range(0, len(references), group_size)]

    reference_count = 0

    ## For each group of 50 references, make an API call to get a list of references published in the given time frame
    ## and in one of the provided lists of journals
    for k in chunked_references:
        ref_response = requests.get("https://api.openalex.org/works?filter=ids.openalex:" + k + ",publication_year:" + pub_year + ",primary_location.source.id:https://openalex.org/S142990027|https://openalex.org/S145429826|https://openalex.org/S119950638|https://openalex.org/S163534328|https://openalex.org/S163545350|https://openalex.org/S92522684|https://openalex.org/S11810700|https://openalex.org/S102896891|https://openalex.org/S89389284|https://openalex.org/S159120381|https://openalex.org/S31748134&per_page=100&mailto=smurphy13@iit.edu")

        if ref_response.status_code == 200:
            reference_data = ref_response.json()

            # Sort the list of references according to the journals contained in the journals_count dictionary
            for l in reference_data["results"]:

                try:
                    reference_source = l['primary_location']['source']['id']

                    if reference_source in journal_titles:
                        journal = journal_titles[reference_source]
                        reference_count += 1
                        journal_counts[journal] += 1

                        if reference_count % 100 == 0:
                            print(f"{reference_count} references identified for these journals...")

                except:
                    pass

    print(f"{reference_count} total references identified for articles in these journals.")

    return journal_counts