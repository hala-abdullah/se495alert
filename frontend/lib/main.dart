import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';

import 'data.dart';
import 'screens/login_page.dart';

/// PSU Alerts & Notifications - Flutter client (prototype).
///
/// Uses synthetic data from data.dart. Screens live in lib/screens/.
/// Arabic text lives in translations.dart.
void main() {
  runApp(const PsuAlertsApp());
}

/// Root widget: sets the app title, theme and language,
/// then opens the login page.
class PsuAlertsApp extends StatelessWidget {
  const PsuAlertsApp({super.key});

  // PSU navy blue, used to generate the app's colours
  static const psuBlue = Color(0xFF003366);

  @override
  Widget build(BuildContext context) {
    // Rebuild the whole app when the en/ar button is tapped
    return ValueListenableBuilder<String>(
      valueListenable: language,
      builder: (context, lang, _) {
        return MaterialApp(
          title: 'PSU Alerts',
          debugShowCheckedModeBanner: false,
          theme: ThemeData(
            useMaterial3: true,
            colorScheme: ColorScheme.fromSeed(seedColor: psuBlue),
            appBarTheme: const AppBarTheme(centerTitle: true),
          ),
          // Arabic switches the text and flips the layout to right-to-left
          locale: Locale(lang),
          supportedLocales: const [Locale('en'), Locale('ar')],
          localizationsDelegates: GlobalMaterialLocalizations.delegates,
          home: const LoginPage(),
        );
      },
    );
  }
}
