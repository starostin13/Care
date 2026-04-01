import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/alliance.dart';
import '../models/battle.dart';
import '../models/map_cell.dart';
import '../models/mission.dart';
import '../models/warmaster.dart';
import 'api_service.dart';

/// Caches bootstrap data locally so the app works when offline.
///
/// Data is stored as JSON in [SharedPreferences].  Call [refresh] to pull
/// fresh data from the server, and [load] to restore from local storage.
class CacheService {
  static const _keyBootstrapJson = 'bootstrap_json';
  static const _keyPendingResults = 'pending_results_json';
  static const _keyBaseUrl = 'server_base_url';
  static const _defaultBaseUrl = 'http://192.168.1.125:5555';

  final SharedPreferences _prefs;

  CacheService(this._prefs);

  // ── Server URL ──────────────────────────────────────────────────────────

  String get baseUrl => _prefs.getString(_keyBaseUrl) ?? _defaultBaseUrl;

  Future<void> setBaseUrl(String url) async {
    await _prefs.setString(_keyBaseUrl, url);
  }

  // ── Bootstrap snapshot ───────────────────────────────────────────────────

  /// In-memory snapshot to avoid repeated JSON decoding on every getter call.
  BootstrapData? _bootstrapSnapshot;

  /// Returns the memoized bootstrap snapshot, loading from storage if needed.
  BootstrapData? get _cachedBootstrap {
    _bootstrapSnapshot ??= load();
    return _bootstrapSnapshot;
  }

  /// Invalidates the in-memory snapshot so the next getter call re-reads from
  /// storage (called automatically after refresh/save).
  void _invalidateBootstrapCache() {
    _bootstrapSnapshot = null;
  }

  /// Fetches fresh data from [apiService] and stores it locally.
  Future<BootstrapData> refresh(ApiService apiService) async {
    final data = await apiService.fetchBootstrap();
    await _saveBootstrap(data);
    _invalidateBootstrapCache();
    return data;
  }

  /// Loads the last cached bootstrap snapshot.  Returns `null` when there is
  /// no cached data yet.
  BootstrapData? load() {
    final raw = _prefs.getString(_keyBootstrapJson);
    if (raw == null) return null;
    try {
      final json = jsonDecode(raw) as Map<String, dynamic>;
      return BootstrapData.fromJson(json);
    } catch (_) {
      return null;
    }
  }

  Future<void> _saveBootstrap(BootstrapData data) async {
    final json = {
      'generated_at': data.generatedAt,
      'alliances': data.alliances.map((a) => a.toJson()).toList(),
      'warmasters': data.warmasters.map((w) => w.toJson()).toList(),
      'map': {
        'cells': data.mapCells.map((c) => c.toJson()).toList(),
        'edges': data.mapEdges.map((e) => e.toJson()).toList(),
      },
      'pending_missions': data.pendingMissions
          .map((m) => {
                'id': m.id,
                'deploy': m.deploy,
                'rules': m.rules,
                'cell': m.cell,
                'mission_description': m.missionDescription,
                'created_date': m.createdDate,
              })
          .toList(),
    };
    await _prefs.setString(_keyBootstrapJson, jsonEncode(json));
  }

  // ── Offline pending battle results ───────────────────────────────────────

  /// All battle results recorded locally and not yet synced to the server.
  List<PendingBattleResultEntry> loadPendingResults() {
    final raw = _prefs.getString(_keyPendingResults);
    if (raw == null) return [];
    try {
      return (jsonDecode(raw) as List<dynamic>)
          .map((e) =>
              PendingBattleResultEntry.fromJson(e as Map<String, dynamic>))
          .toList();
    } catch (_) {
      return [];
    }
  }

  /// Saves a battle result locally for later sync when offline.
  Future<void> addPendingResult(PendingBattleResultEntry entry) async {
    final current = loadPendingResults();
    current.add(entry);
    await _savePendingResults(current);
  }

  /// Removes successfully synced entries.
  Future<void> removeSyncedResults(List<int> battleIds) async {
    final current = loadPendingResults();
    final remaining =
        current.where((e) => !battleIds.contains(e.battleId)).toList();
    await _savePendingResults(remaining);
  }

  Future<void> _savePendingResults(
      List<PendingBattleResultEntry> entries) async {
    await _prefs.setString(
      _keyPendingResults,
      jsonEncode(entries.map((e) => e.toJson()).toList()),
    );
  }

  // ── Convenience getters ──────────────────────────────────────────────────

  List<Alliance> get cachedAlliances => _cachedBootstrap?.alliances ?? [];
  List<Warmaster> get cachedWarmasters => _cachedBootstrap?.warmasters ?? [];
  List<MapCell> get cachedMapCells => _cachedBootstrap?.mapCells ?? [];
  List<MapEdge> get cachedMapEdges => _cachedBootstrap?.mapEdges ?? [];
  List<PendingMission> get cachedPendingMissions =>
      _cachedBootstrap?.pendingMissions ?? [];
}
