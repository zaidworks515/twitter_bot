import numpy as np
from moviepy.video.io.ImageSequenceClip import ImageSequenceClip
from moviepy.video.io.VideoFileClip import VideoFileClip, AudioFileClip
from moviepy.editor import CompositeAudioClip
from PIL import Image, ImageDraw, ImageFont
from moviepy.audio.fx.all import volumex  
import os
import random
from elevenlabs.client import ElevenLabs
import whisper
from moviepy.editor import VideoFileClip
import cv2
from PIL import ImageFont
import math
from config import whisper_model


# os.environ["PATH"] += os.pathsep + r"D:\projects\tesseract\trial\twitter_bot\video_generation\ffmpeg\bin"

def eleven_labs_audio_generation(generated_tweet, eleven_labs_api_key):
    clear_previous_data()
    client = ElevenLabs(
        api_key=eleven_labs_api_key,
        )

    audio_stream = client.text_to_speech.convert_as_stream(
        text=generated_tweet,
        # voice_id="TY",
        voice_id="zgl2jwLKx42OFNfQgsDQ",
        model_id="eleven_multilingual_v2",
        voice_settings={"stability": 0.3, "similarity_boost": 0.8, "style": 0.3}
    )

    audio_file_path = "./video_generation/voice_over/output_audio.mp3"

    if audio_stream:
        with open(audio_file_path, "wb") as audio_file:
            for chunk in audio_stream:
                if isinstance(chunk, bytes):
                    audio_file.write(chunk)
            return audio_file_path
    else:
        return None


def augment_video(video_path, times):
    cap = cv2.VideoCapture(video_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')

    out = cv2.VideoWriter("./video_generation/first_output.mp4", fourcc, float(fps), (width, height))

    frames = []

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)

    cap.release()

    if len(frames) < 7:  
        print("Not enough frames to process smoothly.")
        return

    frames = frames[5:]

    sequence = []
    for i in range(times):
        if i % 2 == 0:
            sequence.extend(frames)  
        else:
            sequence.extend(frames[::-1])

    for frame in sequence:
        out.write(frame)

    out.release()
    print(f"Video saved as first_output.mp4 with {times} sequence(s).")


def increase_template_video_length(audio_path, video_path): 
    
    audio = AudioFileClip(audio_path)
    video = VideoFileClip(video_path)
    
    audio_length = audio.duration
    video_length = video.duration
    print(audio_length)
    
    # NOW, MAKING THE VIDEO EQUAL TO THE AUDIO LENGTH....
    
    if audio_length > video_length:
        time_length = audio_length/video_length
        
        max_video_length = math.ceil(time_length)
        
        augment_video(video_path, max_video_length)
        
        second_video = VideoFileClip('./video_generation/first_output.mp4')
        second_video.audio = audio.subclip(0, audio.duration)

        trimmed_video = second_video.subclip(0, audio_length)


        trimmed_video.write_videofile("./video_generation/trimmed_output.mp4", codec="libx264", audio_codec="aac")
        return True
    
    elif audio_length <= video_length:
        second_video = video
        second_video.audio = audio.subclip(0, audio.duration)

        trimmed_video = second_video.subclip(0, audio_length)


        trimmed_video.write_videofile("./video_generation/trimmed_output.mp4", codec="libx264", audio_codec="aac")
        return True

    else:
        return False
            

def add_background_music(video_path, music_path, output_path, music_volume=0.15):
    video = VideoFileClip(video_path)
    bg_music = AudioFileClip(music_path).fx(volumex, music_volume) 

    bg_music = bg_music.set_duration(video.duration)  
    final_audio = CompositeAudioClip([video.audio, bg_music])
    final_video = video.set_audio(final_audio)
    final_video.write_videofile(output_path, codec="libx264", audio_codec="aac")


    return os.path.exists(output_path)

def clear_previous_data():
    os.remove("./video_generation/voice_over/output_audio.mp3") if os.path.exists("./video_generation/voice_over/output_audio.mp3") else None
    os.remove("./video_generation/first_output.mp4") if os.path.exists("./video_generation/first_output.mp4") else None
    os.remove("./video_generation/trimmed_output.mp4") if os.path.exists("./video_generation/trimmed_output.mp4") else None
    os.remove("./video_generation/video_with_subtitles.mp4") if os.path.exists("./video_generation/video_with_subtitles.mp4") else None
    os.remove("./video_generation/final_video_with_music.mp4") if os.path.exists("./video_generation/final_video_with_music.mp4") else None
    os.remove("./video_generation/augmented_video.mp4") if os.path.exists("./video_generation/augmented_video.mp4") else None


last_video_template_used = None

def split_text_into_chunks(text, duration, max_words=5):
    words = text.split()
    chunks = []
    total_words = len(words)
    duration_per_word = duration / total_words if total_words else 0

    for i in range(0, total_words, max_words):
        chunk_text = " ".join(words[i: i + max_words])
        chunk_duration = len(chunk_text.split()) * duration_per_word
        chunks.append((chunk_text, chunk_duration))

    return chunks

def make_video_complete(video_dir='./video_generation/video_templates'):
    result = None
    # PREVIOUS AUDIO AND VIDEO
    
    global last_video_template_used
    all_video_templates = os.listdir(video_dir)

    if last_video_template_used is not None:
        all_video_templates.remove(last_video_template_used)  # to prevent the repetitions

    selected_template_file = random.choice(all_video_templates)
    last_video_template_used = selected_template_file

    selected_template_path = f"{video_dir}/{selected_template_file}"
    print(f"FILE : {selected_template_path}")

    first_step = increase_template_video_length(audio_path="./video_generation/voice_over/output_audio.mp3", video_path=f"{selected_template_path}")    
    

    if first_step:
        video_path = "./video_generation/trimmed_output.mp4"

        video = VideoFileClip(video_path)
        fps = video.fps
        frame_width, frame_height = int(video.w), int(video.h)

        audio_path = "./video_generation/voice_over/output_audio.mp3"
        video.audio.write_audiofile(audio_path)

        model = whisper.load_model(whisper_model)   #to add from env
        result = model.transcribe(audio_path)
        print("Second step of video generation is completed...")
    
    else:
        print('First step failed.')


    if result:
        subtitles = []
        shift_time = -0.1
        

        for segment in result["segments"]:
            start_time = max(0, segment["start"] + shift_time)
            end_time = segment["end"] + shift_time
            duration = end_time - start_time

            text_chunks = split_text_into_chunks(segment["text"], duration)

            for chunk_text, chunk_duration in text_chunks:
                subtitles.append({"start": start_time, "end": start_time + chunk_duration, "text": chunk_text})
                start_time += chunk_duration  

        font_path = "./video_generation/font/neue_pixel_sans/NeuePixelSans.ttf"
        font_size = 55
        font = ImageFont.truetype(font_path, font_size)

        left_right_margin = 40
        bottom_margin = 40
        max_text_width = frame_width - (2 * left_right_margin)

    def wrap_text(text, font, max_width):
        words = text.split()
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + " " + word if current_line else word
            text_size = font.getbbox(test_line)
            text_width = text_size[2] - text_size[0]

            if text_width <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        return lines

    def draw_text(frame, text):
        img_pil = Image.fromarray(frame)
        draw = ImageDraw.Draw(img_pil)

        wrapped_lines = wrap_text(text, font, max_text_width)
        total_text_height = sum(font.getbbox(line)[3] - font.getbbox(line)[1] for line in wrapped_lines)
        text_y = frame_height - bottom_margin - total_text_height

        shadow_offset = 3
        bold_offset = 0

        for line in wrapped_lines:
            text_width = font.getbbox(line)[2] - font.getbbox(line)[0]
            text_x = max(left_right_margin, (frame_width - text_width) // 2)  # Center horizontally

            draw.text((text_x + shadow_offset, text_y + shadow_offset), line, font=font, fill=(0, 0, 0))

            for dx in range(-bold_offset, bold_offset + 1):
                for dy in range(-bold_offset, bold_offset + 1):
                    draw.text((text_x + dx, text_y + dy), line, font=font, fill=(255, 255, 255))

            text_y += font.getbbox(line)[3] - font.getbbox(line)[1]

        return np.array(img_pil)
    

    frames = []
    for i, frame in enumerate(video.iter_frames(fps=fps, dtype="uint8")):
        timestamp = i / fps
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        for subtitle in subtitles:
            if subtitle["start"] <= timestamp <= subtitle["end"]:
                frame_rgb = draw_text(frame_rgb, subtitle["text"])

        frame_rgb = cv2.cvtColor(frame_rgb, cv2.COLOR_BGR2RGB)
        frames.append(frame_rgb)

    output_video_path = "./video_generation/video_with_subtitles.mp4"
    clip = ImageSequenceClip(frames, fps=fps)
    clip = clip.set_audio(video.audio)
    clip.write_videofile(output_video_path, codec="libx264", audio_codec="aac")

    print("Video processing complete. Saved as:", output_video_path)
    
        
    if os.path.exists(output_video_path):
        music_dir = "./video_generation/background_voices"
        music_path = os.path.join(music_dir, random.choice(os.listdir(music_dir)))
        output_path =  "./video_generation/final_video_with_music.mp4"

        music_vid = add_background_music(output_video_path, music_path, output_path)
        
    if music_vid:
        return True

