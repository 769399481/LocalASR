"""Encode authored Windows TTS as a local browser/video test fixture in asr."""
from pathlib import Path
import sys
import wave
import av
import numpy as np
from PIL import Image, ImageDraw

if Path(sys.prefix).name.lower() != "asr":
    raise RuntimeError("Use Conda asr")
directory = Path(__file__).resolve().parents[1] / "validation/phase11/fixtures"
with wave.open(str(directory / "meeting.wav")) as source:
    rate = source.getframerate()
    samples = np.frombuffer(source.readframes(source.getnframes()), dtype="<i2")
duration = len(samples) / rate
with av.open(str(directory / "meeting.mp4"), "w") as output:
    video = output.add_stream("libx264", rate=10)
    video.width, video.height, video.pix_fmt = 960, 540, "yuv420p"
    audio = output.add_stream("aac", rate=rate)
    audio.layout = "mono"
    picture = Image.new("RGB", (960, 540), "#20384a")
    draw = ImageDraw.Draw(picture)
    draw.text((80, 100), "LocalASR: authored meeting-style test", fill="white", font_size=30)
    draw.text((80, 160), "Synthetic voices / alternating turns / short pauses", fill="white", font_size=24)
    draw.text((80, 210), "No microphone capture. No real meeting participants.", fill="white", font_size=24)
    for i in range(int(duration * 10) + 1):
        frame = av.VideoFrame.from_image(picture)
        frame.pts = i
        for packet in video.encode(frame):
            output.mux(packet)
    for packet in video.encode():
        output.mux(packet)
    for offset in range(0, len(samples), 1024):
        frame = av.AudioFrame.from_ndarray(samples[offset:offset+1024].reshape(1,-1), format="s16", layout="mono")
        frame.sample_rate, frame.pts = rate, offset
        for packet in audio.encode(frame):
            output.mux(packet)
    for packet in audio.encode():
        output.mux(packet)
(directory / "player.html").write_text('''<!doctype html><meta charset="utf-8"><title>LocalASR meeting-style validation</title>
<style>body{background:#172430;color:white;font:22px sans-serif;margin:30px}video{width:90vw;max-height:80vh}</style>
<h1>Authored meeting-style test video</h1><p>Synthetic English dialogue. Audio plays through the default output device.</p>
<video src="meeting.mp4" controls loop></video>''', encoding="utf-8")
print(f"Fixture: {duration:.2f}s, {(directory/'meeting.mp4').stat().st_size} bytes")
