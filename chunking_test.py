from dotenv import load_dotenv
import os
import json
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))


with open('processed/CRACKINGTHE.json', 'r') as f:
    data = json.load(f)

transcript = data['transcript']

# print(transcript)

CHUNK_SIZE = 500
OVERLAP = 100

def chunk_text(text, chunk_size, overlap):
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)

        start = end - overlap
    
    return chunks

chunks = chunk_text(transcript, CHUNK_SIZE, OVERLAP)
# print(f"Total chunks: {len(chunks)}")
# print(f"First chunk preview: {chunks[0]}")
# print(f"Last chunk preview: {chunks[-1]}")

def get_embedding(text):
    response = client.embeddings.create(
        model = "text-embedding-3-small",
        input = text
    )
    return response.data[0].embedding

# test_embedding = get_embedding(chunks[0])
# print(f"output length: {len(test_embedding)}")
# for chunk in chunks:
#     get_embedding(chunk)

embedded_chunks = []

for i, chunk in enumerate(chunks):
    embedding = get_embedding(chunk)
    embedded_chunks.append({
        "chunk_id": i,
        "text": chunk,
        "embedding": embedding
    })

    print(f"embedded chunk {i + 1} out of {len(chunks)}")

with open('embedded_chunks', 'w') as f:
    json.dump(embedded_chunks, f)

print(f"Saved {len(embedded_chunks)} embedded chunks")
