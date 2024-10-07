from dictionaries import journal_IDs
import pandas as pd

Eighties = {'https://openalex.org/S142990027': 71, 'https://openalex.org/S119950638': 19, 'https://openalex.org/S145429826': 1, 'https://openalex.org/S163534328': 3, 'https://openalex.org/S163545350': 0, 'https://openalex.org/S92522684': 43, 'https://openalex.org/S11810700': 30, 'https://openalex.org/S102896891': 0, 'https://openalex.org/S89389284': 52, 'https://openalex.org/S159120381': 0, 'https://openalex.org/S31748134': 312}
Nineties = {'https://openalex.org/S142990027': 85, 'https://openalex.org/S119950638': 22, 'https://openalex.org/S145429826': 1, 'https://openalex.org/S163534328': 7, 'https://openalex.org/S163545350': 0, 'https://openalex.org/S92522684': 66, 'https://openalex.org/S11810700': 41, 'https://openalex.org/S102896891': 3, 'https://openalex.org/S89389284': 101, 'https://openalex.org/S159120381': 3, 'https://openalex.org/S31748134': 662}
Aughts = {'https://openalex.org/S142990027': 124, 'https://openalex.org/S119950638': 25, 'https://openalex.org/S145429826': 1, 'https://openalex.org/S163534328': 12, 'https://openalex.org/S163545350': 0, 'https://openalex.org/S92522684': 133, 'https://openalex.org/S11810700': 65, 'https://openalex.org/S102896891': 17, 'https://openalex.org/S89389284': 275, 'https://openalex.org/S159120381': 21, 'https://openalex.org/S31748134': 2494}
Teens = {'https://openalex.org/S142990027': 187, 'https://openalex.org/S119950638': 33, 'https://openalex.org/S145429826': 5, 'https://openalex.org/S163534328': 12, 'https://openalex.org/S163545350': 0, 'https://openalex.org/S92522684': 312, 'https://openalex.org/S11810700': 87, 'https://openalex.org/S102896891': 128, 'https://openalex.org/S89389284': 498, 'https://openalex.org/S159120381': 30, 'https://openalex.org/S31748134': 12097}

decades = [Eighties, Nineties, Aughts, Teens]

def journal_title_replace(decade_dict, journal_titles):
    decade = {}
    for key, value in decade_dict.items():
        if key in journal_titles.values():
            for key2, value2 in journal_titles.items():
                if value2 == key:
                    decade[key2] = value
    return decade

decade = journal_title_replace(Eighties, journal_IDs)
def create_csv_from_dict(my_dict, csv_name):
    df = pd.DataFrame(list(my_dict.items()), columns=['Journal Title', 'Citations'])

    csv_file = csv_name + ".csv"

    df.to_csv(csv_file, index=False)

    print(f"Citation data recorded to {csv_file}")

create_csv_from_dict(decade, "IMM_cited_by_80s")


journal_IDs = {
    "Journal of Marketing"                           : "https://openalex.org/S142990027",
    "Journal of Marketing Research"                  : "https://openalex.org/S119950638",
    "Journal of Consumer Research"                   : "https://openalex.org/S145429826",
    "Marketing Science"                              : "https://openalex.org/S163534328",
    "Journal of Consumer Psychology"                 : "https://openalex.org/S163545350",
    "Journal of the Academy of Marketing Science"    : "https://openalex.org/S92522684",
    "International Journal of Research in Marketing" : "https://openalex.org/S11810700",
    "Psychology and Marketing"                       : "https://openalex.org/S102896891",
    "European Journal of Marketing"                  : "https://openalex.org/S89389284",
    "Journal of Retailing"                           : "https://openalex.org/S159120381",
    "Industrial Marketing Management"                : "https://openalex.org/S31748134",
}
reversed_dict = {value: key for key, value in journal_IDs.items()}