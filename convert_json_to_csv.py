import pandas as pd
import json

# Data
json_path = "master_citation_data.json"

with open(json_path, 'r') as file:
    journals_master = json.load(file)

# Prepare data for the DataFrame
data = [["Publishing Journal",
         "OAID",
         "ISSN",
         "Citation Type",
         "Citing or Referenced Journal",
         "Thirties",
         "Forties",
         "Fifties",
         "Sixties",
         "Seventies",
         "Eighties",
         "Nineties",
         "Aughts",
         "Teens",
         "Twenties"]
        ]

for journal in journals_master:
    journal_data = []

    for journal_name, counts in journal["cited_by"]["Thirties"].items():

            # Append journal info as a list
            journal_data.append([journal["title"], journal["oaid"], journal["issn"], "cited_by", journal_name])

    for decade, counts_dict in journal["cited_by"].items():

        for journal_name, count in counts_dict.items():

            for i in journal_data:
                print(i)

                if i[4] == journal_name:
                    i.append(count)

    data.extend(journal_data)

# Create a DataFrame
df = pd.DataFrame(data[1:], columns=data[0])

# Write the DataFrame to a CSV file
df.to_csv("journals_data_pandas.csv", index=False)

print("CSV file 'journals_data_pandas.csv' created successfully!")