import json

from flask import Flask, render_template, request, redirect, abort, url_for
from sqlalchemy import create_engine, text, exc
from sqlalchemy.orm import sessionmaker, scoped_session
app = Flask(__name__)

engine = create_engine('postgresql://postgres:12345@localhost/blog_db')
db = scoped_session(sessionmaker(bind=engine))


posts_file = 'posts.json'


def load_posts():
    with open(posts_file, encoding='utf=8') as f:
        posts = json.load(f)
        return posts


def write_posts(posts):
    with open(posts_file, 'w+', encoding='utf=8') as f:
        json.dump(posts, f, ensure_ascii=False)


def get_post_by_id(id):
    post = db.execute(
        text(
            f'SELECT posts.id, posts.title, posts.description, '
            f'posts.date_pub, (SELECT COUNT(*) FROM likes '
            f'WHERE likes.post_id = {id}) AS like_count, users.username, '
            f'json_agg(json_build_object(\'text\', '
            f'commentaries.commentary_text, \'date\', '
            f'commentaries.commentary_date)) AS commentaries '
            f'FROM posts JOIN users ON posts.author = users.id '
            f'LEFT JOIN commentaries ON posts.id = commentaries.post_id '
            f'WHERE posts.id = {id} GROUP BY posts.id, posts.title, '
            f'posts.description, posts.date_pub, users.username;'
        )).first()
    return post


@app.route("/")
def index():
    query = (
        f'SELECT posts.id, posts.title, posts.description, posts.date_pub, '
        f'users.username, (SELECT COUNT(*) FROM likes WHERE '
        f'likes.post_id = posts.id) AS like_count FROM posts '
        f'JOIN users ON posts.author = users.id; '
    )
    posts = db.execute(text(query)).all()
    return render_template('index.html', posts=posts)


@app.route('/posts/<int:id>')
def post_detail(id):
    try:
        post = get_post_by_id(id)
        print(post)
    except IndexError:
        abort(404)
    return render_template('post_detail.html', post=post)


@app.route("/add_post", methods=['GET', 'POST'])
def add_post():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        db.execute(text(
            f"INSERT INTO posts (title, description, author) "
            f"VALUES ('{title}', '{description}', {1});"
        ))
        db.commit()
        return redirect('/')
    return render_template('add_post.html')


@app.route("/delete_post/<int:id>")
def delete_post(id):
    try:
        db.execute(
            text(
                f'DELETE FROM likes '
                f'WHERE post_id = {id};'
                f'DELETE FROM commentaries '
                f'WHERE post_id = {id};'
                f'DELETE FROM posts '
                f'WHERE posts.id = {id};'
            ))
        db.commit()
    except IndexError:
        abort(404)
    return redirect(url_for('index'))


@app.route("/edit_post/<int:id>", methods=['GET', 'POST'])
def edit_post(id):
    post = get_post_by_id(id)
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        db.execute(text(
            f"UPDATE posts "
            f"SET title='{title}', description='{description}', date_pub = NOW() "
            f"WHERE id = {id};"
        ))
        db.commit()
        return redirect('/')
    return render_template('edit.html', post=post)


@app.route("/comment_post/<int:id>", methods=['GET', 'POST'])
def comment_post(id):
    try:
        if request.method == 'POST':
            comment = request.form.get('comment')
            db.execute(text(
                f"INSERT INTO commentaries (post_id, commentary_text) VALUES ({id}, '{comment}')"
            ))
            db.commit()
            return redirect(url_for('post_detail', id=id))
    except exc.SQLAlchemyError:
        return "Вы ввели слишком длинный комментарий!"
    return render_template('post_detail.html')


@app.route("/like_post/<int:id>", methods=['GET', 'POST'])
def like_post(id):
    if request.method == 'POST':
        db.execute(text(
            f"INSERT INTO likes (post_id, author_id) VALUES ({id}, 1)"
        ))
        db.commit()
        return redirect('/')
    return redirect(url_for('index'))


if __name__ == "__main__":
    app.run(debug=True)