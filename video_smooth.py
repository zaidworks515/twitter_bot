import subprocess
import os

os.environ["PATH"] += os.pathsep + r"video_generation\ffmpeg\bin"

def increase_fps(input_video, output_video, fps=60):
    """
    Increase the frame rate of a video using FFmpeg.
    
    Parameters:
    input_video (str): Path to the input video file.
    output_video (str): Path to save the output video.
    fps (int): Desired frame rate (default is 60 FPS).
    """
    
    command = [
    "ffmpeg", "-i", input_video,
    "-vf", f"fps={fps}",
    "-y", output_video
    ]
    
    
    try:
        subprocess.run(command, check=True)
        print(f"Video processing complete. Saved as {output_video}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")


