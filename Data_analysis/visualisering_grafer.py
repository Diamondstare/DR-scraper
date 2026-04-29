import matplotlib.pyplot as plt
import numpy as np
class particlusters:
    
    # Plot 1: Count of clusters within each party
    def lineplot(data,farve,navn):
        party_cluster_counts=data.Data_with_labels.groupby(['party_code', 'cluster']).size().unstack(fill_value=0) 
        plt.figure(figsize=(14, 8))
        ax = party_cluster_counts.plot(
            kind='bar',
            stacked=False,
            figsize=(14, 8),
            color=[farve[i] for i in party_cluster_counts.columns]
        )

        # Customize the plot
        plt.title('Count of Clusters Within Each Party', fontsize=14, pad=20)
        plt.xlabel('Party Code', fontsize=12)
        plt.ylabel('Count', fontsize=12)
        plt.xticks(rotation=45, ha='right')

        # Assign colors to party codes
        for i, party in enumerate(party_cluster_counts.index):
            ax.get_xticklabels()[i].set_color(farve.get(party, 'gray'))

        # Rename legend labels
        handles, labels = ax.get_legend_handles_labels()
        new_labels = [navn.get(int(label), f'Cluster {label}') for label in labels]
        ax.legend(handles, new_labels, title='Cluster', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        plt.show()
    
    def boxplot(data,farve,navn):
        party_cluster_counts=data.Data_with_labels.groupby(['party_code', 'cluster']).size().unstack(fill_value=0) 
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
                label=navn.get(cluster, f'Cluster {cluster}'),
                color=farve.get(cluster, 'gray')
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