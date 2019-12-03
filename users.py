import webapp2
import os
import jinja2 
import urllib
import hashlib
import hmac
import re
import cgi
import datetime
from string import maketrans
from google.appengine.ext import db
from google.appengine.ext.db import polymodel
from blog import *
import json

f=0
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),autoescape=True)		

USER_RE=re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASSWORD_RE=re.compile(r"^.{3,20}$")
EMAIL_RE=re.compile(r"^[\S]+@[\S]+.[\S]+$")

def check_cookie(self):
	username=self.request.cookies.get('user_id')
	if username:
		user=username.split("|")
		un=user[0]
		user[0]=make_secure(user[0])
		if user[0]==user[1]:
			ucnt=User.all()
			ucnt.filter("username =",str(un))
			for u in ucnt:
				if u.username:
					return u.username
				else:
					return 
				break
		else:
			return 
	else:
		return 


def valid_username(username):
	return USER_RE.match(username)

def valid_password(password):
	return PASSWORD_RE.match(password)

def valid_email(email):
	return EMAIL_RE.match(email)

def valid_verify(verify,password):
	return verify==password


def users_key(group = 'default'):
    return db.Key.from_path('users', group)

class User(db.Model):
	username=db.StringProperty(required=True)
	pass_hash=db.StringProperty(required=True)
	email=db.EmailProperty()
	created=db.DateTimeProperty(auto_now_add=True)
	last_modified = db.DateTimeProperty(auto_now = True)

class user_signup(Handler):
	def write_form(self,username="",email="",error0="",error1="",error2="",error3="",error4=""):
		self.render("user_signup.html", username=username,email=email, error0=error0, error1=error1, error2=error2, error3=error3,error4=error4)

	def get(self):
		self.write_form()

	def post(self):
		f=0
		uname=self.request.get('username')
		pswrd=self.request.get('password')
		ver=self.request.get('verify')
		em=self.request.get('email')
		username=valid_username(escape_html(uname))
		password=valid_password(escape_html(pswrd))
		verify=valid_verify(escape_html(ver),escape_html(pswrd))
		email=valid_email(escape_html(em))
		e1=""
		e2=""
		e3=""
		e4=""
		e0=""		
		if not username:
			e1="Enter a valid username"
		if not password:
			e2="Enter a valid password"
		if not verify:
			e3="Enter a valid verify"
		if not email:
			e4="Enter a valid email"
		if not (username and password and verify and email):
			self.write_form(uname,em,e0,e1,e2,e3,e4)
		else:
			ucount=db.GqlQuery("Select * from User where username=:uu",uu=str(uname))
			for u in ucount:
				if u.username:
					e0="User already exists"
					f=1
				break
			if f==1:
				self.write_form(uname,em,e0,e1,e2,e3,e4)
			else:
				a=User(username=uname, pass_hash=make_secure(str(pswrd)),parent=users_key())
				a.put()
				a.put()
				print(a.parent())
				self.login(uname)
				self.redirect('/welcome')

class Login(Handler):
	def get(self):
		user=self.request.cookies.get('user_id')
		if user:
			self.redirect('/welcome')
		else:
			self.render("login.html",username="",password="",err="")
			self.inituser()

	def post(self):
		username=self.request.get('username')
		password=self.request.get('password')
		print username
		err=""
		q=db.GqlQuery("Select * from User where username = :uu", uu=str(username))
		print q
		for r in q:
			if r.username:
				print r.username
				p=check_pass(password,r.pass_hash)
				if p:
					print "corect"
					self.login(username)
					self.redirect('/welcome')
				else:
					err="Invalid Credentials"
					self.render("login.html",username=username,err=err)
			else:
				err="Invalid Credentials"
				self.render("login.html",username=username,err=err)

class Logout(Handler):
	def get(self):
		self.inituser()
		self.redirect('/signup')

class ThanksHandler(Handler):
	def get(self):
		p=check_cookie(self)
		if p:
			self.render("signedup.html", user=p)
		else:
			self.redirect('/signup')

app = webapp2.WSGIApplication([('/?(?:.json)?', MainPage),
	('/signup',user_signup),
	('/welcome',ThanksHandler),
	('/login',Login),
	('/logout',Logout),	
	('/newpost', NewPost),
	('/([0-9]+)(?:.json)?',PostPage)], debug=True)
