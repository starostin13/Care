import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../services/cache_service.dart';
import 'missions_screen.dart';
import 'battle_result_screen.dart';
import 'sync_screen.dart';
import 'settings_screen.dart';

/// App state shared across screens.
class AppState extends ChangeNotifier {
  final CacheService cache;
  late ApiService api;

  AppState(this.cache) {
    api = ApiService(baseUrl: cache.baseUrl);
  }

  bool _loading = false;
  String? _error;
  String? _lastRefreshed;

  bool get loading => _loading;
  String? get error => _error;
  String? get lastRefreshed => _lastRefreshed;

  void updateBaseUrl(String url) {
    cache.setBaseUrl(url);
    api = ApiService(baseUrl: url);
    notifyListeners();
  }

  Future<void> refreshBootstrap() async {
    _loading = true;
    _error = null;
    notifyListeners();
    try {
      final data = await cache.refresh(api);
      _lastRefreshed = data.generatedAt;
      _error = null;
    } on ApiException catch (e) {
      _error = 'Server error ${e.statusCode}: ${e.message}';
    } catch (e) {
      _error = 'Failed to connect: $e';
    } finally {
      _loading = false;
      notifyListeners();
    }
  }
}

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _selectedIndex = 0;

  static const List<_NavItem> _navItems = [
    _NavItem(Icons.sync, 'Bootstrap'),
    _NavItem(Icons.flag, 'Missions'),
    _NavItem(Icons.sports_esports, 'Record Result'),
    _NavItem(Icons.upload, 'Sync'),
    _NavItem(Icons.settings, 'Settings'),
  ];

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    final pages = [
      _BootstrapPage(state: state),
      const MissionsScreen(),
      const BattleResultScreen(),
      const SyncScreen(),
      const SettingsScreen(),
    ];

    return Scaffold(
      appBar: AppBar(
        title: const Text('CareBot'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        actions: [
          if (state.loading)
            const Padding(
              padding: EdgeInsets.all(16),
              child: SizedBox(
                width: 20,
                height: 20,
                child: CircularProgressIndicator(strokeWidth: 2),
              ),
            ),
        ],
      ),
      body: pages[_selectedIndex],
      bottomNavigationBar: NavigationBar(
        selectedIndex: _selectedIndex,
        onDestinationSelected: (i) => setState(() => _selectedIndex = i),
        destinations: _navItems
            .map((item) => NavigationDestination(
                  icon: Icon(item.icon),
                  label: item.label,
                ))
            .toList(),
      ),
    );
  }
}

class _BootstrapPage extends StatelessWidget {
  final AppState state;

  const _BootstrapPage({required this.state});

  @override
  Widget build(BuildContext context) {
    final cache = state.cache;
    final data = cache.load();

    return RefreshIndicator(
      onRefresh: state.refreshBootstrap,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          if (state.error != null)
            Card(
              color: Theme.of(context).colorScheme.errorContainer,
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Text(state.error!),
              ),
            ),
          if (state.lastRefreshed != null || data != null)
            Text(
              'Last refreshed: ${state.lastRefreshed ?? data?.generatedAt ?? '—'}',
              style: Theme.of(context).textTheme.bodySmall,
            ),
          const SizedBox(height: 16),
          ElevatedButton.icon(
            onPressed: state.loading ? null : state.refreshBootstrap,
            icon: const Icon(Icons.sync),
            label: const Text('Refresh Data'),
          ),
          const SizedBox(height: 24),
          if (data == null)
            const Center(
                child: Text('No cached data. Tap "Refresh Data" to load.')),
          if (data != null) ...[
            _SectionTile(
              title: 'Alliances',
              count: data.alliances.length,
              children: data.alliances
                  .map((a) => ListTile(
                        leading: CircleAvatar(
                          backgroundColor: _parseColor(a.color),
                          radius: 12,
                        ),
                        title: Text(a.name),
                        trailing:
                            Text('Resources: ${a.commonResource}'),
                      ))
                  .toList(),
            ),
            _SectionTile(
              title: 'Warmasters',
              count: data.warmasters.length,
              children: data.warmasters
                  .map((w) => ListTile(
                        leading:
                            const Icon(Icons.person),
                        title: Text(w.displayName),
                        subtitle: w.allianceId != null
                            ? Text('Alliance: ${w.allianceId}')
                            : null,
                      ))
                  .toList(),
            ),
            _SectionTile(
              title: 'Map Cells',
              count: data.mapCells.length,
              children: data.mapCells
                  .take(10)
                  .map((c) => ListTile(
                        leading: const Icon(Icons.hexagon),
                        title: Text('Cell #${c.id}'),
                        subtitle: c.patron != null
                            ? Text('Patron: ${c.patron}')
                            : const Text('Unclaimed'),
                        trailing: c.hasWarehouse
                            ? const Icon(Icons.warehouse, size: 16)
                            : null,
                      ))
                  .toList(),
            ),
            _SectionTile(
              title: 'Pending Missions',
              count: data.pendingMissions.length,
              children: data.pendingMissions
                  .map((m) => ListTile(
                        leading: const Icon(Icons.assignment),
                        title: Text(m.missionDescription),
                        subtitle: Text('${m.rules} — ${m.deploy}'),
                      ))
                  .toList(),
            ),
          ],
        ],
      ),
    );
  }

  Color _parseColor(String? hex) {
    if (hex == null) return Colors.grey;
    try {
      return Color(int.parse(hex.replaceFirst('#', '0xFF')));
    } catch (_) {
      return Colors.grey;
    }
  }
}

class _SectionTile extends StatelessWidget {
  final String title;
  final int count;
  final List<Widget> children;

  const _SectionTile({
    required this.title,
    required this.count,
    required this.children,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: ExpansionTile(
        title: Text('$title ($count)'),
        children: children.isEmpty
            ? [const ListTile(title: Text('None'))]
            : children,
      ),
    );
  }
}

class _NavItem {
  final IconData icon;
  final String label;

  const _NavItem(this.icon, this.label);
}
