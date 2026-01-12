#!/usr/bin/env python3
"""
VTT Caption Processor for RAG Pipeline
Processes YouTube auto-generated VTT files with rolling caption format.
Removes timestamps, line numbers, and deduplicates scrolling text.
"""

import json
import re
from pathlib import Path


def parse_vtt_blocks(vtt_content: str) -> list[str]:
    """
    Parse VTT content into text blocks, removing timestamps and metadata.
    """
    lines = vtt_content.split('\n')
    blocks = []
    current_block = []
    in_block = False

    for line in lines:
        line = line.strip()

        # Skip WEBVTT header and empty lines
        if line.startswith('WEBVTT') or line.startswith('Kind:') or line.startswith('Language:'):
            continue

        # Skip numeric line identifiers (cue IDs)
        if re.match(r'^\d+$', line):
            # If we were building a block, save it
            if current_block:
                block_text = ' '.join(current_block)
                if block_text:
                    blocks.append(block_text)
                current_block = []
            continue

        # Skip timestamp lines (00:00:00,000 --> 00:00:00,000)
        if re.match(r'^\d{2}:\d{2}:\d{2}[.,]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[.,]\d{3}', line):
            continue

        # Skip empty lines (block separator)
        if not line:
            if current_block:
                block_text = ' '.join(current_block)
                if block_text:
                    blocks.append(block_text)
                current_block = []
            continue

        # This is actual caption text
        # Remove any VTT styling tags like <c> </c>
        line = re.sub(r'<[^>]+>', '', line)
        if line:
            current_block.append(line)

    # Don't forget the last block
    if current_block:
        block_text = ' '.join(current_block)
        if block_text:
            blocks.append(block_text)

    return blocks


def deduplicate_rolling_captions(blocks: list[str]) -> str:
    """
    Smart deduplication for YouTube's rolling caption format.

    The rolling format shows accumulated text where each block contains
    all previous text plus new words. We extract only the new content
    from each block while preserving natural speech repetitions.
    """
    if not blocks:
        return ""

    result_parts = []
    prev_text = ""

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        # Normalize whitespace for comparison
        block_normalized = ' '.join(block.split())
        prev_normalized = ' '.join(prev_text.split())

        if not prev_normalized:
            # First block - keep it all
            result_parts.append(block_normalized)
            prev_text = block_normalized
            continue

        # Check if current block starts with previous text (rolling format)
        if block_normalized.startswith(prev_normalized):
            # Extract only the new portion
            new_text = block_normalized[len(prev_normalized):].strip()
            if new_text:
                result_parts.append(new_text)
            prev_text = block_normalized
        elif prev_normalized.startswith(block_normalized):
            # Current block is subset of previous (can happen with timing overlaps)
            # Skip it - we already have this content
            continue
        else:
            # Completely new section (scene change, speaker change, etc.)
            # Check for partial overlap at the end of prev_text
            overlap_found = False

            # Try to find overlap by checking if end of prev matches start of current
            min_overlap = 3  # Minimum words to consider as overlap
            prev_words = prev_normalized.split()
            block_words = block_normalized.split()

            for overlap_size in range(min(len(prev_words), len(block_words)), min_overlap - 1, -1):
                prev_end = ' '.join(prev_words[-overlap_size:])
                block_start = ' '.join(block_words[:overlap_size])

                if prev_end == block_start:
                    # Found overlap - only add the non-overlapping part
                    new_text = ' '.join(block_words[overlap_size:])
                    if new_text:
                        result_parts.append(new_text)
                    prev_text = block_normalized
                    overlap_found = True
                    break

            if not overlap_found:
                # No overlap detected - this is genuinely new content
                result_parts.append(block_normalized)
                prev_text = block_normalized

    # Join all parts and clean up
    full_text = ' '.join(result_parts)

    # Final cleanup: normalize whitespace and fix common issues
    full_text = re.sub(r'\s+', ' ', full_text)  # Multiple spaces to single
    full_text = re.sub(r'\s+([.,!?])', r'\1', full_text)  # Space before punctuation

    return full_text.strip()


def extract_video_info(filename: str) -> tuple[str, str]:
    """
    Extract video ID and title from VTT filename.

    Expected formats:
    - "Video Title [video_id].en.vtt"
    - "Video Title.en.vtt" (video_id extracted differently or set to filename)
    """
    stem = filename

    # Remove .en.vtt, .en.srt or similar suffix
    for suffix in ['.en.vtt', '.vtt', '.en-US.vtt', '.en.srt', '.srt', '.en-US.srt']:
        if stem.endswith(suffix):
            stem = stem[:-len(suffix)]
            break

    # Try to extract video ID from brackets [video_id]
    bracket_match = re.search(r'\[([a-zA-Z0-9_-]{11})\]$', stem)
    if bracket_match:
        video_id = bracket_match.group(1)
        title = stem[:bracket_match.start()].strip()
    else:
        # No video ID in brackets - use filename as title, generate ID from filename
        title = stem
        # Create a pseudo-ID from the title (first 11 chars of sanitized title)
        video_id = re.sub(r'[^a-zA-Z0-9]', '', title)[:11] or 'unknown'

    # Clean up title
    title = title.strip(' -_')

    return video_id, title


def process_vtt_file(vtt_path: Path) -> dict:
    """
    Process a single VTT file and return structured data.
    """
    with open(vtt_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Parse and deduplicate
    blocks = parse_vtt_blocks(content)
    clean_transcript = deduplicate_rolling_captions(blocks)

    # Extract metadata from filename
    video_id, title = extract_video_info(vtt_path.name)

    return {
        "video_id": video_id,
        "title": title,
        "transcript": clean_transcript,
        "source_file": vtt_path.name
    }


def process_all_vtt_files(input_dir: str = "transcripts", output_dir: str = "processed"):
    """
    Process all VTT files in the input directory.
    Creates individual JSON files and a combined all_transcripts.json.
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    # Create output directory if it doesn't exist
    output_path.mkdir(parents=True, exist_ok=True)

    # Find all VTT and SRT files
    vtt_files = list(input_path.glob("*.vtt")) + list(input_path.glob("*.srt"))

    if not vtt_files:
        print(f"No VTT files found in {input_dir}/")
        print("Please place your .vtt files in the transcripts/ directory.")
        return

    print(f"Found {len(vtt_files)} VTT file(s) to process...")

    all_transcripts = []

    for vtt_file in vtt_files:
        print(f"  Processing: {vtt_file.name}")

        try:
            result = process_vtt_file(vtt_file)
            all_transcripts.append(result)

            # Write individual JSON file
            output_file = output_path / f"{result['video_id']}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            print(f"    -> {output_file.name} ({len(result['transcript'])} chars)")

        except Exception as e:
            print(f"    ERROR: {e}")
            continue

    # Write combined JSON file
    if all_transcripts:
        combined_file = output_path / "all_transcripts.json"
        with open(combined_file, 'w', encoding='utf-8') as f:
            json.dump(all_transcripts, f, indent=2, ensure_ascii=False)

        print(f"\nCreated combined file: {combined_file}")
        print(f"Total videos processed: {len(all_transcripts)}")

    return all_transcripts


if __name__ == "__main__":
    import sys

    # Allow custom input/output directories via command line
    input_dir = sys.argv[1] if len(sys.argv) > 1 else "transcripts"
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "processed"

    process_all_vtt_files(input_dir, output_dir)
