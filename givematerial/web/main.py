from flask import Flask, render_template, request
from pathlib import Path
import sqlite3

import givematerial.extractors
import givematerial.learningstatus
from givematerial.recommendation import get_recommendations

app = Flask(__name__)


@app.route("/", methods=['get', 'post'])
def home():
    wk_token = request.form.get('wktoken', default=None)

    if wk_token:
        sqlite_conn = sqlite3.connect('givematerial.sqlite')

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
            learnable_extractor)
    else:
        recommendations = []

    return render_template("home.html", recommendations=recommendations)


if __name__ == "__main__":
    app.run(debug=True)
