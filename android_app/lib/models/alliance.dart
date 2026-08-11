class Alliance {
  final int id;
  final String name;
  final String? color;
  final int commonResource;

  const Alliance({
    required this.id,
    required this.name,
    this.color,
    required this.commonResource,
  });

  factory Alliance.fromJson(Map<String, dynamic> json) => Alliance(
        id: json['id'] as int,
        name: json['name'] as String,
        color: json['color'] as String?,
        commonResource: (json['common_resource'] as num?)?.toInt() ?? 0,
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'name': name,
        'color': color,
        'common_resource': commonResource,
      };
}
