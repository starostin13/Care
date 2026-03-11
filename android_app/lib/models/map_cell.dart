class MapCell {
  final int id;
  final int? planetId;
  final int? patron;
  final String? state;
  final bool hasWarehouse;

  const MapCell({
    required this.id,
    this.planetId,
    this.patron,
    this.state,
    this.hasWarehouse = false,
  });

  factory MapCell.fromJson(Map<String, dynamic> json) => MapCell(
        id: json['id'] as int,
        planetId: json['planet_id'] as int?,
        patron: json['patron'] as int?,
        state: json['state'] as String?,
        hasWarehouse: json['has_warehouse'] == true ||
            (json['has_warehouse'] as int?) == 1,
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'planet_id': planetId,
        'patron': patron,
        'state': state,
        'has_warehouse': hasWarehouse,
      };
}

class MapEdge {
  final int? id;
  final int leftHexagon;
  final int rightHexagon;
  final String? state;

  const MapEdge({
    this.id,
    required this.leftHexagon,
    required this.rightHexagon,
    this.state,
  });

  factory MapEdge.fromJson(Map<String, dynamic> json) => MapEdge(
        id: json['id'] as int?,
        leftHexagon: json['left_hexagon'] as int,
        rightHexagon: json['right_hexagon'] as int,
        state: json['state'] as String?,
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'left_hexagon': leftHexagon,
        'right_hexagon': rightHexagon,
        'state': state,
      };
}
