import pandas as pd
from dictionaries import journal_oaids


for journal_title, journal_oaid in journal_oaids.items():
    article_csv_filename = rf"{journal_title}-nineties-to-present-duplicates_removed"
    citing_csv_filename = f"{journal_title}-citing_articles-all_types - File 1"

    articles_csv = pd.read_csv(article_csv_filename + ".csv", dtype=str, low_memory=False)

    for j, row in articles_csv.iterrows():
        citations_csv = pd.read_csv(citing_csv_filename + ".csv", dtype=str, low_memory=False)
        unique_citations_counter = 0

        for k, cite_row in citations_csv.iterrows():
            if cite_row['cites_article'] == row['work_oaid']:
                unique_citations_counter += 1

        print(f"{journal_title}: {row['work_oaid']}: {unique_citations_counter} unique citations")

        row['unique_cited_by_count'] = unique_citations_counter
        articles_csv.to_csv(article_csv_filename + ".csv", index=False)


