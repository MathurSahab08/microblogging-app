from datetime import datetime, timezone
from flask import render_template, flash, redirect, url_for, request, g, \
    current_app
from flask_login import current_user, login_required
from flask_babel import _, get_locale
import sqlalchemy as sa
from langdetect import detect, LangDetectException
from Y import db
from Y.main.forms import EditProfileForm, EmptyForm, PostForm
from Y.models import User, Post
#from Y.translate import translate
from Y.main import bp


# handlers for the application routes are written as Python functions, 
# called 'view functions'. View functions are mapped to 
# one or more route URLs so that Flask knows 
# what logic to execute when a client requests 
# a given URL.
@bp.route('/', methods=['GET','POST'])
@bp.route('/index', methods=['GET','POST'])
@login_required
def index():
        try:
        
            global showUsers
            showUsers=False
            form= PostForm()

            # POST request
            if form.validate_on_submit():
                post = Post(body=form.post.data, author=current_user)
                db.session.add(post)
                db.session.commit()
                flash(('Your post is now live!'))

                # redirected back to index page when responding to POST request on a form submission --> aka Post/Redirect/Get pattern
                # this is done to avoid re-submitting the form in case the user hits the refresh button
                # redirection switches the request back to 'GET'
                return redirect(url_for('main.index'))
            
            # posts = [
            #     {
            #         'author': {'username': 'John'},
            #         'body': 'Beautiful day in Portland!'
            #     },
            #     {
            #         'author': {'username': 'Susan'},
            #         'body': 'The Avengers movie was so cool!'
            #     }
            # ]

            page = request.args.get('page', 1, type=int)
            posts= db.paginate(current_user.following_posts(), page=page, per_page=current_app.config['POSTS_PER_PAGE'], error_out=False)

            # next_num and prev_num are available through the pagination object above
            next_url = url_for('main.index', page=posts.next_num) if posts.has_next else None
            prev_url = url_for('main.index', page=posts.prev_num) if posts.has_prev else None


            if request.method == 'POST':
                showUsers=True
                def displayUsers():
                    global users
                    users= [str(i).replace('<','').replace('>','').split()[1] for i in list(db.session.query(User).all())]
                    print("full list of users ->", users)
                return render_template('index.html', title='Home-Page', posts=posts.items, displayUsers=displayUsers(), showUsers=showUsers, users=users, form = form, next_url=next_url, prev_url=prev_url)
            elif request.method == 'GET':
                def displayUsers():
                    print("display users button not pressed")

                    #  render_template() takes a template filename and 
                    # a variable list of template arguments, 
                    # and returns the same template, 
                    # but with all the placeholders in it replaced with actual values.
                return render_template('index.html', title='Home-Page', posts=posts.items, displayUsers=displayUsers(), showUsers=showUsers, form = form, next_url=next_url, prev_url=prev_url)
        except Exception as e:
            print(e)

@bp.route('/user/<username>')
@login_required
def user(username):

    # first_or_404 will either yield a value or raise 404 error and exit this view function
    user= db.first_or_404(sa.select(User).where(User.username == username))
    page = request.args.get('page', 1, type=int)
    query = user.posts.select().order_by(Post.timestamp.desc())
    posts = db.paginate(query, page=page,
                        per_page=current_app.config['POSTS_PER_PAGE'],
                        error_out=False)
    
    # extra username argument as it is required by this view function
    next_url = url_for('user', username=user.username, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('user', username=user.username, page=posts.prev_num) \
        if posts.has_prev else None
    form = EmptyForm()
    return render_template('user.html', user=user, posts=posts.items, form= form, next_url=next_url, prev_url=prev_url,)

# 'before_request' decorator registers the below function
# to be executed right before any of the other view functions defined in this module
# whatever actions that are needed to be performed right before handling a request can be defined here
@bp.before_request
def before_request():

    if current_user.is_authenticated:

        # 'current_user' -> Flask-Login will invoke the user loader callback function, which will run a 
        # database query that will put the target user in the database session
        current_user.last_seen= datetime.now(timezone.utc)

        # db.session.add() not needed here as current_user (user in db session) has been updated with the above value
        db.session.commit()

@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash(_('Your changes have been saved.'))
        return redirect(url_for('main.edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title=_('Edit Profile'),
                           form=form)


@bp.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == username))
        if user is None:
            flash(_('User %(username)s not found.', username=username))
            return redirect(url_for('main.index'))
        if user == current_user:
            flash(_('You cannot follow yourself!'))
            return redirect(url_for('main.user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash(_('You are following %(username)s!', username=username))
        return redirect(url_for('main.user', username=username))
    else:
        return redirect(url_for('main.index'))


@bp.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == username))
        if user is None:
            flash(_('User %(username)s not found.', username=username))
            return redirect(url_for('main.index'))
        if user == current_user:
            flash(_('You cannot unfollow yourself!'))
            return redirect(url_for('main.user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash(_('You are not following %(username)s.', username=username))
        return redirect(url_for('main.user', username=username))
    else:
        return redirect(url_for('main.index'))
    
@bp.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    query = sa.select(Post).order_by(Post.timestamp.desc())
    posts = db.paginate(query, page=page,
                        per_page=current_app.config['POSTS_PER_PAGE'],
                        error_out=False)
    next_url = url_for('main.explore', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('main.explore', page=posts.prev_num) \
        if posts.has_prev else None

    # .items contains list of items obtained from the pagination object
    return render_template('main.index.html', title=_('Explore'),
                            posts=posts.items, next_url=next_url,
                            prev_url=prev_url)

