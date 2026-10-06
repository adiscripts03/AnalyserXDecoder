import numpy as np
from rag_app.embeddings import embeddings


def cosine_similarity(v1, v2) -> float:
    dot_product = np.dot(v1, v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    return float(dot_product / (norm_v1 * norm_v2))


text1 = "IIIT Nagpur is an engineering institute."

text2 = "IIIT Nagpur is a college."
text3 = "I love eating pizza."

vector1 = embeddings.embed_query(text1)
vector2 = embeddings.embed_query(text2)
vector3 = embeddings.embed_query(text3)

print("Vector 1 length:", len(vector1))
print("Vector 2 length:", len(vector2))
print("Vector 3 length:", len(vector3))

sim_1_2 = cosine_similarity(vector1, vector2)
sim_1_3 = cosine_similarity(vector1, vector3)
sim_2_3 = cosine_similarity(vector2, vector3)

print("\n--- Similarity Scores ---")
print(f"Similarity (Text 1 vs Text 2): {sim_1_2:.4f}  (Similar topics: engineering institute vs college)")
print(f"Similarity (Text 1 vs Text 3): {sim_1_3:.4f}  (Dissimilar: institute vs pizza)")
print(f"Similarity (Text 2 vs Text 3): {sim_2_3:.4f}  (Dissimilar: college vs pizza)")