#!/usr/bin/env python3
"""
Whisper Fast large v3 transcription script for YouTube Shorts
Generates DaVinci Resolve compatible SRT files and plain TXT files
Batch processes all audio/video files from 'in' folder to 'out' folder
"""

import argparse
import os
import sys
import warnings
from pathlib import Path
from typing import List, Tuple
from tqdm import tqdm

# Suppress all warnings before importing ctranslate2
warnings.filterwarnings("ignore", category=UserWarning)
os.environ['PYTHONWARNINGS'] = 'ignore'

from faster_whisper import WhisperModel


def format_timestamp(seconds: float) -> str:
    """Convert seconds to SRT timestamp format (HH:MM:SS,mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def split_text_by_chars(text: str, max_chars: int = 10) -> List[str]:
    """
    Split text into chunks with max characters, trying to break at word boundaries
    """
    words = text.strip().split()
    chunks = []
    current_chunk = ""

    for word in words:
        # If adding this word would exceed max_chars
        if len(current_chunk) + len(word) + (1 if current_chunk else 0) > max_chars:
            # If we have a current chunk, save it
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = word
            else:
                # Single word exceeds max_chars, split it
                chunks.append(word[:max_chars])
                current_chunk = word[max_chars:]
        else:
            # Add word to current chunk
            if current_chunk:
                current_chunk += " " + word
            else:
                current_chunk = word

    # Add remaining chunk
    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def split_segment_by_time(
    segment_text: str,
    start_time: float,
    end_time: float,
    max_chars: int = 10
) -> List[Tuple[str, float, float]]:
    """
    Split a segment into smaller chunks with proportional time allocation
    Returns list of (text, start, end) tuples
    """
    chunks = split_text_by_chars(segment_text, max_chars)
    if not chunks:
        return []

    total_duration = end_time - start_time
    duration_per_chunk = total_duration / len(chunks)

    result = []
    for i, chunk in enumerate(chunks):
        chunk_start = start_time + (i * duration_per_chunk)
        chunk_end = start_time + ((i + 1) * duration_per_chunk)
        result.append((chunk, chunk_start, chunk_end))

    return result


def transcribe_audio(
    audio_path: str,
    model: WhisperModel,
    language: str = "ru",
    pbar: tqdm = None
) -> List[Tuple[str, float, float]]:
    """
    Transcribe audio/video file using Whisper Fast
    Returns list of (text, start_time, end_time) tuples
    """
    if pbar:
        pbar.set_description(f"🎤 Transcribing")

    # Transcribe with word-level timestamps
    segments, info = model.transcribe(
        audio_path,
        language=language,
        word_timestamps=True,
        vad_filter=False  # Keep all pauses for DaVinci Resolve compatibility
    )

    if pbar:
        pbar.set_description(f"✓ Language: {info.language} ({info.language_probability:.0%})")

    # Collect all segments
    all_segments = []
    segments_list = list(segments)

    for segment in segments_list:
        # Use word-level timestamps if available
        if hasattr(segment, 'words') and segment.words:
            for word in segment.words:
                all_segments.append((
                    word.word.strip(),
                    word.start,
                    word.end
                ))
        else:
            # Fall back to segment-level timestamps
            all_segments.append((
                segment.text.strip(),
                segment.start,
                segment.end
            ))

    return all_segments


def generate_srt(
    segments: List[Tuple[str, float, float]],
    output_path: str,
    max_chars: int = 10,
    pbar: tqdm = None
):
    """
    Generate SRT file in DaVinci Resolve format
    Each subtitle has max_chars characters
    """
    if pbar:
        pbar.set_description(f"💾 Generating SRT")

    with open(output_path, 'w', encoding='utf-8') as f:
        subtitle_index = 1

        for text, start, end in segments:
            # Split segment if it exceeds max_chars
            chunks = split_segment_by_time(text, start, end, max_chars)

            for chunk_text, chunk_start, chunk_end in chunks:
                # Write subtitle in DaVinci Resolve format
                # Note: text starts with a space (as seen in examples)
                f.write(f"{subtitle_index}\n")
                f.write(f"{format_timestamp(chunk_start)} --> {format_timestamp(chunk_end)}\n")
                f.write(f" {chunk_text}\n")
                f.write("\n")

                subtitle_index += 1

    if pbar:
        pbar.set_description(f"✓ Created {subtitle_index - 1} subtitles")


def generate_txt(
    segments: List[Tuple[str, float, float]],
    output_path: str,
    pbar: tqdm = None
):
    """
    Generate plain text file with recognized text
    """
    if pbar:
        pbar.set_description(f"💾 Generating TXT")

    with open(output_path, 'w', encoding='utf-8') as f:
        # Join all text segments with spaces
        full_text = " ".join(text.strip() for text, _, _ in segments)
        f.write(full_text)

    if pbar:
        pbar.set_description(f"✓ Created text file")


def get_supported_files(directory: Path) -> List[Path]:
    """
    Get all supported audio/video files from directory
    """
    # Supported formats
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv', '.m4v', '.mpg', '.mpeg'}
    audio_extensions = {'.wav', '.mp3', '.m4a', '.flac', '.aac', '.ogg', '.wma', '.opus'}
    all_extensions = video_extensions | audio_extensions

    files = []
    for ext in all_extensions:
        files.extend(directory.glob(f'*{ext}'))
        files.extend(directory.glob(f'*{ext.upper()}'))

    return sorted(files)


def process_batch(
    input_dir: Path,
    output_dir: Path,
    model_size: str = "large-v3",
    device: str = "auto",
    compute_type: str = "auto",
    language: str = "ru",
    max_chars: int = 10
):
    """
    Process all audio/video files from input directory
    """
    # Ensure directories exist
    input_dir.mkdir(exist_ok=True)
    output_dir.mkdir(exist_ok=True)

    # Get all supported files
    files = get_supported_files(input_dir)

    if not files:
        print(f"❌ No audio/video files found in {input_dir}")
        return

    print(f"\n{'='*60}")
    print(f"  📁 Found {len(files)} file(s) to process")
    print(f"  🤖 Loading Whisper model: {model_size}")
    print(f"{'='*60}\n")

    # Initialize model once for all files with automatic CPU fallback
    try:
        model = WhisperModel(
            model_size,
            device=device,
            compute_type=compute_type
        )
        device_emoji = "🚀" if device in ["auto", "cuda"] else "💻"
        print(f"{device_emoji} Model loaded on: {device}\n")
    except Exception as e:
        if device == "auto" or device == "cuda":
            print(f"⚠️  Failed to load model on {device}")
            print(f"💻 Falling back to CPU with int8 precision\n")
            device = "cpu"
            compute_type = "int8"
            model = WhisperModel(
                model_size,
                device=device,
                compute_type=compute_type
            )
        else:
            raise

    processed = 0
    skipped = 0
    errors = 0

    # Process files with progress bar
    with tqdm(files, desc="📊 Overall Progress", unit="file", ncols=100,
              bar_format='{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]') as pbar_main:

        for file_path in pbar_main:
            # Determine output paths
            output_srt_path = output_dir / f"{file_path.stem}.srt"
            output_txt_path = output_dir / f"{file_path.stem}.txt"

            # Update main progress bar
            pbar_main.set_description(f"📊 [{processed+skipped+1}/{len(files)}] {file_path.name[:30]}")

            # Check if already processed
            if output_srt_path.exists() and output_txt_path.exists():
                skipped += 1
                pbar_main.write(f"   ⏭️  Skipped: {file_path.name} (already processed)")
                continue

            try:
                # Create sub-progress bar for this file
                with tqdm(total=3, desc=f"   🎬 {file_path.name[:35]}",
                         leave=False, ncols=100, bar_format='{desc} | {bar} {n}/3') as pbar_file:

                    # Transcribe
                    segments = transcribe_audio(
                        str(file_path),
                        model=model,
                        language=language,
                        pbar=pbar_file
                    )
                    pbar_file.update(1)

                    # Generate SRT
                    generate_srt(segments, str(output_srt_path), max_chars=max_chars, pbar=pbar_file)
                    pbar_file.update(1)

                    # Generate TXT
                    generate_txt(segments, str(output_txt_path), pbar=pbar_file)
                    pbar_file.update(1)

                processed += 1
                pbar_main.write(f"   ✅ Completed: {file_path.name} → {output_srt_path.name}, {output_txt_path.name}")

            except Exception as e:
                errors += 1
                pbar_main.write(f"   ❌ Error: {file_path.name} - {str(e)[:50]}")

    # Summary
    print(f"\n{'='*60}")
    print(f"  🎉 Batch processing complete!")
    print(f"  {'='*56}")
    print(f"     ✅ Processed:  {processed:>3}")
    print(f"     ⏭️  Skipped:    {skipped:>3}")
    print(f"     ❌ Errors:     {errors:>3}")
    print(f"  {'='*56}")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Batch transcribe audio/video files using Whisper Fast large v3"
    )
    parser.add_argument(
        "-i", "--input-dir",
        default="in",
        help="Input directory with audio/video files (default: in)"
    )
    parser.add_argument(
        "-o", "--output-dir",
        default="out",
        help="Output directory for SRT and TXT files (default: out)"
    )
    parser.add_argument(
        "-m", "--model",
        default="large-v3",
        help="Whisper model size (default: large-v3)"
    )
    parser.add_argument(
        "-c", "--max-chars",
        type=int,
        default=10,
        help="Maximum characters per subtitle (default: 10)"
    )
    parser.add_argument(
        "-l", "--language",
        default="ru",
        help="Language code (default: ru for Russian)"
    )
    parser.add_argument(
        "-d", "--device",
        default="auto",
        choices=["auto", "cpu", "cuda"],
        help="Device to use for inference (default: auto)"
    )
    parser.add_argument(
        "--compute-type",
        default="auto",
        choices=["auto", "int8", "float16", "float32"],
        help="Compute type for inference (default: auto)"
    )

    args = parser.parse_args()

    # Convert to Path objects
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)

    # Process all files in batch
    try:
        process_batch(
            input_dir=input_dir,
            output_dir=output_dir,
            model_size=args.model,
            device=args.device,
            compute_type=args.compute_type,
            language=args.language,
            max_chars=args.max_chars
        )
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
