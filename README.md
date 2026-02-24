# content-engine host

Host repository that coordinates all four pipeline services.

## Run full pipeline

```bash
python run_pipeline.py \
  --clips /path/to/clip1.mp4 /path/to/clip2.mp4 \
  --music /path/to/song.mp3 \
  --run-dir ./runs/local-run
```

Artifacts written into the run directory:
- `clip-analysis.json`
- `music-analysis.json`
- `timeline.json`
- `final.mp4`
- `run-manifest.json`
