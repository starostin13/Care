import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'home_screen.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  late TextEditingController _urlCtrl;

  @override
  void initState() {
    super.initState();
    final state = context.read<AppState>();
    _urlCtrl = TextEditingController(text: state.cache.baseUrl);
  }

  @override
  void dispose() {
    _urlCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Text('Settings', style: Theme.of(context).textTheme.headlineSmall),
        const SizedBox(height: 16),
        Text('Server URL', style: Theme.of(context).textTheme.titleMedium),
        const SizedBox(height: 8),
        Row(
          children: [
            Expanded(
              child: TextField(
                controller: _urlCtrl,
                decoration: const InputDecoration(
                  hintText: 'http://192.168.1.125:5555',
                  border: OutlineInputBorder(),
                ),
                keyboardType: TextInputType.url,
              ),
            ),
            const SizedBox(width: 8),
            ElevatedButton(
              onPressed: () {
                state.updateBaseUrl(_urlCtrl.text.trim());
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('Server URL updated')),
                );
              },
              child: const Text('Save'),
            ),
          ],
        ),
        const SizedBox(height: 24),
        const Divider(),
        ListTile(
          leading: const Icon(Icons.info_outline),
          title: const Text('Version'),
          trailing: const Text('1.0.0'),
        ),
        ListTile(
          leading: const Icon(Icons.sync),
          title: const Text('Current server URL'),
          subtitle: Text(state.cache.baseUrl),
        ),
      ],
    );
  }
}
