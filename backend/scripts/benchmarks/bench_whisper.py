"""Whisper accuracy/speed on real FLEURS speech (hi/mr/ta, 8 clips each).

Run from backend/ after `python -m scripts.benchmarks.fetch_fleurs`:
  .venv/Scripts/python -m scripts.benchmarks.bench_whisper cpu ml_models/whisper/ggml-small.bin "small (CPU)"
  .venv/Scripts/python -m scripts.benchmarks.bench_whisper gpu http://localhost:8081 "large-v3-turbo (GPU)"
Language is given (the app passes the user's language as a hint), so this measures transcription.
See docs/deferred/gpu-whisper.md.
"""

import csv
import re
import sys
import time
import unicodedata
from pathlib import Path

import httpx

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).parent / "data" / "fleurs"
LANGS = {"hi_in": "hi", "mr_in": "mr", "ta_in": "ta"}


def norm(s: str) -> str:
    s = unicodedata.normalize("NFC", s).lower()
    s = "".join(" " if unicodedata.category(c).startswith("P") else c for c in s)
    return re.sub(r"\s+", " ", s).strip()


def edit_distance(a, b) -> int:
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i]
        for j, y in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x != y)))
        prev = cur
    return prev[-1]


def refs(lang_dir: Path) -> dict[str, str]:
    out = {}
    with open(lang_dir / "dev.tsv", encoding="utf-8") as f:
        for row in csv.reader(f, delimiter="\t", quoting=csv.QUOTE_NONE):
            out[row[1]] = row[3]
    return out


def make_cpu(model_path: str):
    from pywhispercpp.model import Model

    from app.ai.stt import read_wav_16k

    m = Model(model_path, n_threads=12, print_realtime=False, print_progress=False, print_timestamps=False,
              redirect_whispercpp_logs_to=None)

    def run(wav: Path, lang: str) -> str:
        audio = read_wav_16k(wav)
        return " ".join(s.text.strip() for s in m.transcribe(audio, language=lang))
    return run


def make_gpu(url: str):
    client = httpx.Client(timeout=120)

    def run(wav: Path, lang: str) -> str:
        with open(wav, "rb") as f:
            r = client.post(f"{url}/inference", files={"file": (wav.name, f, "audio/wav")},
                            data={"language": lang, "response_format": "json", "temperature": "0.0"})
        r.raise_for_status()
        return r.json()["text"]
    return run


def main():
    mode, target = sys.argv[1], sys.argv[2]
    label = sys.argv[3] if len(sys.argv) > 3 else Path(target).name
    run = make_cpu(target) if mode == "cpu" else make_gpu(target)
    # warm-up
    first = next((ROOT / "hi_in").glob("*.wav"))
    run(first, "hi")
    total_c = total_ce = total_w = total_we = 0
    total_audio = total_time = 0.0
    for d, lang in LANGS.items():
        r = refs(ROOT / d)
        c = ce = w = we = 0
        t_lang = 0.0
        for wav in sorted((ROOT / d).glob("*.wav")):
            ref = norm(r[wav.name])
            t = time.perf_counter()
            hyp = norm(run(wav, lang))
            t_lang += time.perf_counter() - t
            import wave
            with wave.open(str(wav)) as wf:
                total_audio += wf.getnframes() / wf.getframerate()
            ce += edit_distance(ref, hyp); c += len(ref)
            we += edit_distance(ref.split(), hyp.split()); w += len(ref.split())
        print(f"  {label:28} {lang}: CER {100*ce/c:5.1f}%  WER {100*we/w:5.1f}%  time {t_lang:5.1f}s for 8 clips")
        total_c += c; total_ce += ce; total_w += w; total_we += we; total_time += t_lang
    print(f"SUMMARY {label}: CER {100*total_ce/total_c:.1f}%  WER {100*total_we/total_w:.1f}%  "
          f"speed {total_audio/total_time:.1f}x realtime ({total_time:.0f}s for {total_audio:.0f}s audio)")
    # example
    wav = sorted((ROOT / "mr_in").glob("*.wav"))[0]
    print("  mr sample REF:", norm(refs(ROOT / "mr_in")[wav.name])[:120])
    print("  mr sample HYP:", norm(run(wav, "mr"))[:120])


if __name__ == "__main__":
    main()
