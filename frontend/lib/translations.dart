import 'package:flutter/material.dart';

// English -> Arabic for every piece of text in the app (NFR-19).
// Text not in the list (e.g. a new alert someone types) stays as written.
const arabic = {
  // Login
  'Login': 'تسجيل الدخول',
  'Student': 'طالب',
  'Faculty': 'عضو هيئة التدريس',
  'Email': 'البريد الإلكتروني',
  'Password': 'كلمة المرور',
  'Enter': 'دخول',
  'Wrong email or password': 'البريد الإلكتروني أو كلمة المرور غير صحيحة',
  // Student home + alert page
  'Recent Alert': 'آخر تنبيه',
  'Past Alerts': 'التنبيهات السابقة',
  'Acknowledge': 'تأكيد الاستلام',
  'Comments': 'التعليقات',
  'Write a comment': 'اكتب تعليقاً',
  'Send comment': 'إرسال التعليق',
  'Preferences': 'التفضيلات',
  'SMS': 'رسائل نصية',
  'Push': 'إشعارات التطبيق',
  // Faculty / Admin
  'New Alert': 'تنبيه جديد',
  'Sent Alerts': 'التنبيهات المرسلة',
  'Views': 'المشاهدات',
  'Title': 'العنوان',
  'Message': 'الرسالة',
  'Severity': 'الأهمية',
  'Course': 'المقرر',
  'Section': 'الشعبة',
  'Section 1': 'الشعبة 1',
  'Section 2': 'الشعبة 2',
  'All Courses': 'جميع المقررات',
  'Send': 'إرسال',
  'Fill in title, severity and course': 'أدخل العنوان والأهمية والمقرر',
  'High': 'عالية',
  'Medium': 'متوسطة',
  'Low': 'منخفضة',
  // Fake data
  'Amal': 'أمل',
  'Dr.Reem AlSuhaibani': 'د. ريم السحيباني',
  'Dr.Iman': 'د. إيمان',
  'PSU Admin': 'إدارة الجامعة',
  'User1': 'مستخدم 1',
  'Thanks!': 'شكراً!',
  'Campus closed today': 'الحرم الجامعي مغلق اليوم',
  'Campus is closed due to weather.': 'الحرم الجامعي مغلق بسبب الطقس.',
  'SE495 quiz moved': 'تم نقل اختبار SE495',
  'The quiz is moved to Wednesday.': 'تم نقل الاختبار إلى يوم الأربعاء.',
  'ARAB101 class cancelled': 'إلغاء محاضرة ARAB101',
  'Class cancelled today for personal reasons.':
      'أُلغيت المحاضرة اليوم لظروف خاصة.',
};

// tr(context, 'Login') -> 'Login' or 'تسجيل الدخول' depending on the app language.
// Reading the locale from context makes the screen rebuild when en/ar is tapped.
String tr(BuildContext context, String english) =>
    Localizations.localeOf(context).languageCode == 'ar'
    ? arabic[english] ?? english
    : english;
