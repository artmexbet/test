from flask import *
from data import db_session, users
from flask_login import LoginManager, login_required, logout_user, login_user, current_user
from forms.user import RegisterForm, LoginForm, CaloriesForm
from data.users import User
from data.friendship import Friend
from requests import get, post

app = Flask(__name__)
app.config["SECRET_KEY"] = "IIOIIA HOCOPOGA"
login_manager = LoginManager()
login_manager.init_app(app)

KEY = "128aca014emsh84e178dd3d4b64fp121dcdjsncaff36b7e4bc"


def translate(text):
    url = "https://translated-mymemory---translation-memory.p.rapidapi.com/api/get"

    querystring = {"langpair": "ru|en", "q": text, "mt": "1", "onlyprivate": "0", "de": "a@b.c"}

    headers = {
        "X-RapidAPI-Host": "translated-mymemory---translation-memory.p.rapidapi.com",
        "X-RapidAPI-Key": "128aca014emsh84e178dd3d4b64fp121dcdjsncaff36b7e4bc"
    }

    response = get(url, headers=headers, params=querystring)

    return response.json()


def get_calories(name):
    url = "https://calorieninjas.p.rapidapi.com/v1/nutrition"

    querystring = {"query": name}

    headers = {
        "X-RapidAPI-Host": "calorieninjas.p.rapidapi.com",
        "X-RapidAPI-Key": KEY
    }

    response = get(url, headers=headers, params=querystring)
    return response.json()


def get_translated_calories(name):
    return get_calories(translate(name)["responseData"]["translatedText"])


# Регистрация
@app.route('/register', methods=['GET', 'POST'])
def reqister():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Пароли не совпадают")
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', title='Регистрация',
                                   form=form,
                                   message="Такой пользователь уже есть")
        user = User(
            name=form.name.data,
            email=form.email.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)


# Vhod
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == "POST" and form.is_submitted():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.name == form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


# Main page
@app.route('/')
def main_page():
    return render_template('main_page.html', title='Главная страница')


@login_required
@app.route('/profile')
def profile():
    eat = current_user.eat
    dates = set()
    for e in eat:
        dates.add(e.modified_date)
    return render_template('profile.html', str_id=str(current_user.id), dates=dates, title="Профиль")


@app.route('/calories', methods=['GET', 'POST'])
def calories(string=''):
    cal = {"items": [0, 0]}
    if request.method == "POST":
        string = request.form.get("proj")
        cal = get_translated_calories(string)
    return render_template('calories.html', calories=cal["items"], name=string)


@login_required
@app.route("/calories/<string:date>")
def date_calories(date):
    temp = sorted([i for i in current_user.eat if str(i.modified_date) == date],
                  key=lambda x: x.eat_time)
    a = {"Завтрак": [], "Обед": [], "Ужин": []}
    for i in temp:
        a[i.eat_time].append(i)
    return render_template("date_calories.html", food=a, title="Отчёт о питании")


@login_required
@app.route("/change_password", methods=["POST"])
def change_password():
    form = request.form
    sess = db_session.create_session()
    if current_user.check_password(form.get("oldPassword", "")):
        current_user.set_password(form["newPassword"])
        sess.commit()
    return redirect("/profile")


@login_required
@app.route("/change_photo", methods=["POST"])
def change_photo():
    file = request.files['photo']
    file.save("static/user_photos/" + str(current_user.id) + ".png")
    sess = db_session.create_session()
    sess.query(User).get(current_user.id).has_photo = True
    current_user.has_photo = True
    sess.commit()
    return redirect("/profile")


@login_required
@app.route("/edit_calories", methods=["POST"])
def edit_calories():
    form = request.form
    a = get_translated_calories(form["name"])

    db_sess = db_session.create_session()
    food = Friend(
        user_id=current_user.id,
        name=form["name"],
        proteins=a['items'][0]["protein_g"],
        fat=a['items'][0]["fat_total_g"],
        carbohydrates=a['items'][0]["carbohydrates_total_g"],
        fibers=a['items'][0]["fiber_g"],
        calories=a['items'][0]["calories"],
        sugar=a['items'][0]['sugar_g'],
        eat_time=form["eat_time"],
        grams=int(form["proj1"] if form["proj1"] else 100)
    )
    db_sess.add(food)
    db_sess.commit()

    return redirect("/calories")


if __name__ == '__main__':
    db_session.global_init("db/blogs.db")
    app.run(port=8080, host='127.0.0.1')
