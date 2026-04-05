import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/battle.dart';
import '../services/api_service.dart';
import 'home_screen.dart';

class SyncScreen extends StatefulWidget {
  const SyncScreen({super.key});

  @override
  State<SyncScreen> createState() => _SyncScreenState();
}

class _SyncScreenState extends State<SyncScreen> {
  bool _syncing = false;
  String? _error;
  List<_SyncResult>? _lastSyncResults;

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    final pending = state.cache.loadPendingResults();

    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            'Sync Offline Results',
            style: Theme.of(context).textTheme.headlineSmall,
          ),
          const SizedBox(height: 8),
          Text(
            '${pending.length} pending result(s) waiting to be synced.',
            style: Theme.of(context).textTheme.bodyMedium,
          ),
          const SizedBox(height: 16),
          if (_error != null)
            Card(
              color: Theme.of(context).colorScheme.errorContainer,
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Text(_error!),
              ),
            ),
          ElevatedButton.icon(
            onPressed:
                (pending.isEmpty || _syncing) ? null : () => _sync(state),
            icon: _syncing
                ? const SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.cloud_upload),
            label: const Text('Sync Now'),
          ),
          const SizedBox(height: 24),
          Expanded(
            child: ListView(
              children: [
                if (pending.isNotEmpty) ...[
                  Text('Pending:',
                      style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: 8),
                  ...pending.map(
                    (e) => Card(
                      child: ListTile(
                        leading: const Icon(Icons.pending),
                        title: Text('Battle #${e.battleId}'),
                        subtitle: Text(
                            '${e.fstplayerScore} : ${e.sndplayerScore}  —  ${e.submitterId}'),
                        trailing: Text(
                          _formatDate(e.createdAt),
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                      ),
                    ),
                  ),
                ],
                if (_lastSyncResults != null) ...[
                  const SizedBox(height: 16),
                  Text('Last sync results:',
                      style: Theme.of(context).textTheme.titleMedium),
                  const SizedBox(height: 8),
                  ..._lastSyncResults!.map(
                    (r) => Card(
                      color: r.success ? Colors.green.shade50 : Colors.red.shade50,
                      child: ListTile(
                        leading: Icon(
                          r.success ? Icons.check_circle : Icons.error,
                          color: r.success ? Colors.green : Colors.red,
                        ),
                        title: Text('Battle #${r.battleId}'),
                        subtitle: Text(r.status),
                      ),
                    ),
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _sync(AppState state) async {
    final pending = state.cache.loadPendingResults();
    if (pending.isEmpty) return;

    setState(() {
      _syncing = true;
      _error = null;
      _lastSyncResults = null;
    });

    try {
      final results = await state.api.syncBattleResults(pending);
      final syncResults = results.map((r) {
        return _SyncResult(
          battleId: r.battleId,
          status: r.status,
          success: r.isApplied || r.isAlreadyConfirmed,
        );
      }).toList();

      final syncedIds = syncResults
          .where((r) => r.success)
          .map((r) => r.battleId)
          .toList();

      await state.cache.removeSyncedResults(syncedIds);

      setState(() => _lastSyncResults = syncResults);
    } on ApiException catch (e) {
      setState(() => _error = 'Server error ${e.statusCode}: ${e.message}');
    } catch (e) {
      setState(() => _error = 'Error: $e');
    } finally {
      setState(() => _syncing = false);
    }
  }

  String _formatDate(DateTime dt) {
    return '${dt.year}-${_pad(dt.month)}-${_pad(dt.day)} '
        '${_pad(dt.hour)}:${_pad(dt.minute)}';
  }

  String _pad(int n) => n.toString().padLeft(2, '0');
}

class _SyncResult {
  final int battleId;
  final String status;
  final bool success;

  const _SyncResult({
    required this.battleId,
    required this.status,
    required this.success,
  });
}
