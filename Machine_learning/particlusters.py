import numpy as np
import pandas as pd
import ML_model_clusters

data= ML_model_clusters.cluster_data(7)
data.plot(type_plot="lineplot")
data = pd.read_csv("Data/output_renset.csv")






