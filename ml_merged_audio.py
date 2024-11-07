import yt_dlp
import os
import sys
import ffmpeg
import tempfile

def download_videos(singer_name, num_videos, duration, output_file):
    output_dir = "downloaded_audios"
    os.makedirs(output_dir, exist_ok=True)

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'noplaylist': True,
        'default_search': 'ytsearch',
        'continuedl': False,
        'retries': 10,
        'ignoreerrors': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            search_results = ydl.extract_info(f"ytsearch{num_videos}:{singer_name}", download=False)
            if not search_results or not search_results.get('entries'):
                print("No search results found")
                return

            successful_downloads = 0
            for entry in search_results['entries'][:num_videos]:
                try:
                    print(f"Downloading: {entry.get('title', 'Unknown Title')}")
                    ydl.download([entry['url']])
                    successful_downloads += 1
                except Exception as e:
                    print(f"Failed to download {entry.get('title', 'Unknown Title')}: {str(e)}")
                    continue

            print(f"Downloaded {successful_downloads} out of {num_videos} videos.")
            if successful_downloads > 0:
                crop_and_merge_audios(output_dir, output_file, duration)
            else:
                print("No successful downloads to process.")

        except Exception as e:
            print(f"Error during download: {str(e)}")

def crop_and_merge_audios(input_dir, output_file, duration=20):
    cropped_dir = os.path.join(input_dir, "cropped")
    os.makedirs(cropped_dir, exist_ok=True)

    audio_files = []
    for i, file in enumerate(os.listdir(input_dir)):
        if file.endswith(".mp3"):
            input_path = os.path.join(input_dir, file)
            cropped_path = os.path.join(cropped_dir, f"cropped_{i}.mp3")

            # Crop the audio file to the specified duration
            ffmpeg.input(input_path, t=duration).output(cropped_path).run(overwrite_output=True)
            audio_files.append(cropped_path)

    if not audio_files:
        print("No audio files to merge.")
        return

    # Use a temporary file list for concatenation
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as file_list:
        for audio in audio_files:
            file_list.write(f"file '{audio}'\n")
        file_list.flush()

    # Merge all cropped audio files into a single output file
    ffmpeg.input(file_list.name, format='concat', safe=0).output(output_file, c='copy').run(overwrite_output=True)
    print(f"All audios merged into {output_file}")

    # Clean up temporary file list
    os.remove(file_list.name)


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python <program.py> <SingerName> <NumberOfVideos> <AudioDuration> <OutputFileName>")
        sys.exit(1)

    singer_name = sys.argv[1]
    try:
        num_videos = int(sys.argv[2])
        duration = int(sys.argv[3])
        output_file = sys.argv[4]

        download_videos(singer_name, num_videos, duration, output_file)
    except ValueError:
        print("Number of videos and duration must be integers.")
