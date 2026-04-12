from app import app, db, seed_data

if __name__ == "__main__":
    with app.app_context():
        db.create_all()   # creates any new tables (e.g. online_exams)
        seed_data()       # seeds only if DB is empty
    app.run(debug=True, port=5000)