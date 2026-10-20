import pytest
from sqlalchemy.exc import IntegrityError

from models import Exercise, Workout, WorkoutExercise, db


def make_exercise(client, **overrides):
    payload = {"name": "Squat", "category": "Strength", "equipment_needed": True}
    payload.update(overrides)
    return client.post("/exercises", json=payload)


def make_workout(client, **overrides):
    payload = {"date": "2026-10-01", "duration_minutes": 45, "notes": "Leg day"}
    payload.update(overrides)
    return client.post("/workouts", json=payload)


# ---------- exercises ----------

def test_create_and_get_exercise(client):
    response = make_exercise(client)
    assert response.status_code == 201
    created = response.get_json()
    assert created["name"] == "Squat"
    assert created["equipment_needed"] is True

    fetched = client.get(f"/exercises/{created['id']}")
    assert fetched.status_code == 200
    assert fetched.get_json()["name"] == "Squat"


def test_list_exercises(client):
    make_exercise(client)
    make_exercise(client, name="Plank", category="Core")
    response = client.get("/exercises")
    assert response.status_code == 200
    assert [e["name"] for e in response.get_json()] == ["Plank", "Squat"]


def test_exercise_defaults_equipment_needed_to_false(client):
    response = client.post("/exercises", json={"name": "Push-up", "category": "Strength"})
    assert response.status_code == 201
    assert response.get_json()["equipment_needed"] is False


def test_duplicate_exercise_name_is_rejected(client):
    make_exercise(client)
    response = make_exercise(client)
    assert response.status_code == 409


def test_exercise_missing_fields(client):
    response = client.post("/exercises", json={"name": "Squat"})
    assert response.status_code == 400
    assert "category" in response.get_json()["errors"]


def test_exercise_blank_name_rejected_by_schema(client):
    response = make_exercise(client, name="   ")
    assert response.status_code == 400
    assert "name" in response.get_json()["errors"]


def test_exercise_unknown_field_rejected(client):
    response = make_exercise(client, id=99)
    assert response.status_code == 400


def test_non_json_body_rejected(client):
    response = client.post("/exercises", data="nope")
    assert response.status_code == 400


def test_get_missing_exercise(client):
    response = client.get("/exercises/999")
    assert response.status_code == 404
    assert response.get_json() == {"error": "Not found"}


def test_delete_exercise(client):
    exercise_id = make_exercise(client).get_json()["id"]
    assert client.delete(f"/exercises/{exercise_id}").status_code == 204
    assert client.get(f"/exercises/{exercise_id}").status_code == 404


def test_delete_missing_exercise(client):
    assert client.delete("/exercises/999").status_code == 404


# ---------- workouts ----------

def test_create_and_get_workout(client):
    response = make_workout(client)
    assert response.status_code == 201
    created = response.get_json()
    assert created["date"] == "2026-10-01"
    assert created["workout_exercises"] == []

    assert client.get(f"/workouts/{created['id']}").status_code == 200


def test_list_workouts_newest_first(client):
    make_workout(client, date="2026-10-01")
    make_workout(client, date="2026-10-05")
    dates = [w["date"] for w in client.get("/workouts").get_json()]
    assert dates == ["2026-10-05", "2026-10-01"]


@pytest.mark.parametrize("duration", [0, -5, "abc", 12.5])
def test_workout_invalid_duration(client, duration):
    response = make_workout(client, duration_minutes=duration)
    assert response.status_code == 400
    assert "duration_minutes" in response.get_json()["errors"]


def test_workout_invalid_date(client):
    response = make_workout(client, date="not-a-date")
    assert response.status_code == 400
    assert "date" in response.get_json()["errors"]


def test_workout_missing_required_fields(client):
    response = client.post("/workouts", json={})
    assert response.status_code == 400
    errors = response.get_json()["errors"]
    assert "date" in errors and "duration_minutes" in errors


def test_workout_notes_too_long(client):
    response = make_workout(client, notes="x" * 501)
    assert response.status_code == 400


def test_get_missing_workout(client):
    assert client.get("/workouts/999").status_code == 404


def test_delete_workout(client):
    workout_id = make_workout(client).get_json()["id"]
    assert client.delete(f"/workouts/{workout_id}").status_code == 204
    assert client.get(f"/workouts/{workout_id}").status_code == 404


# ---------- adding an exercise to a workout ----------

def add_link(client, workout_id, exercise_id, **payload):
    return client.post(
        f"/workouts/{workout_id}/exercises/{exercise_id}/workout_exercises", json=payload
    )


def test_add_exercise_to_workout(client):
    workout_id = make_workout(client).get_json()["id"]
    exercise_id = make_exercise(client).get_json()["id"]

    response = add_link(client, workout_id, exercise_id, sets=4, reps=8)
    assert response.status_code == 201
    link = response.get_json()
    assert link["sets"] == 4 and link["reps"] == 8
    assert link["exercise"]["name"] == "Squat"
    assert link["workout"]["id"] == workout_id


def test_workout_detail_includes_exercises(client):
    workout_id = make_workout(client).get_json()["id"]
    exercise_id = make_exercise(client).get_json()["id"]
    add_link(client, workout_id, exercise_id, sets=3, duration_seconds=60)

    detail = client.get(f"/workouts/{workout_id}").get_json()
    assert len(detail["workout_exercises"]) == 1
    assert detail["workout_exercises"][0]["exercise"]["name"] == "Squat"
    assert "workout" not in detail["workout_exercises"][0]


def test_exercise_detail_includes_workouts(client):
    workout_id = make_workout(client).get_json()["id"]
    exercise_id = make_exercise(client).get_json()["id"]
    add_link(client, workout_id, exercise_id, reps=10)

    detail = client.get(f"/exercises/{exercise_id}").get_json()
    assert detail["workout_exercises"][0]["workout"]["id"] == workout_id


def test_same_exercise_can_be_used_in_many_workouts(client):
    exercise_id = make_exercise(client).get_json()["id"]
    first = make_workout(client).get_json()["id"]
    second = make_workout(client, date="2026-10-02").get_json()["id"]
    assert add_link(client, first, exercise_id, reps=5).status_code == 201
    assert add_link(client, second, exercise_id, reps=5).status_code == 201


def test_add_requires_reps_or_duration(client):
    workout_id = make_workout(client).get_json()["id"]
    exercise_id = make_exercise(client).get_json()["id"]
    response = add_link(client, workout_id, exercise_id, sets=3)
    assert response.status_code == 400


def test_add_rejects_negative_numbers(client):
    workout_id = make_workout(client).get_json()["id"]
    exercise_id = make_exercise(client).get_json()["id"]
    response = add_link(client, workout_id, exercise_id, reps=-1)
    assert response.status_code == 400


def test_add_with_missing_workout_or_exercise(client):
    workout_id = make_workout(client).get_json()["id"]
    exercise_id = make_exercise(client).get_json()["id"]
    assert add_link(client, 999, exercise_id, reps=5).status_code == 404
    assert add_link(client, workout_id, 999, reps=5).status_code == 404


def test_deleting_workout_removes_its_links(client):
    workout_id = make_workout(client).get_json()["id"]
    exercise_id = make_exercise(client).get_json()["id"]
    add_link(client, workout_id, exercise_id, reps=5)
    client.delete(f"/workouts/{workout_id}")
    assert WorkoutExercise.query.count() == 0
    assert client.get(f"/exercises/{exercise_id}").status_code == 200


def test_deleting_exercise_removes_its_links(client):
    workout_id = make_workout(client).get_json()["id"]
    exercise_id = make_exercise(client).get_json()["id"]
    add_link(client, workout_id, exercise_id, reps=5)
    client.delete(f"/exercises/{exercise_id}")
    assert WorkoutExercise.query.count() == 0
    assert client.get(f"/workouts/{workout_id}").get_json()["workout_exercises"] == []


# ---------- model validations (raised directly, bypassing the schema) ----------

def test_model_rejects_blank_exercise_name():
    with pytest.raises(ValueError):
        Exercise(name="  ", category="Core")


def test_model_rejects_non_positive_duration():
    with pytest.raises(ValueError):
        Workout(date=__import__("datetime").date.today(), duration_minutes=0)


def test_model_rejects_bad_date():
    with pytest.raises(ValueError):
        Workout(date="2026-10-01", duration_minutes=30)


def test_model_rejects_negative_reps():
    with pytest.raises(ValueError):
        WorkoutExercise(reps=-3)


# ---------- table constraints (bypass validators with raw SQL) ----------

def test_db_rejects_zero_duration_workout(client):
    with pytest.raises(IntegrityError):
        db.session.execute(
            db.text("INSERT INTO workouts (date, duration_minutes) VALUES ('2026-10-01', 0)")
        )
    db.session.rollback()


def test_db_rejects_link_without_reps_or_duration(client):
    workout_id = make_workout(client).get_json()["id"]
    exercise_id = make_exercise(client).get_json()["id"]
    with pytest.raises(IntegrityError):
        db.session.execute(
            db.text(
                "INSERT INTO workout_exercises (workout_id, exercise_id, sets) "
                f"VALUES ({workout_id}, {exercise_id}, 3)"
            )
        )
    db.session.rollback()


def test_db_rejects_blank_exercise_name(client):
    with pytest.raises(IntegrityError):
        db.session.execute(
            db.text("INSERT INTO exercises (name, category, equipment_needed) VALUES ('  ', 'Core', 0)")
        )
    db.session.rollback()


def test_db_enforces_unique_exercise_name(client):
    make_exercise(client)
    with pytest.raises(IntegrityError):
        db.session.execute(
            db.text("INSERT INTO exercises (name, category, equipment_needed) VALUES ('Squat', 'Core', 0)")
        )
    db.session.rollback()
    