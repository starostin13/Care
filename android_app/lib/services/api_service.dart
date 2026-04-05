import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/alliance.dart';
import '../models/battle.dart';
import '../models/map_cell.dart';
import '../models/mission.dart';
import '../models/warmaster.dart';

/// Snapshot of all data required for offline mission generation,
/// returned by [GET /api/bootstrap].
class BootstrapData {
  final String generatedAt;
  final List<Alliance> alliances;
  final List<Warmaster> warmasters;
  final List<MapCell> mapCells;
  final List<MapEdge> mapEdges;
  final List<PendingMission> pendingMissions;

  const BootstrapData({
    required this.generatedAt,
    required this.alliances,
    required this.warmasters,
    required this.mapCells,
    required this.mapEdges,
    required this.pendingMissions,
  });

  factory BootstrapData.fromJson(Map<String, dynamic> json) {
    final map = json['map'] as Map<String, dynamic>? ?? {};
    return BootstrapData(
      generatedAt: json['generated_at'] as String? ?? '',
      alliances: (json['alliances'] as List<dynamic>? ?? [])
          .map((e) => Alliance.fromJson(e as Map<String, dynamic>))
          .toList(),
      warmasters: (json['warmasters'] as List<dynamic>? ?? [])
          .map((e) => Warmaster.fromJson(e as Map<String, dynamic>))
          .toList(),
      mapCells: (map['cells'] as List<dynamic>? ?? [])
          .map((e) => MapCell.fromJson(e as Map<String, dynamic>))
          .toList(),
      mapEdges: (map['edges'] as List<dynamic>? ?? [])
          .map((e) => MapEdge.fromJson(e as Map<String, dynamic>))
          .toList(),
      pendingMissions: (json['pending_missions'] as List<dynamic>? ?? [])
          .map((e) => PendingMission.fromJson(e as Map<String, dynamic>))
          .toList(),
    );
  }
}

class CreateMissionRequest {
  final String rules;
  final String attackerId;
  final String defenderId;

  const CreateMissionRequest({
    required this.rules,
    required this.attackerId,
    required this.defenderId,
  });

  Map<String, dynamic> toJson() => {
        'rules': rules,
        'attacker_id': attackerId,
        'defender_id': defenderId,
      };
}

class CreateMissionResponse {
  final int battleId;
  final Mission? mission;

  const CreateMissionResponse({required this.battleId, this.mission});

  factory CreateMissionResponse.fromJson(Map<String, dynamic> json) =>
      CreateMissionResponse(
        battleId: json['battle_id'] as int,
        mission: json['mission'] != null
            ? Mission.fromJson(json['mission'] as Map<String, dynamic>)
            : null,
      );
}

/// REST client that talks to the CareBot Flask API.
class ApiService {
  final String baseUrl;
  final http.Client _client;

  ApiService({required this.baseUrl, http.Client? client})
      : _client = client ?? http.Client();

  Uri _uri(String path) => Uri.parse('$baseUrl$path');

  Map<String, String> get _jsonHeaders => {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      };

  /// Fetches the full bootstrap snapshot for offline caching.
  Future<BootstrapData> fetchBootstrap() async {
    final response = await _client.get(_uri('/api/bootstrap'));
    _checkStatus(response, 200);
    final json = jsonDecode(response.body) as Map<String, dynamic>;
    return BootstrapData.fromJson(json);
  }

  /// Creates a new mission and battle for [request].
  Future<CreateMissionResponse> createMission(
      CreateMissionRequest request) async {
    final response = await _client.post(
      _uri('/api/missions'),
      headers: _jsonHeaders,
      body: jsonEncode(request.toJson()),
    );
    _checkStatus(response, 201);
    final json = jsonDecode(response.body) as Map<String, dynamic>;
    return CreateMissionResponse.fromJson(json);
  }

  /// Submits the result of [battleId] and applies map/reward consequences.
  Future<BattleResult> submitBattleResult({
    required int battleId,
    required int fstplayerScore,
    required int sndplayerScore,
    required String submitterId,
  }) async {
    final response = await _client.post(
      _uri('/api/battles/$battleId/result'),
      headers: _jsonHeaders,
      body: jsonEncode({
        'fstplayer_score': fstplayerScore,
        'sndplayer_score': sndplayerScore,
        'submitter_id': submitterId,
      }),
    );
    if (response.statusCode == 404) {
      return BattleResult(battleId: battleId, status: 'not_found');
    }
    if (response.statusCode == 409) {
      return BattleResult(battleId: battleId, status: 'already_confirmed');
    }
    _checkStatus(response, 200);
    final json = jsonDecode(response.body) as Map<String, dynamic>;
    return BattleResult.fromJson(json);
  }

  /// Submits multiple battle results in a single request.
  Future<List<BattleResult>> syncBattleResults(
      List<PendingBattleResultEntry> entries) async {
    final results =
        entries.map((e) => e.toJson()..remove('created_at')).toList();
    final response = await _client.post(
      _uri('/api/battles/sync'),
      headers: _jsonHeaders,
      body: jsonEncode({'results': results}),
    );
    _checkStatus(response, 200);
    final json = jsonDecode(response.body) as Map<String, dynamic>;
    return (json['results'] as List<dynamic>)
        .map((e) => BattleResult.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  void _checkStatus(http.Response response, int expected) {
    if (response.statusCode != expected) {
      String message;
      try {
        final body = jsonDecode(response.body) as Map<String, dynamic>;
        message = body['error']?.toString() ?? response.body;
      } catch (_) {
        message = response.body;
      }
      throw ApiException(statusCode: response.statusCode, message: message);
    }
  }
}

class ApiException implements Exception {
  final int statusCode;
  final String message;

  const ApiException({required this.statusCode, required this.message});

  @override
  String toString() => 'ApiException($statusCode): $message';
}
