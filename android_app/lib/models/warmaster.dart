class Warmaster {
  final String telegramId;
  final int? allianceId;
  final String? nickname;
  final String? faction;
  final String? language;
  final bool notificationEnabled;
  final bool isAdmin;

  const Warmaster({
    required this.telegramId,
    this.allianceId,
    this.nickname,
    this.faction,
    this.language,
    this.notificationEnabled = false,
    this.isAdmin = false,
  });

  factory Warmaster.fromJson(Map<String, dynamic> json) {
    final dynamic rawIsAdmin = json['is_admin'];
    final bool isAdmin = rawIsAdmin == true || rawIsAdmin == 1;

    final dynamic rawNotificationsEnabled = json['notifications_enabled'];
    final dynamic rawNotificationEnabled = json['notification_enabled'];
    final bool notificationEnabled = rawNotificationsEnabled == true ||
        rawNotificationsEnabled == 1 ||
        rawNotificationEnabled == 1;

    return Warmaster(
      telegramId: json['telegram_id'].toString(),
      allianceId: json['alliance'] as int?,
      nickname: json['nickname'] as String?,
      faction: json['faction'] as String?,
      language: json['language'] as String?,
      notificationEnabled: notificationEnabled,
      isAdmin: isAdmin,
    );
  }

  Map<String, dynamic> toJson() => {
        'telegram_id': telegramId,
        'alliance': allianceId,
        'nickname': nickname,
        'faction': faction,
        'language': language,
        'notifications_enabled': notificationEnabled,
        'is_admin': isAdmin,
      };

  String get displayName => nickname ?? telegramId;
}
