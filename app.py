import os
import numpy as np
import soundfile as sf
from scipy.signal import firwin, lfilter, resample
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from flask import Flask, request, render_template, send_file, redirect, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'static/outputs'
PLOT_FOLDER = os.path.join(app.root_path, 'static', 'images')
ALLOWED_EXTENSIONS = {'wav', 'flac', 'ogg', 'mp3'}  # soundfile supports these

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['PLOT_FOLDER'] = PLOT_FOLDER
app.config['PLOT_FOLDER'] = PLOT_FOLDER

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(PLOT_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# =============================== 
# AUDIO PROCESSING FUNCTION
# ===============================
def bass_booster(input_file, Fs, cutoff, filter_order, bass_gain):
    x, fs = sf.read(input_file)

    # Stereo → Mono
    if x.ndim > 1:
        x = np.mean(x, axis=1)

    if fs != Fs:
        num_samples = int(len(x) * Fs / fs)
        x = resample(x, num_samples)

    x = x / np.max(np.abs(x)) * 0.9

    lpf = firwin(filter_order + 1, cutoff, fs=Fs)
    x_bass = lfilter(lpf, 1.0, x)

    y = x + (bass_gain - 1) * x_bass

    y = np.clip(y, -1.0, 1.0)

    return x, x_bass, y

# ===============================
# FFT FUNCTION
# ===============================
def plot_fft(signal, Fs, title, filename):
    plt.figure(figsize=(8, 6))
    fft_vals = np.abs(np.fft.rfft(signal))
    freqs = np.fft.rfftfreq(len(signal), 1 / Fs)
    plt.plot(freqs, fft_vals)
    plt.xlim(0, 2000)
    plt.title(title)
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Magnitude")
    plt.savefig(filename)
    plt.close()

# ===============================
# COMBINED TIME + FREQUENCY PLOTS
# ===============================
def plot_time_and_frequency(x, x_bass, y, Fs, plot_folder, session_id):
    time = np.arange(len(x)) / Fs

    # Time domain plots - separate images
    plt.figure(figsize=(10, 4))
    plt.plot(time[:min(5000, len(time))], x[:min(5000, len(x))])
    plt.title("Original Audio (Time)")
    plt.xlabel("Time (s)")
    plt.ylabel("Amplitude")
    time_orig = os.path.join(plot_folder, f'time_original_{session_id}.png')
    plt.savefig(time_orig)
    plt.close()

    plt.figure(figsize=(10, 4))
    plt.plot(time[:min(5000, len(time))], x_bass[:min(5000, len(x_bass))])
    plt.title("Extracted Bass (Time)")
    plt.xlabel("Time (s)")
    plt.ylabel("Amplitude")
    time_bass = os.path.join(plot_folder, f'time_bass_{session_id}.png')
    plt.savefig(time_bass)
    plt.close()

    plt.figure(figsize=(10, 4))
    plt.plot(time[:min(5000, len(time))], y[:min(5000, len(y))])
    plt.title("Bass Boosted Output (Time)")
    plt.xlabel("Time (s)")
    plt.ylabel("Amplitude")
    time_boost = os.path.join(plot_folder, f'time_boosted_{session_id}.png')
    plt.savefig(time_boost)
    plt.close()

    # Frequency domain plots
    plot_fft(x, Fs, "Original Spectrum", os.path.join(plot_folder, f'original_fft_{session_id}.png'))
    plot_fft(x_bass, Fs, "Bass Spectrum", os.path.join(plot_folder, f'bass_fft_{session_id}.png'))
    plot_fft(y, Fs, "Boosted Spectrum", os.path.join(plot_folder, f'boosted_fft_{session_id}.png'))

    return f'images/time_original_{session_id}.png', f'images/time_bass_{session_id}.png', f'images/time_boosted_{session_id}.png', f'original_fft_{session_id}.png', f'bass_fft_{session_id}.png', f'boosted_fft_{session_id}.png'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(input_path)

        # Get parameters
        Fs = 44100
        cutoff = int(request.form['cutoff'])
        filter_order = int(request.form['filter_order'])
        bass_gain = float(request.form['bass_gain'])

        # Process
        x, x_bass, y = bass_booster(input_path, Fs, cutoff, filter_order, bass_gain)

        # Save output
        output_filename = f"bass_boosted_{filename}"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        sf.write(output_path, y, Fs)

        # Generate plots
        session_id = str(hash(filename))  # Simple session id
        time_orig, time_bass, time_boost, orig_fft, bass_fft, boost_fft = plot_time_and_frequency(x, x_bass, y, Fs, app.config['PLOT_FOLDER'], session_id)

        return render_template('result.html', 
                               time_orig=time_orig,
                               time_bass=time_bass,
                               time_boost=time_boost,
                               orig_fft=orig_fft,
                               bass_fft=bass_fft,
                               boost_fft=boost_fft,
                               output_file=output_filename)

    return redirect(request.url)

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(os.path.join(app.config['OUTPUT_FOLDER'], filename), as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)