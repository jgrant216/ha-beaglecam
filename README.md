# BeagleCam Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)

Custom integration to monitor your **Minton BeagleCam** (3D printer camera) inside [Home Assistant](https://www.home-assistant.io/).

---

## 📸 Features

- ✅ Connects to your BeagleCam via its local IP address or hostname
- ✅ Authenticates using your configured username and password
- ✅ Polls **camera information**, **print status**, **temperature data**
- ✅ Surfaces a camera feed from the BeagleCam, suitable for dashboards and AI processing
- ✅ Many sensors available, resembling OctoPrint's available sensors:
  - Printer status (idle, printing, paused, completed)
  - File name
  - Progress (%)
  - Job start time and estimated completion time
  - Nozzle/bed temps (current and target)
- ✅ Real-time updates every 10 seconds
- ✅ Fails gracefully and reconnects

---

## 🔧 Installation

### HACS (Custom Repo)
Until this is added to the default HACS list, install manually:

1. Go to **HACS → Integrations → 3 dots → Custom Repositories**
2. Add this repo: `https://github.com/jgrant216/ha-beaglecam`
3. Category: **Integration**
4. Install `BeagleCam`
5. Restart Home Assistant

---

## ⚙️ Configuration

1. Go to **Settings → Devices & Services**
2. Click **"Add Integration"**
3. Search for **"BeagleCam"**
4. Enter:
   - IP Address or Hostname
   - Username
   - Password

Home Assistant will validate the connection using `cmd: 100` (`check_user`).

---

## 🧪 Entity Example

After setup, you'll see a single BeagleCam device with 10 sensor entities, including:

- `binary_sensor.beaglecam_printing`: On/Off if printing
- `sensor.beaglecam_current_state`: Current printer state (idle, printing, paused, completed)
- `sensor.beaglecam_current_file`: Current file name
- `sensor.beaglecam_job_percentage`: Print progress percentage
- `sensor.beaglecam_job_start_time`: Start time of current job
- `sensor.beaglecam_job_estimated_finish_time`: Estimated time of completion
- `sensor.beaglecam_actual_nozzle_temp`: Current nozzle temperature
- `sensor.beaglecam_actual_bed_temp`: Current bed temperature
- `sensor.beaglecam_target_nozzle_temperature`: Target nozzle temperature
- `sensor.beaglecam_target_bed_temperature`: Target bed temperature

Plus, a camera entity: `camera.beaglecam_camera`