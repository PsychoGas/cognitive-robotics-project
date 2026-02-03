from PIL import Image
import os

INPUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(INPUT_DIR, "clean")
THRESHOLD = 128  # pixels below this -> black, above -> white

os.makedirs(OUTPUT_DIR, exist_ok=True)

for filename in sorted(os.listdir(INPUT_DIR)):
    if not filename.endswith(".gif"):
        continue

    img = Image.open(os.path.join(INPUT_DIR, filename))
    clean_frames = []
    durations = []

    frame_idx = 0
    while True:
        try:
            img.seek(frame_idx)
        except EOFError:
            break

        frame = img.convert("L")  # grayscale
        frame = frame.point(lambda p: 255 if p >= THRESHOLD else 0, mode="1")
        clean_frames.append(frame.convert("P"))
        durations.append(img.info.get("duration", 42))
        frame_idx += 1

    out_path = os.path.join(OUTPUT_DIR, filename)
    clean_frames[0].save(
        out_path,
        save_all=True,
        append_images=clean_frames[1:],
        duration=durations,
        loop=0,
    )
    print(f"{filename}: {frame_idx} frames -> {out_path}")
