import os
import chromadb
import json
import time
from openai import OpenAI
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

chroma_client = chromadb.PersistentClient(path='./chroma_db')
collection = chroma_client.get_or_create_collection(
    name="youtube_transcripts",
    metadata={"description": "The Black Female Engineer YouTube Content"}
    )

PROCESSED_DIR = "processed"

def process_all_transcripts():
    processed_path = Path(PROCESSED_DIR)
    json_files = list(processed_path.glob("*.json"))
    print(f"Found {len(json_files)} transcript files to process")
    all_transcripts = []

    for i, file in enumerate(json_files):
        print(f"On number {i} out of {len(json_files)}")
        with open(file, 'r') as f:
            data = json.load(f)
        
        transcript = data['transcript']
        title = data.get('video_title', file.stem)
        print(f"Loaded transcript: {len(transcript)} characters!")

        all_transcripts.append({
            'title': title,
            'transcript': transcript,
            'video_id': file.stem
        })

    return all_transcripts

all_transcripts = process_all_transcripts()

# Now, chunk the transcripts

CHUNK_SIZE = 500
OVERLAP = 100

def create_chunks(transcript, chunks_size, overlap):
    chunks = []
    start = 0

    while start < len(transcript):
        end = start + chunks_size
        chunk = transcript[start:end]
        chunks.append(chunk)

        start = end - overlap
    
    return chunks

def chunk_all_transcripts(all_transcripts):
    all_chunks = []
    for i, video in enumerate(all_transcripts):
        chunks = create_chunks(video['transcript'], CHUNK_SIZE, OVERLAP)
        print(f"Created {len(chunks)} chunks")
        
        all_chunks.append({
            'title': video['title'],
            'video_id': video['video_id'],
            'chunks': chunks
        })
    
    return all_chunks

all_chunks = chunk_all_transcripts(all_transcripts)

print(f"\nTotal videos chunked: {len(all_chunks)}")











# CHUNK_SIZE = 500
# OVERLAP = 100

# def create_chunks(text, chunk_size, overlap):
#     start = 0
#     chunks = []

#     while start < len(text):
#         end = start + chunk_size
#         chunk = text[start:end]
#         chunks.append(chunk)

#         start = end - overlap

#     return chunks

# chunks = create_chunks(transcript, CHUNK_SIZE, OVERLAP)
# print(f"length of chunks: {len(chunks)}")

# #  Now we need to create embeddings from the chunked text

# def create_embedding(text):
#     response = client.embeddings.create(
#         model = "text-embedding-3-small",
#         input = text
#     )

#     embedding = response.data[0].embedding
#     return embedding

# # embedding = create_embedding(chunks[0])

# def create_structured_embedding():
#     structured_embedding = []
#     ids = []
#     documents = []
#     embeddings = []

#     for i, chunk in enumerate(chunks):
#         embedding = create_embedding(chunk)
#         ids.append(str(i))
#         documents.append(chunk)
#         embeddings.append(embedding)
#         print(f"Embedded chunk {i + 1} of {len(chunks)}")
    
#     collection.add(
#         ids = ids,
#         documents = documents,
#         embeddings = embeddings
#     )
    
#     return collection

# create_structured_embedding()

# print(f"added {collection.count()} embeddings")
