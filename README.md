# 🔬 Arduino Oscilloscope — Real-Time Serial Plotter (Professional Modular GUI Tool)

![Python](https://img.shields.io/badge/Python-3.9+-blue)
![PyQt6](https://img.shields.io/badge/PyQt6-GUI-green)
![pyqtgraph](https://img.shields.io/badge/pyqtgraph-Realtime%20Plotting-orange)
![License](https://img.shields.io/badge/License-MIT-lightgrey)
![Status](https://img.shields.io/badge/Status-Active-success)

A **professional modular Python desktop application** that turns any Arduino + ADC into a real-time digital oscilloscope — live waveform, FFT spectrum, trigger, and full measurement suite, all in a dark-themed PyQt6 GUI.

This project follows a clean **core / ui / file_io** architecture, includes **persistent JSON settings**, and is built to be extended (new probes, new measurements, new export formats) without touching the GUI code.

---

## 🎯 Why This Tool Exists

Most "Arduino oscilloscope" scripts on GitHub are:

* ❌ A single 200-line script with everything hardcoded
* ❌ matplotlib-based (too slow for real-time)
* ❌ No trigger, no FFT, no measurements
* ❌ Settings reset every run

This tool fixes all of that — `pyqtgraph` for smooth real-time rendering, a proper trigger system, live FFT with peak detection, and a settings system that remembers your setup between sessions.

⚠️ **Designed for low-voltage ADC signals (0–5V range). Never connect mains voltage directly to an Arduino analog pin.**

---

## 🎥 Demo Video

[![Watch the Demo](https://img.youtube.com/vi/YOUTUBE_VIDEO_ID_HERE/0.jpg)](https://www.youtube.com/watch?v=YOUTUBE_VIDEO_ID_HERE)

---

## 🖼️ GUI Preview

### 🔹 Main Window — Live Waveform + FFT

![Main GUI Screenshot](https://github.com/user-attachments/assets/PLACEHOLDER_MAIN)

### 🔹 Settings Dialog — Theme Customization

![Settings Screenshot](https://github.com/user-attachments/assets/PLACEHOLDER_SETTINGS)

---

## ✨ Core Features

* 🖥️ Dark-themed desktop GUI (PyQt6 + pyqtgraph, no matplotlib)
* 📈 Real-time scrolling waveform (33 ms refresh / ~30 FPS)
* 📊 Live FFT spectrum with peak frequency annotation
* 🎯 Rising/falling edge trigger with draggable trigger line
* 🔁 Linear ADC→voltage mapping (customizable, enable/disable toggle)
* 📐 Y-range, V/div, and dV/dt overlay (merged vertical controls)
* ⏱️ Time/div, buffer size (512–4096), and sample rate controls
* 📋 Live measurement bar — Freq, Period, Vpp, Vmax, Vmin, Vrms, Duty Cycle, dV/dt
* 💾 Export waveform/FFT to CSV, screenshot to PNG, raw data to WAV
* ⚙️ Settings dialog — persistent theme & color customization (JSON)
* ⌨️ Run/Pause toggle via toolbar button or Spacebar
* 🧩 Modular architecture (`core/`, `ui/`, `file_io/`, `config/`)
* 🛠 Production-style codebase with full docstrings

---

## 🧠 Architecture Overview

```
GUI (PyQt6 + pyqtgraph)
   │
   ├── main_window.py   → Assembles all panels, refresh loop (QTimer)
   │
   ├── controls_panel.py → Connection, mapping, timebase, trigger, FFT settings
   │
   ├── waveform_widget.py → Time-domain plot + trigger line
   │
   ├── fft_widget.py     → Frequency-domain plot + peak label
   │
   ├── measurements_panel.py → Live readout bar
   │
   ├── core/serial_worker.py → QThread serial reader + ADC→V mapping
   │
   ├── core/dsp.py       → FFT, RMS, Vpp, frequency, duty cycle, dV/dt
   │
   ├── core/trigger.py   → Edge-trigger detection
   │
   ├── core/ring_buffer.py → Thread-safe circular sample buffer
   │
   ├── file_io/file_exporter.py → CSV / PNG / WAV export
   │
   └── config/settings.py → Persistent AppSettings (JSON)
```

Flow:

```
Arduino → Serial → SerialWorker (QThread) → RingBuffer → DSP/Trigger → Plots/Measurements
```

---

## 📂 Project Structure

```
oscilloscope-serial-plotter/
│
├── main.py                   # Entry point
├── requirements.txt
├── icon.png                  # App icon (taskbar + title bar)
│
├── config/
│   └── settings.py           # Persistent AppSettings dataclass
│
├── core/
│   ├── serial_worker.py      # QThread serial reader
│   ├── ring_buffer.py        # Thread-safe circular buffer
│   ├── dsp.py                # FFT, RMS, Vpp, frequency, dV/dt
│   └── trigger.py            # Edge trigger detection
│
├── ui/
│   ├── main_window.py        # QMainWindow — assembles everything
│   ├── waveform_widget.py    # Time-domain pyqtgraph widget
│   ├── fft_widget.py         # Frequency-domain pyqtgraph widget
│   ├── controls_panel.py     # Left-side scrollable controls
│   ├── measurements_panel.py # Bottom measurement bar
│   ├── settings_dialog.py    # Theme/color preferences dialog
│   └── styles.qss            # Dark QSS theme
│
├── file_io/
│   └── file_exporter.py      # CSV / PNG / WAV export
│
├── logs/
├── storage/                  # settings.json + exported files
└── README.md
```

---

## ⚙️ Tech Stack

| Layer        | Technology     |
| ------------ | -------------- |
| GUI          | PyQt6          |
| Plotting     | pyqtgraph      |
| Serial I/O   | pyserial       |
| DSP / Math   | NumPy          |
| Audio Export | soundfile      |
| Persistence  | JSON (built-in)|

---

## 🚀 Installation

### 1️⃣ Clone repo

```bash
git clone https://github.com/ar-titumir/oscilloscope-serial-plotter.git
cd oscilloscope-serial-plotter
```

### 2️⃣ Create virtual environment

```bash
python -m venv venv
venv\Scripts\activate
```

### 3️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ Run Application

```bash
python main.py
```

---

## 🖥️ How to Use

### 🔹 Connect to Arduino

1. Select COM port (refresh with ⟳ if not listed)
2. Select baud rate (9600 / 115200 / 250000)
3. Click **Connect**

### 🔹 Configure Signal Mapping

1. Enable/disable the **Signal Mapping** toggle
2. Set ADC range (default `0 → 1023`) and Volt range (default `0 → 5`)
3. Click **Apply Mapping**

### 🔹 Adjust Display

* **Timebase** → Time/div, buffer size, sample rate
* **Vertical / dV/dt** → Y min/max, V/div, dV/dt overlay + threshold
* **Trigger** → Enable, set level (drag the red line on the plot), choose Rising/Falling edge

### 🔹 Run / Pause

* Click the toolbar **Run/Pause** button, or press **Spacebar**

---

## 🔌 Arduino Sketch (minimal)

```cpp
void setup() {
  Serial.begin(115200);
}

void loop() {
  Serial.println(analogRead(A0));
}
```

---

## 🧩 Modular Design Philosophy

This project is structured like a real software project:

| Module                   | Purpose                          |
| ------------------------- | --------------------------------- |
| main.py                   | App launcher + icon/theme setup   |
| core/serial_worker.py     | Serial I/O + ADC→V conversion     |
| core/dsp.py               | Signal processing & measurements  |
| core/trigger.py           | Trigger detection                 |
| core/ring_buffer.py       | Thread-safe sample storage        |
| ui/*                      | All GUI panels & widgets          |
| file_io/file_exporter.py  | CSV / PNG / WAV export             |
| config/settings.py        | Persistent settings (JSON)        |

Benefits:

* Easier debugging
* Easier expansion (new probes, new measurements)
* Cleaner code
* Production ready
* Scalable

---

## 💾 Settings Persistence

All settings (colors, mapping, trigger, timebase, theme) are auto-saved to
`storage/settings.json` on every change and on application close.

Delete this file to reset everything to defaults.

---

## ⌨️ Keyboard Shortcuts

| Shortcut   | Action            |
| ---------- | ----------------- |
| `Space`    | Run / Pause       |
| `Ctrl + S` | Save Waveform CSV |
| `Ctrl + P` | Save Screenshot   |
| `Ctrl + Q` | Quit              |

---

## 🛣 Roadmap

Future improvements:

* Multi-channel support
* Cursors / delta measurements
* XY (Lissajous) mode
* Persistence / waveform afterglow
* Auto-scale button
* Config file export/import
* EXE build
* Dark/light theme presets

---

## ⚠️ Important Notes

* Keep your Arduino on a fixed, known sample rate for accurate frequency/FFT readings
* ADC input range is 0–5V (Uno/Nano) — do not exceed this without a voltage divider
* COM port must not be in use by Arduino IDE Serial Monitor while connected
* Windows, Linux, and macOS supported

---

## 👨‍💻 Author

**ar_titumir**
GitHub: [https://github.com/ar-titumir](https://github.com/ar-titumir)

If this project helped you, give it a ⭐

## 📜 License

This project is licensed under the MIT License.

See the LICENSE file for details.
