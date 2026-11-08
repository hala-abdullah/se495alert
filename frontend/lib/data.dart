import 'package:flutter/material.dart';

// ---------- Fake data only (no real people or contacts) ----------

// Fake accounts: email -> (name, role). Password for all: 1234
const accounts = {
  'student@psu.test': ('Amal', 'Student'),
  'faculty@psu.test': ('Dr.Reem AlSuhaibani', 'Faculty'),
  'admin@psu.test': ('PSU Admin', 'Admin'),
};

class Alert {
  String title, body, sender, severity, course;
  int views;
  bool acknowledged = false;
  List<(String, String)> comments; // (user, text)
  Alert(
    this.title,
    this.body,
    this.sender,
    this.severity,
    this.course,
    this.views,
    this.comments,
  );
}

List<Alert> fakeAlerts() => [
  Alert(
    'Campus closed today',
    'Campus is closed due to weather.',
    'PSU Admin',
    'High',
    'All Courses',
    120,
    [('User1', 'Thanks!')],
  ),
  Alert(
    'SE495 quiz moved',
    'The quiz is moved to Wednesday.',
    'Dr.Reem AlSuhaibani',
    'Medium',
    'SE495',
    25,
    [],
  ),
  Alert(
    'ARAB101 class cancelled',
    'Class cancelled today for personal reasons.',
    'Dr.Iman',
    'Low',
    'ARAB101',
    10,
    [],
  ),
];

var alerts = fakeAlerts();
var userName = '';
var userRole = '';
final language = ValueNotifier('en');
