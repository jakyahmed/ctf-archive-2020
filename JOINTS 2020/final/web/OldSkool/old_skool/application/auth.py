from flask_login import login_user, logout_user, login_required, current_user
from .models import User
from . import db
from flask import Flask, render_template, session, make_response, \
	request, Response, redirect, url_for, flash, current_app as app, Blueprint
from .utils import RegisterForm
from flask_generic_views import TemplateView, MethodView
from passlib.hash import bcrypt


auth = Blueprint('auth', __name__)

class RegisterView(TemplateView):
	template_name = "register.html"

	def get(self):
		form = RegisterForm()
		return render_template(self.template_name, form=form)

	def post(self):
		form = RegisterForm(request.form)

		if form.validate():
			username = form.username.data
			bio = form.bio.data
			motto = form.motto.data
			existing_user = User.query.filter(User.username==username).first()

			if existing_user:
				flash("Username sudah ada yang punya !", "danger")
				return render_template(self.template_name, form=form)
			else:
				password = bcrypt.hash(form.password.data)
				new_user = User(username=username,
								bio=bio,
								password=password,
								admin=False,
								motto=motto)
				
				db.session.add(new_user)
				db.session.commit()
				flash('Registrasi berhasil, silahkan login','success')
				return redirect(url_for("login"))
		else:
			return render_template(self.template_name, form=form)


class LoginView(TemplateView):
	template_name = "login.html"

	def get(self):
		return render_template(self.template_name)

	def post(self):
		username = request.form.get("username")
		password = request.form.get("password")

		user = User.query.filter(User.username == username).first()
		if user:
			if bcrypt.verify(password, user.password):
				login_user(user)
				flash("Login Sukses", "success")
				return redirect(url_for("profile"))
			else:
				flash("Password Salah :(", "danger")
		else:
			flash("Username gaada !", "danger")

		return redirect(url_for("login"))


class LogoutView(TemplateView):
	decorators = [login_required]

	def get(self):
		logout_user()
		flash("Sukses Logout", "success")
		return redirect(url_for("index"))


app.add_url_rule('/register', view_func=RegisterView.as_view('register'))
app.add_url_rule('/login', view_func=LoginView.as_view('login'))
app.add_url_rule('/logout', view_func=LogoutView.as_view('logout'))