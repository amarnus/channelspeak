from google.appengine.api import channel
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp import util
from google.appengine.api import users
from google.appengine.api.users import User
from google.appengine.ext.webapp import template
from django.utils import simplejson as json
import time
import cgi

class Message(db.Model):
	author = db.UserProperty()
	message = db.StringProperty()
	roomkey = db.StringProperty()
	timestamp = db.DateTimeProperty(auto_now_add=True)

class Room(db.Model):
	name = db.StringProperty()
	owner = db.UserProperty()
	members = db.ListProperty(User)
	
class NotFoundHandler(webapp.RequestHandler):
	def get(self):
		self.error(404)
		
class ChatRelayHandler(webapp.RequestHandler):
	def post(self):
		respond = self.response.out.write
		roomkey = self.request.get('room')
		message = cgi.escape(self.request.get('message'))
		if not roomkey:
			return self.error(404)
		room = Room.get_by_key_name(roomkey)
		if not room:
			return self.error(404)
		user = users.get_current_user()
		if user not in room.members:
			return self.error(404)
		Message(author=user, message=message, roomkey=roomkey).put()
		for member in room.members:
			value = {
				'type': 'message',
				'author': user.nickname().lower(),
				'message': message
			}
			if user.user_id() != member.user_id():
				channel.send_message(member.user_id() + room.name, json.dumps(value))
		respond('Message relayed by server')
				
class ChannelHandler(webapp.RequestHandler):
	def get(self):
		respond = self.response.out.write
		roomkey = self.request.get('room')
		if not roomkey:
			return self.redirect('/')
		room = Room.get_by_key_name(roomkey)
		if not room:
			return self.redirect('/')
		user = users.get_current_user()
		if user not in room.members: 
			others = room.members
			room.members.append(user)
			room.put()
			value = {
				'type': 'arrived',
				'author': user.nickname().lower(),
				'time': time.time()
			}
			for peer in others:
				try:
					channel.send_message(peer.user_id() + room.name, value)
				except Exception, e:
					pass # Silently forget if a message cannot be sent to a client because he is not currently online
		messages = db.GqlQuery('SELECT * FROM Message WHERE roomkey=:1 ORDER BY timestamp ASC', roomkey).fetch(1000)
		variables = {
			'name': room.name,
			'roomKey': roomkey,
			'owner': room.owner.nickname().lower(),
			'members': map(lambda x: x.nickname().lower() if x else '', room.members),
			'token': channel.create_channel(user.user_id() + room.name),
			'messages': map(lambda x: { 'author': x.author.nickname().lower(), 'text': x.message } if x else '', messages),
			'logoutUrl': users.create_logout_url('/')
		}
		respond(template.render('templates/room.html', variables))
		
class CreateHandler(webapp.RequestHandler):
	def get(self):
		channel_name = self.request.get('name')
		if not channel_name:
			return self.redirect('/')
		user = users.get_current_user()
		channel_id = user.user_id() + str('/' + channel_name.replace(' ', '-'));
		Room(key_name=channel_id, owner=user, name=channel_name, members=[user]).put()
		self.redirect('/groupChat?room=' + channel_id)

class MainHandler(webapp.RequestHandler):
	def get(self):
		self.response.out.write(open('templates/index.html', 'r').read())
		
def main():
	app = webapp.WSGIApplication([
		('/', MainHandler),
		('/createChannel', CreateHandler),
		('/groupChat', ChannelHandler),
		('/chatRelay', ChatRelayHandler),
		('/.*', NotFoundHandler)
	], debug=True)
	util.run_wsgi_app(app)
	
main()