import 'package:flutter/material.dart';

import 'data.dart';
import 'translations.dart';

// Shared pieces used by several screens

// Top bar from the wireframe: "en" button on the left, PSU in the middle
AppBar psuBar(BuildContext context, {List<Widget>? actions}) => AppBar(
  centerTitle: true,
  title: Text(tr(context, 'PSU')),
  actions: actions,
  leading: ValueListenableBuilder(
    valueListenable: language,
    builder: (_, lang, _) => TextButton(
      onPressed: () => language.value = lang == 'en' ? 'ar' : 'en',
      child: Text(lang),
    ),
  ),
);

Future go(BuildContext context, Widget page) =>
    Navigator.push(context, MaterialPageRoute(builder: (_) => page));

Widget heading(BuildContext context, String text) => Padding(
  padding: const EdgeInsets.symmetric(vertical: 12),
  child: Text(tr(context, text), style: const TextStyle(fontSize: 22)),
);

// ✓ button: acknowledge the alert as read (filled when done)
Widget ackButton(BuildContext context, Alert a, StateSetter setState) =>
    IconButton(
      tooltip: tr(context, 'Acknowledge'),
      icon: Icon(
        a.acknowledged ? Icons.check_circle : Icons.check_circle_outline,
      ),
      onPressed: () => setState(() {
        if (!a.acknowledged) a.views++;
        a.acknowledged = true;
      }),
    );
