import sys, soundfile as sf, os
from kokoro_onnx import Kokoro
from misaki import ja
M = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")
k = Kokoro(f"{M}/kokoro-v1.0.onnx", f"{M}/voices-v1.0.bin")
g2p = ja.JAG2P()
voice, speed, out = sys.argv[1], float(sys.argv[2]), sys.argv[3]
text = sys.argv[4]
r = g2p(text); ph = r[0] if isinstance(r, tuple) else r
print(text, "->", ph)
samples, sr = k.create(ph, voice=voice, speed=speed, lang="ja", is_phonemes=True)
sf.write(out, samples, sr); print(out, len(samples)/sr)
