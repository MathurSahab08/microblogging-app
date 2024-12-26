from typing import Optional
from datetime import datetime, timezone
import sqlalchemy as sa
import sqlalchemy.orm as so
from Y import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from Y import login
from hashlib import md5
from time import time
import jwt
from flask import current_app

# followers
'''
follower_id ___|___ followed_id
               |
               |
               |
''' 

#users
'''
username,email,password_hash, posts, about_me, last_seen, | id ____|____following ___|___ followers
                                                          |        |                 |
                                                          |        |                 |
                                                          |        |                 |
'''
# self referential many-to-many relationship
# followers table is the association table
#Each record in this table represents one link between a follower user and a followed user
followers = sa.Table(
    'followers',
    db.metadata,

    # both columns are primary keys but do not hold unique values
    # combination of both columns creates a unique key called 'compound primary key'
    sa.Column('follower_id', sa.Integer, sa.ForeignKey('user.id'),
              primary_key=True),
    sa.Column('followed_id', sa.Integer, sa.ForeignKey('user.id'),
              primary_key=True)
)


#db.Model is the base class for all models and is inherited by the User class here
class User(UserMixin, db.Model):

    # using python 'Type Hints' here, denoted by : for variables
    # -> denotes the return type of a python function
    id: so.Mapped[int] = so.mapped_column(primary_key=True)

    #'so.Mapped' wrapper declares the data type of the column and ensures that the column is non-nullable
    # indexing allows better searches
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True)

    # optional keyword allows column to be nullable
    # so.Mapped() function allows to set more constraints on columns including the size of the string columns
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))

    # posts is a relationship attribute, not a column
    # so.relationship is a model class and represents the other side of the relationship
    # back_populates argument contain the name of the relationship attribute on the other side of the relationship
    posts: so.WriteOnlyMapped['Post'] = so.relationship(back_populates='author')
    about_me: so.Mapped[Optional[str]] = so.mapped_column(sa.String(140))
    last_seen: so.Mapped[Optional[datetime]] = so.mapped_column(default=lambda: datetime.now(timezone.utc))

    # relationship attribute of type 'User'
    following: so.WriteOnlyMapped['User'] = so.relationship(

        # secondary is for association table
        secondary=followers, 
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        back_populates='followers')
    
    followers: so.WriteOnlyMapped['User'] = so.relationship(
        secondary=followers, 
        primaryjoin=(followers.c.followed_id == id),
        secondaryjoin=(followers.c.follower_id == id),
        back_populates='following')


    # function to print objects
    def __repr__(self):
        return '<User {}>'.format(self.username)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}'
    
    def follow(self, user):

        # here the user is the person that the current_user wants to follow
        if not self.is_following(user):
            self.following.add(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.following.remove(user)

    def is_following(self, user):
        query = self.following.select().where(User.id == user.id)

        #return true when query has 1 result
        #return false when query has 0(None) result
        return db.session.scalar(query) is not None

    def followers_count(self):

        # inner query needs to be converted to a sub query
        query = sa.select(sa.func.count()).select_from(
            self.followers.select().subquery())
        return db.session.scalar(query)

    def following_count(self):
        query = sa.select(sa.func.count()).select_from(
            self.following.select().subquery())
        return db.session.scalar(query)
    
    def following_posts(self):

        # two separate references to the user model, i.e, two separate tables out of the same single table/model
        Author = so.aliased(User)
        Follower = so.aliased(User)

        # total 3 tables joined together
        # self.id points to the fact that the current user wants posts of authors who have the current user as their follower
        return (
            sa.select(Post)
            .join(Post.author.of_type(Author)) #'of_type' indicates that right side of relationship is with Author alias
            .join(Author.followers.of_type(Follower), isouter=True) # outer join to include posts from authors with 0 followers
            .where(sa.or_(
                Follower.id == self.id,
                Author.id == self.id, # include posts by user themselves
            ))
            .group_by(Post) # to remove duplicate posts
            .order_by(Post.timestamp.desc())
        )
    # post_id (will repeat to map 1 post with many followers) | post_author_id (will repeat bcoz posts are repeating) | followerOfAuthor_id (will point to different posts but will not repeat for the same post) 
    # --> filter only those posts where current_user is a follower of the author of those posts

    # returns a token
    def get_reset_password_token(self, expires_in=600):

        # HS256 is a encoding algorithm
        # 10 mins expiry time
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'], algorithm='HS256')
    
    #a static method, which means that it can be invoked directly from the class. 
    # A static method is similar to a class method, with the only difference that static methods do not receive the class as a first argument.
    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])['reset_password']
        except:
            return
        return db.session.get(User, id)
    


class Post(db.Model):

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    body: so.Mapped[str] = so.mapped_column(sa.String(140))
    timestamp: so.Mapped[datetime] = so.mapped_column(index=True, default=lambda: datetime.now(timezone.utc))
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), index=True)

    # 'author' is a relationship attribute
    author: so.Mapped[User] = so.relationship(back_populates='posts')

    def __repr__(self):
        return '<Post {}>'.format(self.body)

# user loader function
# automatically invoked whenever 'current_user' is referenced
# puts the user with the provided ID into the db session
@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))