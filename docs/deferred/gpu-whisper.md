# Deferred: GPU speech-to-text (whisper.cpp on CUDA)

**Status:** paused on 1 October 2026, during build step 7 (AI adapters). Not blocking any later step.
**Update (same day):** the background build **finished** — image `saathi-whisper-cuda:v1.9.4` (4.5 GB) exists. Resume at section 4 step **b**.
**Why paused:** building the GPU Whisper image took many hours on a slow connection and was still compiling, so we moved on to step 8.
**Impact while paused:** voice input works on CPU with Whisper `small`, but **Marathi accuracy is poor** and transcription is slower than real time (numbers below). Fix this before any demo that relies on Marathi voice.

---

## 1. Why we wanted this

Benchmark of the current setup (Whisper `small`, CPU, 12 threads) on 24 real recorded clips from Google FLEURS (8 each Hindi, Marathi, Tamil), measured with character error rate (CER):

| Language | CER | WER | Notes |
|---|---|---|---|
| Hindi | 24.3% | 55.5% | usable but rough |
| Marathi | **68.8%** | 105.6% | **unusable** — often outputs multilingual garbage (e.g. `suit ических means of ˃ iende…`) |
| Tamil | 21.5% | 80.7% | rough |
| **All** | **38.7%** | 78.1% | **0.8× real time** (354 s to transcribe 298 s of speech) |

A GPU makes a much larger, more accurate model practical. The target is **`large-v3-turbo` (q5_0, 574 MB)** — the newest large Whisper model, which is far better on Indian languages — with `medium` (q5_0, 539 MB) as the comparison. Both files are already downloaded to `backend/ml_models/whisper/`.

## 2. What we tried, and where it got stuck

1. **Official prebuilt image `ghcr.io/ggml-org/whisper.cpp:main-cuda`** (6 GB download).
   It found the GPU (`ggml_cuda_init: found 1 CUDA devices`) and then **crashed with exit code 132 (SIGILL, illegal instruction)**.
   Cause: the image is compiled with CPU instructions (AVX-512) that this laptop's **AMD Ryzen 7 7735HS** does not have. The image has been deleted.
2. **Build our own image** — `backend/docker/whisper/Dockerfile` (written and committed).
   It pins whisper.cpp **v1.9.4**, CUDA **13.0.3**, compiles for AVX2 CPUs (`-DGGML_AVX512=OFF`) and GPU architectures `75;80;86;89` (RTX 4050 = 89), and builds only `whisper-server` as one static binary.
   - First attempt failed: the 2.3 GB CUDA `devel` base layer download was cut off (`short read: unexpected EOF`).
   - Second attempt: the base image eventually downloaded (docker reported ~29,760 s for that step on this connection), the source cloned, and **compilation reached ~65%** (the CUDA kernels are the slow part) when we paused.
   - The build was left running in the background; **it may have finished on its own.** Check first (section 4).

## 3. What is already done (no need to redo)

- **Code is ready for both modes.** `backend/app/ai/stt.py`:
  - `WHISPER_SERVER_URL` set → sends audio to `whisper-server` over HTTP (`POST /inference`, `language=auto`, `response_format=verbose_json`), re-runs with the right language if Whisper picked one outside en/hi/mr/ta, and applies the hi/mr tie-break with the user's language.
  - `WHISPER_SERVER_URL` blank (current) → in-process CPU with `WHISPER_MODEL_PATH`.
  - `/health` pings the server in server mode (`stt.check_available()`).
- **Models downloaded:** `ggml-small.bin` (in use), `ggml-medium-q5_0.bin`, `ggml-large-v3-turbo-q5_0.bin`.
- **Benchmark tooling in the repo:**
  - `backend/scripts/benchmarks/fetch_fleurs.py` — downloads the 24 test clips + reference transcripts (clips already present in `backend/scripts/benchmarks/data/fleurs/`, git-ignored).
  - `backend/scripts/benchmarks/bench_whisper.py` — CER/WER and speed, CPU or GPU server.
  - `backend/scripts/benchmarks/bench_llm.py` — the LLM benchmark used for the model switch (section 7).

## 4. How to finish it (≈20–30 minutes once the image exists)

All commands from `backend/` unless noted.

**a. Is the image built?**
```sh
docker image ls saathi-whisper-cuda
```
If it is missing, rebuild (Docker caches the finished layers, so it resumes from the compile step):
```sh
docker build -t saathi-whisper-cuda:v1.9.4 docker/whisper
```
To speed up the compile on this machine only, build just for the RTX 4050: add `--build-arg CUDA_ARCHITECTURES=89`.

**b. Check the server's JSON fields.** The adapter reads `detected_language` (or `language`), `detected_language_probability`, `language_probabilities`, `text` and `segments[].avg_logprob`. Confirm against the real response and adjust `_transcribe_server` in `app/ai/stt.py` if names differ:
```sh
docker run -d --name whisper-test --gpus all -p 8081:8080 -v "$PWD/ml_models/whisper:/models:ro" \
  saathi-whisper-cuda:v1.9.4 -m /models/ggml-large-v3-turbo-q5_0.bin -fa
curl -s localhost:8081/inference -F file=@scripts/benchmarks/data/fleurs/mr_in/<any>.wav \
  -F language=auto -F response_format=verbose_json | head -c 1500
```

**c. Benchmark** (stop the test container between models):
```sh
.venv/Scripts/python -m scripts.benchmarks.bench_whisper gpu http://localhost:8081 "large-v3-turbo (GPU)"
```
Repeat with `ggml-medium-q5_0.bin` and `ggml-small.bin`. Compare against the CPU baseline in section 1.

**d. Decide.** Switch if the GPU model clearly beats the baseline (expect large CER drops, especially Marathi) **and** total GPU memory still fits (section 5). Otherwise keep CPU.

**e. Wire it in** — add to `docker-compose.dev.yml`:
```yaml
  whisper:
    build: ./docker/whisper
    image: saathi-whisper-cuda:v1.9.4
    restart: unless-stopped
    command: ["-m", "/models/${WHISPER_SERVER_MODEL:-ggml-large-v3-turbo-q5_0.bin}", "-fa"]
    ports:
      - "${WHISPER_PORT:-8081}:8080"
    volumes:
      - ./ml_models/whisper:/models:ro
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
```
Then in `backend/.env`: `WHISPER_SERVER_URL=http://localhost:8081` and update `.env.example`, `ml_models/README.md`, `README.md` and `ASSUMPTIONS.md` (Step 7 section).

**f. Verify:** `python -m app.ai.demo stt`, and `/api/v1/health` shows `"stt": true` with the container up and `false` with it stopped.

## 5. GPU memory budget (RTX 4050 Laptop, 6 GB)

| Model | Approx. GPU memory |
|---|---|
| LLM `gemma4:e4b-it-qat` | 3.1 GB (measured, fully on GPU) |
| Embeddings `bge-m3` | ~1.2 GB |
| Whisper `large-v3-turbo` q5_0 | ~1 GB (to measure) |
| **Total** | **~5.3 GB of 6 GB** — tight but expected to fit |

If it doesn't fit, options in order: use Whisper `medium` q5_0; run `bge-m3` on CPU; or fall back to the smaller LLM `gemma4:e2b-it-qat` (1.7 GB, already downloaded, scored 19/20 but thinner answers).

## 6. Alternatives if the custom build keeps failing

- **faster-whisper (CTranslate2) with CUDA** via pip (`faster-whisper` + `nvidia-cublas-cu12` + `nvidia-cudnn-cu12`) in the backend venv. Easier on Windows, but it is not whisper.cpp (the spec names whisper.cpp / "Whisper GGUF"); would need a third backend in `stt.py` and a note in `ASSUMPTIONS.md`.
- **Build pywhispercpp from source with CUDA** on Windows — needs the CUDA Toolkit and Visual Studio Build Tools (several GB); avoids Docker.
- **Larger model on CPU** — `medium`/`large-v3-turbo` on CPU is likely 2–3× slower than `small`, which is already slower than real time. Not recommended.

## 7. Related decision made in the same session: LLM switched to Gemma 4

This part is **complete**. Benchmarked with `scripts/benchmarks/bench_llm.py` on Saathi tasks in hi/mr/ta, plus a human read of every output:

| Model | Score | Avg latency | GPU memory | Verdict |
|---|---|---|---|---|
| qwen2.5:7b-instruct (old) | 16/20, 1 invalid JSON | 11.2 s | 5.4 GB (21% on CPU) | Tamil near-gibberish, stilted Marathi |
| **gemma4:e4b-it-qat (chosen)** | **20/20** | **2.3 s** | **3.1 GB** | natural hi/mr/ta |
| gemma4:e2b-it-qat (fallback) | 19/20 | 2.4 s | 1.7 GB | one misleading Marathi claim about SIP |
| qwen3.5:4b | 20/20 automated | 2.3 s | 3.1 GB | **rejected:** Tamil scam advice said to tap the link |

Also added `LLM_REASONING_EFFORT=none` (sent as `reasoning_effort`): Gemma 4 is a "thinking" model and returned invalid structured output until thinking was turned off. qwen2.5 and qwen3.5 were deleted from Ollama; gemma4:e2b was kept as the fallback.

## Update (Step 15): Marathi on CPU is much better than the original benchmark suggested
The 68.8% Marathi CER above came from Whisper small's **native Marathi decoder**, which fails outright on about half of real clips. Decoding Marathi speech with the **Hindi** decoder (same Devanagari script) gives **42% CER and is 5× faster**; the API now does this by default (`WHISPER_MR_DECODE_AS=hi`). GPU Whisper is therefore less urgent for Marathi. When it is resumed, benchmark both `WHISPER_MR_DECODE_AS=mr` and `=hi` with the larger model and keep whichever is better.
