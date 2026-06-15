# Arduino Oscilloscope

A real-time desktop oscilloscope for Arduino ADC data — built with **PyQt6** + **pyqtgraph**.

---

## Features

| Category | Features |
|---|---|
| **Signal** | Scrolling time-domain waveform, FFT spectrum |
| **Mapping** | Linear ADC→voltage mapping (customisable range, tick-mark toggle) |
| **Trigger** | Rising/Falling edge, draggable trigger line |
| **Vertical** | Y min/max range, V/div spinbox, dV/dt overlay |
| **Timebase** | Time/div, configurable buffer size & sample rate |
| **Measurements** | Freq, Period, Vpp, Vmax, Vmin, Vrms, Duty Cycle, dV/dt RMS |
| **Export** | Waveform CSV, FFT CSV, Screenshot (PNG), WAV |
| **Settings** | Persistent JSON settings, theme colour picker |
| **Shortcuts** | `Space` → Run/Pause, `Ctrl+S` → Save CSV, `Ctrl+Q` → Quit |

---

## Quick Start

```bash
pip install -r requirements.txt
python main.py
```

## Arduino Sketch (minimal)

```cpp
void setup() { Serial.begin(115200); }
void loop()  { Serial.println(analogRead(A0)); }
```

## File Structure

```
arduino_oscilloscope/
├── main.py                  # Entry point
├── requirements.txt
├── config/
│   └── settings.py          # Persistent AppSettings dataclass
├── core/
│   ├── serial_worker.py     # QThread serial reader
│   ├── ring_buffer.py       # Thread-safe circular buffer
│   ├── dsp.py               # FFT, RMS, Vpp, frequency, dV/dt
│   └── trigger.py           # Edge trigger detection
├── ui/
│   ├── main_window.py       # QMainWindow — assembles everything
│   ├── waveform_widget.py   # Time-domain pyqtgraph widget
│   ├── fft_widget.py        # Frequency-domain pyqtgraph widget
│   ├── controls_panel.py    # Left-side scrollable controls
│   ├── measurements_panel.py# Bottom measurement bar
│   ├── settings_dialog.py   # Theme/colour preferences dialog
│   └── styles.qss           # Dark QSS theme
├── io/
│   └── file_exporter.py     # CSV / PNG / WAV export
├── logs/
└── storage/                 # settings.json + exported files
```

## Settings Persistence

All settings (colours, mapping, trigger, timebase) are auto-saved to
`storage/settings.json` on every change and on application close.
Delete this file to reset to defaults.
