import json

with open('processed/CRACKINGTHE.json', 'r') as f:
    data = json.load(f)

transcript = data['transcript']

print(transcript)

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
print(f"Total chunks: {len(chunks)}")
print(f"First chunk preview: {chunks[0]}")
print(f"Last chunk preview: {chunks[-1]}")

