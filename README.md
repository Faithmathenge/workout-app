# Workout Tracker API

A Flask backend for a workout application used by personal trainers. It tracks workouts and the reusable exercises that make them up, including sets, reps or duration for each exercise in a workout. Built with Flask, SQLAlchemy, Flask-Migrate and Marshmallow.

## Installation

```bash
git clone https://github.com/Faithmathenge/workout-app.git
cd workout-app
pipenv install
pipenv shell
cd server
flask db init
flask db migrate -m "Create workouts, exercises, workout_exercises"
flask db upgrade
python seed.py
```

## Run

```bash
cd server
flask run
```

The API runs at `http://127.0.0.1:5000`.

## Tests

```bash
cd server
pytest
```

## Data model

- **Exercise**: `name` (unique), `category`, `equipment_needed`
- **Workout**: `date`, `duration_minutes`, `notes`
- **WorkoutExercise** (join table): `workout_id`, `exercise_id`, `reps`, `sets`, `duration_seconds`

A workout has many exercises and an exercise can appear in many workouts, through `WorkoutExercise`.

## Endpoints

| Method | Route                                                              | Description                                                                      | Success |
| ------ | ------------------------------------------------------------------ | -------------------------------------------------------------------------------- | ------- |
| GET    | `/workouts`                                                        | List all workouts (newest first)                                                 | 200     |
| GET    | `/workouts/<id>`                                                   | One workout with its exercises, reps, sets and durations                         | 200     |
| POST   | `/workouts`                                                        | Create a workout (`date`, `duration_minutes`, optional `notes`)                  | 201     |
| DELETE | `/workouts/<id>`                                                   | Delete a workout and its exercise links                                          | 204     |
| GET    | `/exercises`                                                       | List all exercises                                                               | 200     |
| GET    | `/exercises/<id>`                                                  | One exercise with the workouts it appears in                                     | 200     |
| POST   | `/exercises`                                                       | Create an exercise (`name`, `category`, optional `equipment_needed`)             | 201     |
| DELETE | `/exercises/<id>`                                                  | Delete an exercise and its workout links                                         | 204     |
| POST   | `/workouts/<workout_id>/exercises/<exercise_id>/workout_exercises` | Add an exercise to a workout (`reps` and/or `duration_seconds`, optional `sets`) | 201     |

Errors return JSON: `400` for invalid data, `404` when a record is not found, `409` for a duplicate exercise name.

## Validations

- **Table constraints:** unique exercise name, non-blank name and category, workout duration > 0, reps/sets/duration >= 0, and every workout exercise needs reps or a duration.
- **Model validations:** `@validates` on names, dates, durations, reps, sets and duration_seconds.
- **Schema validations:** Marshmallow field validators (length, range, strict integers), custom `@validates` for blank names, and `@validates_schema` requiring reps or duration.

## Project structure

```
server/
├── app.py       # app factory, extensions, error handlers
├── models.py    # SQLAlchemy models, relationships, constraints, validations
├── schemas.py   # Marshmallow schemas
├── routes.py    # API endpoints (blueprint)
├── seed.py      # example data for all models
└── tests/       # pytest suite
```
