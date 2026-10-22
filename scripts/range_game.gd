extends Node3D

const RANGE_SCENE: PackedScene = preload("res://assets/machforge_range.glb")
const METERS_TO_UNITS := 0.25
const GRAVITY := 9.81
const AIR_DENSITY := 1.225
const DRAG_COEFFICIENT := 0.32
const PROJECTILE_MASS := 1.25
var projectile_radius_meters := 0.085

var camera: Camera3D
var projectile: MeshInstance3D
var trail: MeshInstance3D
var velocity := Vector2.ZERO # x and y velocity in metres per second
var wind_mps := 0.0
var flight_time := 0.0
var traveled_m := 0.0
var peak_m := 0.0
var max_range_m := 140.0
var running := false
var shape_roundness := 0.2
var nose_length_ratio := 0.5
var body_width_ratio := 0.5
var hud_labels: Dictionary = {}
var trace_points: Array[Vector3] = []
var range_label: Label
var launch_button: Button


func _ready() -> void:
	_setup_world()
	_add_range_model()
	_setup_camera()
	_build_hud()
	_create_projectile()
	_refresh_hud()


func _physics_process(delta: float) -> void:
	if not running:
		return
	var dt := minf(delta, 1.0 / 30.0)
	var relative_velocity := velocity - Vector2(wind_mps, 0.0)
	var speed := relative_velocity.length()
	var area := PI * projectile_radius_meters * projectile_radius_meters
	var drag_force := 0.5 * AIR_DENSITY * DRAG_COEFFICIENT * area * speed * speed
	var drag_accel := drag_force / PROJECTILE_MASS
	var drag_direction := relative_velocity.normalized()
	velocity.x -= drag_direction.x * drag_accel * dt
	velocity.y -= (GRAVITY + drag_direction.y * drag_accel) * dt
	flight_time += dt
	traveled_m += maxf(0.0, velocity.x + wind_mps) * dt
	peak_m = maxf(peak_m, (projectile.position.y - 2.08) / METERS_TO_UNITS)
	projectile.position.x += (velocity.x + wind_mps) * dt * METERS_TO_UNITS
	projectile.position.y += velocity.y * dt * METERS_TO_UNITS
	projectile.rotation.z = atan2(velocity.y, velocity.x)
	_update_trail()
	_refresh_hud()
	if projectile.position.y <= 0.45 or traveled_m >= max_range_m or flight_time > 12.0:
		running = false
		launch_button.text = "FIRE AGAIN"
		range_label.text = "SHOT COMPLETE  /  %.1f m" % traveled_m


func _setup_world() -> void:
	var world := WorldEnvironment.new()
	var environment := Environment.new()
	environment.background_mode = Environment.BG_SKY
	var sky := Sky.new()
	var sky_material := ProceduralSkyMaterial.new()
	sky_material.sky_top_color = Color("071426")
	sky_material.sky_horizon_color = Color("304c61")
	sky_material.ground_bottom_color = Color("101a27")
	sky_material.ground_horizon_color = Color("263747")
	sky.sky_material = sky_material
	environment.sky = sky
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.ambient_light_color = Color("8299aa")
	environment.ambient_light_energy = 0.55
	environment.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	world.environment = environment
	add_child(world)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-48, -28, 0)
	sun.light_color = Color("c8e5ff")
	sun.light_energy = 1.4
	sun.shadow_enabled = true
	add_child(sun)


func _add_range_model() -> void:
	var model := RANGE_SCENE.instantiate()
	model.name = "BlenderRangeAsset"
	add_child(model)


func _setup_camera() -> void:
	camera = Camera3D.new()
	camera.name = "RangeCamera"
	camera.position = Vector3(10.5, 22.0, 29.0)
	camera.fov = 52.0
	camera.current = true
	add_child(camera)
	camera.look_at(Vector3(16.0, 1.8, 0.0), Vector3.UP)


func _create_projectile() -> void:
	projectile = MeshInstance3D.new()
	projectile.name = "TestProjectile"
	projectile.mesh = _make_projectile_mesh()
	var material := StandardMaterial3D.new()
	material.albedo_color = Color("ffb64c")
	material.metallic = 0.72
	material.roughness = 0.22
	material.emission_enabled = true
	material.emission = Color("ff7728")
	material.emission_energy_multiplier = 1.25
	projectile.material_override = material
	projectile.position = Vector3(13.15, 2.08, 0)
	add_child(projectile)
	projectile.visible = true
	trail = MeshInstance3D.new()
	trail.name = "FlightTrace"
	trail.mesh = ImmediateMesh.new()
	var trace_material := StandardMaterial3D.new()
	trace_material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	trace_material.albedo_color = Color("48dff2")
	trace_material.emission_enabled = true
	trace_material.emission = Color("20c9ef")
	trace_material.emission_energy_multiplier = 2.0
	trail.material_override = trace_material
	add_child(trail)


func _make_projectile_mesh() -> ArrayMesh:
	var sections: Array[Vector2] = [
		Vector2(0.0, 0.015 + shape_roundness * 0.075),
		Vector2(0.05 + nose_length_ratio * 0.16, 0.08 + body_width_ratio * 0.10),
		Vector2(0.10 + nose_length_ratio * 0.20, 0.12 + body_width_ratio * 0.10),
		Vector2(0.38 + nose_length_ratio * 0.18, 0.12 + body_width_ratio * 0.10),
		Vector2(0.51 + nose_length_ratio * 0.16, 0.10 + body_width_ratio * 0.08),
		Vector2(0.57 + nose_length_ratio * 0.14, 0.015),
	]
	var mesh := ArrayMesh.new()
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var slices := 24
	for section in range(sections.size() - 1):
		for i in range(slices):
			var a0 := TAU * float(i) / slices
			var a1 := TAU * float(i + 1) / slices
			var p00 := _profile_point(sections[section], a0)
			var p01 := _profile_point(sections[section], a1)
			var p10 := _profile_point(sections[section + 1], a0)
			var p11 := _profile_point(sections[section + 1], a1)
			st.add_vertex(p00)
			st.add_vertex(p10)
			st.add_vertex(p11)
			st.add_vertex(p00)
			st.add_vertex(p11)
			st.add_vertex(p01)
	st.generate_normals()
	st.commit(mesh)
	return mesh


func _profile_point(section: Vector2, angle: float) -> Vector3:
	return Vector3(section.x, cos(angle) * section.y, sin(angle) * section.y)


func _build_hud() -> void:
	var canvas := CanvasLayer.new()
	canvas.layer = 10
	add_child(canvas)
	var root := Control.new()
	root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	canvas.add_child(root)

	var left := _make_panel(root, "Launcher Console", Vector2(22, 22), Vector2(326, 730), false)
	var left_box := _panel_box(left, "LAUNCH CONTROL", "MACHFORGE  /  RANGE 07")
	_add_setting_label(left_box, "MUZZLE VELOCITY", "velocity", "72 m/s")
	_add_slider(left_box, "velocity", 30, 120, 72, 1, "m/s")
	_add_setting_label(left_box, "ELEVATION", "angle", "18°")
	_add_slider(left_box, "angle", 3, 42, 18, 0, "°")
	_add_setting_label(left_box, "CROSSWIND", "wind", "0 m/s")
	_add_slider(left_box, "wind", -15, 15, 0, 1, "m/s")
	_add_setting_label(left_box, "NOSE PROFILE", "shape", "20% round")
	_add_slider(left_box, "shape", 0, 100, 20, 0, "%")
	_add_setting_label(left_box, "NOSE LENGTH", "nose_length", "50%")
	_add_slider(left_box, "nose_length", 0, 100, 50, 1, "%")
	_add_setting_label(left_box, "BODY WIDTH", "body_width", "50%")
	_add_slider(left_box, "body_width", 0, 100, 50, 1, "%")
	var hint := Label.new()
	hint.text = "Adjust the launch and tip profile, then compare the flight trace."
	hint.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	hint.add_theme_color_override("font_color", Color("9db3c4"))
	hint.add_theme_font_size_override("font_size", 14)
	left_box.add_child(hint)
	launch_button = Button.new()
	launch_button.text = "FIRE TEST"
	launch_button.custom_minimum_size = Vector2(0, 54)
	launch_button.add_theme_font_size_override("font_size", 18)
	launch_button.pressed.connect(_fire)
	left_box.add_child(launch_button)
	var reset_button := Button.new()
	reset_button.text = "RESET RANGE"
	reset_button.custom_minimum_size = Vector2(0, 42)
	reset_button.pressed.connect(_reset)
	left_box.add_child(reset_button)

	var right := _make_panel(root, "Flight Readout", Vector2(-282, 22), Vector2(260, 270), true)
	var right_box := _panel_box(right, "LIVE TELEMETRY", "EDUCATIONAL SIMULATION")
	_add_readout(right_box, "RANGE", "range", "—")
	_add_readout(right_box, "ALTITUDE", "altitude", "—")
	_add_readout(right_box, "TIME OF FLIGHT", "time", "—")
	_add_readout(right_box, "PEAK ALTITUDE", "peak", "—")
	_add_readout(right_box, "MACH", "mach", "—")

	range_label = Label.new()
	range_label.text = "RANGE READY  /  SINGLE ROUND"
	range_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	range_label.add_theme_color_override("font_color", Color("a9c6d9"))
	range_label.add_theme_font_size_override("font_size", 15)
	range_label.set_anchors_and_offsets_preset(Control.PRESET_CENTER_BOTTOM)
	range_label.offset_left = -180
	range_label.offset_top = -52
	range_label.offset_right = 180
	range_label.offset_bottom = -18
	root.add_child(range_label)


func _make_panel(root: Control, panel_name: String, position: Vector2, size: Vector2, right_aligned: bool) -> PanelContainer:
	var panel := PanelContainer.new()
	panel.name = panel_name
	panel.custom_minimum_size = size
	panel.size = size
	panel.set_anchors_preset(Control.PRESET_TOP_RIGHT if right_aligned else Control.PRESET_TOP_LEFT)
	if right_aligned:
		panel.offset_left = position.x
		panel.offset_top = position.y
		panel.offset_right = position.x + size.x
		panel.offset_bottom = position.y + size.y
	else:
		panel.position = position
	panel.add_theme_stylebox_override("panel", _panel_style())
	root.add_child(panel)
	return panel


func _panel_style() -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = Color(0.025, 0.055, 0.085, 0.93)
	style.border_color = Color("267c9b")
	style.set_border_width_all(1)
	style.set_corner_radius_all(8)
	style.content_margin_left = 18
	style.content_margin_right = 18
	style.content_margin_top = 16
	style.content_margin_bottom = 16
	return style


func _panel_box(panel: PanelContainer, title: String, subtitle: String) -> VBoxContainer:
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 9)
	panel.add_child(box)
	var eyebrow := Label.new()
	eyebrow.text = subtitle
	eyebrow.add_theme_color_override("font_color", Color("55d8e9"))
	eyebrow.add_theme_font_size_override("font_size", 11)
	box.add_child(eyebrow)
	var heading := Label.new()
	heading.text = title
	heading.add_theme_color_override("font_color", Color("eff8ff"))
	heading.add_theme_font_size_override("font_size", 22)
	box.add_child(heading)
	var rule := HSeparator.new()
	box.add_child(rule)
	return box


func _add_setting_label(parent: VBoxContainer, title: String, key: String, initial: String) -> void:
	var row := HBoxContainer.new()
	var label := Label.new()
	label.text = title
	label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	label.add_theme_color_override("font_color", Color("bfd0dd"))
	label.add_theme_font_size_override("font_size", 12)
	row.add_child(label)
	var value := Label.new()
	value.text = initial
	value.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	value.add_theme_color_override("font_color", Color("67e5f0"))
	row.add_child(value)
	hud_labels[key + "_setting"] = value
	parent.add_child(row)


func _add_slider(parent: VBoxContainer, key: String, minimum: float, maximum: float, initial: float, step: float, suffix: String) -> void:
	var slider := HSlider.new()
	slider.min_value = minimum
	slider.max_value = maximum
	slider.step = step
	slider.value = initial
	slider.custom_minimum_size = Vector2(0, 26)
	hud_labels[key + "_value"] = initial
	slider.value_changed.connect(func(value: float): _setting_changed(key, value, suffix))
	parent.add_child(slider)


func _add_readout(parent: VBoxContainer, title: String, key: String, initial: String) -> void:
	var row := HBoxContainer.new()
	var heading := Label.new()
	heading.text = title
	heading.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	heading.add_theme_color_override("font_color", Color("9db3c4"))
	heading.add_theme_font_size_override("font_size", 12)
	row.add_child(heading)
	var value := Label.new()
	value.text = initial
	value.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	value.add_theme_color_override("font_color", Color("ffffff"))
	value.add_theme_font_size_override("font_size", 15)
	hud_labels[key] = value
	row.add_child(value)
	parent.add_child(row)


func _setting_changed(key: String, value: float, suffix: String) -> void:
	var label: Label = hud_labels.get(key + "_setting")
	hud_labels[key + "_value"] = value
	if key == "shape":
		shape_roundness = value / 100.0
		label.text = "%d%% round" % int(value)
	elif key == "nose_length":
		nose_length_ratio = value / 100.0
		label.text = "%d%%" % int(value)
	elif key == "body_width":
		body_width_ratio = value / 100.0
		projectile_radius_meters = 0.055 + body_width_ratio * 0.06
		label.text = "%d%%" % int(value)
	if key in ["shape", "nose_length", "body_width"] and not running:
		projectile.mesh = _make_projectile_mesh()
	elif key == "velocity":
		label.text = "%d %s" % [int(value), suffix]
	elif key == "angle":
		label.text = "%d%s" % [int(value), suffix]
	elif key == "wind":
		wind_mps = value
		label.text = "%0.0f %s" % [value, suffix]


func _fire() -> void:
	_reset()
	var speed := float(hud_labels.get("velocity_value", 72.0))
	var angle_deg := float(hud_labels.get("angle_value", 18.0))
	velocity = Vector2(speed * cos(deg_to_rad(angle_deg)), speed * sin(deg_to_rad(angle_deg)))
	projectile.rotation.z = deg_to_rad(angle_deg)
	projectile.visible = true
	running = true
	launch_button.text = "IN FLIGHT…"
	range_label.text = "TRACKING ROUND  /  LIVE FLIGHT"


func _reset() -> void:
	running = false
	flight_time = 0.0
	traveled_m = 0.0
	peak_m = 0.0
	projectile.position = Vector3(13.15, 2.08, 0)
	projectile.visible = true
	trace_points.clear()
	trace_points.append(projectile.position)
	(trail.mesh as ImmediateMesh).clear_surfaces()
	launch_button.text = "FIRE TEST"
	range_label.text = "RANGE READY  /  SINGLE ROUND"
	_refresh_hud()


func _refresh_hud() -> void:
	if not is_instance_valid(projectile):
		return
	var altitude := maxf(0.0, (projectile.position.y - 2.08) / METERS_TO_UNITS)
	var speed := velocity.length()
	var mach := speed / 343.0
	_set_readout("range", "%.1f m" % traveled_m)
	_set_readout("altitude", "%.1f m" % altitude)
	_set_readout("time", "%.2f s" % flight_time)
	_set_readout("peak", "%.1f m" % peak_m)
	_set_readout("mach", "%.2f" % mach)


func _set_readout(key: String, value: String) -> void:
	var label: Label = hud_labels.get(key)
	if label:
		label.text = value


func _update_trail() -> void:
	trace_points.append(projectile.position)
	var curve := trail.mesh as ImmediateMesh
	curve.clear_surfaces()
	curve.surface_begin(Mesh.PRIMITIVE_LINE_STRIP)
	for point in trace_points:
		curve.surface_add_vertex(point)
	curve.surface_end()
