import pandas as pd
import string

## Function to convert a JSON file that is structured as a list of regular dictionary objects to a CSV file where the
## dictionary keys become the columns
def json_to_csv(json_data, csv_filename):
    data = []
    columns = []
    for key, value in json_data[0].items():
        columns.append(key)

    data.append(columns)

    for i in json_data:
        item_data = []

        for key, value in i.items():
            item_data.append(value)

        data.append(item_data)

    # Create a DataFrame
    df = pd.DataFrame(data[1:], columns=data[0])

    # Write the DataFrame to a CSV file
    df.to_csv(f"{csv_filename}.csv", index=False)

    print(f"CSV file {csv_filename}.csv created successfully!")

def scrub(text):
    translation_table = str.maketrans('', '', string.punctuation)
    cleaned_text = text.translate(translation_table).lower()
    cleaned_text = ''.join(char for char in cleaned_text if ord(char) < 128)
    return cleaned_text