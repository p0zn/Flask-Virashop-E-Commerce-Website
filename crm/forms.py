from flask_wtf import FlaskForm
from flask_login import current_user
from flask_wtf.file import FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, IntegerField , DecimalField, FileField
from wtforms.validators import DataRequired,Length,Email,EqualTo, ValidationError
from crm.models import Category, User

class RegistrationForm(FlaskForm):
    name = StringField("Name",validators=[DataRequired(),Length(min=0,max=20)])
    lastname = StringField("Lastname",validators=[DataRequired(),Length(min=0,max=20)])
    phone = StringField("Phone",validators=[DataRequired(),Length(min=11,max=11)])
    username = StringField("Username",validators=[DataRequired(),Length(min=5,max=20)])
    email = StringField("Email",validators=[Email(),DataRequired()])
    password = PasswordField("Password",validators=[DataRequired()])
    confirm_password = PasswordField("Confirm Password",validators=[DataRequired(),EqualTo("password")])
    submit = SubmitField("Sign Up")

    def validate_username(self,username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError("Username already exists")

    def validate_email(self,email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError("Email already exists")

class LoginForm(FlaskForm):
    username = StringField("Username",validators=[DataRequired(),Length(min=5,max=20)])
    password = PasswordField("Password",validators=[DataRequired()])
    remember = BooleanField("Remember Me")
    submit = SubmitField("Login")


class ProductForm(FlaskForm):
    ProductName = StringField('Product Name',validators=[DataRequired()])
    CategoryId = IntegerField('Category ID',validators=[DataRequired()])
    QuantityPerUnit = StringField('Quantity Per Unit', validators=[DataRequired()])
    UnitPrice = DecimalField('Unit Price', validators=[DataRequired()])
    UnitInStock = IntegerField('Unit In Stock', validators=[DataRequired()])
    Description = TextAreaField('Description', validators=[DataRequired()])
    image_1 = FileField('Image 1',  validators=[FileAllowed(['jpg', 'png'])])
    image_2 = FileField('Image 2',  validators=[FileAllowed(['jpg', 'png'])])
    image_3 = FileField('Image 3',  validators=[FileAllowed(['jpg', 'png'])])
    Submit = SubmitField("Submit")


class CommentForm(FlaskForm):
    comment_text = TextAreaField('Comment',validators=[DataRequired()])
    submit = SubmitField("Submit")


class UpdateAccountForm(FlaskForm):
    name = StringField("Name",validators=[DataRequired(),Length(min=0,max=20)])
    lastname = StringField("Lastname",validators=[DataRequired(),Length(min=0,max=20)])
    phone = StringField("Phone",validators=[DataRequired(),Length(min=11,max=11)])
    address = TextAreaField('Address', validators=[DataRequired()])
    username = StringField("Username",validators=[DataRequired(),Length(min=5,max=20)])
    email = StringField("Email",validators=[Email(),DataRequired()])
    picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png','jpeg'])])
    submit = SubmitField("Update Profile")

    def validate_username(self,username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError("Username already exists")

    def validate_email(self,email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError("Email already exists")


class RequestResetForm(FlaskForm):
    email = StringField("Email",validators=[Email(),DataRequired()])
    submit = SubmitField("Request Reset Password")

    def validate_email(self,email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError("There is no account with that email. You must register first.")


class ResetPasswordForm(FlaskForm):
    password = PasswordField("Password",validators=[DataRequired()])
    confirm_password = PasswordField("Confirm Password",validators=[DataRequired(),EqualTo("password")])
    submit = SubmitField("Reset Password")



