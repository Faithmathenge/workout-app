from marshmallow import Schema, ValidationError, fields, validate, validates, validates_schema


class ExerciseSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=80))
    category = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    equipment_needed = fields.Bool(load_default=False)
    workout_exercises = fields.List(
        fields.Nested("WorkoutExerciseSchema", exclude=("exercise",)), dump_only=True
    )

    @validates("name")
    def validate_name(self, value):
        if not value.strip():
            raise ValidationError("Name cannot be blank.")

    @validates("category")
    def validate_category(self, value):
        if not value.strip():
            raise ValidationError("Category cannot be blank.")


class WorkoutSchema(Schema):
    id = fields.Int(dump_only=True)
    date = fields.Date(required=True)
    duration_minutes = fields.Int(required=True, strict=True, validate=validate.Range(min=1))
    notes = fields.Str(allow_none=True, validate=validate.Length(max=500))
    workout_exercises = fields.List(
        fields.Nested("WorkoutExerciseSchema", exclude=("workout",)), dump_only=True
    )


class WorkoutExerciseSchema(Schema):
    id = fields.Int(dump_only=True)
    workout_id = fields.Int(dump_only=True)
    exercise_id = fields.Int(dump_only=True)
    reps = fields.Int(allow_none=True, strict=True, validate=validate.Range(min=0))
    sets = fields.Int(allow_none=True, strict=True, validate=validate.Range(min=0))
    duration_seconds = fields.Int(allow_none=True, strict=True, validate=validate.Range(min=0))
    exercise = fields.Nested(
        "ExerciseSchema", only=("id", "name", "category", "equipment_needed"), dump_only=True
    )
    workout = fields.Nested(
        "WorkoutSchema", only=("id", "date", "duration_minutes"), dump_only=True
    )

    @validates_schema
    def require_reps_or_duration(self, data, **kwargs):
        if data.get("reps") is None and data.get("duration_seconds") is None:
            raise ValidationError("Provide reps or duration_seconds.", field_name="reps")


exercise_schema = ExerciseSchema()
exercises_schema = ExerciseSchema(many=True, exclude=("workout_exercises",))
workout_schema = WorkoutSchema()
workouts_schema = WorkoutSchema(many=True, exclude=("workout_exercises",))
workout_exercise_schema = WorkoutExerciseSchema()
