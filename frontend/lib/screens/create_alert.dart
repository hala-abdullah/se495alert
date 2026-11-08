import 'package:flutter/material.dart';

import '../data.dart';
import '../translations.dart';
import '../widgets.dart';

// ---------- 5. New alert: Title, Severity, Course, Section, Send ----------

class CreateAlert extends StatefulWidget {
  const CreateAlert({super.key});
  @override
  State<CreateAlert> createState() => _CreateAlertState();
}

class _CreateAlertState extends State<CreateAlert> {
  final title = TextEditingController();
  final body = TextEditingController();
  String? severity, course, section;

  bool get isAdmin => userRole == 'Admin';
  // Faculty: Medium/Low and own courses. Admin: High too, and every course.
  List<String> get severities =>
      isAdmin ? ['High', 'Medium', 'Low'] : ['Medium', 'Low'];
  List<String> get courses => isAdmin
      ? ['CS101', 'ARAB101', 'SE495', 'All Courses']
      : ['CS101', 'ARAB101', 'SE495', 'All Courses'];

  Widget dropdown(
    String hint,
    List<String> options,
    String? value,
    ValueChanged<String?> onChanged,
  ) => DropdownButton(
    hint: Text(tr(context, hint)),
    value: value,
    items: [
      for (final o in options)
        DropdownMenuItem(value: o, child: Text(tr(context, o))),
    ],
    onChanged: (v) => setState(() => onChanged(v)),
  );

  void send() {
    if (title.text.isEmpty || severity == null || course == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(tr(context, 'Fill in title, severity and course')),
        ),
      );
      return;
    }
    final target = section == null ? course! : '$course $section';
    alerts.insert(
      0,
      Alert(title.text, body.text, userName, severity!, target, 0, []),
    );
    Navigator.pop(context);
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: psuBar(context),
    body: ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              children: [
                TextField(
                  controller: title,
                  decoration: InputDecoration(labelText: tr(context, 'Title')),
                ),
                TextField(
                  controller: body,
                  maxLines: 5,
                  decoration: InputDecoration(
                    labelText: tr(context, 'Message'),
                  ),
                ),
              ],
            ),
          ),
        ),
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceEvenly,
          children: [
            dropdown('Severity', severities, severity, (v) => severity = v),
            dropdown('Course', courses, course, (v) {
              course = v;
              section = null;
            }),
          ],
        ),
        // Section only when one course is picked
        if (course != null && course != 'All Courses')
          Center(
            child: dropdown(
              'Section',
              ['Section 1', 'Section 2'],
              section,
              (v) => section = v,
            ),
          ),
        const SizedBox(height: 24),
        Center(
          child: ElevatedButton(
            onPressed: send,
            child: Text(tr(context, 'Send')),
          ),
        ),
      ],
    ),
  );
}
