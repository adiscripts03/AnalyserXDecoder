import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings

load_dotenv()

print("API key loaded:", bool(os.getenv("GOOGLE_API_KEY")))

embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001"
)

text = "IIIT Nagpur is an engineering institute."

vector = embeddings.embed_query(text)

print("Vector length:", len(vector))
print("First 10 values:", vector[:10])