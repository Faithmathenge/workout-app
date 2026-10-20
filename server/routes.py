from flask import Blueprint, request
from marshmallow import ValidationError

from models import Exercise, Workout, WorkoutExercise, db
from schemas import (
    exercise_schema,
    exercises_schema,
    workout_exercise_schema,
    workout_schema,
    workouts_schema,
)

api = Blueprint("api", __name__)


def json_body():
    """Return the request's JSON object, or raise a 400-style validation error."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValidationError({"_schema": ["Request body must be a JSON object."]})
    return data


def save(record):
    db.session.add(record)
    db.session.commit()
    return record


# ---------- workouts ----------

@api.get("/workouts")
def list_workouts():
    workouts = Workout.query.order_by(Workout.date.desc(), Workout.id.desc()).all()
    return workouts_schema.dump(workouts), 200


@api.get("/workouts/<int:workout_id>")
def get_workout(workout_id):
    workout = db.get_or_404(Workout, workout_id)
    return workout_schema.dump(workout), 200


@api.post("/workouts")
def create_workout():
    data = workout_schema.load(json_body())
    return workout_schema.dump(save(Workout(**data))), 201


@api.delete("/workouts/<int:workout_id>")
def delete_workout(workout_id):
    workout = db.get_or_404(Workout, workout_id)
    db.session.delete(workout)
    db.session.commit()
    return "", 204


# ---------- exercises ----------

@api.get("/exercises")
def list_exercises():
    exercises = Exercise.query.order_by(Exercise.name).all()
    return exercises_schema.dump(exercises), 200


@api.get("/exercises/<int:exercise_id>")
def get_exercise(exercise_id):
    exercise = db.get_or_404(Exercise, exercise_id)
    return exercise_schema.dump(exercise), 200


@api.post("/exercises")
def create_exercise():
    data = exercise_schema.load(json_body())
    return exercise_schema.dump(save(Exercise(**data))), 201


@api.delete("/exercises/<int:exercise_id>")
def delete_exercise(exercise_id):
    exercise = db.get_or_404(Exercise, exercise_id)
    db.session.delete(exercise)
    db.session.commit()
    return "", 204


# ---------- adding an exercise to a workout ----------

@api.post("/workouts/<int:workout_id>/exercises/<int:exercise_id>/workout_exercises")
def add_exercise_to_workout(workout_id, exercise_id):
    workout = db.get_or_404(Workout, workout_id)
    exercise = db.get_or_404(Exercise, exercise_id)
    data = workout_exercise_schema.load(json_body())
    link = WorkoutExercise(workout=workout, exercise=exercise, **data)
    return workout_exercise_schema.dump(save(link)), 201
