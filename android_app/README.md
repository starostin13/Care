# CareBot Android App

Flutter companion application for the CareBot Warhammer 40K campaign management system.

## Features

- **Bootstrap cache** — fetches and stores alliances, warmasters, map cells and pending missions for offline use
- **Mission generation** — select two players and a ruleset to generate a new mission via the backend API
- **Battle result recording** — submit battle scores immediately or save offline for later sync
- **Offline sync** — batch upload all locally saved results in a single request

## Getting Started

### Prerequisites

- [Flutter SDK](https://docs.flutter.dev/get-started/install) ≥ 3.10
- Android Studio or VS Code with Flutter extension

### Installation

```bash
cd android_app
flutter pub get
flutter run
```

### Configuration

Set the server URL in the **Settings** tab to point to your CareBot backend:

```
http://<your-server-ip>:5555
```

The default is `http://192.168.1.125:5555`.

## Architecture

```
lib/
├── main.dart                 # Entry point & app initialisation
├── models/
│   ├── alliance.dart         # Alliance data model
│   ├── battle.dart           # BattleResult & PendingBattleResultEntry
│   ├── map_cell.dart         # MapCell & MapEdge
│   ├── mission.dart          # Mission & PendingMission
│   └── warmaster.dart        # Warmaster (player) model
├── services/
│   ├── api_service.dart      # REST client (http)
│   └── cache_service.dart    # Local cache (shared_preferences)
└── screens/
    ├── home_screen.dart      # Bootstrap dashboard + AppState provider
    ├── missions_screen.dart  # Mission generation form
    ├── battle_result_screen.dart  # Record / save offline
    ├── sync_screen.dart      # Upload pending offline results
    └── settings_screen.dart  # Server URL configuration
```

## Backend API

The app communicates with the Flask backend exposed by the CareBot bot container:

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/bootstrap` | GET | Fetch full game state snapshot for offline caching |
| `/api/missions` | POST | Create mission + battle between two warmasters |
| `/api/battles/<id>/result` | POST | Submit battle scores and apply consequences |
| `/api/battles/sync` | POST | Batch submit multiple offline results |

## Running Tests

```bash
cd android_app
flutter test
```
