class Mission {
  final int id;
  final String deploy;
  final String rules;
  final int? cell;
  final String missionDescription;
  final String? winnerBonus;
  final int status;
  final String? createdDate;
  final String? mapDescription;
  final String? rewardConfig;

  const Mission({
    required this.id,
    required this.deploy,
    required this.rules,
    this.cell,
    required this.missionDescription,
    this.winnerBonus,
    required this.status,
    this.createdDate,
    this.mapDescription,
    this.rewardConfig,
  });

  factory Mission.fromJson(Map<String, dynamic> json) => Mission(
        id: json['id'] as int,
        deploy: json['deploy'] as String,
        rules: json['rules'] as String,
        cell: json['cell'] as int?,
        missionDescription: json['mission_description'] as String,
        winnerBonus: json['winner_bonus'] as String?,
        status: json['status'] as int,
        createdDate: json['created_date'] as String?,
        mapDescription: json['map_description'] as String?,
        rewardConfig: json['reward_config'] as String?,
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'deploy': deploy,
        'rules': rules,
        'cell': cell,
        'mission_description': missionDescription,
        'winner_bonus': winnerBonus,
        'status': status,
        'created_date': createdDate,
        'map_description': mapDescription,
        'reward_config': rewardConfig,
      };

  bool get isCompleted => status == 3;
  bool get isActive => status == 1;
  bool get isPendingConfirmation => status == 2;
}

class PendingMission {
  final int id;
  final String deploy;
  final String rules;
  final int? cell;
  final String missionDescription;
  final String? createdDate;

  const PendingMission({
    required this.id,
    required this.deploy,
    required this.rules,
    this.cell,
    required this.missionDescription,
    this.createdDate,
  });

  factory PendingMission.fromJson(Map<String, dynamic> json) => PendingMission(
        id: json['id'] as int,
        deploy: json['deploy'] as String,
        rules: json['rules'] as String,
        cell: json['cell'] as int?,
        missionDescription: json['mission_description'] as String,
        createdDate: json['created_date'] as String?,
      );
}
