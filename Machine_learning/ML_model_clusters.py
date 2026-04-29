from sklearn.cluster import MiniBatchKMeans
import numpy as np
import pandas as pd 
import matplotlib as plt
import importlib 
import sys
from pathlib import Path

path_root = Path(__file__).parents[1]
sys.path.append(str(path_root)) 
from  Data_analysis.visualisering_grafer import particlusters as pc




standartfarve=cluster_colors = {
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
standartnavn=cluster_names = {
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

class cluster_data:
    def __init__(self,n_clusters):
        # loads the cleaned data
        Data = pd.read_csv("Data/Output_renset.csv")
        print(Data["answers"].apply(lambda x: [int(i) for i in x.split()]))
        svar=np.array((Data[["Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7", "Q8", "Q9", "Q10", "Q11", "Q12", "Q13", "Q14", "Q15", "Q16", "Q17", "Q18", "Q19", "Q20", "Q21", "Q22", "Q23", "Q24", "Q25"]]))
        # initalises the modelpa[]
        self.kmeans = MiniBatchKMeans(n_clusters=n_clusters, random_state=42)
        #print(svar)
        print(self.kmeans.fit_predict(svar))
        Data["cluster"] = self.kmeans.fit_predict(svar)
        self.Data_with_labels=Data
        # calculates number 
        #required_data = X.loc[ ["first_name", "last_name", "party_code"]].copy()
        
        #
    def plot(self,type_plot="boxplot",farve=standartfarve,navn=standartnavn):
        if type_plot=="boxplot":
            pc.boxplot(self,farve,navn)
        if type_plot=="lineplot":
            pc.lineplot(self,farve,navn)
    


def elbow_method(max_clusters):

    inertia = []

    for k in range(1, max_clusters + 1):
        cluster=cluster_data(k)
        inertia.append(cluster.kmeans.inertia_)

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
    plt.show()