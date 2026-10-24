# RoadVision AI

AI-powered road damage detection dashboard for potholes, cracks, and manholes.

## Project overview
RoadVision AI is a computer vision dashboard that lets users upload a road image, run AI-based inspection, and review detections with confidence scores.

## Included files
- `README.md` — project documentation
- `static/` — dashboard frontend files
- `main.py` — FastAPI backend
- `best.pt` — trained YOLO model
- `road_damage_comparison.csv` — sample comparison data
- `runs/` — generated inference output

## Core features
- upload road images
- analyze damage with YOLOv8
- filter detections by confidence threshold
- visualize results in the dashboard
- send results to automation tools such as n8n

## Notes
This repository is prepared for clean GitHub upload without generated local artifacts.
