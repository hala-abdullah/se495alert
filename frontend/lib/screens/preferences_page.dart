import 'package:flutter/material.dart';

import '../translations.dart';
import '../widgets.dart';

// ---------- 6. Preferences: Email / SMS / Push ----------

class PreferencesPage extends StatefulWidget {
  const PreferencesPage({super.key});
  @override
  State<PreferencesPage> createState() => _PreferencesPageState();
}

class _PreferencesPageState extends State<PreferencesPage> {
  final prefs = {'Email': true, 'SMS': true, 'Push': true};

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: psuBar(context),
    body: ListView(
      padding: const EdgeInsets.all(16),
      children: [
        heading(context, 'Preferences'),
        for (final channel in prefs.keys)
          SwitchListTile(
            title: Text(tr(context, channel)),
            value: prefs[channel]!,
            onChanged: (on) => setState(() => prefs[channel] = on),
          ),
      ],
    ),
  );
}
