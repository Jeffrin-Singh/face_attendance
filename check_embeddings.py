import pickle

with open("embeddings.pkl", "rb") as f:
    data = pickle.load(f)

print("Embeddings content:")
print(data)
print("\nNumber of registered users:", len(data))
