# BeagleCam Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)

Custom integration to monitor your **Minton BeagleCam** (3D printer camera) inside [Home Assistant](https://www.home-assistant.io/).

---

## 📸 Features

- ✅ Connects to your BeagleCam via its local IP address
- ✅ Authenticates using your printer's username and password
- ✅ Polls **print status** (`cmd: 318`)
- ✅ Polls **temperature data** (`cmd: 302`)
- ✅ Shows data in a **single sensor** with rich attributes:
  - File name
  - Progress (%)
  - Time left
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
   - IP Address
   - Username
   - Password

Home Assistant will validate the connection using `cmd: 312` (`get_prconnectstate`).

---

## 🧪 Entity Example

After setup, you'll see a single sensor entity:

**Entity ID**: `sensor.beaglecam_print_status`  
**State**: Current print progress (e.g., `42`)  
**Attributes**:

```yaml
file_name: benchy.gcode
progress: 42
time_left: 1680
tempture_noz: 205
tempture_bed: 60
des_tempture_noz: 210
des_tempture_bed: 60
