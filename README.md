# arm-compose

Docker Compose setup for [Automatic Ripping Machine (ARM)](https://github.com/automatic-ripping-machine/automatic-ripping-machine).

## Setup

1. Copy `.env.example` to `.env` and adjust values for your environment:
   ```sh
   cp .env.example .env
   ```

2. Edit `.env`:
   - Set `DOCKER_DATA_PATH` to the host directory where ARM config, media, logs, and db will live
   - Set `ARM_NAS_COMPLETED_PATH` and `ARM_NAS_MUSIC_PATH` to your NAS mount points (must be direct mounts — no symlinks)
   - Set `TZ` to your local timezone

3. Start the stack:
   ```sh
   docker compose up -d
   ```

## Devices

The compose file maps three Blu-ray drives and their corresponding SCSI generic devices. Adjust the `devices` list in `compose.yaml` to match your actual drive layout:

| Device | Purpose |
|--------|---------|
| `/dev/sr0`–`/dev/sr2` | Optical drives |
| `/dev/sg1`–`/dev/sg3` | SCSI generic (required for MakeMKV) |

## Volumes

| Host path | Container path | Purpose |
|-----------|---------------|---------|
| `$DOCKER_DATA_PATH/config` | `/etc/arm/config` | ARM configuration |
| `$DOCKER_DATA_PATH/media` | `/home/arm/media` | Working/staging media |
| `$DOCKER_DATA_PATH/logs` | `/home/arm/logs` | ARM logs |
| `$DOCKER_DATA_PATH/db` | `/home/arm/db` | ARM database |
| `$ARM_NAS_COMPLETED_PATH` | `/home/arm/media/completed` | Completed video to NAS |
| `$ARM_NAS_MUSIC_PATH` | `/home/arm/music` | Ripped audio CDs to NAS |