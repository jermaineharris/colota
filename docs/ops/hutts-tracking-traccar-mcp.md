# Hutts Tracking + Traccar (garage-one)

Private GPS stack for the **Hutts Tracking** Android app (Colota fork).

**MCP:** `GET /cursor/runbook/hutts-tracking-traccar`  
**Wiki:** https://docs.huttsenterprises.com/infra/hutts-tracking-traccar  
**App package:** `com.huttsmedia.huttstracking`  
**Source (Gitea):** https://git.huttsenterprises.com/infra/hutts-tracking  
**Upstream:** Colota (AGPLv3) — keep license + attribution.

## Where it runs

| Piece | Host | Notes |
|-------|------|--------|
| Traccar Docker | `hetzner-fleet-garage-one` | HDD box (`sda`/`sdb` Toshiba 3.6T). **Not** utility-one, **not** Asustor. |
| Compose | `/opt/hutts-tracking-traccar/docker-compose.yml` | `restart: unless-stopped` |
| Data (HDD) | `/var/lib/garage-data2/hutts-tracking-traccar/{data,logs,conf}` | Symlinked from compose dir as `storage` |
| Tailscale IP | `100.117.121.99` | **Only** bind address for published ports |
| Web UI | `http://100.117.121.99:8082` | Tailscale required |
| OsmAnd ingest | `http://100.117.121.99:5055/` | What the phone POSTs/GETs |
| Admin password file | `/root/.config/hutts-tracking-traccar.admin.pass` | mode `600` — do not commit |

Public WAN ports are **not** opened. Phone and operators need Tailscale.

## Hutts Tracking phone settings

| Setting | Value |
|---------|--------|
| Template | Traccar |
| Server URL | `http://100.117.121.99:5055/` |
| HTTP method | GET (OsmAnd) |
| Custom field `id` | `huttstracking` (must match Traccar device `uniqueId`) |
| Recommended preset | **Balanced** (30s interval, ≥5m distance, batched sync) |

### Do not use Instant while stationary

**Instant** (5s / 0m distance) records GPS jitter as new points. Sitting still can produce ~100 near-duplicate locations in minutes. Defaults in the fork are **Balanced**.

If local history is already polluted: clear locations/queue in-app (or wipe app data) after switching preset, then restart tracking with Tailscale on.

## Device / login

| Item | Value |
|------|--------|
| Traccar device name | Hutts Tracking Pixel |
| `uniqueId` | `huttstracking` |
| Web login email | `admin@huttsmedia.com` |
| Web password | read from `/root/.config/hutts-tracking-traccar.admin.pass` on garage-one |
| Registration | **off** (`web.registration=false` in `conf/traccar.xml`) |

## Ops commands (garage-one)

```bash
ssh hetzner-fleet-garage-one
cd /opt/hutts-tracking-traccar
docker compose ps
docker compose logs -f --tail=100
docker compose restart
# password (root only):
sudo cat /root/.config/hutts-tracking-traccar.admin.pass
```

Smoke OsmAnd (should return HTTP 200 when device id exists):

```bash
NOW=$(date +%s)000
curl -sS -o /dev/null -w "%{http_code}\n" \
  "http://100.117.121.99:5055/?id=huttstracking&lat=27.95&lon=-82.46&timestamp=$NOW&altitude=10&speed=0&bearing=0&accuracy=5&batt=80"
```

## Build / install app

Monorepo under `apps/mobile` (React Native). GMS release:

```bash
cd apps/mobile/android
./gradlew assembleGmsRelease -PreactNativeArchitectures=arm64-v8a
# APK: app/build/outputs/apk/gms/release/app-gms-arm64-v8a-release.apk
adb install -r app/build/outputs/apk/gms/release/app-gms-arm64-v8a-release.apk
```

Debug builds need Metro unless you install the release APK.

## Related docs (do not confuse)

| Doc | What it is |
|-----|------------|
| `GET /cursor/runbook/fleet-ops-mobile` | Hutts **Ops** dashboard APK (`com.huttsmedia.ops`) |
| `GET /cursor/runbook/fleet-analytics-mobile` | Hutts **Analytics** mobile |
| `GET /cursor/runbook/fleet-publisher-android` | Offline publisher readers |
| This runbook | **GPS tracking** phone app + Traccar |

## AGPL note

Hutts Tracking is a private fork of Colota (AGPLv3). Network use of a modified version requires offering corresponding source to users who interact with it over the network. Keep LICENSE and upstream copyright headers.
