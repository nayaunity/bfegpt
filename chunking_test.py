import os
import chromadb
import json
import time
import uuid
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
    all_transcripts = []

    for i, file in enumerate(json_files):
        with open(file, 'r') as f:
            data = json.load(f)
        
        transcript = data['transcript'][500:]
        title = data.get('video_title', file.stem)

        all_transcripts.append({
            'title': title,
            'transcript': transcript,
            'video_id': file.stem
        })

    return all_transcripts

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
        
        all_chunks.append({
            'title': video['title'],
            'video_id': video['video_id'],
            'chunks': chunks
        })
    
    return all_chunks

def create_embedding(text):
    response = client.embeddings.create(
        model = "text-embedding-3-small",
        input = text
    )

    embedding = response.data[0].embedding
    return embedding

def embed_all_chunks(all_chunks):
    all_ids = []
    all_documents = []
    all_embeddings = []
    all_metadatas = []

    for video in all_chunks:
        print(f"embedding {video['title'][:50]}...")
        
        for i, chunk in enumerate(video['chunks']):
            embedding = create_embedding(chunk)
            chunk_id = f"{video['video_id']}_{uuid.uuid4().hex[:8]}"

            all_ids.append(chunk_id)
            all_documents.append(chunk)
            all_embeddings.append(embedding)
            all_metadatas.append({
                'title': video['title'],
                'video_id': video['video_id'],
                'chunk_index': i
            })

            print(f"  Embedded chunk {i + 1} of {len(video['chunks'])}")
    
    collection.add(
        ids = all_ids,
        documents = all_documents,
        embeddings = all_embeddings,
        metadatas = all_metadatas
    )
    print(f"\nStored {len(all_ids)} embeddings in ChromaDB!")

# # Clear existing data
# chroma_client.delete_collection(name="youtube_transcripts")
# collection = chroma_client.get_or_create_collection(
#     name="youtube_transcripts",
#     metadata={"description": "The Black Female Engineer YouTube Content"}
# )

# all_transcripts = process_all_transcripts()
# all_chunks = chunk_all_transcripts(all_transcripts)
# embed_all_chunks(all_chunks)


def find_relevant_chunks(query, top_k=5):
    query_embedding = create_embedding(query)

    results = collection.query(
        query_embeddings = [query_embedding],
        n_results = top_k,
        include = ["documents", "metadatas", "distances"]

    )

    return results

def ask(query):
    results = find_relevant_chunks(query)

    chunks = results['documents'][0]
    context = "\n\n".join(chunks)

    response = client.chat.completions.create(
        model = "gpt-4o-mini",
        messages = [
            {
                "role": "system",
                "content": "You are Naya, the creator behind @TheBlackFemaleEngineer. Answer questions based only on the provided context from your YouTube videos. Be helpful, warm, and conversational—like you're talking to your audience."
            },
            {
                "role": "user",
                "content": f"Content from your videos: \n{context}\nQuestion{query}"
            }
        ]
    )

    print(response.choices[0].message.content)

def rewrite_query(query):
    response = client.chat.completions.create(
        model = "gpt-4o-mini",
        messages = [
            {
                "role": "system",
                "content": "You rewrite user queries to improve search results. The content being searched is from a YouTube channel about becoming a self-taught software engineer. This process involves not only learning the appropriate curriculum, but also getting a software engineering job. Rewrite the query to be more specific and include relevant terms. Return only the rewritten query, nothing else."
            },
            {
                "role": "user",
                "content": query
            }
        ]
    )

    rewritten_question = response.choices[0].message.content
    print(f"Rewritten question is: {rewritten_question}")
    ask(rewritten_question)

rewrite_query("How do I get started?")
# ask("How do I get started?")
