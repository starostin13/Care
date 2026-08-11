import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'services/cache_service.dart';
import 'screens/home_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final prefs = await SharedPreferences.getInstance();
  final cache = CacheService(prefs);

  runApp(
    ChangeNotifierProvider(
      create: (_) => AppState(cache),
      child: const CareBotApp(),
    ),
  );
}

class CareBotApp extends StatelessWidget {
  const CareBotApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'CareBot',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF6B2D2D)),
        useMaterial3: true,
      ),
      home: const HomeScreen(),
    );
  }
}
