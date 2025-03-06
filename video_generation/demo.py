import os
import whisper

os.environ["PATH"] += os.pathsep + r"D:\Tessaract\Projects API\twitter bot\twitter_bot\video generation\ffmpeg\bin"

model = whisper.load_model("small")
result = model.transcribe("sample.mp3")
print(result["text"])