from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import date, time
from werkzeug.security import generate_password_hash


# create the database interface
db = SQLAlchemy()


class Teacher(UserMixin, db.Model):
    __tablename__='teachers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(25))
    email = db.Column(db.String(25), unique=True)
    password_hash = db.Column(db.String(200))

    def __init__(self, name, email, password_hash): 
        self.name = name 
        self.email=email
        self.password_hash=password_hash
    
    def setPassword(self,newpassword_hash):
        self.password_hash=newpassword_hash
    



class Student(UserMixin,db.Model):
    __tablename__='students'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(25))
    email = db.Column(db.String(25), unique=True)
    password_hash = db.Column(db.String(200))
    games_played = db.Column(db.Integer, default=0)

    gold_medals = db.Column(db.Integer, default=0)
    silver_medals = db.Column(db.Integer, default=0)
    bronze_medals = db.Column(db.Integer, default=0)
    team_gold_wins = db.Column(db.Integer, default=0)

    best_streak = db.Column(db.Integer, default=0)
    
    def __init__(self, name,email, password_hash):  
        self.name = name
        self.email = email
        self.password_hash = password_hash

    def setPassword(self,newpassword_hash):
        self.password_hash=newpassword_hash
    
        
class Game(db.Model):
    __tablename__='games'
    id = db.Column(db.Integer, primary_key=True)
    game_pin = db.Column(db.String(10), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('teachers.id'))
    qaset_id = db.Column(db.Integer, db.ForeignKey('q_and_a_sets.id'))
    capacity = db.Column(db.Integer)
    players = db.Column(db.Integer)
    is_active = db.Column(db.Boolean)
    gamemode = db.Column(db.String(30))
    timelimit = db.Column(db.Integer)
    end_time = db.Column(db.Integer)
    question_order = db.Column(db.String)

    players_list = db.relationship("GamePlayer", backref="game", cascade="all, delete-orphan")
    question_stats = db.relationship("GameQuestionStat", backref="game", cascade="all, delete-orphan")
    question_student_stats = db.relationship("GameQuestionStudent", backref="game", cascade="all, delete-orphan")
    flagged_questions = db.relationship("GameFlaggedQuestion", cascade="all, delete-orphan")

    def __init__(self, game_pin, user_id, qaset_id, capacity, is_active, gamemode, timelimit):
        self.game_pin = game_pin
        self.user_id = user_id
        self.qaset_id = qaset_id
        self.capacity = capacity
        self.is_active = is_active
        self.players = 0
        self.gamemode = gamemode
        self.timelimit = timelimit
        


class GamePlayer(db.Model):
    __tablename__ = 'game_players'

    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'))
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'))
    score = db.Column(db.Integer, default=0)
    team_id = db.Column(db.Integer, db.ForeignKey('game_teams.id'))
    is_connected = db.Column(db.Boolean)
    question_index = db.Column(db.Integer, default=0)
    current_streak = db.Column(db.Integer, default=0)
    highest_streak = db.Column(db.Integer, default=0)

    team = db.relationship("GameTeam",back_populates="players")
    
    def __init__(self, game_id, student_id):
        self.game_id = game_id
        self.student_id = student_id
        self.score = 0
        self.is_connected = True
        self.current_streak = 0


class GameTeam(db.Model):
    __tablename__ = "game_teams"

    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey("games.id"))
    name = db.Column(db.String(50))
    score = db.Column(db.Integer, default=0)
    players = db.relationship("GamePlayer",back_populates="team",cascade="all, delete")



class Folder(db.Model):
    __tablename__='folders'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text())
    user_id = db.Column(db.Integer, db.ForeignKey('teachers.id'))
    
    sets = db.relationship("Q_and_A_Set", backref="folder", cascade="all, delete-orphan")

    def __init__(self, name, user_id):
        self.name=name
        self.user_id = user_id





class Q_and_A_Set(db.Model):
    __tablename__='q_and_a_sets'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text())
    folder_id = db.Column(db.Integer, db.ForeignKey('folders.id'))
    date = db.Column(db.Date())
    is_private = db.Column(db.Boolean())

    questions = db.relationship("Question", backref="qset", cascade="all, delete-orphan")

    def __init__(self, name, folder_id, date, is_private):
        self.name=name
        self.folder_id = folder_id
        self.date = date
        self.is_private = is_private




class Question(db.Model):
    __tablename__='questions'
    id = db.Column(db.Integer, primary_key=True)
    set_id = db.Column(db.Integer, db.ForeignKey('q_and_a_sets.id'))
    question = db.Column(db.Text())
    answer = db.Column(db.Text())
    fakeans1 = db.Column(db.Text())
    fakeans2 = db.Column(db.Text())
    fakeans3 = db.Column(db.Text())

    def __init__(self, set_id, question, answer, fakeans1, fakeans2, fakeans3):
        self.set_id = set_id
        self.question = question
        self.answer = answer
        self.fakeans1 = fakeans1
        self.fakeans2 = fakeans2
        self.fakeans3 = fakeans3




class GameQuestionStat(db.Model):
    __tablename__ = "game_question_stats"

    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey("games.id"), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id"), nullable=False)
    total_answers = db.Column(db.Integer, default=0)   # Total attempts
    correct_students = db.Column(db.Integer, default=0) # How many were correct

    # To support DISTINCT student accuracy
    distinct_students = db.Column(db.Integer, default=0)

    # Accuracy value (0.0–1.0)
    accuracy = db.Column(db.Float, default=0.0)

    # retention metrics:
    # – how many times we revisited a question for a student who had previously been correct
    retention_checks = db.Column(db.Integer, default=0)
    # – how many of those revisits were wrong (correct → wrong)
    retention_drops = db.Column(db.Integer, default=0)
    # retention_rate = 1 - retention_drops / retention_checks
    retention_rate = db.Column(db.Float, default=1.0)

    __table_args__ = (
        db.UniqueConstraint("game_id", "question_id", name="unique_game_question_stat"),
    ) # Game and question must be unique - no duplicates for the same game and question combo. 


class GameQuestionStudent(db.Model):
    __tablename__ = "game_question_students"

    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey("games.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id"), nullable=False)
    last_correct = db.Column(db.Boolean, nullable=True)
    # has this student EVER answered this question correctly in this game?
    has_ever_been_correct = db.Column(db.Boolean, default=False)
    attempts = db.Column(db.Integer, default=0)

    __table_args__ = (
        db.UniqueConstraint("game_id", "student_id", "question_id", name="unique_answer_once"),
    ) # Game, student, and question must be unique - no duplicates for the same student, game and question combo. 


class GameFlaggedQuestion(db.Model):
    __tablename__ = "game_flagged_questions"
    
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey("games.id", ondelete="CASCADE"), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id"), nullable=False)
    count = db.Column(db.Integer, default=1)








def dbinit():
    # these two lines can be used to populate the events table a little bit.
    # Events_list= [Event("Event 1",date(2024,4,12),time(12,30),2,100,"Uni",5), Event("Event 2",date(2024,4,12),time(12,30),2,2,"Home",1)]
    #db.session.add_all(Events_list)
    # --- Create Teachers ---
    t1 = Teacher(
        name="Alice Teacher",
        email="alice",
        password_hash=generate_password_hash("alice")
    )
    
    s1 = Student(
        name="a Student",
        email="a",
        password_hash=generate_password_hash("a")
    )

    s2 = Student(
        name="b Student",
        email="b",
        password_hash=generate_password_hash("b")
    )

    s3 = Student(
        name="lara",
        email="lara",
        password_hash=generate_password_hash("lara")
    )

    s4 = Student(
        name="hannah",
        email="hannah",
        password_hash=generate_password_hash("hannah")
    )

    s5 = Student(
        name="farheen",
        email="farheen",
        password_hash=generate_password_hash("farheen")
    )


    db.session.add_all([t1, s1, s2, s3, s4, s5])
    db.session.commit()

    # --- Create Folder for Teacher 1 ---
    f1 = Folder(
        name="Science Folder",
        user_id=t1.id
    )
    db.session.add(f1)
    db.session.commit()

    # --- Create Q&A Sets ---
    from datetime import date

    set1 = Q_and_A_Set(
        name="Biology Basics",
        folder_id=f1.id,
        date=date.today(),
        is_private=False
    )

    set2 = Q_and_A_Set(
        name="Chemistry Practice",
        folder_id=f1.id,
        date=date.today(),
        is_private=False
    )

    db.session.add_all([set1, set2])
    db.session.commit()

    # --- Add 1 Question to set1 ---
    q1 = Question(
        set_id=set1.id,
        question="What is the powerhouse of the cell?",
        answer="Mitochondria",
        fakeans1="Ribosome",
        fakeans2="Nucleus",
        fakeans3="Chloroplast"
    )

    db.session.add(q1)
    db.session.commit()
    extra_questions = [
        Question(
            set_id=set1.id,
            question="What molecule carries genetic information?",
            answer="DNA",
            fakeans1="RNA",
            fakeans2="Protein",
            fakeans3="ATP"
        ),
        Question(
            set_id=set1.id,
            question="Which organelle is responsible for photosynthesis?",
            answer="Chloroplast",
            fakeans1="Mitochondria",
            fakeans2="Golgi apparatus",
            fakeans3="Endoplasmic reticulum"
        ),
        Question(
            set_id=set1.id,
            question="What is the basic unit of life?",
            answer="Cell",
            fakeans1="Atom",
            fakeans2="Molecule",
            fakeans3="Organ"
        ),
        Question(
            set_id=set1.id,
            question="Which blood cells help fight infection?",
            answer="White blood cells",
            fakeans1="Red blood cells",
            fakeans2="Platelets",
            fakeans3="Stem cells"
        ),
        Question(
            set_id=set1.id,
            question="What part of the cell contains the genetic material?",
            answer="Nucleus",
            fakeans1="Mitochondria",
            fakeans2="Cytoplasm",
            fakeans3="Cell membrane"
        ),
        Question(
            set_id=set1.id,
            question="What process do plants use to make food?",
            answer="Photosynthesis",
            fakeans1="Respiration",
            fakeans2="Fermentation",
            fakeans3="Digestion"
        ),
        Question(
            set_id=set1.id,
            question="What type of macromolecule are enzymes?",
            answer="Proteins",
            fakeans1="Lipids",
            fakeans2="Carbohydrates",
            fakeans3="Nucleic acids"
        )
    ]

    db.session.add_all(extra_questions)
    db.session.commit()
    maths_set = Q_and_A_Set(
        name="Maths Year 8",
        folder_id=f1.id,
        date=date.today(),
        is_private=False
    )
    db.session.add(maths_set)
    db.session.commit()
    maths_questions = [
        Question(
            set_id=maths_set.id,
            question="What is 7 × 8?",
            answer="56",
            fakeans1="48",
            fakeans2="64",
            fakeans3="58"
        ),
        Question(
            set_id=maths_set.id,
            question="Solve: 12 + 15",
            answer="27",
            fakeans1="26",
            fakeans2="29",
            fakeans3="25"
        ),
        Question(
            set_id=maths_set.id,
            question="What is the square root of 81?",
            answer="9",
            fakeans1="8",
            fakeans2="6",
            fakeans3="7"
        ),
        Question(
            set_id=maths_set.id,
            question="Solve: 45 ÷ 5",
            answer="9",
            fakeans1="8",
            fakeans2="7",
            fakeans3="10"
        ),
        Question(
            set_id=maths_set.id,
            question="What is 15% of 200?",
            answer="30",
            fakeans1="20",
            fakeans2="25",
            fakeans3="35"
        ),
        Question(
            set_id=maths_set.id,
            question="What is 3² + 4²?",
            answer="25",
            fakeans1="12",
            fakeans2="18",
            fakeans3="30"
        ),
        Question(
            set_id=maths_set.id,
            question="Solve: 100 − 37",
            answer="63",
            fakeans1="73",
            fakeans2="67",
            fakeans3="57"
        ),
        Question(
            set_id=maths_set.id,
            question="What is the value of π rounded to 2 decimal places?",
            answer="3.14",
            fakeans1="3.10",
            fakeans2="3.12",
            fakeans3="3.16"
        ),
        Question(
            set_id=maths_set.id,
            question="How many degrees are in a right angle?",
            answer="90",
            fakeans1="45",
            fakeans2="180",
            fakeans3="120"
        ),
        Question(
            set_id=maths_set.id,
            question="What is 9 × 9?",
            answer="81",
            fakeans1="72",
            fakeans2="91",
            fakeans3="89"
        )
    ]

    chem_q = Question(
        set_id=set2.id,
        question="What is the chemical formula for table salt?",
        answer="NaCl",
        fakeans1="KCl",
        fakeans2="Na2CO3",
        fakeans3="CaCl2"
    )
    db.session.add(chem_q)
    db.session.add_all(maths_questions)
    db.session.commit()


    # --- Create Evaluation Sets folder for Alice ---
    evaluation_folder = Folder(
        name="Evaluation Sets",
        user_id=t1.id
    )
    db.session.add(evaluation_folder)
    db.session.commit()

    # --- Create GCSE Biology set ---
    gcse_biology = Q_and_A_Set(
        name="GCSE Biology",
        folder_id=evaluation_folder.id,
        date=date.today(),
        is_private=False
    )
    db.session.add(gcse_biology)
    db.session.commit()

    # --- GCSE Biology Questions ---
    gcse_biology_questions = [
        Question(gcse_biology.id, "What is the basic unit of life?", "Cell", "Atom", "Molecule", "Tissue"),
        Question(gcse_biology.id, "Which organelle controls the cell?", "Nucleus", "Mitochondria", "Ribosome", "Cell wall"),
        Question(gcse_biology.id, "Where does aerobic respiration occur?", "Mitochondria", "Nucleus", "Cytoplasm", "Chloroplast"),
        Question(gcse_biology.id, "What is the function of the ribosome?", "Protein synthesis", "Energy production", "Photosynthesis", "Cell division"),
        Question(gcse_biology.id, "What substance is chlorophyll?", "Green pigment", "Protein", "Enzyme", "Hormone"),
        Question(gcse_biology.id, "What is produced during photosynthesis?", "Glucose", "Carbon dioxide", "Oxygen only", "Protein"),
        Question(gcse_biology.id, "Which gas is needed for photosynthesis?", "Carbon dioxide", "Oxygen", "Nitrogen", "Hydrogen"),
        Question(gcse_biology.id, "Which gas is released during photosynthesis?", "Oxygen", "Carbon dioxide", "Nitrogen", "Hydrogen"),
        Question(gcse_biology.id, "What is diffusion?", "Movement from high to low concentration", "Movement using energy", "Movement through membranes", "Movement against gradient"),
        Question(gcse_biology.id, "What is osmosis?", "Movement of water through a membrane", "Movement of ions", "Diffusion of oxygen", "Active transport"),
        Question(gcse_biology.id, "Which process requires energy?", "Active transport", "Diffusion", "Osmosis", "Filtration"),
        Question(gcse_biology.id, "What enzyme breaks down starch?", "Amylase", "Protease", "Lipase", "Catalase"),
        Question(gcse_biology.id, "What is the role of enzymes?", "Speed up reactions", "Stop reactions", "Store energy", "Kill bacteria"),
        Question(gcse_biology.id, "What affects enzyme activity?", "Temperature", "Light only", "Sound", "Gravity"),
        Question(gcse_biology.id, "Which system transports oxygen?", "Circulatory system", "Digestive system", "Respiratory system", "Nervous system"),
        Question(gcse_biology.id, "Which organ pumps blood?", "Heart", "Lung", "Brain", "Kidney"),
        Question(gcse_biology.id, "What is the function of red blood cells?", "Carry oxygen", "Fight infection", "Clot blood", "Digest food"),
        Question(gcse_biology.id, "What gas do humans breathe out?", "Carbon dioxide", "Oxygen", "Nitrogen", "Hydrogen"),
        Question(gcse_biology.id, "What is the role of white blood cells?", "Fight pathogens", "Carry oxygen", "Clot blood", "Produce enzymes"),
        Question(gcse_biology.id, "What causes disease?", "Pathogens", "Genes", "Hormones", "Enzymes"),
        Question(gcse_biology.id, "What is a pathogen?", "Disease-causing microorganism", "Antibody", "Cell organelle", "Virus only"),
        Question(gcse_biology.id, "What type of reproduction involves one parent?", "Asexual", "Sexual", "Binary", "Selective"),
        Question(gcse_biology.id, "What carries genetic information?", "DNA", "Protein", "RNA only", "Glucose"),
        Question(gcse_biology.id, "What is variation?", "Differences between individuals", "Cell division", "Mutation only", "Adaptation"),
        Question(gcse_biology.id, "Which process produces gametes?", "Meiosis", "Mitosis", "Fertilisation", "Replication"),
        Question(gcse_biology.id, "What is fertilisation?", "Fusion of gametes", "Cell division", "Growth", "Mutation"),
        Question(gcse_biology.id, "What is an ecosystem?", "Community and environment", "Single organism", "Population only", "Food chain"),
        Question(gcse_biology.id, "Which level comes first in a food chain?", "Producer", "Consumer", "Decomposer", "Predator"),
        Question(gcse_biology.id, "What do decomposers do?", "Break down dead material", "Make food", "Hunt prey", "Store energy")
    ]

    db.session.add_all(gcse_biology_questions)
    db.session.commit()

    # --- Create a fake game for testing ---
    #test_game = Game(
    #    game_pin="123456",
    #    user_id=t1.id,         # teacher 1
    #    qaset_id=set1.id,      # the Biology Basics set
    #    capacity=30,
    #    is_active=False
    #)

    #db.session.add(test_game)
    #db.session.commit()

    #print("Test game created with pin 123456")

    print("Database initialised with sample data.")
    




