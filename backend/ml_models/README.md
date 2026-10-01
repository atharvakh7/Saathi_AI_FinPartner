# ml_models/

Local model files (not committed). Paths are configured in `backend/.env`. Download commands used for local setup are below.

| Folder | Contents | Env var | Source | Licence |
|---|---|---|---|---|
| `whisper/` | `ggml-small.bin` (466 MB; in use, CPU) | `WHISPER_MODEL_PATH` | huggingface.co/ggerganov/whisper.cpp | MIT |
| `whisper/` | `ggml-large-v3-turbo-q5_0.bin`, `ggml-medium-q5_0.bin` (for GPU; see `docs/deferred/gpu-whisper.md`) | — | same | MIT |
| `piper/` | `en_US-lessac-medium` | `PIPER_VOICE_EN` | huggingface.co/rhasspy/piper-voices | Blizzard 2013 dataset licence (**non-commercial**) |
| `piper/` | `hi_IN-pratham-medium` (male) | `PIPER_VOICE_HI` | same | CC BY-NC-SA 4.0 (**non-commercial**) |
| `piper/` | `mr_IN-google-medium` (9 speakers; speaker 0 used) | `PIPER_VOICE_MR` | same | CC BY-SA 4.0 (attribution required) |
| — | No Piper voice exists for Tamil | `PIPER_VOICE_TA` blank | — | App falls back to on-device TTS (spec A8) |
| `tessdata/` | `eng`, `hin`, `mar`, `tam` `.traineddata` | `TESSDATA_PREFIX` | github.com/tesseract-ocr/tessdata | Apache 2.0 |
| `scam_distilbert/` | Fine-tuned `distilbert-base-multilingual-cased` (optional, not included) | `SCAM_MODEL_DIR` | — | — |

**Before any commercial launch, replace the English and Hindi voices** with commercially licensed ones (or train your own Piper voice), and credit the Marathi voice (CC BY-SA) in the app's About screen.

```sh
HF=https://huggingface.co/rhasspy/piper-voices/resolve/main
curl -L -o whisper/ggml-small.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin
for v in en/en_US/lessac/medium/en_US-lessac-medium hi/hi_IN/pratham/medium/hi_IN-pratham-medium mr/mr_IN/google/medium/mr_IN-google-medium; do
  n=$(basename $v); curl -L -o piper/$n.onnx $HF/$v.onnx; curl -L -o piper/$n.onnx.json $HF/$v.onnx.json
done
for l in eng hin mar tam; do curl -L -o tessdata/$l.traineddata https://github.com/tesseract-ocr/tessdata/raw/main/$l.traineddata; done
```

Tesseract itself: Windows `winget install UB-Mannheim.TesseractOCR`; Linux `apt install tesseract-ocr`.
