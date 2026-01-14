# import os
# import re
# import chromadb
# from openai import OpenAI
# from dotenv import load_dotenv

# load_dotenv()
# client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# chroma_client = chromadb.PersistentClient(path="./chroma_db")
# collection = chroma_client.get_or_create_collection(name="youtube_transcripts")

# def clean_vtt(file_path):
#     with open(file_path, 'r') as f:
#         content = f.read()
    
#     lines = content.split('\n')
#     text_lines = []
    
#     for line in lines:
#         # Skip line numbers
#         if re.match(r'^\d+$', line.strip()):
#             continue
#         # Skip timestamps
#         if re.match(r'\d{2}:\d{2}:\d{2}', line):
#             continue
#         # Skip empty lines and header
#         if line.strip() == '' or line.strip() == 'WEBVTT':
#             continue
#         text_lines.append(line.strip())
    
#     # Deduplicate rolling captions
#     cleaned = []
#     for line in text_lines:
#         if not cleaned or line not in cleaned[-1]:
#             cleaned.append(line)
    
#     return ' '.join(cleaned)