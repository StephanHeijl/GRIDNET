# Create your views here.
from django.http import HttpResponse
from GRIDNET.models import *
from django.shortcuts import redirect
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q

from GRIDNET.PyCondor import PyCondor

from pprint import pformat as pf
import datetime, tarfile, time, base64

# Relative function
import os, json,re
def rel(*x):
    return os.path.join(os.path.abspath(os.path.dirname(__file__)),*x)
	
# Import smtplib for the actual sending function
import smtplib
from email.mime.text import MIMEText

# This handles jobs that are submitted with the wizard on GRIDNET
def addJobWizardDo(request):
	if not request.user.is_authenticated():
		redirect("index.htm")

	if request.method == "POST":
		req = request.POST
	elif request.method == "GET":
		try:
			req = json.loads(request.GET['request'])
		except ValueError as err:
			return HttpResponse( json.dumps(
				{'Response':'Error: Error in JSON string: %s' % err.args }
			))
		
	try:
		owner = request.user
		try:
			if int(req['Task']) > 0:
				task = Task.objects.get(id=req['Task'])
		except:
			return HttpResponse( json.dumps( {'Response':'Error: No valid task selected'} ) )
			
		try:
			if int(req['Grid']) > 0:
				grid = Grid.objects.get(id=req['Grid'])
			else:
				grid = None
		except:
			return HttpResponse( json.dumps( {'Response':'Error: No valid grid selected'} ) )
			
		try:
			if int(req['Node']) > 0:
				node = Node.objects.get(id=req['Node'])
			else:
				node = None
		except:
			return HttpResponse( json.dumps( {'Response':'Error: No valid node selected'} ) )
		
		split = int(req['Split'])
		
		job = Job(owner=owner,task=task,parameters=req['Parameters'],description=req['Description'],grid=grid,node=node)
		job.save()
		job_id = job.id

	except KeyError as err:
		return HttpResponse( json.dumps(
			{'Response':'Error: not all required keys in JSON string. "%s" was not found.' % err.args }
		))
	
	fname = "Jobs/%s/%s"
	os.makedirs(rel("Jobs/%s" % job.id))

	if 'File' in request.FILES:
		for f in request.FILES.values():
			with open(rel(fname % (job_id, ""))+f.name,"w") as destination:
				for chunk in f.chunks():
					destination.write(chunk)
					
		job.id = job_id
		job.save()
	
	requirements = ""	
	
	jobfile = PyCondor().makeJobFile(	task.taskname,
										job.owner,
										job.description,
										task.command,
										job.parameters,
										job_id,
										requirements=requirements)
										
	with open(rel(fname % (job_id, "CondorFile.job")),"w+") as jf:
		jf.write(jobfile)
	job.condor_id = int(0)
	job.save()
	
	tarname = "Jobs/%s/job_%s_files.tar.gz" % ( job.id, job.id )
	tf = tarfile.open(rel(tarname), "w:gz")
	job.file = rel(tarname)
	job.save()
	
	
	os.chdir(rel("Jobs/%s/" % job.id))
	for file in os.listdir("."):
		tf.add(file)
	tf.close()
	
	return HttpResponse(json.dumps({'Response':'OK','JobFile':jobfile, 'Condor_ID':0, 'AllFiles':tarname}))
	
# This handles jobs that are submitted with a custom submit file
def addJobManualDo(request):
	if not request.user.is_authenticated():
		redirect("index.htm")

	if request.method == "POST":
		req = request.POST
	elif request.method == "GET":
		try:
			req = json.loads(request.GET['request'])
		except ValueError as err:
			return HttpResponse( json.dumps(
				{'Response':'Error: Error in JSON string: %s' % err.args }
			))
	try:
		owner = request.user
		task = Task.objects.get(taskname="Custom")
			
		try:
			if int(req['Grid']) > 0:
				grid = Grid.objects.get(id=req['Grid'])
			else:
				grid = None
		except:
			return HttpResponse( json.dumps( {'Response':'Error: No valid grid selected'} ) )
		
		job = Job(owner=owner,task=task,parameters="",description="",grid=grid,node=None)
		job.save()
		job_id = job.id

	except KeyError as err:
		return HttpResponse( json.dumps(
			{'Response':'Error: not all required keys in JSON string. "%s" was not found.' % err.args }
		))
	
	fname = "Jobs/%s/%s"
	os.makedirs(rel("Jobs/%s" % job.id))

	if 'File' in request.FILES:
		for f in request.FILES.values():
			with open(rel(fname % (job_id, ""))+f.name,"w") as destination:
				for chunk in f.chunks():
					destination.write(chunk)
					
		job.id = job_id
		job.save()
	
	requirements = ""	
	
	jobfile = req['submit']
	with open(rel(fname % (job_id, "CondorFile.job")),"w+") as jf:
		jf.write(jobfile)

	job.condor_id = 0
	job.save()
	
	tarname = "Jobs/%s/job_%s_files.tar.gz" % ( job.id, job.id )
	tf = tarfile.open(rel(tarname), "w:gz")
	job.file = rel(tarname)
	job.save()
	
	os.chdir(rel("Jobs/%s/" % job.id))
	for file in os.listdir("."):
		tf.add(file)
	tf.close()
	
	return HttpResponse(json.dumps({'Response':'OK','JobFile':jobfile, 'Condor_ID':0, 'AllFiles':tarname}))

def checkPassword(username, pw):
	requirements = []
	
	if pw == username:
		requirements.append("Cannot be the same as your username.")
		return requirements
	
	if len(pw) < 6:
		requirements.append("Needs to be longer then 6 characters")
	
	# Count capital letters
	if len(re.findall("[A-Z]" ,pw)) < 1:
		requirements.append("Needs one or more capital letters")
	
	# Get all special characters
	special = len(pw) - len(re.findall("\w", pw))
		
	if special < 1:
		requirements.append("Needs one or more special characters")
	
	return requirements

def changePasswordDo(request):
	if not request.user.is_authenticated():
		redirect("index.htm")

	if request.method == "POST":
		req = request.POST
	elif request.method == "GET":
		return HttpResponse( json.dumps(
			{'Response':'Error: Password cannot be changed like this.' }
		))
	
	original_pass = req['previous']
	if req['newOne'] == req['newTwo']:
		new_password = req['newOne']
	else:
		return HttpResponse( json.dumps(
			{'Response':'Error: The new passwords do not match.' }
		))
		
	check = checkPassword(request.user.username, new_password)
	
	if len(check) > 0:
		return HttpResponse( json.dumps(
			{'Response':'Error: Your new password does not follow the following requirements:\n<ul><li>-%s</li></ul>' % "</li><li>-".join(['%s' % r for r in check ])}
		))
		
	if len(new_password.strip()) == 0:
		return HttpResponse( json.dumps(
			{'Response':'Error: You need to select a new password. An empty string won\'t do.' }
		))
	
	valid_pass = request.user.check_password(original_pass)
	if valid_pass:
		request.user.set_password(new_password)
		request.user.save()
		return HttpResponse(json.dumps({'Response':'OK'}))
	else:
		return HttpResponse( json.dumps(
			{'Response':'Error: Your given original password does not match the one we have on record.' }
		))
		
def changeNodeTaskDo(request):
	if request.method == "POST":
		req = request.POST
	elif request.method == "GET":
		return HttpResponse( json.dumps(
			{'Response':'Error: Node tasks cannot be changed like this.' }
		))
	
	try:
		node = request.POST['node']
	except:
		return HttpResponse( json.dumps(
			{'Response':'Error: No node given' }
		))
	
	tasks = []
	paths = {}
	for key,value in request.POST.items():
		try:
			type,task = key.split("_")
		except:
			continue
		
		if type == "path":
			paths[int(task)] = value
			
		if type == "task":
			tasks.append(int(task))
	
	available = NodeTask.objects.filter(node=node)

	alreadyChecked  = []
	for task in available:
		if task.id not in tasks:
			task.delete()
		else:
			alreadyChecked.append(task.id)
				
	for task in tasks:
		if task in alreadyChecked:
			continue
			
		if paths[task] == "":
			path = Task.objects.filter(id=task)[0].command
		else:
			path = paths[task]
		
		nt = NodeTask(node=Node.objects.filter(id=node)[0],task=Task.objects.filter(id=task)[0],path=path)
		nt.save()
		
	return HttpResponse( json.dumps(
			{'Response':'OK' }
		))
	
def convertToB64(request):
	encf = ""
	if 'File' in request.FILES:
		f = request.FILES['File'].read()
		
		try:
			encf = base64.b64encode(f)
			response = "OK"
		except Exception as e:
			response = e
				
	else:
		response = "No file included"
		
	return HttpResponse( json.dumps(
			{'Response':response, "encoded":encf }
		))
	

def jobs(request,type):
	jobTypes = ['Queued','Submitted','Working','Completed','Failed']
	limit = request.GET['limit'] if 'limit' in request.GET else -1
	
	thisGrid = Grid.objects.filter(IP=request.META['REMOTE_ADDR'])
	
	if type in jobTypes:
		jobs = Job.objects.filter(Q(status=type), Q(grid=thisGrid) | Q(grid=None))
		if limit >= 0:
			jobs = jobs[:limit]
		
		theJobs = {}
		for job in jobs:
			theJobs[job.id] = { 'Condor_ID':job.condor_id,
								'Owner':job.owner.username,
								'Task':job.task.taskname,
								'Files':"http://www.cytosine.nl/GRIDNET/jobs/Files?id=%s" % job.id}
		
			job.status = "Submitted"
			job.started_on = datetime.datetime.now()
			job.save()
			
		return HttpResponse(json.dumps(theJobs))
	elif type == "Files":
		job_id = request.GET['id']
		related_job = Job.objects.filter(id=job_id)
		
		if len(related_job) > 0:
			os.chdir(rel("Jobs/%s/" % related_job[0].id))
			
			f = open("job_%s_files.tar.gz" % related_job[0].id ).read()
		else:
			return HttpResponse(json.dumps("Not a valid request."))
		
		return HttpResponse(f, content_type="application/x-tar")
	
	elif type == "Results":
		job_id = request.GET['id']
		related_job = Job.objects.filter(id=job_id)
		
		if len(related_job) > 0:
			os.chdir(rel("Jobs/%s/" % related_job[0].id))
			
			f = open("job_%s_results.tar.gz" % related_job[0].id ).read()
		else:
			return HttpResponse(json.dumps("Not a valid request."))
		
		response = HttpResponse(f, content_type = "application/x-tar" )
		response['Content-Disposition'] = "attachment; filename=results_for_job_%s.tar.gz" % related_job[0].id
		response['Content-Length'] = len(f)
		return response	
	elif type == "Remove":
		if not request.user.is_authenticated():
			redirect("index.htm")
		job_id = request.GET['id']
		Job.objects.filter(id=job_id).delete()
		return HttpResponse(json.dumps("Job %s removed." % job_id))
		
	elif type == "Refresh":
		if not request.user.is_authenticated():
			redirect("index.htm")
		job_id = request.GET['id']
		job = Job.objects.filter(id=job_id)[0]
		job.status = "Queued"
		job.save()
		return HttpResponse(json.dumps("Job %s refreshed." % job_id))
		
	else:
		return HttpResponse(json.dumps("Not a valid request."))

def getTasks(request):
	node = request.GET.get("node", -1)
	if node >= 0:
		t = {}
		tasks = NodeTask.objects.filter(node=node)
		for task in tasks:
			t[task.task.id] = task.path
	else:
		t = []
		tasks = Task.objects.all()
		for task in tasks:
			t.append([task.id, task.taskname,task.command])
		
	return HttpResponse(json.dumps(t))
		
def getDropdownTasks(request):
	tasks = Task.objects.all()
	t = []
	for task in tasks:
		t.append("<option value='%s'>%s</option>" % (task.id, task.taskname))
	
	return HttpResponse("\n".join(t))
	
def getDropdownGrids(request):
	grids = Grid.objects.all()
	g = ["<option value='0'>Any</option>"]
	for grid in grids:
		g.append("<option value='%s'>%s</option>" % (grid.id, grid.name))
	
	return HttpResponse("\n".join(g))

def getDropdownNodes(request):
	try:
		task = request.GET.get("task",False)
		int(task)
	except ValueError:
		task = False;
	try:
		grid = request.GET.get("grid",False)
		int(grid)
	except ValueError:
		grid = False;
	
	try:
		online = int(request.GET.get("online", False))
	except ValueError:
		online = False;	
	
	
	if(not grid and not task ):
		nodes = Node.objects.all()
	elif(grid and not task):
		nodes = Node.objects.filter(grid=grid)
	elif(task and not grid) or grid == "0":
		# Check all the nodes that are equipped for this task
		nt = NodeTask.objects.filter(task=task)		
		nodes_with_task = [n.node.id for n in nt]
		nodes = Node.objects.filter(id__in=nodes_with_task)
	else:
		nt = NodeTask.objects.filter(task=task)		
		nodes_with_task = [n.node.id for n in nt]
		nodes = Node.objects.filter(grid=grid,id__in=nodes_with_task)
	
	if online:
		conNodes = nodes.filter(connected=True)
		nodes = filter(lambda n: n.grid.state == "Online", conNodes)
	
	if len(nodes) > 0:
		n = ["<option value='0'>Any</option>"]
		for node in nodes:
			n.append("<option value='%s'>%s</option>" % (node.id, node.name))
	else:
		n = ["<option disabled=disabled>No nodes satisfy your requirements.</option>"]
	
	return HttpResponse("\n".join(n))

def saveStatus(ip,status):
	gridWithThisIp = Grid.objects.filter(IP=ip)
	
	allOtherGrids = Grid.objects.all().exclude(IP=ip)
	# Check for the staleness of all the other grids
	for grid in allOtherGrids:
		if grid.last_update + datetime.timedelta(minutes=30) < datetime.datetime.now():
			if grid.state not in ["Gone", "Error"]:
				grid.state = "Offline"	
		elif grid.last_update + datetime.timedelta(minutes=10) < datetime.datetime.now():
			grid.state = "Stale"
		else:
			grid.state = "Online"
		grid.save()
	
	if len(	gridWithThisIp ) == 0:
		cgrid = Grid(IP=ip,location="New Grid",last_update=datetime.datetime.now(),state="Online")
		cgrid.save()
	else:
		cgrid = gridWithThisIp[0]
	
	currentNodes = []
	allNodes = Node.objects.filter(grid=cgrid).update(connected=False) # Set all nodes to offline, only re-set them if we know they are online
	for key, value in json.loads(status).items(): # Load the keys and values from PyCondor's JSON output
		if key == "Totals":
			continue # Totals are currently not recorded
		elif key == "@":
			cgrid.state="Online"
			cgrid.last_update = datetime.datetime.now() # @ contains the update time
			cgrid.save()
		elif "@" in key: # This just leaves the "real" node names
			namesplit = key.split("@")
			
			nodename = namesplit[1] # Remove the @ in the node name ( usually is slotN@nodename )
			slot_n = int(namesplit[0].split("slot")[-1])
			
			thisNode = Node.objects.filter(name=nodename,grid=cgrid) # Load the node with this name
			
			if len(thisNode) == 0: # If the node does not exist, add it.
				node = Node(grid=cgrid, name=nodename, connected=True, benchScore=1)
				node.save()
			else:
				node = thisNode[0]
				node.connected = True
				node.save()
			
			if nodename not in currentNodes:
				currentNodes.append(nodename)
				node.connected=True
				node.save()
				
			slot = Slot.objects.filter(node=node, slot_n=slot_n)
			if len(slot) == 0:
				thisSlot = Slot(node=node, slot_n=slot_n, state=dict(value)["State"])
			else:
				thisSlot = slot[0]
				thisSlot.state = dict(value)["State"]
			
			thisSlot.save()		
		else:
			pass


def currentState(request):
	reported = {"Status":False,"Queue":False,"Batch":False,"Completed":False}
	if "status" in request.POST:
		with open(rel("status.json"),"w") as state:
			state.write(request.POST['status'])
		
		saveStatus(request.META['REMOTE_ADDR'],request.POST['status'])
		reported["Status"] = True
		
	if "queue" in request.POST:
		with open(rel("queue.json"),"w") as queue:
			queue.write(request.POST['queue'])
			
		q = json.loads(request.POST['queue'])
		for system in q:
			if system == "@":
				continue
			
			processCounts = {}
			
			for job in q[system]:
				jobId, pId = str(dict(job)['ID']).split(".")
				
				if int(jobId) in processCounts:
					processCounts[int(jobId)] += 1
				else:
					processCounts[int(jobId)] = 1
			
			for process, count in processCounts.items():
				j = Job.objects.filter(condor_id=int(process))
				if len(j) == 0:
					continue
				j[0].processes_running = count
				j[0].save()	
		
		reported["Queue"] = processCounts
		
	if "batch" in request.POST:		
		for k,v in json.loads(request.POST['batch']).items():
			j = Job.objects.filter(id=k)[0]
			j.status = "Working"			
			j.condor_id = v
			j.save()
		
		reported["Batch"] = True
		
	if "completed" in request.POST:
		with open(rel("completed.json"),"w") as comp:
			comp.write(request.POST['completed'])
	
	return HttpResponse(json.dumps(reported))
		
def distress(request):
	ip = request.META['REMOTE_ADDR'];
	gridWithThisIp = Grid.objects.filter(IP=ip)	
	
	if len(gridWithThisIp) < 0:
		return HttpResponse(json.dumps({"Response":"denied"}))
	else:
		cgrid = gridWithThisIp[0]
	
	if cgrid.state != "Error":
		cgrid.state = "Error"
		cgrid.save()
	else:
		return HttpResponse(json.dumps({"Response":"denied - known"}))
	
	message = request.POST.get("Error", "General error. Please check out the grid logs.")
	
	
	s = smtplib.SMTP('localhost')
	sendTo = []

	for user in User.objects.all():
		if user.is_staff:
			sendTo.append(user.email)
	
	msg = "Subject: %s\r\nFrom: %s\r\nTo: %s\r\n\r\n" % (	'Error occured on grid "%s"' % cgrid,
															"root@cytosine.nl", 
															', '.join(sendTo))
															
	msg += "\r\n" + message
	
	allLogs = os.listdir(rel("Logs"))
	cgridLogs = filter(lambda l: "GRID_"+str(cgrid.id) in l, allLogs)
	
	for log in cgridLogs:
		logfile = open(rel(os.path.join("Logs", log)), "r")
		msg += "\r\n --- \r\n" + logfile.read()
		logfile.close()
	
	s.sendmail("root@cytosine.nl", sendTo, msg)
	s.quit()
	
	return HttpResponse(json.dumps({"Response":"OK"}))
	
def reportMRHLogs(request):
	ip = request.META['REMOTE_ADDR'];
	gridWithThisIp = Grid.objects.filter(IP=ip)	
	
	if len(gridWithThisIp) < 0:
		return HttpResponse(json.dumps({"Response":"denied"}))
	else:
		cgrid = gridWithThisIp[0]
		
	logs = request.POST
	
	for logname, log in logs.items():
		try:
			lognameSplit = logname.split(".")
			logFileName  = '.'.join(['.'.join(lognameSplit[:-1]), "GRID_"+str(cgrid.id), lognameSplit[-1]])
			f = open(rel(os.path.join("Logs", logFileName)), "w")
			f.write(log)
			f.close()
		except Exception as e:
			return HttpResponse(json.dumps({"Response":"Error: " + str(e) }))
		
	return HttpResponse(json.dumps({"Response":"OK", "Logs uploaded":logs.keys(), "Amount of logs": len(logs)}))
	
		
def results(request,job):
	success = []
	error = []
	for job,f in request.FILES.items():
		try:
			resultsname = rel("Jobs/%s/%s" % (job, f.name))
			with open(resultsname, 'wb') as destination:
				for chunk in f.chunks():
				    destination.write(chunk)
				destination.close()
				
			cjob = Job.objects.filter(id=int(job))[0]
			if cjob.status == "Completed":
				return HttpResponse(json.dumps({"Response":"Already completed"}))
				
			cjob.status = "Completed"
			cjop.processes_running = 0
			cjob.ended_on = datetime.datetime.now()
			cjob.save()			
			
			owner = cjob.owner
			
			if len(owner.email) > 0:
				s = smtplib.SMTP('localhost')
				sendTo = []
				
				msg = "Subject: %s\r\nFrom: %s\r\nTo: %s\r\n\r\n" % (	'Your job with id %s was completed!' % cjob.id,
																		"root@cytosine.nl", 
																		owner.email)
																		
				delta = cjob.ended_on - cjob.started_on
				
				days = delta.days
				hours = int( delta.seconds / 3600 )
				minutes = ((delta.seconds % 3600) / 60)
				seconds = delta.seconds % 3600 % 60
																		
				msg += "\r\nYour %s job has finished. It was completed on %s. \r\n" % (cjob.task, cjob.ended_on.strftime("%d/%m/%y %H:%M"))
				msg += "In total it has taken %s days, %s hours, %s minutes and %s seconds" % (days,hours,minutes,seconds)
				msg += "\r\nPlease visit http://www.cytosine.nl/GRIDNET/ to download the results."
				msg += "\r\n\r\nThis message was automatically generated. Please do not reply to this email."
				msg += "\r\nIf you don't want to receive these messages anymore, remove your email adress from your GRIDNET profile."
				
				s.sendmail("root@cytosine.nl", owner.email, msg)
				s.quit()			
			
			success.append(job)
		except Exception as e:
			error.append((job,str(e)))		
		        
	return HttpResponse(json.dumps({"success":success,"error":dict(error)}))
		

def files(request,file):
	contt = {
		"css"		: "text/css",
		"js"		: "text/javascript",
		"png"		: "image/png",
		"jpg"		: "image/jpeg",
		"ttf"		: "application/octet-stream"
	}
	
	f = open(rel("ViewFiles/%s" % file))
	response = HttpResponse(f, content_type=contt[file.split(".")[-1]])
	if file.split(".")[-1] not in ['css','js']:
		response['Expires'] = "Wed, 01 Jan %s 16:00:00 GMT" % datetime.datetime.now().year # Expires over een jaar, alleen files.
		response['Cache-Control'] = "max-age=31536000" # Cache maximaal een jaar
		
	return response

def getUserData(user):
	jobsn = Job.objects.filter(owner=user).exclude(status="Completed")
	subscribeduser = SubscribedUser.objects.filter(user=user)
	
	return {'name': user.username, 
			'credits' : subscribeduser[0].credits if subscribeduser.count() > 0 else 0,
			'jobsn' : jobsn.count(),
			}
	
def index(request):
	# Do some user authentication magic
	un, pw = request.POST.get('Username',''), request.POST.get('Password','')
	user = authenticate(username=un, password=pw)
	
	header = Application.objects.filter(name="GRIDNET")[0]
	
	if request.user.is_authenticated():
		userdata = getUserData(request.user)
		html = open(rel("ViewFiles/index.htm"),"r").read().format(	header,
																	"admin" if request.user.is_staff else "user",
																	userdata['name'],
																	userdata['credits'],
																	userdata['jobsn'])
	elif user and user.is_active:
		login(request,user)
		userdata = getUserData(user)
		html = open(rel("ViewFiles/index.htm"),"r").read().format(	header,
																	"admin" if request.user.is_staff else "user",
																	userdata['name'],
																	userdata['credits'],
																	userdata['jobsn'])
	else:
		if "login_attempt" in request.GET:
			html = open(rel("ViewFiles/login.htm"),"r").read().format(header,"block")
		else:
			html = open(rel("ViewFiles/login.htm"),"r").read().format(header,"none")
		
	return HttpResponse(html)
	
def tour(request):
	html = open(rel("ViewFiles/tour.htm"),"r").read()
	return HttpResponse(html)

def logout_page(request):
	logout(request)
	return redirect("index.htm")

def getJobs(request):
	allJobs = bool(request.GET.get('all',0))
	if allJobs and request.user.is_staff:
		jobs = Job.objects.all()
	else:
		jobs = Job.objects.filter(owner=request.user)
		
	theJobs = {}
	for job in jobs:
		theJobs[job.id] = {	'ID':job.id,
							'Owner':job.owner.username,
							'Task':job.task.taskname,
							'Created_On':str(job.created_on),
							'Status': job.status,
							'Processes_Running': job.processes_running,
							'Description': job.description,
							'Completed_on':str(job.ended_on) if job.ended_on else ""
						  }
	
	return HttpResponse( json.dumps(theJobs) )

def getGrids(request):
	grids = Grid.objects.all().exclude(state="Offline").exclude(state="Gone")
	
	overview = {}
	for grid in grids:
		overview[grid.name] = {}
		overview[grid.name]["last_update"] = grid.last_update.strftime("%d/%m/%y %H:%M")
		overview[grid.name]["state"] = grid.state
		overview[grid.name]["nodes"] = {}
		
		nodes = Node.objects.filter(grid=grid)
		for node in nodes:
			overview[grid.name]["nodes"][node.name] = {}
			overview[grid.name]["nodes"][node.name]["online"] = node.connected
			
			if node.connected:
				slots = Slot.objects.filter(node=node)
				overview[grid.name]["nodes"][node.name]["slots"] = []
				for slot in slots:
					overview[grid.name]["nodes"][node.name]["slots"].append(slot.state)
				
	return HttpResponse(json.dumps(overview))
	
def screen(request):
	if not request.user.is_authenticated():
		redirect("login.htm")

	screen_slug = request.GET.get('screen','home')

	screen = TileScreen.objects.get(slug=screen_slug)
	tiles = Tile.objects.filter(tilescreen=screen.id).order_by('order')

	html = []
	
	for tile in tiles:
		screen, cont, action = "","",""
		
		if tile.linked_screen:
			screen = " screen='%s'" % tile.linked_screen
		if tile.linked_cont:
			cont = " cont='%s'" % tile.linked_cont.slug
		if tile.linked_action:
			action = " action='%s:%s'" % (tile.linked_action.action,tile.linked_action.parameters)
		
		html.append("<div class='tile'%s%s%s>%s</div>" % (screen, cont, action, tile.title))
	
	return HttpResponse('\n'.join(html))
	
def cont(request):
	if not request.user.is_authenticated():
		return redirect('login.htm')	
	
	cont_slug = request.GET.get('cont','start')
	cont = Cont.objects.get(slug=cont_slug)
	form = json.loads(request.GET.get('format'))
	try:
		contents = cont.contents.format(*form)
	except:
		contents = cont.contents
	html = "<h2>%s</h2>\n%s" % (cont.title, contents)
	
	return HttpResponse(html)
