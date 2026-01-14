# from dotenv import load_dotenv
# import os
# import numpy as np
# import json
# from openai import OpenAI

# load_dotenv()
# client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# # Step 1: open the embedding data
# with open('embedded_chunks', 'r') as f:
#     embedded_chunks = json.load(f)

# def cosign_similarity(vec1, vec2):
#     vec1 = np.array(vec1)
#     vec2 = np.array(vec2)

#     return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

# def search(query, top_k=3):
#     query_embedding = client.embeddings.create(
#         model = "text-embedding-3-small",
#         input = query
#     ).data[0].embedding
    
#     results = []
#     for chunk in embedded_chunks:
#         similarity = cosign_similarity(chunk['embedding'], query_embedding)
#         results.append({
#             "chunk_id": chunk["chunk_id"],
#             "text": chunk["text"],
#             "similarity": similarity
#         })
    
#     results.sort(key=lambda x:x['similarity'], reverse=True)

#     return results[:top_k]

# query = "What advice do you have about resumes?"
# results = search(query)

# def ask(question):
#     results = search(question)
#     chunks_text = []
    
#     for r in results:
#         chunks_text.append(r["text"])
    
#     context = "\n\n".join(chunks_text)

#     prompt = f"""Use the following context to answer the question. If the context doesn't contain enough information, say so

#     Context: {context}
#     Question: {question}
#     Answer: """

#     response = client.chat.completions.create(
#         model="gpt-4o-mini",
#         messages=[{
#             "role": "user",
#             "content": prompt
#         }]
#     )

#     return response.choices[0].message.content

# answer = ask("What advice do you have about resumes?")
# print(answer)

from dotenv import load_dotenv
from openai import OpenAI
import os
import chromadb

load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="youtube_transcripts")

def embed_query(query):
    response = client.embeddings.create(
        model = "text-embedding-3-small",
        input = query
    )
    query_embedding = response.data[0].embedding
    return query_embedding

def collect_relevant_chunks(query, top_k=3):
    query_embedding = embed_query(query)

    chunks_results = collection.query(
        query_embeddings = [query_embedding],
        n_results = top_k
    )

    return chunks_results

def ask(question):
    results = collect_relevant_chunks(question)
    chunks_text = results['documents'][0]
    context = "\n\n".join(chunks_text)
    prompt = f"""Use the following context to answer the question. If the context doesn't contain enough information, say so

    Context: {context}
    Question: {question}
    Answer: """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": prompt
        }]
    )

    return response.choices[0].message.content

answer = ask("what advice do you have regarding resumes?")
print(f"Answer: {answer}")
