import 'package:flutter/material.dart';

import '../data.dart';
import '../translations.dart';
import '../widgets.dart';
import 'staff_home.dart';
import 'student_home.dart';

// ---------- 1. Login ----------

class LoginPage extends StatefulWidget {
  const LoginPage({super.key});
  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final email = TextEditingController();
  final password = TextEditingController();
  String tab = 'Student';
  String error = '';

  void login() {
    final account = accounts[email.text.trim()];
    final ok =
        account != null &&
        password.text == '1234' &&
        (tab == 'Student') == (account.$2 == 'Student');
    if (!ok) {
      setState(() => error = 'Wrong email or password');
      return;
    }
    userName = account.$1;
    userRole = account.$2;
    go(
      context,
      userRole == 'Student' ? const StudentHome() : const StaffHome(),
    );
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: psuBar(context),
    body: ListView(
      padding: const EdgeInsets.all(24),
      children: [
        Center(
          child: Text(
            tr(context, 'Login'),
            style: const TextStyle(fontSize: 28),
          ),
        ),
        const SizedBox(height: 16),
        SegmentedButton(
          segments: [
            ButtonSegment(
              value: 'Student',
              label: Text(tr(context, 'Student')),
            ),
            ButtonSegment(
              value: 'Faculty',
              label: Text(tr(context, 'Faculty')),
            ),
          ],
          selected: {tab},
          onSelectionChanged: (s) => setState(() => tab = s.first),
        ),
        TextField(
          controller: email,
          decoration: InputDecoration(labelText: tr(context, 'Email')),
        ),
        TextField(
          controller: password,
          obscureText: true,
          decoration: InputDecoration(labelText: tr(context, 'Password')),
        ),
        Text(tr(context, error), style: const TextStyle(color: Colors.red)),
        ElevatedButton(onPressed: login, child: Text(tr(context, 'Enter'))),
      ],
    ),
  );
}
