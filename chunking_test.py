# from dotenv import load_dotenv
# import os
# import json
# from openai import OpenAI

# load_dotenv()

# client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))


# with open('processed/CRACKINGTHE.json', 'r') as f:
#     data = json.load(f)

# transcript = data['transcript']

# # print(transcript)

# CHUNK_SIZE = 500
# OVERLAP = 100

# def chunk_text(text, chunk_size, overlap):
#     chunks = []
#     start = 0

#     while start < len(text):
#         end = start + chunk_size
#         chunk = text[start:end]
#         chunks.append(chunk)

#         start = end - overlap
    
#     return chunks

# chunks = chunk_text(transcript, CHUNK_SIZE, OVERLAP)
# # print(f"Total chunks: {len(chunks)}")
# # print(f"First chunk preview: {chunks[0]}")
# # print(f"Last chunk preview: {chunks[-1]}")

# def get_embedding(text):
#     response = client.embeddings.create(
#         model = "text-embedding-3-small",
#         input = text
#     )
#     return response.data[0].embedding

# # test_embedding = get_embedding(chunks[0])
# # print(f"output length: {len(test_embedding)}")
# # for chunk in chunks:
# #     get_embedding(chunk)

# embedded_chunks = []

# for i, chunk in enumerate(chunks):
#     embedding = get_embedding(chunk)
#     embedded_chunks.append({
#         "chunk_id": i,
#         "text": chunk,
#         "embedding": embedding
#     })

#     print(f"embedded chunk {i + 1} out of {len(chunks)}")

# with open('embedded_chunks', 'w') as f:
#     json.dump(embedded_chunks, f)

# print(f"Saved {len(embedded_chunks)} embedded chunks")

import os
import chromadb
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

chroma_client = chromadb.PersistentClient(path='./chroma_db')
collection = chroma_client.get_or_create_collection(name="youtube_transcripts")

# Get text which is the transcript

with open('processed/CRACKINGTHE.json', 'r') as f:
    data = json.load(f)

transcript = data['transcript']
#  Now we need to chunk the text

CHUNK_SIZE = 500
OVERLAP = 100

def create_chunks(text, chunk_size, overlap):
    start = 0
    chunks = []

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)

        start = end - overlap

    return chunks

chunks = create_chunks(transcript, CHUNK_SIZE, OVERLAP)
print(f"length of chunks: {len(chunks)}")

#  Now we need to create embeddings from the chunked text

def create_embedding(text):
    response = client.embeddings.create(
        model = "text-embedding-3-small",
        input = text
    )

    embedding = response.data[0].embedding
    return embedding

# embedding = create_embedding(chunks[0])

def create_structured_embedding():
    structured_embedding = []
    ids = []
    documents = []
    embeddings = []

    for i, chunk in enumerate(chunks):
        embedding = create_embedding(chunk)
        ids.append(str(i))
        documents.append(chunk)
        embeddings.append(embedding)
        print(f"Embedded chunk {i + 1} of {len(chunks)}")
    
    collection.add(
        ids = ids,
        documents = documents,
        embeddings = embeddings
    )
    
    return collection

create_structured_embedding()

print(f"added {collection.count()} embeddings")
