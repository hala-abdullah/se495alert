import 'package:flutter/material.dart';

import '../data.dart';
import '../translations.dart';
import '../widgets.dart';
import 'alert_page.dart';
import 'preferences_page.dart';

// ---------- 2. Student home: Recent Alert + Past Alerts ----------

class StudentHome extends StatefulWidget {
  const StudentHome({super.key});
  @override
  State<StudentHome> createState() => _StudentHomeState();
}

class _StudentHomeState extends State<StudentHome> {
  void open(Widget page) => go(context, page).then((_) => setState(() {}));

  Widget commentButton(Alert a) => IconButton(
    tooltip: tr(context, 'Comments'),
    icon: const Icon(Icons.comment_outlined),
    onPressed: () => open(AlertPage(alert: a)),
  );

  // "Sender - Severity" line under each alert title
  String senderLine(Alert a) =>
      '${tr(context, a.sender)} - ${tr(context, a.severity)}';

  @override
  Widget build(BuildContext context) {
    final recent = alerts.first;
    return Scaffold(
      appBar: psuBar(
        context,
        actions: [
          IconButton(
            tooltip: tr(context, 'Preferences'),
            icon: const Icon(Icons.settings),
            onPressed: () => open(const PreferencesPage()),
          ),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          heading(context, 'Recent Alert'),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    tr(context, recent.title),
                    style: const TextStyle(fontSize: 18),
                  ),
                  Text(senderLine(recent)),
                  const SizedBox(height: 12),
                  Text(tr(context, recent.body)),
                  Row(
                    children: [
                      ackButton(context, recent, setState),
                      commentButton(recent),
                    ],
                  ),
                ],
              ),
            ),
          ),
          heading(context, 'Past Alerts'),
          for (final a in alerts.skip(1))
            Card(
              child: ListTile(
                title: Text(tr(context, a.title)),
                subtitle: Text(senderLine(a)),
                trailing: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [ackButton(context, a, setState), commentButton(a)],
                ),
              ),
            ),
        ],
      ),
    );
  }
}
