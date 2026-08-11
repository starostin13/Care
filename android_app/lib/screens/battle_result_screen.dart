import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/battle.dart';
import '../services/api_service.dart';
import 'home_screen.dart';

class BattleResultScreen extends StatefulWidget {
  const BattleResultScreen({super.key});

  @override
  State<BattleResultScreen> createState() => _BattleResultScreenState();
}

class _BattleResultScreenState extends State<BattleResultScreen> {
  final _formKey = GlobalKey<FormState>();
  final _battleIdCtrl = TextEditingController();
  final _fstScoreCtrl = TextEditingController();
  final _sndScoreCtrl = TextEditingController();
  String? _submitterId;

  bool _offline = false;
  bool _loading = false;
  String? _error;
  BattleResult? _result;

  @override
  void dispose() {
    _battleIdCtrl.dispose();
    _fstScoreCtrl.dispose();
    _sndScoreCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    final warmasters = state.cache.cachedWarmasters;

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Form(
        key: _formKey,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text(
              'Record Battle Result',
              style: Theme.of(context).textTheme.headlineSmall,
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _battleIdCtrl,
              decoration: const InputDecoration(
                labelText: 'Battle ID',
                border: OutlineInputBorder(),
              ),
              keyboardType: TextInputType.number,
              validator: (v) =>
                  (v == null || v.isEmpty) ? 'Required' : null,
            ),
            const SizedBox(height: 12),
            Row(
              children: [
                Expanded(
                  child: TextFormField(
                    controller: _fstScoreCtrl,
                    decoration: const InputDecoration(
                      labelText: 'Player 1 Score',
                      border: OutlineInputBorder(),
                    ),
                    keyboardType: TextInputType.number,
                    validator: (v) =>
                        (v == null || v.isEmpty) ? 'Required' : null,
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: TextFormField(
                    controller: _sndScoreCtrl,
                    decoration: const InputDecoration(
                      labelText: 'Player 2 Score',
                      border: OutlineInputBorder(),
                    ),
                    keyboardType: TextInputType.number,
                    validator: (v) =>
                        (v == null || v.isEmpty) ? 'Required' : null,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            DropdownButtonFormField<String>(
              decoration: const InputDecoration(
                labelText: 'Submitter (you)',
                border: OutlineInputBorder(),
              ),
              value: _submitterId,
              items: warmasters
                  .map((w) => DropdownMenuItem(
                        value: w.telegramId,
                        child: Text(w.displayName),
                      ))
                  .toList(),
              onChanged: (v) => setState(() => _submitterId = v),
              validator: (v) =>
                  (v == null || v.isEmpty) ? 'Required' : null,
            ),
            const SizedBox(height: 12),
            SwitchListTile(
              title: const Text('Save offline (sync later)'),
              subtitle: const Text(
                  'Enable when you have no internet connection'),
              value: _offline,
              onChanged: (v) => setState(() => _offline = v),
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
              onPressed: _loading ? null : _submit,
              icon: _loading
                  ? const SizedBox(
                      width: 16,
                      height: 16,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : Icon(_offline ? Icons.save : Icons.send),
              label: Text(_offline ? 'Save Offline' : 'Submit Result'),
            ),
            const SizedBox(height: 24),
            if (_result != null) _buildResult(_result!),
          ],
        ),
      ),
    );
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    if (_submitterId == null) {
      setState(() => _error = 'Please select the submitter');
      return;
    }

    final battleId = int.tryParse(_battleIdCtrl.text);
    final fst = int.tryParse(_fstScoreCtrl.text);
    final snd = int.tryParse(_sndScoreCtrl.text);

    if (battleId == null || fst == null || snd == null) {
      setState(() => _error = 'Battle ID and scores must be numbers');
      return;
    }

    final state = context.read<AppState>();

    setState(() {
      _loading = true;
      _error = null;
      _result = null;
    });

    try {
      if (_offline) {
        await state.cache.addPendingResult(PendingBattleResultEntry(
          battleId: battleId,
          fstplayerScore: fst,
          sndplayerScore: snd,
          submitterId: _submitterId!,
        ));
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('Result saved offline')),
          );
        }
        _resetForm();
      } else {
        final result = await state.api.submitBattleResult(
          battleId: battleId,
          fstplayerScore: fst,
          sndplayerScore: snd,
          submitterId: _submitterId!,
        );
        setState(() => _result = result);
      }
    } on ApiException catch (e) {
      setState(() => _error = 'Server error ${e.statusCode}: ${e.message}');
    } catch (e) {
      setState(() => _error = 'Error: $e');
    } finally {
      setState(() => _loading = false);
    }
  }

  void _resetForm() {
    _battleIdCtrl.clear();
    _fstScoreCtrl.clear();
    _sndScoreCtrl.clear();
    setState(() {
      _submitterId = null;
      _offline = false;
    });
  }

  Widget _buildResult(BattleResult result) {
    final color = result.isApplied
        ? Colors.green.shade50
        : result.isAlreadyConfirmed
            ? Colors.orange.shade50
            : Colors.red.shade50;
    final icon = result.isApplied
        ? '✅'
        : result.isAlreadyConfirmed
            ? '⚠️'
            : '❌';
    final label = result.isApplied
        ? 'Result applied!'
        : result.isAlreadyConfirmed
            ? 'Already confirmed'
            : 'Battle not found';

    return Card(
      color: color,
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('$icon $label',
                style: Theme.of(context).textTheme.titleMedium),
            Text('Battle ID: ${result.battleId}'),
            if (result.missionId != null)
              Text('Mission ID: ${result.missionId}'),
            if (result.rewards != null)
              Text('Rewards: ${result.rewards}'),
          ],
        ),
      ),
    );
  }
}
