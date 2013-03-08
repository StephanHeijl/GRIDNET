from django.db import models
from django.contrib.auth.models import *

# Application info
class Application(models.Model):
	name = models.CharField(max_length=64)
	version = models.FloatField()
	header = models.CharField(max_length=128)
	author = models.CharField(max_length=64)
	license = models.TextField(null=True)
	
	def __unicode__(self):
		return self.header

# Interface parts
class Action(models.Model):
	name = models.CharField(max_length=32)
	slug = models.SlugField()
	action = models.CharField(max_length=32)
	parameters = models.CharField(max_length=128,blank=True,null=True)
	description = models.TextField(blank=True,null=True)

	def __unicode__(self):
		return self.name
	
class TileScreen(models.Model):
	name = models.CharField(max_length=32)
	slug = models.SlugField()
	
	def __unicode__(self):
		return self.name

class Cont(models.Model):
	title = models.CharField(max_length=64)
	contents = models.TextField()
	slug = models.SlugField()

	def __unicode__(self):
		return self.title

class Tile(models.Model):
	title = models.CharField(max_length=64)
	tilescreen = models.ForeignKey(TileScreen)
	linked_screen = models.ForeignKey(TileScreen, blank=True, null=True, related_name="tile_linked_screen")
	linked_cont = models.ForeignKey(Cont, blank=True, null=True, related_name="tile_linked_cont")
	linked_action = models.ForeignKey(Action, blank=True, null=True)
	order = models.IntegerField()

	def __unicode__(self):
		name = [self.title]
		if self.linked_screen:
			name.append("Linked to screen: "+self.linked_screen.name)
		if self.linked_cont:
			name.append("Linked to cont: "+self.linked_cont.title)
		
		return ', '.join(name)

# Needed for GridJob Functionality

GRIDSTATE_CHOICES = (
	("Online","Online - this grid has recently reported itself."),
	("Stale","Stale - it has been some time since this grid has reported in."),
	("Offline","Offline - this grid is disconnected from GRIDNET."),
	("Gone","This grid doesn't exist anymore.")
)

class Grid(models.Model):
	name = models.CharField(max_length="64", default="NewGrid")
	location = models.CharField(max_length="64", default="Netherlands")
	IP = models.CharField(max_length="15", default="0.0.0.0")
	state = models.CharField(max_length=7,
                            choices=GRIDSTATE_CHOICES,
                            default="Offline")
	last_update = models.DateTimeField(blank=True)
	
	def __unicode__(self):
		return "%s at %s (last online at %s) " % (self.name, self.location, self.last_update.strftime("%d/%m/%y %H:%M"))
	
class Node(models.Model):
	grid = models.ForeignKey(Grid, null=True)
	name = models.CharField(max_length="32", default="NewNode")
	connected = models.BooleanField(default="")
	benchScore = models.IntegerField()
	
	def __unicode__(self):
		return "%s at %s" % (self.name , self.grid.name)

class Slot(models.Model):
	node = models.ForeignKey(Node, null=True)
	slot_n = models.IntegerField(null=True)
	state = models.CharField(max_length=20, null=True)

class Task(models.Model):
	taskname = models.CharField(max_length=32)
	command = models.CharField(max_length=32)
	default_parameters = models.TextField()
	permission_level_required = models.CharField(max_length=1)

	def __unicode__(self):
		return "%s" % (self.taskname)
		
class NodeTask(models.Model):
	node = models.ForeignKey(Node)
	task = models.ForeignKey(Task)
	path = models.CharField(max_length="256", null=True)
	
	def __unicode__(self):
		return "%s is equipped with %s" % (self.node.name, self.task.taskname)

class Job(models.Model):
	owner = models.ForeignKey(User, null=True)
	grid = models.ForeignKey(Grid, null=True)
	node = models.ForeignKey(Node, null=True)
	condor_id = models.IntegerField(null=True, blank=True)
	task = models.ForeignKey(Task, null=True)
	parameters = models.TextField(blank=True)
	file = models.FileField(upload_to="JobFiles/", null=True, blank=True)
	status = models.CharField(max_length=20, default='Queued', editable=False)
	created_on = models.DateTimeField(auto_now_add=True, blank=True)
	started_on = models.DateTimeField(editable=False, null=True, blank=True)
	ended_on = models.DateTimeField(editable=False, null=True, blank=True)
	eta = models.DateTimeField(editable=False, null=True, blank=True)
	description = models.TextField(blank=True)

	def __unicode__(self):
		return "Job by %s, created on %s" % (self.owner,self.created_on)

# Users/Finances
SUBSCRIPTION_CHOICES = (
	("Free","Free account"),
	("Trial","Trial account"),
	("Student","Student license"),
	("Stretch","Stretch license"),
	("Year_t1","Year_tier1"),
	("Year_t3","Year_tier3"),
	("Year_t2","Year_tier2"),
)
class Subscription(models.Model):
	type = models.CharField(max_length=7,
                            choices=SUBSCRIPTION_CHOICES,
                            default="Free")
	monthly_allowance = models.IntegerField(default=0)
	
	def __unicode__(self):
		return self.type

class SubscribedUser(models.Model): 
	user = models.OneToOneField(User)
	subscription = models.ForeignKey(Subscription,db_index=True)
	credits = models.IntegerField(default=0)
	
	def __unicode__(self):
		return "%s with a %s subscription." % (self.user.username,self.subscription.type)
