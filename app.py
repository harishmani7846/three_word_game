from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import json

app = Flask(__name__)
app.secret_key = "supersecret"

# -------------------- Initialize Database --------------------
def init_db():
    with sqlite3.connect("game.db", timeout=5) as conn:
        cursor = conn.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT UNIQUE,
                            password TEXT
                          )""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS games (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            player1 TEXT,
                            player2 TEXT,
                            player3 TEXT,
                            rounds INTEGER,
                            story TEXT,
                            date_played DATETIME DEFAULT CURRENT_TIMESTAMP
                          )""")
        conn.commit()

init_db()

# -------------------- Login --------------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        with sqlite3.connect("game.db", timeout=5) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
            user = cursor.fetchone()
        if user:
            session["username"] = username
            return redirect(url_for("game_setup"))
        else:
            flash("Invalid username or password!", "error")
    return render_template("login.html")

# -------------------- Register --------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        try:
            with sqlite3.connect("game.db", timeout=5) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
                conn.commit()
            flash("Registration successful! Login now.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Username already exists!", "error")
        except sqlite3.OperationalError as e:
            flash(f"Database error: {e}", "error")
    return render_template("register.html")

# -------------------- Game Setup --------------------
@app.route("/game_setup", methods=["GET", "POST"])
def game_setup():
    if "username" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        session["players"] = [
            request.form.get("player1"),
            request.form.get("player2"),
            request.form.get("player3")
        ]
        session["rounds"] = int(request.form.get("rounds"))
        session["story"] = []
        session["turn"] = 0
        session["current_round"] = 1
        return redirect(url_for("game"))

    return render_template("game_setup.html")

# -------------------- Game --------------------
@app.route("/game", methods=["GET", "POST"])
def game():
    if "username" not in session:
        return redirect(url_for("login"))

    players = session.get("players", [])
    rounds = session.get("rounds", 1)
    story = session.get("story", [])
    turn = session.get("turn", 0)
    current_round = session.get("current_round", 1)
    finished = False

    if request.method == "POST":
        word = request.form.get("word")
        story.append(f"{players[turn]}: {word}")
        turn += 1
        if turn >= len(players):
            turn = 0
            current_round += 1
        if current_round > rounds:
            finished = True
            final_story = " ".join([line.split(": ")[1] for line in story])
            # Save game to DB safely
            try:
                with sqlite3.connect("game.db", timeout=5) as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO games (player1, player2, player3, rounds, story) VALUES (?, ?, ?, ?, ?)",
                        (players[0], players[1], players[2], rounds, json.dumps(final_story))
                    )
                    conn.commit()
            except sqlite3.OperationalError as e:
                flash(f"Database error: {e}", "error")
            return render_template("game.html", players=players, rounds=rounds, story=story,
                                   current_player=players[0], finished=True, final_story=final_story)

    # Update session
    session["story"] = story
    session["turn"] = turn
    session["current_round"] = current_round

    return render_template("game.html", players=players, rounds=rounds, story=story,
                           current_player=players[turn], finished=False)

# -------------------- History --------------------
@app.route("/history")
def history():
    if "username" not in session:
        return redirect(url_for("login"))

    with sqlite3.connect("game.db", timeout=5) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT player1, player2, player3, rounds, story, date_played FROM games ORDER BY date_played DESC")
        games = cursor.fetchall()
    # Convert JSON story back to string
    games = [(p1, p2, p3, rounds, json.loads(story), date) for p1, p2, p3, rounds, story, date in games]
    return render_template("history.html", games=games)

# -------------------- Logout --------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# -------------------- Run App --------------------
if __name__ == "__main__":
    app.run(debug=True)
