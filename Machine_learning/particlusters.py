import numpy as np
import pandas as pd
import ML_model_clusters

data= ML_model_clusters.cluster_data(7)
data.plot(type_plot="lineplot")
data = pd.read_csv("Data/output_renset.csv")






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

# Define colors for clusters
cluster_colors = {
    0: '#DDA0DD',  # lys lilla
    1: '#FFA500',  # orange
    2: '#800080',  # mørk lilla
    3: '#ADD8E6',  # lys blå
    4: '#00008B',  # mørk blå
    5: '#FF0000',  # rød
    6: '#008000',  # grøn
    7: '#006400',  # mørk grøn
    8: '#FFFF00',  # gul
    9: '#A52A2A'   # brun
}

# Define names for clusters
cluster_names = {
    0: 'Radikale Centrum Venstre',
    1: 'Nationalistisk Højre',
    2: 'Moderat - Centrum Højre',
    3: 'LA',
    4: 'Centrum Højre',
    5: 'Centrum Venstre',
    6: 'Venstre - Meget Venstre',
    7: 'Cluster 7',
    8: 'Cluster 8',
    9: 'Cluster 9'
}

# Plot 1: Count of clusters within each party
plt.figure(figsize=(14, 8))
ax = party_cluster_counts.plot(
    kind='bar',
    stacked=False,
    figsize=(14, 8),
    color=[cluster_colors[i] for i in party_cluster_counts.columns]
)

# Customize the plot
plt.title('Count of Clusters Within Each Party', fontsize=14, pad=20)
plt.xlabel('Party Code', fontsize=12)
plt.ylabel('Count', fontsize=12)
plt.xticks(rotation=45, ha='right')

# Assign colors to party codes
for i, party in enumerate(party_cluster_counts.index):
    ax.get_xticklabels()[i].set_color(party_colors.get(party, 'gray'))

# Rename legend labels
handles, labels = ax.get_legend_handles_labels()
new_labels = [cluster_names.get(int(label), f'Cluster {label}') for label in labels]
ax.legend(handles, new_labels, title='Cluster', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.show()
def boxplot(data,farve,navn):

    # Plot 2: Normalized distribution of clusters within each party
    plt.figure(figsize=(14, 8))
    party_cluster_normalized = party_cluster_counts.div(party_cluster_counts.sum(axis=1), axis=0)

    # Plot each cluster as a separate bar
    bottom = np.zeros(len(party_cluster_normalized))
    for cluster in party_cluster_normalized.columns:
        plt.bar(
            party_cluster_normalized.index,
            party_cluster_normalized[cluster],
            bottom=bottom,
            label=cluster_names.get(cluster, f'Cluster {cluster}'),
            color=cluster_colors.get(cluster, 'gray')
        )
        bottom += party_cluster_normalized[cluster]

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
        7: ('mørk grøn', '#006400'),
        8: ('gul', '#FFFF00'),
        9: ('brun', '#A52A2A')
    }

    cluster_names = {
        0: 'Radikale Centrum Venstre',
        1: 'Nationalistisk Højre',
        2: 'Moderat - Centrum Højre',
        3: 'LA',
        4: 'Centrum Højre',
        5: 'Centrum Venstre',
        6: 'Venstre - Meget Venstre',
        7: 'Cluster 7',
        8: 'Cluster 8',
        9: 'Cluster 9'
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

# Calculate inertia for each cluster count
inertia = []
max_clusters = 15

for k in range(1, max_clusters + 1):
    kmeans = MiniBatchKMeans(n_clusters=k, random_state=42)
    kmeans.fit(X)
    inertia.append(kmeans.inertia_)

# Plot inertia
plt.figure(figsize=(10, 6))
plt.plot(range(1, max_clusters + 1), inertia, marker='o', linestyle='--', color='blue')

# Mark the elbow point
elbow_point = 6
plt.axvline(x=elbow_point, color='#FF0000', linestyle='--', label=f'Elbow Point: {elbow_point} clusters')

plt.title('Elbow Method for Optimal Number of Clusters', fontsize=14)
plt.xlabel('Number of Clusters', fontsize=12)
plt.ylabel('Inertia', fontsize=12)
plt.grid(True)
plt.xticks(range(1, max_clusters + 1))
plt.legend()
plt.tight_layout()
#plt.show()

print(f"Anbefalet antal clusters baseret på Elbow-metoden: {elbow_point}")