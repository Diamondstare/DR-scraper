import pandas as pd


df = pd.read_csv("Data/Output.csv", encoding='utf-8')

def data_cleaning(input_list):
    return isinstance(input_list, str) and len(input_list.split()) == 25 and not "0" in input_list.split()


mask = df['answers'].apply(data_cleaning)
df_cleaned = df[mask].copy()




new_columns = df_cleaned['answers'].str.split(expand=True)

# Hvis du vil give kolonnerne navne (f.eks. Spørgsmål 1, 2, 3...)
new_columns.columns = [f'Q{i+1}' for i in range(new_columns.shape[1])]

# Sæt de nye kolonner sammen med dit oprindelige datasæt (hvis du vil beholde navne osv.)
data = pd.concat([df_cleaned, new_columns], axis=1)




data.to_csv("Data/Output_renset.csv", index=False)
