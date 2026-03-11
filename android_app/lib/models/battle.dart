class BattleResult {
  final int battleId;
  final int? missionId;
  final String status;
  final int? missionStatus;
  final Map<String, dynamic>? rewards;

  const BattleResult({
    required this.battleId,
    this.missionId,
    required this.status,
    this.missionStatus,
    this.rewards,
  });

  factory BattleResult.fromJson(Map<String, dynamic> json) => BattleResult(
        battleId: json['battle_id'] as int,
        missionId: json['mission_id'] as int?,
        status: json['status'] as String,
        missionStatus: json['mission_status'] as int?,
        rewards: json['rewards'] as Map<String, dynamic>?,
      );

  bool get isApplied => status == 'applied';
  bool get isAlreadyConfirmed => status == 'already_confirmed';
  bool get isNotFound => status == 'not_found';
}

/// Holds a pending (offline) battle result waiting to be synced.
class PendingBattleResultEntry {
  final int battleId;
  final int fstplayerScore;
  final int sndplayerScore;
  final String submitterId;
  final DateTime createdAt;

  PendingBattleResultEntry({
    required this.battleId,
    required this.fstplayerScore,
    required this.sndplayerScore,
    required this.submitterId,
    DateTime? createdAt,
  }) : createdAt = createdAt ?? DateTime.now();

  Map<String, dynamic> toJson() => {
        'battle_id': battleId,
        'fstplayer_score': fstplayerScore,
        'sndplayer_score': sndplayerScore,
        'submitter_id': submitterId,
        'created_at': createdAt.toIso8601String(),
      };

  factory PendingBattleResultEntry.fromJson(Map<String, dynamic> json) =>
      PendingBattleResultEntry(
        battleId: json['battle_id'] as int,
        fstplayerScore: json['fstplayer_score'] as int,
        sndplayerScore: json['sndplayer_score'] as int,
        submitterId: json['submitter_id'] as String,
        createdAt: json['created_at'] != null
            ? DateTime.parse(json['created_at'] as String)
            : null,
      );
}
