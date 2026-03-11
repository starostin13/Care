import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:carebot_android/services/api_service.dart';
import 'package:carebot_android/models/alliance.dart';
import 'package:carebot_android/models/battle.dart';
import 'package:carebot_android/models/mission.dart';

void main() {
  group('ApiService', () {
    group('fetchBootstrap', () {
      test('parses bootstrap payload correctly', () async {
        final mockClient = MockClient((request) async {
          expect(request.url.path, '/api/bootstrap');
          return http.Response(
            jsonEncode({
              'generated_at': '2025-01-01T00:00:00Z',
              'alliances': [
                {'id': 1, 'name': 'Space Marines', 'color': '#0000FF', 'common_resource': 5},
              ],
              'warmasters': [
                {
                  'telegram_id': '42',
                  'alliance': 1,
                  'nickname': 'Commander',
                  'faction': 'Space Marines',
                  'language': 'ru',
                  'notifications_enabled': true,
                  'is_admin': false,
                },
              ],
              'map': {
                'cells': [
                  {'id': 10, 'planet_id': 1, 'patron': 1, 'state': null, 'has_warehouse': false},
                ],
                'edges': [
                  {'id': 1, 'left_hexagon': 1, 'right_hexagon': 2, 'state': null},
                ],
              },
              'pending_missions': [
                {
                  'id': 1,
                  'deploy': 'Strategic Reserves',
                  'rules': 'killteam',
                  'cell': 10,
                  'mission_description': 'Loot',
                  'created_date': '2025-01-01',
                },
              ],
            }),
            200,
          );
        });

        final api = ApiService(baseUrl: 'http://localhost', client: mockClient);
        final data = await api.fetchBootstrap();

        expect(data.generatedAt, '2025-01-01T00:00:00Z');
        expect(data.alliances.length, 1);
        expect(data.alliances.first.name, 'Space Marines');
        expect(data.warmasters.length, 1);
        expect(data.warmasters.first.nickname, 'Commander');
        expect(data.mapCells.length, 1);
        expect(data.mapCells.first.patron, 1);
        expect(data.mapEdges.length, 1);
        expect(data.pendingMissions.length, 1);
        expect(data.pendingMissions.first.rules, 'killteam');
      });

      test('throws ApiException on non-200 response', () async {
        final mockClient = MockClient((_) async =>
            http.Response(jsonEncode({'error': 'Server error'}), 500));

        final api = ApiService(baseUrl: 'http://localhost', client: mockClient);
        expect(() => api.fetchBootstrap(), throwsA(isA<ApiException>()));
      });
    });

    group('createMission', () {
      test('sends correct payload and parses response', () async {
        final mockClient = MockClient((request) async {
          expect(request.url.path, '/api/missions');
          final body = jsonDecode(request.body) as Map<String, dynamic>;
          expect(body['rules'], 'killteam');
          expect(body['attacker_id'], '1');
          expect(body['defender_id'], '2');
          return http.Response(
            jsonEncode({
              'battle_id': 99,
              'mission': {
                'id': 1,
                'deploy': 'Hammer & Anvil',
                'rules': 'killteam',
                'cell': 5,
                'mission_description': 'Loot',
                'winner_bonus': null,
                'status': 1,
                'created_date': '2025-01-01',
                'map_description': null,
                'reward_config': null,
              },
            }),
            201,
          );
        });

        final api = ApiService(baseUrl: 'http://localhost', client: mockClient);
        final response = await api.createMission(
          const CreateMissionRequest(
            rules: 'killteam',
            attackerId: '1',
            defenderId: '2',
          ),
        );

        expect(response.battleId, 99);
        expect(response.mission, isNotNull);
        expect(response.mission!.missionDescription, 'Loot');
        expect(response.mission!.isActive, true);
      });

      test('throws ApiException on 400 response', () async {
        final mockClient = MockClient((_) async => http.Response(
              jsonEncode({'error': 'rules, attacker_id, and defender_id are required'}),
              400,
            ));

        final api = ApiService(baseUrl: 'http://localhost', client: mockClient);
        expect(
          () => api.createMission(
              const CreateMissionRequest(rules: '', attackerId: '', defenderId: '')),
          throwsA(isA<ApiException>()),
        );
      });
    });

    group('submitBattleResult', () {
      test('returns applied result on success', () async {
        final mockClient = MockClient((_) async => http.Response(
              jsonEncode({
                'status': 'applied',
                'battle_id': 10,
                'mission_id': 1,
                'mission_status': 3,
                'rewards': {'xp': 50},
              }),
              200,
            ));

        final api = ApiService(baseUrl: 'http://localhost', client: mockClient);
        final result = await api.submitBattleResult(
          battleId: 10,
          fstplayerScore: 8,
          sndplayerScore: 4,
          submitterId: '42',
        );

        expect(result.isApplied, true);
        expect(result.battleId, 10);
        expect(result.rewards, {'xp': 50});
      });

      test('returns not_found on 404', () async {
        final mockClient = MockClient((_) async =>
            http.Response(jsonEncode({'status': 'not_found', 'battle_id': 99}), 404));

        final api = ApiService(baseUrl: 'http://localhost', client: mockClient);
        final result = await api.submitBattleResult(
          battleId: 99,
          fstplayerScore: 0,
          sndplayerScore: 0,
          submitterId: '42',
        );
        expect(result.isNotFound, true);
      });

      test('returns already_confirmed on 409', () async {
        final mockClient = MockClient((_) async => http.Response(
              jsonEncode({'status': 'already_confirmed', 'battle_id': 5}),
              409,
            ));

        final api = ApiService(baseUrl: 'http://localhost', client: mockClient);
        final result = await api.submitBattleResult(
          battleId: 5,
          fstplayerScore: 3,
          sndplayerScore: 7,
          submitterId: '42',
        );
        expect(result.isAlreadyConfirmed, true);
      });
    });

    group('syncBattleResults', () {
      test('sends all entries and returns parsed results', () async {
        final mockClient = MockClient((request) async {
          final body = jsonDecode(request.body) as Map<String, dynamic>;
          final results = body['results'] as List;
          expect(results.length, 2);
          return http.Response(
            jsonEncode({
              'results': [
                {'status': 'applied', 'battle_id': 1, 'mission_id': 10},
                {'status': 'not_found', 'battle_id': 2},
              ],
            }),
            200,
          );
        });

        final api = ApiService(baseUrl: 'http://localhost', client: mockClient);
        final results = await api.syncBattleResults([
          PendingBattleResultEntry(
              battleId: 1, fstplayerScore: 5, sndplayerScore: 3, submitterId: '1'),
          PendingBattleResultEntry(
              battleId: 2, fstplayerScore: 0, sndplayerScore: 7, submitterId: '2'),
        ]);

        expect(results.length, 2);
        expect(results[0].isApplied, true);
        expect(results[1].isNotFound, true);
      });
    });
  });

  group('Alliance.fromJson', () {
    test('parses all fields', () {
      final a = Alliance.fromJson({
        'id': 3,
        'name': 'Necrons',
        'color': '#00FF00',
        'common_resource': 10,
      });
      expect(a.id, 3);
      expect(a.name, 'Necrons');
      expect(a.color, '#00FF00');
      expect(a.commonResource, 10);
    });
  });

  group('Mission', () {
    test('status helpers work correctly', () {
      const active = Mission(
          id: 1, deploy: 'd', rules: 'r', missionDescription: 'm', status: 1);
      const confirmed = Mission(
          id: 2, deploy: 'd', rules: 'r', missionDescription: 'm', status: 3);
      expect(active.isActive, true);
      expect(active.isCompleted, false);
      expect(confirmed.isCompleted, true);
    });
  });

  group('PendingBattleResultEntry', () {
    test('round-trips through JSON', () {
      final original = PendingBattleResultEntry(
        battleId: 7,
        fstplayerScore: 10,
        sndplayerScore: 5,
        submitterId: 'user123',
        createdAt: DateTime(2025, 6, 15, 12, 0, 0),
      );
      final json = original.toJson();
      final restored = PendingBattleResultEntry.fromJson(json);
      expect(restored.battleId, original.battleId);
      expect(restored.fstplayerScore, original.fstplayerScore);
      expect(restored.sndplayerScore, original.sndplayerScore);
      expect(restored.submitterId, original.submitterId);
      expect(restored.createdAt, original.createdAt);
    });
  });
}
