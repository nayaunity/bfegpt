import os
import re
import json

def clean_vtt(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    
    lines = content.split('\n')
    text_lines = []
    
    for line in lines:
        # Skip WEBVTT header and metadata
        if line.strip() in ['WEBVTT', ''] or line.startswith('Kind:') or line.startswith('Language:'):
            continue
        # Skip timestamp lines (they contain -->)
        if '-->' in line:
            continue
        # Skip line numbers
        if re.match(r'^\d+$', line.strip()):
            continue
        
        # Remove inline timestamp tags like <00:00:00.719><c> and </c>
        cleaned_line = re.sub(r'<[^>]+>', '', line)
        cleaned_line = cleaned_line.strip()
        
        if cleaned_line:
            text_lines.append(cleaned_line)
    
    # Deduplicate rolling captions (each line often repeats the previous)
    unique_lines = []
    for line in text_lines:
        # Only add if this line isn't contained in the previous one
        if not unique_lines or line not in unique_lines[-1]:
            unique_lines.append(line)
    
    return ' '.join(unique_lines)


def process_all_transcripts():
    input_folder = "transcripts"
    output_folder = "processed"
    
    os.makedirs(output_folder, exist_ok=True)
    
    files = [f for f in os.listdir(input_folder) if f.endswith('.vtt')]
    print(f"Found {len(files)} VTT files")
    
    for i, filename in enumerate(files):
        video_title = filename.replace('.en.vtt', '')
        file_path = os.path.join(input_folder, filename)
        
        transcript = clean_vtt(file_path)
        
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