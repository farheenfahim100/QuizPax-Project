from flask import Flask, render_template, request, flash, redirect, session, make_response, render_template_string, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from werkzeug import security
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from datetime import date, time, datetime
import random
import os
from datetime import date
import random
import string
import time

from flask_wtf import FlaskForm, CSRFProtect
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, Regexp
from flask_wtf.csrf import CSRFError

from flask_socketio import SocketIO, join_room, emit, rooms # emit for unnamed events, send for named events
from flask_mail import Mail, Message


app = Flask(__name__)



app.config['MAIL_SUPPRESS_SEND'] = os.environ.get("MAIL_SUPPRESS_SEND", "true").lower() == "true"
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = os.environ.get("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.environ.get("MAIL_PASSWORD")
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config["TESTING"] = False
mail = Mail(app)

# select the database filename
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///project_database.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


#socketio = SocketIO(app)
# GEVENT: 
socketio = SocketIO(app, async_mode="gevent", cors_allowed_origins="*")

# , logger=True, engineio_logger=True
#socketio = SocketIO(app, cors_allowed_origins="*") # used for k6
print("ASYNC MODE:", socketio.async_mode)
app.secret_key=os.environ.get("SECRET_KEY", "dev-secret-key")
csrf = CSRFProtect(app)



@app.errorhandler(CSRFError)
def handle_csrf_error(e):
  return render_template('error.html', errorMessage=e.description), 400





from db_schema import (
  db,
  Teacher,
  Student,
  Q_and_A_Set,
  Folder,
  Question,
  Game,
  GamePlayer,
  GameTeam,
  GameQuestionStat,
  GameQuestionStudent,
  GameFlaggedQuestion,
  dbinit,
)

# Question alert thresholds
ANSWERED_THRESHOLD = 0.70   # at least 70% of students have attempted
ACCURACY_THRESHOLD = 0.40   # below 40% accuracy -> alert
CHAMPION_GOLD_THRESHOLD = 3   # how many first places must be awarded before champion badge is awarded

# init the database so it can connect with our app
db.init_app(app)

# change this to False to avoid resetting the database every time this app is restarted
resetdb = os.environ.get("FLASK_ENV") == "development"
if resetdb:
  with app.app_context():
    # drop everything, create all the tables, then put some data into the tables
    db.drop_all()
    db.create_all()
    dbinit()

teacher_sids = {}  
# { sid : { "teacher_id": X, "pin": Y } }

student_sids = {}
# { sid : { "student_id": X, "pin": Y } }

all_otp = {}


# k6:
#from project.loadtesting.ws_test import register_ws_test
#from ws_test_sqlite import register_ws_test_sqlite
#register_ws_test_sqlite(app)

# locust:
#from ws_test_locust import register_ws_test_locust
#from loadtesting.ws_test_locust_sql import register_ws_test_locust_sql, seed_dummy_data
#register_ws_test_locust(socketio)
#register_ws_test_locust_sql(socketio)





#route to the index
@app.route('/')
def index():
  return render_template('index.html')

#route to the index
@app.route('/help')
def help():
  return render_template('help.html')

@app.route('/templates/<filename>')
def templateFilename(filename):
  return render_template(f'{filename}.html')


@app.route("/public_sets")
@login_required
def public_sets():
  """
  Display public Q&A sets with pagination.
  """
  PAGE_SIZE = 20

  # Get page number from query string (?page=1)
  page = request.args.get("page", 1, type=int)

  # Query public sets only
  pagination = (Q_and_A_Set.query.filter_by(is_private=False)
    .order_by(Q_and_A_Set.date.desc())
    .paginate(page=page, per_page=PAGE_SIZE, error_out=False)
  )

  return render_template("public_sets.html",sets=pagination.items,pagination=pagination)


@app.route("/public_set/<int:set_id>")
@login_required
def view_public_set(set_id):
  if not session.get("teacher_logged_in"):
    return redirect("/entercode")

  qset = (Q_and_A_Set.query.filter_by(id=set_id, is_private=False).first())

  if not qset:
    return render_template("error.html",errorMessage="Public set with this ID was not found.")

  questions = Question.query.filter_by(set_id=qset.id).all()

  return render_template("public_set_view.html",qset=qset,questions=questions)



login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login" #returns user to login page if not already logged in when accessing those pages


@login_manager.user_loader
def load_user(user_id):
  is_teacher_logged_in = session.get('teacher_logged_in', False)
  if is_teacher_logged_in:
    return Teacher.query.get(int(user_id))
  else:
    return Student.query.get(int(user_id))




class RegisterForm(FlaskForm):
  email = StringField('Email', validators=[DataRequired()])

  password = PasswordField('Password', validators=[
    DataRequired(),
    Length(min=8, message="Password must be at least 8 characters"),
    Regexp(r'.*[A-Z].*', message="Must contain an uppercase letter"),
    Regexp(r'.*[0-9].*', message="Must contain a number"),
    Regexp(r'.*[^A-Za-z0-9].*', message="Must contain a symbol")
  ])


@app.route('/registration', methods=['GET','POST'])
def registration():
  # check if user is already logged in, or if the get method is used and not the post method.
  if current_user.is_authenticated:
    return redirect('/dashboard')
  if request.method=="GET":
    return render_template("registration.html")
  
  if request.method=="POST":
    form = RegisterForm()

    if not form.validate():
      return "Password must be at least 8 characters and include a capital letter, a number, and a symbol.", 400

    #teacher=request.form["teacherorstudent"]
    #name=request.form['name']
    email=request.form['email']
    #password=request.form['password']
    #mypassword_hash = security.generate_password_hash(password)
    allStudents = Student.query.filter_by().all()
    allTeachers = Teacher.query.filter_by().all()
    allEmailAddresses = [student.email for student in allStudents] 
    allEmailAddresses = allEmailAddresses + [teacher.email for teacher in allTeachers]
    if (email in allEmailAddresses):
      return "This email already has a registered account. "
    else:
      return generate_otp(email,". Use this to register your account in your current session")
    

@app.route('/registration-check', methods=['POST'])
def check_reg_otp():
  name=request.form['name']
  email=request.form['email']
  teacher=request.form["teacherorstudent"]
  password=request.form['password']
  otp = request.form['OTPsubmission']
  mypassword_hash=security.generate_password_hash(password)
  if (all_otp[email] == int(otp)):
    del all_otp[email]
    try:
      if teacher == "teacher":
        newuser = Teacher(name=name, email=email, password_hash=mypassword_hash)
        session['teacher_logged_in'] = True
        db.session.add(newuser)
        db.session.commit()
        login_user(newuser)
        return redirect('/dashboard')
      else:
        newuser = Student(name=name, email=email, password_hash=mypassword_hash)
        session['teacher_logged_in'] = False
        db.session.add(newuser)
        db.session.commit()
        login_user(newuser)
        return redirect('/entercode')
    except IntegrityError as exc:
      db.session.rollback()
      return render_template("error.html", errorMessage="There is already a user with this email. Please use a different email address to register or login with this email.")
  else:
    return render_template("error.html", errorMessage="The one-time passcode you entered is incorrect. Please try registering again.")




def generate_otp(email,emailMsg):
  otp = random.randint(100000,999999)
  print(str(otp))
  all_otp[email] = otp
  body = "Your one time passcode to login is " + str(otp) + emailMsg
  email_sent = send_email(email, body, "QuizPax registration passcode")
  if (email_sent):
    return "otp sent to email"
  else:
    return "Email was not sent (@), please try again."




def send_email(recipient, body, subject_to_send):
  with app.app_context():
    msg = Message(subject_to_send, sender=f"{os.getlogin()}@dcs.warwick.ac.uk", recipients=[recipient])
    msg.body = body
    if ("@" not in recipient):
      return False
    else:
      try:
        mail.send(msg)
        print("Test email sent successfully to "+ recipient)
        return True
      except Exception as error:
        print(f'Error sending email: {str(error)}')
        return False
  




@app.route('/reset-password',methods=['POST','GET'])
def reset_password():
  if request.method=="GET":
    return render_template('resetpassword.html')
  if request.method=="POST":
    email = request.form['email']
    allTeachers = Teacher.query.filter_by().all() 
    allStudents = Student.query.filter_by().all()
    allEmailAddresses = [user.email for user in allTeachers] + [user.email for user in allStudents]
    if (email in allEmailAddresses):
      return generate_otp(email, ". Use this to reset your password in your current session")
      # return ajax response for the otp check 
    else:
      # THE EMAIL ADDRESS IS NOT REGISTERED YET so display an error message 
      return "Email address entered has not yet been registered.", 400

@app.route('/resetp-check', methods=['POST'])
def check_resetp_otp():
  email = request.form['email']
  otp = request.form['OTPsubmission']
  password = request.form['password']
  if email not in all_otp:
    return render_template('error.html',errorMessage="Your reset code has expired or was not requested. Please request a new one.")
  if (all_otp[email] != int(otp)):
    return render_template('error.html', errorMessage = "One-time passcodes did not match. Please try to reset password again.")
  
  form = RegisterForm()
  if not form.validate():
    return render_template("error.html",errorMessage=("Password must be at least 8 characters and include a capital letter, a number, and a symbol."))

  # Password is valid beyond this point so we can update password if they are a user
  thisTeacher = Teacher.query.filter_by(email=email).first()
  thisStudent = Student.query.filter_by(email=email).first()
  mypassword_hash=security.generate_password_hash(password)
  # Case 1: They are a student:
  if thisTeacher is None and thisStudent.email==email:
    thisStudent.password_hash = mypassword_hash
    db.session.commit()
    login_user(thisStudent)
    return redirect('/entercode') 
  # Case 2: They are a teacher:
  elif thisStudent is None and thisTeacher.email==email:
    thisTeacher.password_hash = mypassword_hash
    db.session.commit()
    login_user(thisTeacher)
    return redirect('/dashboard') 
  # Case 3: They are neither a student or teacher:
  else:
    return render_template('error.html', errorMessage = "Sorry, no users exist with this email. Please register an account.")



@app.route('/login', methods=['GET','POST'])
def login():
  if current_user.is_authenticated:
    return redirect('/')
  if request.method=="GET":
    return render_template("login.html")
  if request.method=="POST":
    email=request.form['email']
    password=request.form['password']
    teacher = Teacher.query.filter_by(email=email).first()
    student = Student.query.filter_by(email=email).first()
    if teacher is not None:
      if (security.check_password_hash(teacher.password_hash,password) and (email == teacher.email) ):
        user = teacher
        login_user(user)
        session['teacher_logged_in'] = True
        return redirect('/dashboard')
      else:
        return redirect('/login')

    elif student is not None:
      if (security.check_password_hash(student.password_hash,password) and (email == student.email) ) :
        user = student
        login_user(user)
        session['teacher_logged_in'] = False
        return redirect('/entercode')
      else:
        return redirect('login')
    return redirect('/registration')


@app.route('/logout')
@login_required
def logout():
  session.pop('teacher_logged_in', None)
  logout_user()
  return redirect ('/')

def debug_print_database_state():
  print("\n================= DATABASE STATE =================")

  # ---- Teachers ----
  print("\nTeachers:")
  for t in Teacher.query.all():
    print(f"  ID={t.id}, Name={t.name}, Email={t.email}")

  # ---- Students ----
  print("\nStudents:")
  for s in Student.query.all():
    print(f"  ID={s.id}, Name={s.name}, Email={s.email}")

  # ---- Folders ----
  print("\nFolders:")
  for f in Folder.query.all():
    print(f"  ID={f.id}, Name={f.name}, UserID={f.user_id}")

  # ---- Sets ----
  print("\nQ&A Sets:")
  for s in Q_and_A_Set.query.all():
    print(f"  ID={s.id}, Name={s.name}, FolderID={s.folder_id}, Private={s.is_private}")

  # ---- Questions ----
  print("\nQuestions:")
  for q in Question.query.all():
    print(f"  ID={q.id}, SetID={q.set_id}, Q='{q.question}'")

  # ---- Games ----
  print("\nGames:")
  for g in Game.query.all():
    print(f"  ID={g.id}, PIN={g.game_pin}, QSet={g.qaset_id}, Players={g.players}, Active={g.is_active}")

  # ---- Game Players ----
  print("\nGame Players:")
  for gp in GamePlayer.query.all():
      print(f"  ID={gp.id}, GameID={gp.game_id}, StudentID={gp.student_id}, Score={gp.score}")

  # ---- Game Question Stats ----
  print("\nGame Question Stats:")
  for s in GameQuestionStat.query.all():
    print(
      f"  StatID={s.id}, GameID={s.game_id}, QID={s.question_id}, "
      f"Answers={s.total_answers}, Correct={s.correct_students}, "
      f"Distinct={s.distinct_students}, Accuracy={s.accuracy:.2f}, "
      f"RetentionChecks={s.retention_checks}, Drops={s.retention_drops}, "
      f"RetentionRate={s.retention_rate:.2f}"
    )

    # ---- Game Question Student ----
  print("\nGame Question Student Records:")
  for gqs in GameQuestionStudent.query.all():
    print(
      f"  ID={gqs.id}, GameID={gqs.game_id}, StudentID={gqs.student_id}, "
      f"QID={gqs.question_id}, Attempts={gqs.attempts}, "
      f"LastCorrect={gqs.last_correct}, EverCorrect={gqs.has_ever_been_correct}"
    )
  
  # ---- Game Flagged Questions ----
  print("\nGame Flagged Questions:")
  flags = GameFlaggedQuestion.query.all()
  for f in flags:
    print(
      f"  ID={f.id}, GameID={f.game_id}, "
      f"QuestionID={f.question_id}, Count={f.count}"
    )
  print("\n==================================================\n")

def debug_print_rooms():
  rooms = socketio.server.manager.rooms
  print("\n--- SOCKETIO ROOMS ---")
  for namespace, ns_rooms in rooms.items():
    print(f"Namespace: {namespace}")
    for room, sids in ns_rooms.items():
      print(f"  Room {room}: {list(sids)}")
  print("---------------------\n")



@app.route("/entercode", methods=["GET", "POST"])
@login_required
def enter_code():
  # Teachers never use this page
  if session.get('teacher_logged_in'):
    return redirect('/dashboard')

  # Students only beyond here:
  if request.method == "GET":
    return render_template("enter-code.html")

  if request.method == "POST":
    # Get submitted code
    entered_code = request.form.get("code")
    # Check database for this game pin here:
    thisGame = Game.query.filter_by(game_pin=entered_code).first()
    if (thisGame is None):
      # Game does not exist, the user entered an invalid code
      return render_template('error.html', errorMessage = "No game with this game pin.")
    else:
      # CASE 1: Capacity reached - do not allow
      if (thisGame.capacity == thisGame.players):
        return render_template('error.html', errorMessage = "player capacity reached")
      
      gameid = thisGame.id
      existing_player = GamePlayer.query.filter_by(game_id=gameid,student_id=current_user.id).first()
      
      # CASE 2: Rejoining an active game - allow and send straight to play_game
      if (existing_player and thisGame.is_active ==True):
        return redirect(f"/play_game?pin={entered_code}")
      
      # CASE 3: Rejoining lobby (game not started) - allow and send to lobby
      if (existing_player and thisGame.is_active == False):
        return redirect(f"/student_waiting?pin={entered_code}")
          
      # CASE 4: Late joiner (game already active) - create new gp (since capacity is not reached) and allow and send to play_game
      if (thisGame.is_active == True):
        new_player_active_game(thisGame, current_user)
        #newPlayer = GamePlayer(gameid, current_user.id)
        #db.session.add(newPlayer)
        #db.session.commit()
        #thisGame.players = thisGame.players + 1
        #db.session.commit()
        return redirect(f"/play_game?pin={entered_code}")

      # CASE 5: new player entering lobby  
      #print("\nAdding student to lobby...")
      newPlayer = GamePlayer(gameid, current_user.id)
      db.session.add(newPlayer)
      db.session.commit()
      thisGame.players = thisGame.players + 1
      db.session.commit()

      #print(f"Student {current_user.id} joined game {thisGame.id}. Total players = {thisGame.players}")

      # DEBUG — AFTER modification
      #print("\n--- AFTER JOIN ---")
      #debug_print_database_state()
      return redirect(f"/student_waiting?pin={entered_code}")


def new_player_active_game(game, student):
  gp = GamePlayer(game_id=game.id,student_id=student.id)

  # Initialise question index
  order_len = len(game.question_order.split(","))
  gp.question_index = random.randint(0, order_len - 1)

  db.session.add(gp)
  db.session.commit()

  game.players += 1
  db.session.commit()

  # Notify teacher (teacher already in room)
  socketio.emit("player_joined_game",
    {
      "student_id": student.id,
      "name": student.name,
      "score": 0
    },
  room=game.game_pin)




# TEACHER DASHBOARD RELATED - Folder, Sets, Questions CRUD:

@app.route("/dashboard")
@login_required
def dashboard():
  if session.get('teacher_logged_in'):
    # return the teacher dashboard
    userID = current_user.id
    teacher_folders = Folder.query.filter_by(user_id=userID).all()
    active_game = Game.query.filter_by(user_id=userID,is_active=True).first()
    return render_template("dashboard.html", folderList = teacher_folders, active_game=active_game)
  else:
    # return badges dashboard
    student = Student.query.get(current_user.id)
    return render_template("badges.html",student=student,participation_badges=get_participation_badges(student.games_played))
    

def get_participation_badges(games_played):
  thresholds = [1000, 500, 250, 100, 50, 25, 10, 5, 1]
  earned = []

  for t in thresholds:
    if games_played >= t:
      earned.append(t)

  return earned


@app.route('/addfolder', methods=['POST'])
@login_required
def add_folder():
  if not session.get('teacher_logged_in'):
    return redirect('/entercode')
    
  folder_name = request.form.get('foldername')
  if folder_name == "":
    return render_template("error.html", errorMessage="Folder name cannot be empty.")

  new_folder = Folder(name=folder_name, user_id=current_user.id)
  db.session.add(new_folder)
  db.session.commit()
  return redirect('/dashboard')


@app.route("/folderdetails")
@login_required
def folderdetails():
  if not session.get('teacher_logged_in'):
    return redirect('/entercode')
  folder_id = request.args.get("folderid")

  folder = Folder.query.filter_by(id=folder_id, user_id=current_user.id).first()

  if folder is None:
    return render_template("error.html", errorMessage="Folder not found or denied due to unauthorized access.")

  # Load all Q&A sets for this folder
  sets = Q_and_A_Set.query.filter_by(folder_id=folder.id).all()

  return render_template("folderdetails.html", folder=folder, sets=sets)


@app.route("/editfolder", methods=["POST"])
@login_required
def edit_folder():
  if not session.get('teacher_logged_in'):
    return "Unauthorized - only teachers can own sets and edit them. ", 403
  folder_id = request.form.get("folderid")
  new_name = request.form.get("newname")
  folder = Folder.query.filter_by(id=folder_id, user_id=current_user.id).first()
  if folder is None:
    return "Invalid Folder - no folder with this ID exists.", 403
  folder.name = new_name
  db.session.commit()

  return "success"


@app.route("/deletefolder", methods=["POST"])
@login_required
def deletefolder():
  if not session.get('teacher_logged_in'):
    return redirect('/entercode')

  folder_id = request.form.get("folderid")
  
  folder = Folder.query.filter_by(id=folder_id, user_id=current_user.id).first()
  if folder is None:
    return render_template("error.html", errorMessage="Folder not found or unauthorized.")

  # Delete the folder itself
  db.session.delete(folder)
  db.session.commit()

  return redirect('/dashboard')



@app.route("/addset", methods=["POST"])
@login_required
def add_set():
  if not session.get('teacher_logged_in'):
    return redirect('/entercode')

  folder_id = request.form.get("folderid")
  set_name = request.form.get("setname")
  is_private = True if request.form.get("is_private") else False

  folder = Folder.query.filter_by(id=folder_id, user_id=current_user.id).first()
  if folder is None:
    return render_template("error.html", errorMessage="Invalid folder.")

  new_set = Q_and_A_Set(name=set_name,folder_id=folder_id,date=date.today(),is_private=is_private)

  db.session.add(new_set)
  db.session.commit()
  return redirect(f"/folderdetails?folderid={folder_id}")


@app.route("/qsetdetails", methods=["GET"])
@login_required
def qsetdetails():
  if not session.get('teacher_logged_in'):
    return redirect('/entercode')

  set_id = request.args.get("setid")

  qset = Q_and_A_Set.query.join(Folder).filter(Q_and_A_Set.id == set_id,Folder.user_id == current_user.id).first()

  if qset is None:
    return render_template("error.html", errorMessage="Q&A Set not found or unauthorized.")

  questions = Question.query.filter_by(set_id=set_id).all()
  
  folder = Folder.query.filter_by(id=qset.folder_id, user_id=current_user.id).first()
  if folder is None:
    return render_template("error.html", errorMessage="Folder not found or unauthorized.")


  return render_template("set-details.html", qset=qset, questions=questions, folder=folder)


@app.route("/editset", methods=["POST"])
@login_required
def edit_set():
  if not session.get('teacher_logged_in'):
    return "Unauthorized - only teachers can own sets and edit them. ", 403

  set_id = request.form.get("setid")
  new_name = request.form.get("newname")
  new_private = True if request.form.get("newprivate") == "1" else False

  qset = Q_and_A_Set.query.join(Folder).filter(Q_and_A_Set.id == set_id,Folder.user_id == current_user.id).first()

  if qset is None:
    return "Invalid Q&A Set - no set with this ID exists.", 403

  qset.name = new_name
  qset.is_private = new_private
  db.session.commit()

  return "success"


@app.route("/deleteset", methods=["POST"])
@login_required
def delete_set():
  if not session.get('teacher_logged_in'):
    return redirect('/entercode')

  set_id = request.form.get("setid")
  qset = Q_and_A_Set.query.join(Folder).filter(Q_and_A_Set.id == set_id,Folder.user_id == current_user.id).first()
  if qset is None:
    return render_template("error.html", errorMessage="Set not found or unauthorized.")

  folder_id = qset.folder_id

  db.session.delete(qset)
  db.session.commit()

  return redirect(f"/folderdetails?folderid={folder_id}")




def validate_answers(answer, fake1, fake2, fake3):
  answers = [answer, fake1, fake2, fake3]
  return len(set(answers)) == 4



@app.route("/addquestion", methods=["POST"])
@login_required
def add_question():
  if not session.get('teacher_logged_in'):
    return redirect('/entercode')

  set_id = request.form.get("setid")

  qset = Q_and_A_Set.query.join(Folder).filter(Q_and_A_Set.id == set_id, Folder.user_id == current_user.id).first()

  if qset is None:
    return render_template("error.html", errorMessage="Unauthorized or invalid set.")

  # Extract form data
  question = request.form.get("question")
  answer = request.form.get("answer")
  fake1 = request.form.get("fakeans1")
  fake2 = request.form.get("fakeans2")
  fake3 = request.form.get("fakeans3")

  if not validate_answers(answer, fake1, fake2, fake3):
    return render_template("error.html", errorMessage="Correct answer and fake answers must all be different.")


  new_q = Question(set_id=set_id,question=question,answer=answer,fakeans1=fake1,fakeans2=fake2,fakeans3=fake3)

  db.session.add(new_q)
  db.session.commit()

  return redirect(f"/qsetdetails?setid={set_id}")


@app.route("/editquestion", methods=["POST"])
@login_required
def edit_question():

  if not session.get('teacher_logged_in'):
    return "Unauthorized - only teachers can own questions and edit them. ", 403

  qid = request.form.get("qid")
  new_question = request.form.get("question")
  new_answer = request.form.get("answer")
  fake1 = request.form.get("fakeans1")
  fake2 = request.form.get("fakeans2")
  fake3 = request.form.get("fakeans3")

  q = Question.query.join(Q_and_A_Set).join(Folder).filter(Question.id == qid,Folder.user_id == current_user.id).first()

  if q is None:
    return "Invalid Question - no question with this ID exists.", 403

  if not validate_answers(new_answer, fake1, fake2, fake3):
    return "Correct answer and fake answers must all be different.", 403

  q.question = new_question
  q.answer = new_answer
  q.fakeans1 = fake1
  q.fakeans2 = fake2
  q.fakeans3 = fake3

  db.session.commit()
  return "success"


@app.route("/deletequestion", methods=["POST"])
@login_required
def delete_question():
  if not session.get('teacher_logged_in'):
    return redirect('/entercode')

  qid = request.form.get("qid")

  q = Question.query.join(Q_and_A_Set).join(Folder).filter(Question.id == qid, Folder.user_id == current_user.id).first()

  if q is None:
    return render_template("error.html", errorMessage="Question not found or unauthorized.")

  set_id = q.set_id

  db.session.delete(q)
  db.session.commit()

  return redirect(f"/qsetdetails?setid={set_id}")







# GAME CREATION RELATED:

# Get teacher sets for game creation modal - gives the teacher options for choosing a Q&A set for a game. 
@app.route("/get_teacher_sets")
@login_required
def get_teacher_sets():

  if not session.get('teacher_logged_in'):
    return jsonify({"folders": []})

  folders = Folder.query.filter_by(user_id=current_user.id).all()

  result = []
  for f in folders:
    valid_sets = []
    sets = Q_and_A_Set.query.filter_by(folder_id=f.id).all()
    for s in sets:
      if len(s.questions) >= 3:   # only include sets with at least 3 questions
        valid_sets.append({
          "id": s.id,
          "name": s.name
        })
    if valid_sets:
      result.append({
        "id": f.id,
        "name": f.name,
        "sets": valid_sets})
  return jsonify({"folders": result})



def generate_unique_pin():
  while True:
    pin = ''.join(random.choices(string.digits, k=6))
    # Check if PIN already exists in DB
    existing_game = Game.query.filter_by(game_pin=pin).first()
    if not existing_game:
      return pin

def get_valid_qset_for_teacher(setid, teacher_id):
  """
  Validate that a Q&A set exists and belongs to the given teacher, or it is a public Q&A set.

  Args:
    setid (int or str): ID of the Q&A set
    teacher_id (int): ID of the teacher attempting to create the game

  Returns:
    Q_and_A_Set object if valid, otherwise None
  """
  logged_in_set = (Q_and_A_Set.query.join(Folder).filter(Q_and_A_Set.id == setid,Folder.user_id == teacher_id).first())
  if logged_in_set:
    return logged_in_set
  public_set = (Q_and_A_Set.query.filter(Q_and_A_Set.id == setid,Q_and_A_Set.is_private == False).first())
  return public_set



@app.route("/creategame", methods=["POST"])
@login_required
def create_game():
  """
  Create a new game for a teacher by adding the Game object to the database and returning the game pin to the teacher.

  - Validates the teacher is logged in
  - Ensures the selected Q&A set belongs to the teacher
  - Generates a unique game PIN
  - Creates and stores a new Game object in database
  - Returns the game PIN to the frontend
  """
  # Only teachers can create games
  if not session.get('teacher_logged_in'):
    return "Unauthorized - students cannot create games, but can participate in live games.", 403

  # Extract data
  setid = int(request.form.get("setid"))
  gamemode = request.form.get("mode")
  timelimit = int(request.form.get("timelimit", 1))

  # Validate Q&A set
  qset = get_valid_qset_for_teacher(setid, current_user.id)
  if qset is None: 
    return "Invalid Q&A Set - this is not private and does not belong to you.", 403 # If the Q&A set does not belong to this user, or is not public.

  # Check Q&A set has at least 3 questions
  question_count = Question.query.filter_by(set_id=qset.id).count()
  if question_count <= 2:
      return "Not enough questions in this set.", 403

  # Generate unique game pin, create Game object an store in database
  pin = generate_unique_pin()
  new_game = Game(game_pin = pin,user_id = current_user.id,qaset_id = setid,capacity = 30,is_active = False,gamemode = gamemode,timelimit = timelimit)
  db.session.add(new_game)
  db.session.commit()

  # Send response to front end
  return jsonify({"pin": pin}), 200


# GAME LOBBY RELATED:

@app.route("/game_lobby")
@login_required
def game_lobby():
  """
  Display the pre-game lobby for a teacher after they created their game.

  This page:
  - Is accessible only to teachers
  - Verifies the game belongs to the current teacher
  - Shows the list of students who have joined the game along with their connection status
  """

  # Only teachers can see the game lobby
  if not session.get("teacher_logged_in"):
    return redirect('/dashboard')
  
  # Extract game pin from query parameters
  pin = request.args.get("pin")
  # Find the Game in database, verfiy it exists or return an error
  game = Game.query.filter_by(game_pin=pin, user_id=current_user.id).first()
  if game is None:
    return render_template("error.html", errorMessage="Invalid game or unauthorized access.")
  
  # Get all players in this game
  players = (
    db.session.query(Student, GamePlayer.is_connected).join(GamePlayer, GamePlayer.student_id == Student.id)
    .filter(GamePlayer.game_id == game.id)
    .all()
  )
  # Show game lobby using the queried players and game
  return render_template("game_lobby.html", game=game, players=players)


@socketio.on("teacher_join_lobby")
def handle_teacher_join(data):
  """
  Handle a teacher joining/rejoining a game lobby - sends socket.io event to students. 

  This event:
  - Adds the teacher's socket to the correct game room
  - Tracks the teacher's socket ID for reconnection handling
  - Notifies all clients in the lobby that the teacher is connected
  """
  # Extract game PIN from incoming socket data
  pin = data["pin"]
  teacher_id = current_user.id

  # Join the Socket.IO room associated with this game PIN
  debug_print_rooms()
  join_room(pin)
  debug_print_rooms()

  # Track this teacher's socket connection
  teacher_sids[request.sid] = {"teacher_id": teacher_id,"pin": pin}

  print(f"Teacher {teacher_id} joined lobby {pin} with SID {request.sid}")

  # Notify all clients in the lobby that the teacher is connected
  socketio.emit("teacher_reconnected", {"teacher_id": teacher_id}, room=pin)





@socketio.on("student_join_lobby")
def handle_student_join(data):
  """
  Handle a student joining a game lobby via Socket.IO.

  - Adds the student socket to the game room
  - Tracks the student's socket connection
  - Marks the student as connected in the database
  - Notifies the lobby that a new player has joined
  """
  # Extract game PIN from incoming socket data
  pin = data["pin"]
  student_id = current_user.id

  # Join the Socket.IO room associated with this game PIN
  debug_print_rooms()
  join_room(pin)
  debug_print_rooms()

  # Track this student's socket connection
  student_sids[request.sid] = {"student_id": student_id,"pin": pin}

  # Mark in DB as connected
  game = Game.query.filter_by(game_pin=pin).first()
  if game:
    player = GamePlayer.query.filter_by(game_id=game.id, student_id=student_id).first()
    if player:
      player.is_connected = True
      db.session.commit()

  print(f"Student {student_id} joined lobby {pin} with SID {request.sid}")
  # Notify all clients in the lobby that a player has joined - event is only handled by teacher in game_lobby.js
  socketio.emit("player_joined", {"student_id": student_id,"name": current_user.name}, room=pin)


def handle_student_disconnect(sid):
  """
  Handle cleanup when a student disconnects from a game lobby or game.

  This:
  - Marks the student as disconnected in the database
  - Notifies the lobby
  - Removes the socket from the tracking map
  """
  # Look up stored connection info for this socket ID
  info = student_sids.get(sid)
  if not info:
    return

  # Extract student ID and associated game
  student_id = info["student_id"]
  pin = info["pin"]

  #print(f"Student {student_id} disconnected from {pin}")

  # Update database connection status if game exists and this player was in that game
  game = Game.query.filter_by(game_pin=pin).first()
  if game:
    player = GamePlayer.query.filter_by(game_id=game.id,student_id=student_id).first()
    if player:
      player.is_connected = False
      db.session.commit()

    # Notify lobby that player disconnected - event is only handled by teacher
    for socketid, info in teacher_sids.items():
      if info["pin"] == pin:
        socketio.emit("player_disconnected",{"student_id": student_id},room=socketid)
    # Remove socket tracking
    del student_sids[sid]


def handle_teacher_disconnect(sid):
  """
  Handle cleanup when a teacher disconnects.

  Behaviour depends on game state:
  - If the game has not started, cancel and delete it
  - If the game is active, notify clients but keep game state
  """
  # Look up stored connection info for this socket ID
  info = teacher_sids.get(sid)
  if not info:
    return

  # Extract teacher identity and associated game
  teacher_id = info["teacher_id"]
  pin = info["pin"]

  #print(f"Teacher {teacher_id} disconnected from {pin}")

  # Fetch the game associated with this lobby/game PIN
  game = Game.query.filter_by(game_pin=pin).first()

  # Case 1: Game exists but has not started yet - cancel it
  if game and not game.is_active:
    #print(f"Game {pin} is inactive. Cancelling...")
    socketio.emit("game_closed",{"pin": pin},room=pin)
    db.session.delete(game)
    db.session.commit()
    #print(f"Game {pin} removed from database.")

  # Case 2: Game is active - notify clients - students get update that teacher has disconnected but game continues
  else:
    socketio.emit("teacher_disconnected",{"teacher_id": teacher_id},room=pin)

  # Remove socket tracking
  del teacher_sids[sid]


@socketio.on("cancel_game")
def handle_cancel_game(data):
  """
  Handle teacher manually cancelling a game from the lobby.
  """
  # Only teachers can cancel
  if not session.get("teacher_logged_in"):
    return

  pin = data.get("pin")
  if not pin:
    return

  game = Game.query.filter_by(game_pin=pin, user_id=current_user.id).first()
  if not game:
    return

  #print(f"Teacher {current_user.id} cancelled game {pin}")

  # Notify all students in the lobby
  socketio.emit("game_closed", {"pin": pin}, room=pin)

  # Remove game from DB 
  db.session.delete(game)
  db.session.commit()

  for sid, info in list(student_sids.items()):
    if info["pin"] == pin:
      del student_sids[sid]

  for sid, info in list(teacher_sids.items()):
    if info["pin"] == pin:
      del teacher_sids[sid]



@socketio.on("disconnect")
def handle_disconnect():
  """
  Handle Socket.IO disconnection events for both students and teachers.

  This function determines the type of user based on the socket ID and delegates cleanup logic accordingly.
  """
  #print("Disconnect current_user =", current_user)
  #print("Disconnect current_user.id =", getattr(current_user, "id", None))
  sid = request.sid
  
  # User is a Student
  if sid in student_sids:
    handle_student_disconnect(sid)
    return
  # User is a Teacher
  if sid in teacher_sids:
    handle_teacher_disconnect(sid)
    return



@app.route("/student_waiting")
@login_required
def student_waiting():
  """
  Display the waiting room page for a student before the game starts.

  This page:
  - Is accessible only to students
  - Ensures the game exists
  - Ensures the student is registered in the game
  - Prevents access once the game has started
  """
  # Teachers cannot access this page
  if session.get("teacher_logged_in"):
    return redirect("/dashboard")  

  # Extract game PIN from query parameters
  pin = request.args.get("pin")

  # Validate game exists
  game = Game.query.filter_by(game_pin=pin).first()
  if game is None:
    return render_template("error.html", errorMessage="Invalid game PIN.")

  # Validate that the current student is part of this game
  player = GamePlayer.query.filter_by(
    game_id=game.id,
    student_id=current_user.id
  ).first()
  if player is None:
    return render_template("error.html",errorMessage="You are not part of this game.")


  # Prevent access to waiting room once the game has started
  if game.is_active:
    return render_template("error.html",errorMessage="This game has already started. To join the lilve game, use the 'Play Game' option in the navigation bar, and enter the game pin.")
  
  # Render the waiting room view
  return render_template("student_waiting.html", pin=pin)


# START GAME AND END RELATED:

@socketio.on("start_game")
def handle_start_game(data):
  """
  Start a game session.

  This event:
  - Validates the teacher and game ownership
  - Prepares question order and player state
  - Ensures enough players are connected
  - Marks the game as active
  - Notifies all clients and starts the game timer
  """
  # Extract game PIN from socket data
  pin = data.get("pin")
  if not pin:
    return
  
  # Only teachers are allowed to start games
  if not session.get("teacher_logged_in"):
    # Only teachers can start games
    emit("start_denied", {"reason": "not_teacher"}, room=request.sid)
    return
  
  # Validate that the game exists and belongs to this teacher
  game = Game.query.filter_by(game_pin=pin, user_id=current_user.id).first()
  if not game:
    emit("start_denied", {"reason": "no_such_game"}, room=request.sid)
    return

  # Prepare shuffled question order for the game
  num_questions = initialize_question_order(game)

  # Initialize per-player question pointers
  initialize_player_question_indices(game.id, num_questions)

  # Count how many players are currently registered for this game
  player_count = GamePlayer.query.filter_by(game_id=game.id, is_connected=True).count()

  # Ensure there are enough connected players to start
  if player_count < 2:
    emit("start_denied", {"reason": "need_at_least_two", "players": player_count}, room=request.sid)
    return

  if (game.gamemode == "classic_multi" or game.gamemode == "bomb"):
    num_teams = data.get("num_teams")
    player_count = GamePlayer.query.filter_by(game_id=game.id).count()
    max_teams = player_count // 2
    if (not isinstance(num_teams, int) or num_teams < 2 or num_teams > max_teams): # backup is 2 since this is safest number for team mode. 
      num_teams = 2
    
    teams = create_teams_for_game(game, num_teams) # Create teams
    players = GamePlayer.query.filter_by(game_id=game.id).all()
    random.shuffle(players)

    for i, player in enumerate(players): # Add players to teams randomly
      player.team_id = teams[i % len(teams)].id
    db.session.commit()

  # Mark the game as active
  game.is_active = True
  duration_seconds = game.timelimit * 60 # minutes to seconds
  game.end_time = int(time.time()) + duration_seconds
  db.session.commit()

  #print(f"Game {pin} started by teacher {current_user.id} with {player_count} players.")

  # Notify all clients that the game is starting
  socketio.emit("game_starting", {"pin": pin,}, room=pin)

  # Start background timer to auto-end the game
  socketio.start_background_task(end_game_after_delay,pin,duration_seconds)


def create_teams_for_game(game, num_teams):
  teams = []
  for i in range(num_teams):
    team = GameTeam(game_id=game.id,name=f"Team {chr(65+i)}") # Team A, Team B, ...
    db.session.add(team)
    teams.append(team)

  db.session.flush()  # ensures team IDs exist
  return teams


def emit_team_assignments(game):
  """
  Emit team assignments to all clients in the game room.

  Sends:
  - team id
  - team name
  - list of student names per team
  """
  teams = GameTeam.query.filter_by(game_id=game.id).all()

  team_data = []
  for team in teams:
    players = (
      db.session.query(Student.name)
      .join(GamePlayer)
      .filter(GamePlayer.team_id == team.id).all())
    team_data.append({"team_id": team.id,"team_name": team.name,"players": [p[0] for p in players]})

  socketio.emit("teams_assigned",{"teams": team_data},room=game.game_pin)


def initialize_question_order(game):
  """
  Shuffle questions for the game and store the order in the database.
  """
  questions = Question.query.filter_by(set_id=game.qaset_id).all()
  random.shuffle(questions)
  # Store as CSV for reproducible per-player traversal
  game.question_order = ",".join(str(q.id) for q in questions)
  db.session.commit()
  return len(questions)


def initialize_player_question_indices(game_id, num_questions):
  """
  Assign each player a random starting question index.
  """
  players = GamePlayer.query.filter_by(game_id=game_id).all()
  for player in players:
    player.question_index = random.randint(0, num_questions - 1)
  db.session.commit()


def end_game_after_delay(pin, duration_seconds):
  """
  Background task to auto-end a game after a fixed time limit.

  - Wait for the game duration
  - If the game is still active, mark it ended and notify all clients
  - Wait briefly so clients can see end-of-game UI
  - Delete the game record from the database
  """

  socketio.sleep(duration_seconds) # Wait for game duration
  with app.app_context():
    game = Game.query.filter_by(game_pin=pin).first()
    if game and game.is_active:
      game.is_active = False # Change is_active to False and commit changes to database
      debug_print_database_state()
      emit_game_over_with_results(game)
      socketio.start_background_task(cleanup_game_later, game.id)# Remove game and related records from DB
      debug_print_database_state()


def cleanup_game_later(game_id):
  socketio.sleep(5)  # allow UI to settle
  with app.app_context():
    game = Game.query.get(game_id)
    if game:
      db.session.delete(game)
      db.session.commit()


def debug_print_students(student_ids, label):
  print(f"\n========== {label} ==========")
  for sid in student_ids:
    s = Student.query.get(sid)
    if not s:
      continue
    print(
      f"ID={s.id} | "
      f"games_played={s.games_played} | "
      f"gold={s.gold_medals} | "
      f"silver={s.silver_medals} | "
      f"bronze={s.bronze_medals} | "
      f"team_gold_wins={s.team_gold_wins}"
      f"best_streak={s.best_streak}"
    )
  print("================================\n")


def award_end_game_achievements(game, players):
  """
  Award badges, participation, and best streak updates.
  Runs ONCE per game.
  """
  student_ids = [gp.student_id for gp in players]
  #debug_print_students(student_ids, "BEFORE ACHIEVEMENTS")
  # players already sorted by score descending
  for idx, gp in enumerate(players):
    student = Student.query.get(gp.student_id)
    # Participation in games:
    student.games_played += 1

    # Podium badges
    if idx == 0:
      student.gold_medals += 1
    elif idx == 1:
      student.silver_medals += 1
    elif idx == 2:
      student.bronze_medals += 1

    # Highest streak (global over all games)
    if gp.highest_streak > student.best_streak:
      student.best_streak = gp.highest_streak

  db.session.commit()
  #debug_print_students(student_ids, "AFTER ACHIEVEMENTS")


def award_team_win_badge(game):
  """
  Award a team gold win to all members of the winning team.
  Runs only for team-based game modes.
  """

  if game.gamemode not in ("classic_multi", "bomb"):
    return

  teams = GameTeam.query.filter_by(game_id=game.id).all()
  if not teams:
    return

  # Find winning team by total score
  winning_team = max(
    teams,
    key=lambda t: recompute_team_score(t.id)
  )

  # Award gold team win to all members
  winners = GamePlayer.query.filter_by(
    game_id=game.id,
    team_id=winning_team.id
  ).all()

  for gp in winners:
    student = Student.query.get(gp.student_id)
    student.team_gold_wins += 1




def emit_game_over_with_results(game):
  """
  Send game_over ONCE PER STUDENT,
  including only that student's final stats.
  """
  # Notify teacher only — no payload/data
  for sid, info in list(teacher_sids.items()):
    if info["pin"] == game.game_pin:
      socketio.emit("game_over", {}, room=sid)

  # Build leaderboard
  players = (GamePlayer.query.filter_by(game_id=game.id).order_by(GamePlayer.score.desc()).all())
  award_end_game_achievements(game, players)
  award_team_win_badge(game)
  
  db.session.commit()
  total_players = len(players)

  # student_id -> position
  positions = {
    gp.student_id: idx + 1
    for idx, gp in enumerate(players)
  }

  # Emit to each connected student socket
  for sid, info in list(student_sids.items()):
    if info["pin"] != game.game_pin:
      continue

    student_id = info["student_id"]

    gp = next((p for p in players if p.student_id == student_id), None)
    if not gp:
      continue

    socketio.emit("game_over",{
      "position": positions[student_id],
      "score": gp.score,
      "highest_streak": gp.highest_streak,
      "total_players": total_players
      },
      room=sid)



@socketio.on("teacher_join_game")
def teacher_join_game(data):
  """
  Handle a teacher joining (or rejoining) an ACTIVE game.

  This event:
  - Validates the teacher owns the game
  - Ensures the game is already active
  - Reconnects the teacher's socket to the game room
  - Notifies students that the teacher is present
  """

  # Extract game PIN from socket data
  pin = data.get("pin")
  teacher_id = current_user.id

  # Validate that this teacher owns the game and that it is active
  game = Game.query.filter_by(game_pin=pin, user_id=teacher_id).first()
  if not game or not game.is_active:
    emit("game_join_denied", {"error": "unauthorized_or_inactive"}, room=request.sid)
    return

  # Join the Socket.IO room for this active game
  debug_print_rooms()
  join_room(pin)
  debug_print_rooms()

  if game.gamemode == "classic_multi":
    teams = GameTeam.query.filter_by(game_id=game.id).all()
    for team in teams:
      score = recompute_team_score(team.id)
      emit("update_team_score", {
        "team_id": team.id,
        "name": team.name,
        "score": score
      })

  flagged = (db.session.query(GameFlaggedQuestion, Question)
    .join(Question, Question.id == GameFlaggedQuestion.question_id)
    .filter(GameFlaggedQuestion.game_id == game.id).all())

  for flag, q in flagged:
    emit("question_flagged", {
      "question_id": q.id,
      "question_text": q.question,
      "choices": [q.answer, q.fakeans1, q.fakeans2, q.fakeans3],
      "correct_answer": q.answer,
      "count": flag.count
    }, room=request.sid)

  total_players = GamePlayer.query.filter_by(game_id=game.id).count()

  alerts = (
    db.session.query(GameQuestionStat, Question)
    .join(Question)
    .filter(
      GameQuestionStat.game_id == game.id,
      GameQuestionStat.distinct_students >= ANSWERED_THRESHOLD * total_players,
      GameQuestionStat.accuracy <= ACCURACY_THRESHOLD).all()
  )

  for stat, q in alerts:
    emit("question_alert", {
      "question_id": q.id,
      "question_text": q.question,
      "accuracy": stat.accuracy,
      "response_rate": stat.distinct_students / total_players,
      "choices": [q.answer, q.fakeans1, q.fakeans2, q.fakeans3],
      "correct_answer": q.answer
    }, room=request.sid)

  remaining = max(0, int(game.end_time - time.time()))
  emit("timer_sync", {"remaining": remaining})

  # Track this teacher's socket connection
  teacher_sids[request.sid] = {"teacher_id": teacher_id,"pin": pin}

  print(f"Teacher {teacher_id} joined ACTIVE game {pin} with SID {request.sid}")

  # Notify all students that the teacher has reconnected
  socketio.emit("teacher_reconnected_game", {"teacher_id": teacher_id}, room=pin)




@socketio.on("student_join_game")
def student_join_game(data):
  """
  Handle a student joining (or rejoining) an ACTIVE game.

  This event:
  - Validates the game exists and is active
  - Ensures the student is registered in the game
  - Reconnects the student's socket to the game room
  - Marks the student as connected in the database
  - Sends the current question state to the student
  """
  # Extract game PIN from socket data
  pin = data.get("pin")
  student_id = current_user.id

  # Validate that the game exists and is currently active
  game = Game.query.filter_by(game_pin=pin).first()
  if not game or not game.is_active:
    emit("game_join_denied", {"error": "inactive_or_missing_game"}, room=request.sid)
    return

  # Validate that the student is registered for this game
  gp = GamePlayer.query.filter_by(game_id=game.id,student_id=student_id).first()

  if not gp:
    emit("game_join_denied", {"error": "not_in_game"}, room=request.sid)
    return

  # Join the Socket.IO room for this active game
  debug_print_rooms()
  join_room(pin)
  debug_print_rooms()

  # Track this student's socket connection
  student_sids[request.sid] = {
    "student_id": student_id,
    "pin": pin
  }

  # Mark the student as connected in the database
  gp.is_connected = True
  db.session.commit()

  emit("update_score", {
    "student_id": student_id,
    "score": gp.score
  }, room=request.sid)

  print(f"Student {student_id} joined ACTIVE game {pin} with SID {request.sid}")
  if (game.gamemode == "classic_multi" or game.gamemode == "bomb"):
    emit("team_info", {"team_name": gp.team.name}, room=request.sid)

  # Notify teacher that the student has reconnected - only the teacher responds to this event
  # socketio.emit("student_reconnected_game", {"student_id": student_id,"name": current_user.name}, room=pin)
  
  # Send the current question state to this student
  send_question_to_student(game, gp, request.sid)


@app.route("/teacher_game")
@login_required
def teacher_game():
  """
  Render the teacher's in-game view for an active game.

  This page:
  - Is accessible only to teachers
  - Validates game ownership and active state
  - Displays current player scores and connection status
  - Provides the main teacher control/monitoring interface
  """
  # Ensure only teachers can access the teacher game view
  if not session.get("teacher_logged_in"):
    return redirect("/entercode")

  # Extract game PIN from query parameters
  pin = request.args.get("pin")
  if not pin:
    return render_template("error.html", errorMessage="Missing game PIN.")

  # Validate that the game exists and belongs to this teacher
  game = Game.query.filter_by(game_pin=pin, user_id=current_user.id).first()
  if game is None:
    return render_template("error.html", errorMessage="Game not found or unauthorized.")

  # Prevent access if the game has not started
  if not game.is_active:
    return render_template("error.html", errorMessage="This game is not active.")

  # Fetch the associated question set (used for display only)
  qset = Q_and_A_Set.query.get(game.qaset_id)

  # Get all players, their scores, and connection status
  players = (
    db.session.query(Student, GamePlayer.score, GamePlayer.is_connected)
    .join(GamePlayer, GamePlayer.student_id == Student.id)
    .filter(GamePlayer.game_id == game.id).all()
  )
  # Convert time limit from minutes to seconds for frontend timers
  duration_seconds = game.timelimit * 60

  teams = []
  team_members = {}
  if game.gamemode == "classic_multi":
    teams, team_members = get_team_leaderboard_data(game.id) 

  # Render the teacher's in-game dashboard
  return render_template("teacher_game.html", game=game, qset=qset, pin=pin, players=players, duration_seconds=duration_seconds, teams=teams, team_members=team_members)




def get_team_leaderboard_data(game_id):
  """
  Fetch teams, their total scores, and their members
  for rendering the team leaderboard.
  """

  teams = (db.session.query(GameTeam.id,GameTeam.name,db.func.sum(GamePlayer.score))
    .outerjoin(GamePlayer, GamePlayer.team_id == GameTeam.id)
    .filter(GameTeam.game_id == game_id)
    .group_by(GameTeam.id).all()
  )

  team_members = {}
  for team_id, _, _ in teams:
    members = (db.session.query(Student.name).join(GamePlayer, GamePlayer.student_id == Student.id).filter(GamePlayer.team_id == team_id).all())
    team_members[team_id] = [m[0] for m in members]

  return teams, team_members








@app.route("/play_game")
@login_required
def play_game():
  """
  Render the in-game view for a student during an active game.

  This route:
  - Validates the game exists and is active
  - Redirects teachers to the teacher game view
  - Ensures the student is registered in the game
  """
  # Extract game PIN from query parameters
  pin = request.args.get("pin")
  if not pin:
    return render_template("error.html", errorMessage="Missing game PIN.")

  # Validate that the game exists
  game = Game.query.filter_by(game_pin=pin).first()
  if game is None:
    return render_template("error.html", errorMessage="Game not found.")

  # Prevent access if the game is not currently active
  if not game.is_active:
    return render_template("error.html", errorMessage="This game is not active. To join the live game, use the “Play Game” option in the navigation bar, and enter the game pin.")

  # If a teacher accesses this route, redirect them to the teacher view
  if session.get("teacher_logged_in"):
    if game.user_id == current_user.id:
        return redirect(f"/teacher_game?pin={pin}")
    else:
      return render_template("error.html", errorMessage="You are not the teacher for this game.")

  # Validate that the student is registered in this game
  player = GamePlayer.query.filter_by(game_id=game.id,student_id=current_user.id).first()
  if player is None:
    return render_template("error.html", errorMessage="You are not part of this game.")
  
  # Render the student gameplay view
  return render_template("play_game.html", game=game, pin=pin)




# GAME RUNNING RELATED:

def send_question_to_student(game, gp, sid):
  """
  Send the next question to a single student during an active game.

  Current behaviour:
  - Uses a pre-shuffled global question order stored on the Game
  - Advances per-student question index independently
  - Sends a multiple-choice question to the student's socket

  Note:
  - This implementation supports classic solo and classic multiplayer
  - Bomb mode will NOT use this logic and will branch here later 
  """
  # Load the global question order for this game - stored as a CSV string of question IDs, so split to make iterable
  order = [int(x) for x in game.question_order.split(",")]

  # If the student has reached the end of the question list, wrap around back to the beginning
  if gp.question_index >= len(order):
    gp.question_index = 0
    db.session.commit()

  # Determine the next question for this student based on their question_index
  qid = order[gp.question_index]
  
  question = Question.query.get(qid)

  # Construct answer choices (1 correct + 3 distractors)
  choices = [
    question.answer,
    question.fakeans1,
    question.fakeans2,
    question.fakeans3
  ]
  # Shuffle choices so correct answer position is random
  random.shuffle(choices)

  # Send the question to this specific student's socket
  socketio.emit("new_question", {"question_id": qid,"question": question.question,"choices": choices}, room=sid)



def update_streak_and_emit(game_pin, gp, student_id, correct):
  """
  Update a player's streak based on answer correctness
  and emit streak alerts when thresholds are reached.
  """
  if correct:
    gp.current_streak += 1
    
    if gp.current_streak > gp.highest_streak:
      gp.highest_streak = gp.current_streak

    # Emit streak alert only at threshold (6)
    if gp.current_streak >= 6:
      socketio.emit("streak_update",{"student_id": student_id,"name": Student.query.get(student_id).name,"streak": gp.current_streak},room=game_pin)
  else:
    gp.current_streak = 0



def get_valid_active_game_and_player(pin, student_id):
  """
  Validate game existence, active state, and student membership.
  Returns (game, GamePlayer) or (None, None).
  """
  game = Game.query.filter_by(game_pin=pin).first()
  if not game or not game.is_active:
    return None, None

  gp = GamePlayer.query.filter_by(
    game_id=game.id,
    student_id=student_id
  ).first()

  if not gp:
    return None, None

  return game, gp



def update_question_statistics(game, student_id, question, correct):
  """
  Update all per-question learning statistics for a student's answer.

  This includes:
  - distinct students
  - correctness tracking
  - retention checks/drops
  - accuracy and retention rate
  """
  # Find if there is a stat for this game and question
  stat = GameQuestionStat.query.filter_by(game_id=game.id,question_id=question.id).first()

  # No stat - first time question is being, so make a new stat
  if not stat:
    stat = GameQuestionStat(game_id=game.id,question_id=question.id,total_answers=0,correct_students=0,distinct_students=0,accuracy=0.0,retention_checks=0,retention_drops=0,retention_rate=1.0)
    db.session.add(stat)

  # Find if there is a record for this game, player and question
  gqs = GameQuestionStudent.query.filter_by(game_id=game.id,student_id=student_id,question_id=question.id).first()

  # First attempt at this question for this player - add record in database, update distinct students
  if gqs is None:
    gqs = GameQuestionStudent(game_id=game.id,student_id=student_id,question_id=question.id,last_correct=correct,has_ever_been_correct=correct,attempts=1)
    db.session.add(gqs)

    stat.distinct_students += 1
    if correct:
      stat.correct_students += 1

  # Not the first attempt at this question for this player
  else:
    gqs.attempts += 1
    prev = gqs.last_correct

    # First time correct is now
    if not prev and correct:
      if not gqs.has_ever_been_correct:
        stat.correct_students += 1
        gqs.has_ever_been_correct = True

    # Last time correct, now incorrect
    elif prev and not correct:
      stat.retention_checks += 1
      stat.retention_drops += 1

    # Last time correct, now correct
    elif prev and correct:
      stat.retention_checks += 1

    gqs.last_correct = correct

  # Recompute aggregates
  stat.total_answers += 1
  stat.accuracy = (stat.correct_students / stat.distinct_students if stat.distinct_students > 0 else 0.0)
  stat.retention_rate = (1.0 - (stat.retention_drops / stat.retention_checks) if stat.retention_checks > 0 else 1.0)
  return stat



def emit_question_alerts_if_needed(game, question, stat):
  """
  Emit teacher alerts if a question meets response and accuracy thresholds.
  """

  total_players = GamePlayer.query.filter_by(game_id=game.id).count()
  if total_players == 0:
    return

  response_rate = stat.distinct_students / total_players

  if response_rate < ANSWERED_THRESHOLD:
    return

  # Question is being incorrectly answered frequently - alert teacher
  if stat.accuracy <= ACCURACY_THRESHOLD:
    print("Threshold reached for accuracy - will send alert")
    for sid, info in teacher_sids.items():
      if info["pin"] == game.game_pin:
        print("Sending question alert to teacher")
        socketio.emit("question_alert",
          {
            "game_id": game.id,
            "question_id": question.id,
            "question_text": question.question,
            "accuracy": stat.accuracy,
            "response_rate": response_rate,
            "total_answers": stat.total_answers,
            "distinct_students": stat.distinct_students,
            "choices": [
              question.answer,
              question.fakeans1,
              question.fakeans2,
              question.fakeans3
            ],
            "correct_answer": question.answer
          },
          room=sid
        )
  else:
    # No need to broadcast event to all players, just to teacher:
    for sid, info in teacher_sids.items():
      if info["pin"] == game.game_pin:
        socketio.emit("question_clear",{"game_id": game.id,"question_id": question.id},room=sid) 


@socketio.on("request_next_question")
def handle_request_next_question(data):
  """
  Handle a student's request to receive their next question.

  This event:
  - Validates the game exists and is active
  - Ensures the requesting student belongs to the game
  - Sends the next question to the requesting socket only

  Note:
  - This supports classic solo and classic multiplayer
  - Bomb mode will not use this later
  """

  # Extract required fields from socket data
  pin = data.get("pin")
  student_id = data.get("student_id")

  if not pin or not student_id:
    return

  # Validate that the game exists and is currently active
  game = Game.query.filter_by(game_pin=pin).first()
  if not game or not game.is_active:
    return

  # Validate that the student is registered in this game
  gp = GamePlayer.query.filter_by(game_id=game.id,student_id=student_id).first()
  if not gp:
    return

  # Send the next question to this specific student socket, (per-student progression, so sent to their own room)
  send_question_to_student(game, gp, request.sid)




@socketio.on("answer_submitted")
def handle_answer_submitted(data):
  """
  Handle a student's answer submission.

  - Validate submission and game state
  - Update per-question learning statistics
  - Update player score and streak
  - Emit score updates and alerts
  - Send feedback to the submitting student
  """
  # Extract and validate payload
  pin = data.get("pin")
  student_id = data.get("student_id")
  qid = data.get("question_id")
  student_answer = data.get("answer")

  if not pin or not student_id or not qid or not student_answer:
    emit("answer_feedback", {"error": "invalid_data"}, room=request.sid)
    return

  # Validate game and player
  game, gp = get_valid_active_game_and_player(pin, student_id)
  if not game or not gp:
    emit("answer_feedback", {"error": "invalid_game_or_player"}, room=request.sid)
    return
  
  # Validate game time is still ongoing
  if time.time() >= game.end_time:
    emit("game_over", {}, room=request.sid)
    return

  # Validate question ID belongs to this game's question set
  question = Question.query.filter_by(id=qid, set_id=game.qaset_id).first()
  if not question:
    emit("answer_feedback", {"error": "invalid_question"}, room=request.sid)
    return

  # Validate answer - is student's given answer correct?
  correct = (student_answer == question.answer)

  # Learning statistics
  stat = update_question_statistics(game=game,student_id=student_id,question=question,correct=correct)

  # If correct, emit score update to teacher 
  if correct:
    apply_individual_score(gp)
    socketio.emit("update_score",{"student_id": student_id,"score": gp.score},room=pin)
    
    if game.gamemode == "classic_multi":
      team_score = recompute_team_score(gp.team_id)
      socketio.emit("update_team_score", {"team_id": gp.team_id,"score": team_score}, room=pin)

  update_streak_and_emit(pin, gp, student_id, correct)

  db.session.commit()

  # Teacher alerts
  emit_question_alerts_if_needed(game, question, stat)

  # Send feedback to only this student
  emit("answer_feedback", {
    "correct": correct,
    "correct_answer": question.answer
  }, room=request.sid)

  # Advance question index
  gp.question_index += 1
  db.session.commit()



def apply_individual_score(gp):
  """
  Increment an individual player's score (solo / classic mode).

  This function:
  - Updates the GamePlayer score
  """
  gp.score += 1
    

def recompute_team_score(team_id):
  return (db.session.query(db.func.sum(GamePlayer.score)).filter(GamePlayer.team_id == team_id).scalar()or 0)


@socketio.on("flag_question")
def handle_flag_question(data):
  """
  Handle when a student has flagged a question.

  - Validate game state
  - Send question, question ID, answer, choices to teacher
  """
  pin = data.get("pin")
  student_id = data.get("student_id")
  question_id = data.get("question_id")

  if not pin or not student_id or not question_id:
    return

  # Validate game + membership 
  game, gp = get_valid_active_game_and_player(pin, student_id)
  if not game:
    return

  question = Question.query.get(question_id)
  if not question:
    return
  
  flag = GameFlaggedQuestion.query.filter_by(game_id=game.id,question_id=question_id).first()

  if flag:
    flag.count += 1
  else:
    flag = GameFlaggedQuestion(game_id=game.id,question_id=question_id,count=1)
    db.session.add(flag)

  db.session.commit()

  # Relay event to teacher only
  socketio.emit("question_flagged",
    {"question_id": question.id,
    "question_text": question.question,
    "choices": [
      question.answer,
      question.fakeans1,
      question.fakeans2,
      question.fakeans3
    ],
    "correct_answer": question.answer
  },room=pin)


@socketio.on("dismiss_flagged_question")
@login_required
def dismiss_flagged_question(data):
  pin = data.get("pin")
  question_id = data.get("question_id")

  if not pin or not question_id:
    return

  # Ensure teacher owns the game
  game = Game.query.filter_by(game_pin=pin,user_id=current_user.id).first()

  if not game:
    return

  # Delete flagged question from DB
  flag = GameFlaggedQuestion.query.filter_by(game_id=game.id,question_id=question_id).first()

  if flag:
    db.session.delete(flag)
    db.session.commit()



# FOR DEPLOYMENT WITH GEVENT:
if __name__ == "__main__":
  import os
  from dotenv import load_dotenv

  load_dotenv()
  port = int(os.environ.get("FLASK_RUN_PORT", 59238))  

  print(">>>> RUNNING ON PORT:", port)

  socketio.run(app, host="0.0.0.0", port=port, debug=True)