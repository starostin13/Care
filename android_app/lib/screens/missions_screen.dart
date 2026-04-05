import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../models/mission.dart';
import 'home_screen.dart';

class MissionsScreen extends StatefulWidget {
  const MissionsScreen({super.key});

  @override
  State<MissionsScreen> createState() => _MissionsScreenState();
}

class _MissionsScreenState extends State<MissionsScreen> {
  static const _rules = [
    'killteam',
    'boarding_action',
    'combat_patrol',
    'wh40k',
    'battlefleet_gothica',
  ];

  String? _selectedRules;
  String? _attackerId;
  String? _defenderId;
  bool _loading = false;
  String? _error;
  CreateMissionResponse? _result;

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    final warmasters = state.cache.cachedWarmasters;

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            'Generate Mission',
            style: Theme.of(context).textTheme.headlineSmall,
          ),
          const SizedBox(height: 16),
          DropdownButtonFormField<String>(
            decoration: const InputDecoration(
              labelText: 'Rules',
              border: OutlineInputBorder(),
            ),
            value: _selectedRules,
            items: _rules
                .map((r) => DropdownMenuItem(value: r, child: Text(r)))
                .toList(),
            onChanged: (v) => setState(() => _selectedRules = v),
          ),
          const SizedBox(height: 12),
          DropdownButtonFormField<String>(
            decoration: const InputDecoration(
              labelText: 'Attacker',
              border: OutlineInputBorder(),
            ),
            value: _attackerId,
            items: warmasters
                .map((w) => DropdownMenuItem(
                      value: w.telegramId,
                      child: Text(w.displayName),
                    ))
                .toList(),
            onChanged: (v) => setState(() => _attackerId = v),
          ),
          const SizedBox(height: 12),
          DropdownButtonFormField<String>(
            decoration: const InputDecoration(
              labelText: 'Defender',
              border: OutlineInputBorder(),
            ),
            value: _defenderId,
            items: warmasters
                .map((w) => DropdownMenuItem(
                      value: w.telegramId,
                      child: Text(w.displayName),
                    ))
                .toList(),
            onChanged: (v) => setState(() => _defenderId = v),
          ),
          const SizedBox(height: 16),
          if (_error != null)
            Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: Text(
                _error!,
                style: TextStyle(
                    color: Theme.of(context).colorScheme.error),
              ),
            ),
          ElevatedButton.icon(
            onPressed:
                (_loading || _selectedRules == null || _attackerId == null || _defenderId == null)
                    ? null
                    : _submit,
            icon: _loading
                ? const SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.add),
            label: const Text('Generate Mission'),
          ),
          const SizedBox(height: 24),
          if (_result != null) _buildResult(_result!),
          const Divider(),
          Text(
            'Pending Missions (${state.cache.cachedPendingMissions.length})',
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: 8),
          ...state.cache.cachedPendingMissions.map(
            (m) => Card(
              child: ListTile(
                title: Text(m.missionDescription),
                subtitle: Text('${m.rules} | ${m.deploy}'),
                trailing: m.cell != null ? Text('Cell #${m.cell}') : null,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _submit() async {
    final state = context.read<AppState>();
    setState(() {
      _loading = true;
      _error = null;
      _result = null;
    });
    try {
      final response = await state.api.createMission(CreateMissionRequest(
        rules: _selectedRules!,
        attackerId: _attackerId!,
        defenderId: _defenderId!,
      ));
      setState(() => _result = response);
    } on ApiException catch (e) {
      setState(() => _error = 'Server error ${e.statusCode}: ${e.message}');
    } catch (e) {
      setState(() => _error = 'Error: $e');
    } finally {
      setState(() => _loading = false);
    }
  }

  Widget _buildResult(CreateMissionResponse result) {
    final mission = result.mission;
    return Card(
      color: Colors.green.shade50,
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('✅ Mission created!',
                style: Theme.of(context).textTheme.titleMedium),
            Text('Battle ID: ${result.battleId}'),
            if (mission != null) ...[
              Text('Mission: ${mission.missionDescription}'),
              Text('Deploy: ${mission.deploy}'),
              Text('Rules: ${mission.rules}'),
              if (mission.mapDescription != null)
                Text('Map: ${mission.mapDescription}'),
            ],
          ],
        ),
      ),
    );
  }
}
