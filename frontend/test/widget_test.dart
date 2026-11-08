import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:psu_alerts_app/data.dart';
import 'package:psu_alerts_app/main.dart';
import 'package:psu_alerts_app/screens/login_page.dart';

// Fill in the login form and press Enter
Future<void> login(
  WidgetTester t,
  String email, {
  String tab = 'Student',
  String password = '1234',
}) async {
  await t.pumpWidget(const MaterialApp(home: LoginPage()));
  await t.tap(find.text(tab));
  await t.enterText(find.byType(TextField).at(0), email);
  await t.enterText(find.byType(TextField).at(1), password);
  await t.tap(find.text('Enter'));
  await t.pumpAndSettle();
}

Future<void> tapAndWait(WidgetTester t, Finder f) async {
  await t.tap(f);
  await t.pumpAndSettle();
}

void main() {
  // fresh fake data and English for every test
  setUp(() {
    alerts = fakeAlerts();
    language.value = 'en';
  });

  testWidgets('UI-1 wrong password shows an error', (t) async {
    await login(t, 'student@psu.test', password: 'wrong');
    expect(find.text('Wrong email or password'), findsOneWidget);
  });

  testWidgets('UI-2 student sees Recent Alert and Past Alerts', (t) async {
    await login(t, 'student@psu.test');
    expect(find.text('Recent Alert'), findsOneWidget);
    expect(find.text('Campus closed today'), findsOneWidget);
    expect(find.text('Past Alerts'), findsOneWidget);
    expect(find.text('SE495 quiz moved'), findsOneWidget);
  });

  testWidgets('UI-3 student acknowledges an alert', (t) async {
    await login(t, 'student@psu.test');
    await tapAndWait(t, find.byTooltip('Acknowledge').first);
    expect(find.byIcon(Icons.check_circle), findsOneWidget);
  });

  testWidgets('UI-4 student adds a comment', (t) async {
    await login(t, 'student@psu.test');
    await tapAndWait(t, find.byTooltip('Comments').first);
    await t.enterText(find.byType(TextField), 'See you tomorrow');
    await tapAndWait(t, find.byTooltip('Send comment'));
    expect(find.text('See you tomorrow'), findsOneWidget);
  });

  testWidgets('UI-5 faculty cannot pick High severity', (t) async {
    await login(t, 'faculty@psu.test', tab: 'Faculty');
    await tapAndWait(t, find.text('New Alert'));
    await tapAndWait(t, find.text('Severity'));
    expect(find.text('High'), findsNothing);
  });

  testWidgets('UI-6 admin can pick High severity', (t) async {
    await login(t, 'admin@psu.test', tab: 'Faculty');
    await tapAndWait(t, find.text('New Alert'));
    await tapAndWait(t, find.text('Severity'));
    expect(find.text('High'), findsWidgets);
  });

  testWidgets('UI-7 faculty sends an alert', (t) async {
    await login(t, 'faculty@psu.test', tab: 'Faculty');
    await tapAndWait(t, find.text('New Alert'));
    await t.enterText(find.byType(TextField).first, 'Lab cancelled');
    await tapAndWait(t, find.text('Severity'));
    await tapAndWait(t, find.text('Low').last);
    await tapAndWait(t, find.text('Course'));
    await tapAndWait(t, find.text('CS101').last);
    await tapAndWait(t, find.text('Send'));
    expect(find.text('Lab cancelled'), findsOneWidget);
    expect(find.text('Views: 0'), findsOneWidget);
  });

  testWidgets('UI-8 student turns off Email', (t) async {
    await login(t, 'student@psu.test');
    await tapAndWait(t, find.byTooltip('Preferences'));
    await tapAndWait(t, find.text('Email'));
    expect(
      t.widget<SwitchListTile>(find.byType(SwitchListTile).first).value,
      false,
    );
  });

  testWidgets('UI-9 en/ar button switches to Arabic and right-to-left', (
    t,
  ) async {
    await t.pumpWidget(const PsuAlertsApp());
    await tapAndWait(t, find.text('en'));
    expect(find.text('تسجيل الدخول'), findsOneWidget); // "Login"
    expect(find.text('دخول'), findsOneWidget); // "Enter"
    expect(Directionality.of(t.element(find.text('دخول'))), TextDirection.rtl);
  });

  testWidgets('UI-10 student home shows Arabic text', (t) async {
    language.value = 'ar';
    await t.pumpWidget(const PsuAlertsApp());
    await t.enterText(find.byType(TextField).at(0), 'student@psu.test');
    await t.enterText(find.byType(TextField).at(1), '1234');
    await tapAndWait(t, find.text('دخول'));
    expect(find.text('آخر تنبيه'), findsOneWidget); // "Recent Alert"
    expect(find.text('الحرم الجامعي مغلق اليوم'), findsOneWidget);
  });
}
