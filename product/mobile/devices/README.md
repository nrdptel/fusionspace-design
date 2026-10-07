# Real screens

Screenshots of the reference code running in the sample apps on simulators and emulators, captured 2026-10-06. The drawn
mock-ups next to this folder show the intent; these show what the code actually does. Built by `tools/build/kit_devices.py`
from `source/product/devices/`, where `devices.json` records each capture's device, OS, size and what it shows.

![Real screens](preview.png)

| File | Device | Shows |
|---|---|---|
| `ios-island-flight.png` | iPhone 17 Pro, iOS 27.0 (24A434) | Live Activity in the Dynamic Island in flight (compact), -activity flight, over Settings |
| `ios-island-pad.png` | iPhone 17 Pro, iOS 27.0 (24A434) | Live Activity in the Dynamic Island at the pad (compact), -activity pad, over Settings |
| `ios-pad.png` | iPhone 17 Pro, iOS 27.0 (24A434) | Pad screen (field theme), sample app, -screen pad |
| `ios-track.png` | iPhone 17 Pro, iOS 27.0 (24A434) | Track screen, system dark appearance, -screen track |
| `phone-pad.png` | Pixel 10, Android 17, API 37.0 (Google APIs arm64 system image r6, build CE2A.260420.019) | Pad, field theme |
| `phone-track.png` | Pixel 10, Android 17, API 37.0 (Google APIs arm64 system image r6, build CE2A.260420.019) | Track, dark |
| `phone-live-update.png` | Pixel 10, Android 17, API 37.0 (Google APIs arm64 system image r6, build CE2A.260420.019) | Live Update in the notification shade (MetricStyle, semantic style SAFE) |

The sample apps are in `source/product/samples/` (their READMEs list what running them found and fixed).
