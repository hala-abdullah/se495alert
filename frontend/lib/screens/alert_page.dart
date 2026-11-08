import 'package:flutter/material.dart';

import '../data.dart';
import '../translations.dart';
import '../widgets.dart';

// ---------- 3. Alert page: details + comments ----------

class AlertPage extends StatefulWidget {
  final Alert alert;
  const AlertPage({super.key, required this.alert});
  @override
  State<AlertPage> createState() => _AlertPageState();
}

class _AlertPageState extends State<AlertPage> {
  final comment = TextEditingController();

  @override
  Widget build(BuildContext context) {
    final a = widget.alert;
    return Scaffold(
      appBar: psuBar(context),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text(tr(context, a.title), style: const TextStyle(fontSize: 22)),
          Text(tr(context, a.sender)),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(tr(context, a.body)),
                  ackButton(context, a, setState),
                ],
              ),
            ),
          ),
          heading(context, 'Comments'),
          for (final (user, text) in a.comments)
            Card(
              child: ListTile(
                title: Text(tr(context, user)),
                subtitle: Text(tr(context, text)),
              ),
            ),
          TextField(
            controller: comment,
            decoration: InputDecoration(
              labelText: tr(context, 'Write a comment'),
              suffixIcon: IconButton(
                tooltip: tr(context, 'Send comment'),
                icon: const Icon(Icons.send),
                onPressed: () => setState(() {
                  if (comment.text.isEmpty) return;
                  a.comments.add((userName, comment.text));
                  comment.clear();
                }),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
