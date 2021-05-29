from flask import Flask, render_template, request, session, g, redirect, \
    url_for, jsonify
import os
from pathlib import Path
import sqlite3
import uuid

from givematerial.cache import SqliteLearnableCache
import givematerial.db.sqlite
import givematerial.extractors
import givematerial.learningstatus
from givematerial.recommendation import get_recommendations
from givematerial.web import ingest

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET')

DB_NAME = 'givematerial.sqlite'
givematerial.db.sqlite.create_tables(sqlite3.connect(DB_NAME))


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


@app.route("/", methods=['get', 'post'])
def home():
    sqlite_conn = get_conn()

    wk_token = request.form.get('wktoken', default=None)
    # if the user just logged in, add a download request for the token
    if wk_token:
        session['wktoken'] = wk_token
        if user_language(wk_token, sqlite_conn) == 'jp':
            ingest.add_download_request(wk_token, sqlite_conn)
        # redirect to same URL (to allow F5 refresh)
        return redirect(url_for('home'))
    else:
        wk_token = session.get('wktoken', default=None)

    token_finished_downloading = None
    if wk_token:
        language = user_language(wk_token, sqlite_conn)

        # Check if the token data has already been downloaded
        open_dl_requests = ingest.get_open_download_requests(sqlite_conn)
        token_finished_downloading = wk_token not in open_dl_requests

        learning_status = givematerial.learningstatus.SqliteBasedStatus(
            sqlite_conn, wk_token)
        known_words = learning_status.get_known_learnables()
        learning_words = learning_status.get_learning_learnables()
        if language == 'jp':
            learnable_extractor = \
                givematerial.extractors.JapaneseKanjiExtractor()
        elif language == 'hr':
            # Classla does not work inside flask, so we have to rely on
            # pre-parsed data from the cache
            learnable_extractor = givematerial.extractors.NoopExtractor()
        else:
            raise NotImplementedError('Unsupported language')

        # TODO: Cleanup these definitions
        texts_folder = Path('data') / 'texts'
        cache_folder = Path('data') / language / 'cache'

        recommendations = get_recommendations(
            known_words, learning_words, cache_folder, texts_folder, language,
            learnable_extractor, count=20)

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
        wk_token=wk_token,
        token_finished_downloading=token_finished_downloading,
        auto_refresh=auto_refresh)


@app.route("/learning-status", methods=['post'])
def push_learning_status():
    data = request.json
    user_id = data['token']

    sqlite_conn = get_conn()
    # check whether user exists
    c = sqlite_conn.cursor()
    c.execute('SELECT COUNT(*) FROM user WHERE user_id = ?', (user_id,))
    count = c.fetchone()[0]
    if count == 0:
        return jsonify({'error': 'user does not exist'}), 401

    cache = SqliteLearnableCache(sqlite_conn, user_id)
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


if __name__ == "__main__":
    custom_host = os.getenv('HOST_BIND', default=None)

    if custom_host:
        app.run(debug=True, host=custom_host)
    else:
        app.run(debug=True)
