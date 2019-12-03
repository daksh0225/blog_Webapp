import webapp2
import os
import jinja2 
from users import *
from google.appengine.ext import db
import json

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),autoescape=True)	

SECRET="imsosecret"

def render_str(template, **params):
	t = jinja_env.get_template(template)
	return t.render(params)

def escape_html(s):
	return cgi.escape(s,quote=True)

def check_pass(p,h):
	return (make_secure(p))==h
def hash_str(s):
	return hmac.new(SECRET,s).hexdigest()
def make_secure(s):
	return "%s" % (hash_str(s))
def check_secure(h):
	val=h.split('|')
	if val[1]==make_secure(val[0]):
		return val[0]
		
class Handler(webapp2.RequestHandler):
	def write(self,*a,**kw):
		self.response.out.write(*a,**kw)

	def render_str(slef, template, **params):
		t = jinja_env.get_template(template)
		return t.render(params)

	def render(self, template, **kw):
		self.write(self.render_str(template, **kw))

	def inituser(self):
		self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')

	def login(self,user):
		self.response.headers.add_header('Set-Cookie', 'user_id=%s|%s; Path=/'%(str(user),str(make_secure(escape_html(user)))))

	def check_url(self,*a,**kw):
		print(self.request.url)
		if self.request.url.endswith('.json'):
			# print('why')
			self.format='json'			
		else:
			self.format='html'

	def render_json(self,d):
		json_txt=json.dumps(d)
		self.response.headers['Content-Type']='application/json; charset=UTF-8'
		self.write(json_txt)

class Art(db.Model):
	subject=db.StringProperty(required=True)
	content=db.TextProperty(required=True)
	created=db.DateTimeProperty(auto_now_add=True)
	last_modified = db.DateTimeProperty(auto_now = True)


	def render(self):
		self._render_text = self.content.replace('\n', '<br>')
		return render_str("post.html", p = self)

	def as_dict(self):
		time_fmt='%c'
		d={'subject':self.subject,
			'content':self.content,
			'created':self.created.strftime(time_fmt),
			'last_modified':self.last_modified.strftime(time_fmt)}
		return d

def blog_key(name='default'):
	return db.Key.from_path('blogs', name)

class MainPage(Handler):
	def get(self):
		arts=db.GqlQuery("Select * from Art order by created desc limit 10")
		self.check_url()
		if self.format=='html':
			self.render("front.html", arts=arts,s="")
		else:
			self.render_json([p.as_dict() for p in arts])

class NewPost(Handler):
	def render_form(self, subject="", content="", error=""):
		self.render("form.html",subject=subject, content=content, error=error)

	def get(self):
		self.render_form()

	def post(self):
		subject=self.request.get("subject")
		content=self.request.get("content")

		if subject and content:
			a=Art(parent=User,subject=subject, content=content)
			a.put()
			self.redirect('/%s' % str(a.key().id()))

		else:
			error="we need both a subject and some content"
			self.render_form(subject,content,error)

class PostPage(Handler):
	def get(self, post_id):
		key=db.Key.from_path('Art', int(post_id), parent=blog_key())
		post=db.get(key)
		self.check_url()
		# print(post)
		if not post:
			self.error(404)
			return
		if self.format=='html':
			self.render("permalink.html", post=post)
		else:
			print("hello")
			self.render_json(post.as_dict())

