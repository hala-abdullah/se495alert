import 'package:flutter/material.dart';

import '../data.dart';
import '../translations.dart';
import '../widgets.dart';
import 'create_alert.dart';

// ---------- 4. Faculty/Admin home: + New Alert + Sent Alerts ----------

class StaffHome extends StatefulWidget {
  const StaffHome({super.key});
  @override
  State<StaffHome> createState() => _StaffHomeState();
}

class _StaffHomeState extends State<StaffHome> {
  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: psuBar(context),
    body: ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Align(
          alignment: AlignmentDirectional.centerStart,
          child: OutlinedButton.icon(
            icon: const Icon(Icons.add),
            label: Text(tr(context, 'New Alert')),
            onPressed: () =>
                go(context, const CreateAlert()).then((_) => setState(() {})),
          ),
        ),
        heading(context, 'Sent Alerts'),
        for (final a in alerts.where((a) => a.sender == userName))
          Card(
            child: ListTile(
              title: Text(tr(context, a.title)),
              trailing: Text('${tr(context, 'Views')}: ${a.views}'),
            ),
          ),
      ],
    ),
  );
}
