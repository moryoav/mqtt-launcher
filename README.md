# mqtt-launcher

A lightweight Dockerized “launcher” that executes shell commands in response to incoming MQTT messages.

**Repo:** [https://github.com/moryoav/mqtt-launcher](https://github.com/moryoav/mqtt-launcher)

---

## 📦 Features

* Configure arbitrary topic→payload→command mappings
* Publish status (running/stopped/dead) to a retained MQTT topic
* **Home Assistant MQTT-Discovery**: self-advertise buttons, switches or sensors on each connect
* Runs under Docker (no external scripts needed)

---

## ⚙️ Configuration

Edit `launcher.conf` (or provide your own via `MQTTLAUNCHERCONFIG`):

```

# Basic MQTT connection

mqtt_broker     = 'mqtt.example.local'
mqtt_port       = 1883
mqtt_username   = 'your_user'
mqtt_password   = 'your_pass'

# Prefix for all topics

topic\_prefix    = 'mqtt-launcher-1'

# Optional overrides

#mqtt_qos       = 1
#mqtt_keepalive = 60
```

### Topic-to-Command Mapping

Define `topiclist` as:

```
topiclist = {
  "some/topic": {
    "payload1": [ "cmd", "arg1", "arg2" ],
    None:       [ "cmd", "@!@" ]        # default command, substitute payload at @!@
  },
  …
}
```

---

## 🤖 Home Assistant Auto-Discovery

Add an `ha_discovery` array to your config. On every connect, `mqtt-launcher` will publish each entry to:

```
homeassistant/<component>/<node_id>/<object_id>/config
```

Example:

```
ha_discovery = [
  {
    "component":  "button",                # e.g. 'switch', 'sensor', 'light', …
    "node_id":    "example_device",
    "object_id":  "restart_button",
    "config": {
      "name":          "Restart Pi",
      "unique_id":     "pi_restart_button",
      "command_topic": "reboot/pi",
      "payload_press": "reboot",
      "device": {
        "identifiers":  ["DEVICE12345"],
        "manufacturer": "YourCompany",
        "model":        "ModelX",
        "name":         "Example Pi"
      }
    }
  }
]
```

> **Why this helps:**
> • No manual `mosquitto_pub` step
> • Retained config → survives restarts
> • Auto-reconnect safe

---

## 🐳 Docker

### Build

```
docker build -t moryoav/mqtt-launcher .
```

### Run

Minimal:

```
docker run -d \
  -v /path/to/launcher.conf:/mqtt-launcher/launcher.conf:ro \   --network your_net \
  moryoav/mqtt-launcher
  
```
**To allow `chroot /host ... reboot`** (e.g. your `/reboot/pi` button) you can mount the host root and use host networking & privileged mode:

```
docker run -d \
  -v /:/host:ro \
  -v /path/to/launcher.conf:/mqtt-launcher/launcher.conf:ro \   --network host \   --privileged \
  moryoav/mqtt-launcher`
```
---

## 🚀 Usage

1. Customize `launcher.conf`

2. Start container (see above)

3. Send MQTT messages to your topics, e.g.:

   ```
   mosquitto_pub -t reboot/pi -m reboot
   ```

4. Check `/mqtt-launcher/logfile` inside the container (or wherever you pointed `logfile`) for output.

---

## 📄 License

BSD-style (see header in `mqtt-launcher.py`).
