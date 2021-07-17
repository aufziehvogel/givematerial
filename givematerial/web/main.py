from flask import Flask, render_template, request, session, g, redirect, \
    url_for, jsonify
from flask_dance.contrib.github import make_github_blueprint, github
from flask_dance.consumer import oauth_authorized
from flask_login import LoginManager, login_user, UserMixin, \
    current_user, login_required
import os
from pathlib import Path
import sqlite3
import uuid

from givematerial.cache import SqliteLearnableCache
import givematerial.db.sqlite
import givematerial.extractors
import givematerial.learningstatus
from givematerial import recommendation
from givematerial.web import ingest

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
app.secret_key = os.getenv('FLASK_SECRET')
blueprint_gh = make_github_blueprint(
    client_id=os.getenv('GITHUB_CLIENT_ID'),
    client_secret=os.getenv('GITHUB_CLIENT_SECRET'),
)
app.register_blueprint(blueprint_gh, url_prefix="/login")

DB_NAME = 'givematerial.sqlite'
givematerial.db.sqlite.create_tables(sqlite3.connect(DB_NAME))


class User(UserMixin):
    def __init__(self, user_id):
        self.id = user_id


@login_manager.user_loader
def load_user(user_id):
    print(user_id)
    return User(user_id)


@oauth_authorized.connect_via(blueprint_gh)
def logged_in(blueprint, token):
    if not token:
        return False

    resp = blueprint.session.get("/user")
    if not resp.ok:
        return False

    print(resp)
    github_info = resp.json()
    print(github_info)
    github_user_id = str(github_info["login"])

    print(blueprint.name)
    print(token)
    print(github_user_id)

    sqlite_conn = get_conn()
    cur = sqlite_conn.cursor()
    cur.execute(
        'INSERT OR IGNORE INTO user '
        '(user_id, oauth_name, oauth_provider, language) VALUES (?, ?, ?, "hr")',
        (str(uuid.uuid4()), github_user_id, blueprint.name))
    sqlite_conn.commit()

    c = cur.execute('SELECT user_id FROM user WHERE oauth_name = ? '
        'AND oauth_provider = ?', (github_user_id, blueprint.name))

    user = User(c.fetchone()[0])
    print(user.get_id())
    login_user(user)
    print('logged in user')

    return False


def public_registration():
    return bool(int(os.getenv('PUBLIC_REGISTRATION', default=0)))


@app.context_processor
def global_config_variables():
    return {
        'public_registration': public_registration(),
    }


def get_conn():
    if 'sqlite_conn' in g:
        return g.sqlite_conn
    else:
        sqlite_conn = sqlite3.connect(DB_NAME)
        g.sqlite_conn = sqlite_conn
        return sqlite_conn


def user_language(user_id: str, conn: sqlite3.Connection) -> str:
    c = conn.cursor()
    c.execute('SELECT language FROM user WHERE user_id = ?', (user_id,))
    row = c.fetchone()
    if not row:
        language = 'jp'
    else:
        language = row[0]

    return language


def get_learnable_extractor(language: str) \
        -> givematerial.extractors.LearnableExtractor:
    if language == 'jp':
        return givematerial.extractors.JapaneseKanjiExtractor()
    elif language == 'hr':
        # Classla does not work inside flask, so we have to rely on
        # pre-parsed data from the cache
        return givematerial.extractors.NoopExtractor()
    else:
        raise NotImplementedError('Unsupported language')


@app.route("/", methods=['get', 'post'])
def home():
    print(current_user.get_id())
    sqlite_conn = get_conn()

    wk_token = request.form.get('wktoken', default=None)
    # if the user just logged in, add a download request for the token
    if current_user.get_id():
        sqlite_conn.execute(
            'UPDATE user SET last_login = datetime("now") WHERE user_id = ?',
            (current_user.get_id(),))
        sqlite_conn.commit()
        wk_token = current_user.get_id()
    elif wk_token:
        session['wktoken'] = wk_token
        if user_language(wk_token, sqlite_conn) == 'jp':
            ingest.add_download_request(wk_token, sqlite_conn)

        # redirect to same URL (to allow F5 refresh)
        return redirect(url_for('home'))
    else:
        wk_token = session.get('wktoken', default=None)

    token_finished_downloading = None
    most_common_words = []
    if wk_token:
        language = user_language(wk_token, sqlite_conn)

        # Check if the token data has already been downloaded
        open_dl_requests = ingest.get_open_download_requests(sqlite_conn)
        token_finished_downloading = wk_token not in open_dl_requests

        learning_status = givematerial.learningstatus.SqliteBasedStatus(
            sqlite_conn, wk_token)
        known_words = learning_status.get_known_learnables()
        learning_words = learning_status.get_learning_learnables()
        learnable_extractor = get_learnable_extractor(language)

        # TODO: Cleanup these definitions
        texts_folder = Path('data') / 'texts'
        cache_folder = Path('data') / language / 'cache'

        recommendations = recommendation.get_recommendations(
            known_words, learning_words, cache_folder, texts_folder, language,
            learnable_extractor, count=20)
        most_common_words = recommendation.most_common_words(
            known_words, learning_words,
            cache_folder, texts_folder, language, learnable_extractor,
            count=100)

        # TODO: Better (generic) scheme for hiding already finished texts
        cur = sqlite_conn.cursor()
        cur.execute(
            'SELECT text_url FROM reading_list WHERE user_id = ?', (wk_token,))
        already_read = [item[0] for item in cur.fetchall()]
        recommendations = [rec for rec in recommendations
                           if rec.url not in already_read]

    else:
        recommendations = []

    if token_finished_downloading is None:
        auto_refresh = False
    else:
        auto_refresh = not token_finished_downloading

    return render_template(
        "home.html",
        recommendations=recommendations,
        most_common_words=[word for word, count in most_common_words],
        wk_token=wk_token,
        token_finished_downloading=token_finished_downloading,
        auto_refresh=auto_refresh)


@app.route('/recommendations/<language>')
@login_required
def recommendations(language: str):
    sqlite_conn = get_conn()

    most_common_words = []

    if current_user.get_id():
        learning_status = givematerial.learningstatus.SqliteBasedStatus(
            sqlite_conn, current_user.get_id(), language)
        known_words = learning_status.get_known_learnables()
        learning_words = learning_status.get_learning_learnables()
        learnable_extractor = get_learnable_extractor(language)

        # TODO: Cleanup these definitions
        texts_folder = Path('data') / 'texts'
        cache_folder = Path('data') / language / 'cache'

        recommendations = recommendation.get_recommendations(
            known_words, learning_words, cache_folder, texts_folder, language,
            learnable_extractor, count=20)
        most_common_words = recommendation.most_common_words(
            known_words, learning_words,
            cache_folder, texts_folder, language, learnable_extractor,
            count=100)

        # TODO: Better (generic) scheme for hiding already finished texts
        cur = sqlite_conn.cursor()
        cur.execute(
            'SELECT text_url FROM reading_list WHERE user_id = ?', (current_user.get_id(),))
        already_read = [item[0] for item in cur.fetchall()]
        recommendations = [rec for rec in recommendations
                           if rec.url not in already_read]

    else:
        recommendations = []

    return render_template(
        "home.html",
        recommendations=recommendations,
        most_common_words=[word for word, count in most_common_words],
        wk_token=current_user.get_id(),
        token_finished_downloading=True)


@app.route("/learning-status", methods=['post'])
def push_learning_status():
    data = request.json
    user_id = data['token']
    language = data['language']

    sqlite_conn = get_conn()
    # check whether user exists
    c = sqlite_conn.cursor()
    c.execute('SELECT COUNT(*) FROM user WHERE user_id = ?', (user_id,))
    count = c.fetchone()[0]
    if count == 0:
        return jsonify({'error': 'user does not exist'}), 401

    cache = SqliteLearnableCache(sqlite_conn, user_id, language)
    learning, known = cache.read_cache()

    # remove older state
    learning = list(set(learning).difference(data['known']))
    known = list(set(known).difference(data['learning']))
    learning += data['learning']
    known += data['known']

    cache.update_cache(learning, known)

    return jsonify({})


@app.route("/redirect/read")
def redirect_read():
    url = request.args['url']
    mark_read = bool(int(request.args['mark_read']))

    sqlite_conn = get_conn()
    cur = sqlite_conn.cursor()

    wk_token = session.get('wktoken', default=None)

    if mark_read and wk_token:
        cur.execute(
            'INSERT INTO reading_list (user_id, text_url) VALUES (?, ?)',
            (wk_token, url))
        sqlite_conn.commit()

    return redirect(url)


@app.route("/register", methods=['get', 'post'])
def register():
    if not public_registration():
        return 'Public registration not enabled', 404

    token = None

    if 'language' in request.form:
        language = request.form['language']

        token = str(uuid.uuid4())
        sqlite_conn = get_conn()
        cur = sqlite_conn.cursor()
        cur.execute(
            'INSERT INTO user (user_id, language) VALUES (?, ?)',
            (token, language))
        sqlite_conn.commit()

    return render_template('register.html', token=token)


@app.route("/howworks")
def howworks():
    return render_template('howworks.html')


if __name__ == "__main__":
    custom_host = os.getenv('HOST_BIND', default=None)

    if custom_host:
        app.run(debug=True, host=custom_host)
    else:
        app.run(debug=True)
