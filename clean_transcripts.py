import os
import re
import json

def clean_vtt(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    
    lines = content.split('\n')
    text_lines = []
    
    for line in lines:
        # Skip line numbers
        if re.match(r'^\d+$', line.strip()):
            continue
        # Skip timestamps
        if re.match(r'\d{2}:\d{2}:\d{2}', line):
            continue
        # Skip empty lines and header
        if line.strip() == '' or line.strip() == 'WEBVTT':
            continue
        text_lines.append(line.strip())
    
    # Deduplicate rolling captions
    cleaned = []
    for line in text_lines:
        if not cleaned or line not in cleaned[-1]:
            cleaned.append(line)
    
    return ' '.join(cleaned)


def process_all_transcripts():
    input_folder = "transcripts"
    output_folder = "processed"
    
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    
    files = [f for f in os.listdir(input_folder) if f.endswith('.vtt')]
    print(f"Found {len(files)} VTT files")
    
    for i, filename in enumerate(files):
        video_title = filename.replace('.en.vtt', '')
        file_path = os.path.join(input_folder, filename)
        
        # Clean it
        transcript = clean_vtt(file_path)
        
        # Save as JSON
        output_data = {
            "video_title": video_title,
            "transcript": transcript
        }
        
        output_path = os.path.join(output_folder, f"{video_title}.json")
        with open(output_path, 'w') as f:
            json.dump(output_data, f)
        
        print(f"[{i + 1}/{len(files)}] Cleaned: {video_title[:50]}...")
    
    print(f"\nDone! Cleaned transcripts saved to '{output_folder}/'")


process_all_transcripts()
