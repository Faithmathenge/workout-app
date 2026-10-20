from datetime import date, timedelta

from app import app
from models import Exercise, Workout, WorkoutExercise, db


def seed():
    with app.app_context():
        # Clear existing rows (children first) so the seed can be re-run safely.
        WorkoutExercise.query.delete()
        Workout.query.delete()
        Exercise.query.delete()

        squat = Exercise(name="Squat", category="Strength", equipment_needed=True)
        push_up = Exercise(name="Push-up", category="Strength", equipment_needed=False)
        plank = Exercise(name="Plank", category="Core", equipment_needed=False)
        run = Exercise(name="Treadmill Run", category="Cardio", equipment_needed=True)
        db.session.add_all([squat, push_up, plank, run])

        today = date.today()
        leg_day = Workout(date=today - timedelta(days=2), duration_minutes=60, notes="Leg day")
        full_body = Workout(date=today - timedelta(days=1), duration_minutes=45, notes="Full body circuit")
        cardio = Workout(date=today, duration_minutes=30, notes="Easy cardio")
        db.session.add_all([leg_day, full_body, cardio])

        db.session.add_all([
            WorkoutExercise(workout=leg_day, exercise=squat, sets=4, reps=8),
            WorkoutExercise(workout=leg_day, exercise=plank, sets=3, duration_seconds=60),
            WorkoutExercise(workout=full_body, exercise=push_up, sets=3, reps=15),
            WorkoutExercise(workout=full_body, exercise=squat, sets=3, reps=12),
            WorkoutExercise(workout=full_body, exercise=plank, sets=2, duration_seconds=45),
            WorkoutExercise(workout=cardio, exercise=run, duration_seconds=1200),
        ])

        db.session.commit()
        print("Seeded 4 exercises, 3 workouts and 6 workout-exercise links.")


if __name__ == "__main__":
    seed()
    