# arm-for-raspberrypi

Automatische CD-Ripping-Maschine für Raspberry Pi 5 unter Linux mit lokaler Web-UI.

## Web-UI

Die Weboberfläche läuft standardmäßig auf Port **9090**:

```text
http://raspberrypi.local:9090
```

Start im Entwicklungsmodus:

```bash
PYTHONPATH=src python3 -m arm_ripper.server
```

## Installation auf Raspberry Pi OS

```bash
sudo apt update
sudo apt install -y python3 abcde cdparanoia lame eject cd-discid
sudo mkdir -p /opt/arm-for-raspberrypi /srv/music /var/lib/arm-ripper
sudo cp -r src static systemd README.md pyproject.toml /opt/arm-for-raspberrypi/
sudo cp systemd/arm-ripper.service /etc/systemd/system/arm-ripper.service
sudo systemctl daemon-reload
sudo systemctl enable --now arm-ripper.service
```

## Geplante und implementierte Funktionen

- Automatisches Erkennen angeschlossener Linux-Laufwerke unter `/sys/block/sr*`.
- Unterstützung für mehrere CD-/DVD-Laufwerke gleichzeitig.
- Web-UI mit Übersicht aller erkannten Laufwerke.
- Öffnen und Schließen einzelner Laufwerksschubladen über die Web-UI.
- Starten eines Ripping-Jobs pro Laufwerk über die Web-UI.
- Rippen über `abcde`, `cdparanoia` und `lame` in MP3.
- Anzeige des aktuellen Ripping-Status je Laufwerk in der Web-UI.
- Laden von CD-Metadaten über die von `abcde` unterstützten Quellen.
- Automatisches Auswerfen einer CD nach erfolgreichem Rip.
- Fehleranzeige pro Laufwerk, z. B. bei fehlenden Linux-Programmen oder Ripping-Fehlern.
- Protokollierung aller Ripping-Jobs in einer JSON-Statusdatei.

## Multi-Laufwerk-Unterstützung

Die Anwendung verwaltet mehrere optische Laufwerke. Jedes erkannte Laufwerk bekommt einen eigenen Status und kann unabhängig bedient werden.

Pro Laufwerk werden angezeigt:

- Gerätename, z. B. `/dev/sr0` oder `/dev/sr1`.
- Hersteller-/Modellname, sofern verfügbar.
- Zustand: bereit, geöffnet, geschlossen, rippt, fertig oder Fehler.
- Aktueller Track/Fortschritt, sofern verfügbar.
- Schaltflächen zum Öffnen, Schließen und Rippen starten.

## API-Endpunkte

| Methode | Pfad | Zweck |
| --- | --- | --- |
| `GET` | `/api/status` | Gesamtstatus mit Laufwerken, Jobs und Bibliothek anzeigen. |
| `GET` | `/api/drives` | Alle erkannten Laufwerke anzeigen. |
| `POST` | `/api/drives/{id}/open` | Laufwerk öffnen. |
| `POST` | `/api/drives/{id}/close` | Laufwerk schließen. |
| `POST` | `/api/drives/{id}/rip` | Ripping für ein Laufwerk starten. |
| `GET` | `/api/jobs` | Aktuelle und frühere Ripping-Jobs anzeigen. |
| `GET` | `/api/library` | Fertig gerippte Alben anzeigen. |

## Konfiguration

| Umgebungsvariable | Standardwert |
| --- | --- |
| `ARM_RIPPER_HOST` | `0.0.0.0` |
| `ARM_RIPPER_PORT` | `9090` |
| `ARM_RIPPER_MUSIC_DIR` | `./music` |
| `ARM_RIPPER_STATE_FILE` | `./state.json` |
| `ARM_RIPPER_STATIC_DIR` | `./static` |
| `ARM_RIPPER_MP3_BITRATE` | `320k` |
