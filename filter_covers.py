import os
import pickle


with open('ens_knn.pkl', 'rb') as file:
    data, _ = pickle.load(file)

directory = "filtered_covers"
ids = data._itemid_to_index.keys()

for filename in os.listdir(directory):
    id = int(filename[:-4])
    path = os.path.join(directory, filename)

    if id not in ids:
        print("Removed", filename)
        os.remove(path)
        
    


