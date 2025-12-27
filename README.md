# Bass Booster Web App

A user-friendly Flask web application for boosting bass in audio files.

## Features

- Upload audio files (WAV, FLAC, OGG, MP3)
- Adjustable parameters: Cutoff frequency, Filter order, Bass gain
- Visualize time and frequency domain plots
- Download the processed bass-boosted audio

## Installation

1. Clone or download the project.
2. Create a virtual environment: `python -m venv .venv`
3. Activate the virtual environment: `.venv\Scripts\activate` (Windows)
4. Install dependencies: `pip install -r requirements.txt`

## Usage

1. Run the app: `python app.py`
2. Open your browser and go to `http://127.0.0.1:5000/`
3. Upload an audio file and adjust the parameters as desired.
4. Click "Boost Bass!" to process.
5. View the plots and download the output.

## Dependencies

- Flask
- NumPy
- SoundFile
- SciPy
- Matplotlib
- Werkzeug

## Notes

- For MP3 support, ensure you have the appropriate codecs installed (e.g., via conda or system packages).
- Processing large files may take time depending on filter order.
