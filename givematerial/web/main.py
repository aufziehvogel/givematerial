from flask import Flask, render_template, request, session, g, redirect, url_for
import os
from pathlib import Path
import sqlite3

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


@app.route("/", methods=['get', 'post'])
def home():
    sqlite_conn = get_conn()

    wk_token = request.form.get('wktoken', default=None)
    # if the user just logged in, add a download request for the token
    if wk_token:
        ingest.add_download_request(wk_token, sqlite_conn)
        # redirect to same URL (to allow F5 refresh)
        return redirect(url_for('home'))
    else:
        wk_token = session.get('wktoken', default=None)

    token_finished_downloading = None
    if wk_token:
        session['wktoken'] = wk_token

        # Check if the token data has already been downloaded
        open_dl_requests = ingest.get_open_download_requests(sqlite_conn)
        token_finished_downloading = wk_token not in open_dl_requests

        language = 'jp'
        learning_status = givematerial.learningstatus.SqliteBasedStatus(
            sqlite_conn, wk_token)
        known_words = learning_status.get_known_learnables()
        learning_words = learning_status.get_learning_learnables()
        learnable_extractor = givematerial.extractors.JapaneseKanjiExtractor()

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

    return render_template(
        "home.html",
        recommendations=recommendations,
        wk_token=wk_token,
        token_finished_downloading=token_finished_downloading,
        auto_refresh=not token_finished_downloading)


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


if __name__ == "__main__":
    app.run(debug=True)
