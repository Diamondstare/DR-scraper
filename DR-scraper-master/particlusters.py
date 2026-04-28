import numpy as np
import pandas as pd

data = pd.read_csv("output.csv")

def data_cleaning(input_list):
    return len(input_list) == 25 and not "0" in input_list
    
data_list = []
navne_list = []
for index, rows in data["answers"].items():
    if pd.isna(rows):
        pass
    else:
        split_row = rows.split()
        if data_cleaning(split_row):
            data_list.append([int(i) for i in split_row])
            navne_list.append(index)
            
cleaned_data = np.array(data_list)

# Extract required columns and include only the rows that were cleaned
required_data = data.loc[navne_list, ["first_name", "last_name", "party_code"]].copy()
required_data["id"] = navne_list
print(required_data.head())




from sklearn.cluster import MiniBatchKMeans
import numpy as np
import pandas as pd 
import matplotlib

X = cleaned_data

print("Shape:", X.shape)  
print("Første række:", X[0])

n_clusters = 7  # Juster efter behov
kmeans = MiniBatchKMeans(n_clusters=n_clusters, random_state=42)
print(kmeans.fit_predict(X))

# Assign clusters to the original data
required_data["cluster"] = kmeans.fit_predict(X)
print(required_data[["first_name", "last_name", "party_code", "cluster"]].head())

# Create a plot of party_code vs clusters
import matplotlib.pyplot as plt
import seaborn as sns

# Define colors for each party_code
party_colors = {
    "A": "#FF0000",  # rød
    "F": "#FFC0CB",  # pink
    "V": "#00008B",  # mørk blå
    "I": "#008080",  # teal
    "O": "#FFA500",  # orange
    "M": "#800080",  # mørk lilla
    "C": "#008000",  # grøn
    "Ø": "#8B0000",  # darkred
    "B": "#DDA0DD",  # lys lilla
    "Æ": "#ADD8E6",  # lys blå
    "Å": "#90EE90",  # lightgreen
    "H": "#000000",  # black
    "": "#A52A2A"   # brown
}

# Group data by party_code and cluster
party_cluster_counts = required_data.groupby(['party_code', 'cluster']).size().unstack(fill_value=0)

# Plot 1: Count of clusters within each party
plt.figure(figsize=(14, 8))
ax = party_cluster_counts.plot(
    kind='bar',
    stacked=False,
    figsize=(14, 8)
)

# Customize the plot
plt.title('Count of Clusters Within Each Party', fontsize=14, pad=20)
plt.xlabel('Party Code', fontsize=12)
plt.ylabel('Count', fontsize=12)
plt.xticks(rotation=45, ha='right')

# Assign colors to party codes
for i, party in enumerate(party_cluster_counts.index):
    ax.get_xticklabels()[i].set_color(party_colors.get(party, 'gray'))

plt.legend(title='Cluster', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.show()

# Plot 2: Normalized distribution of clusters within each party
plt.figure(figsize=(14, 8))
party_cluster_normalized = party_cluster_counts.div(party_cluster_counts.sum(axis=1), axis=0)

# Plot each party as a separate bar
for cluster in party_cluster_normalized.columns:
    plt.bar(
        party_cluster_normalized.index,
        party_cluster_normalized[cluster],
        label=f'Cluster {cluster}',
        color=sns.color_palette("husl", n_colors=len(party_cluster_normalized.columns))[cluster]
    )

# Customize the plot
plt.title('Normalized Distribution of Clusters Within Each Party', fontsize=14, pad=20)
plt.xlabel('Party Code', fontsize=12)
plt.ylabel('Proportion', fontsize=12)
plt.xticks(rotation=45, ha='right')
plt.legend(title='Cluster', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.show()


# Plot the average response per question for each cluster
def plot_cluster_profiles(X, clusters, n_clusters):
    # Calculate the mean response per question for each cluster
    cluster_profiles = np.array([X[clusters == i].mean(axis=0) for i in range(n_clusters)])

    # Create a line plot
    categories = [f'Q{i+1}' for i in range(X.shape[1])]

    plt.figure(figsize=(14, 8))
    # Define colors and names for each cluster
    cluster_colors = {
        0: ('lys lilla', '#DDA0DD'),
        1: ('orange', '#FFA500'),
        2: ('mørk lilla', '#800080'),
        3: ('lys blå', '#ADD8E6'),
        4: ('mørk blå', '#00008B'),
        5: ('rød', '#FF0000'),
        6: ('grøn', '#008000'),
    }

    cluster_names = {
        0: 'Radikale Centrum Venstre',
        1: 'Nationalistisk Højre',
        2: 'Moderat - Centrum Højre',
        3: 'LA',
        4: 'Centrum Højre',
        5: 'Centrum Venstre',
        6: 'Venstre - Meget Venstre',
    }

    # Plot data for each cluster
    for i, profile in enumerate(cluster_profiles):
        color = cluster_colors.get(i, ('gray', '#808080'))[1]
        name = cluster_names.get(i, f'Cluster {i}')
        plt.scatter(categories, profile, label=name, color=color, s=100)

    # Customize the plot
    plt.title('Average Response per Question for Each Cluster', fontsize=14, pad=20)
    plt.xlabel('Questions', fontsize=12)
    plt.ylabel('Average Response', fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.legend(title='Cluster', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True)
    plt.tight_layout()
    plt.show()

# Fit KMeans and plot cluster profiles
n_clusters = 7  # Juster efter behov
kmeans = MiniBatchKMeans(n_clusters=n_clusters, random_state=42)
clusters = kmeans.fit_predict(X)

# Plot cluster profiles
plot_cluster_profiles(X, clusters, n_clusters)



