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

  factory Warmaster.fromJson(Map<String, dynamic> json) => Warmaster(
        telegramId: json['telegram_id'].toString(),
        allianceId: json['alliance'] as int?,
        nickname: json['nickname'] as String?,
        faction: json['faction'] as String?,
        language: json['language'] as String?,
        // Support both field names from different API versions
        notificationEnabled: json['notifications_enabled'] as bool? ??
            (json['notification_enabled'] as int?) == 1,
        isAdmin: json['is_admin'] == true || (json['is_admin'] as int?) == 1,
      );

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
