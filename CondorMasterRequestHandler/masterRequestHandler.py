from PyCondor import *
import json, requests, os, tarfile, time, re

class Log():
	def __init__(self, filename):
		self.scriptStartTime = time.strftime("%a, %d %b %Y %H:%M:%S")
		self.messages = []
		self.logFileName = filename

	def write(self, message):
		t = time.strftime("%a, %d %b %Y %H:%M:%S")
		self.messages.append((t, message))
		
	def clearMessages(self):
		self.messages = []
	
	def save(self):
		self.logSaveTime = time.strftime("%a, %d %b %Y %H:%M:%S")
		try:
			logfile = open(os.path.join(masterRequestHandler.mainFolder, self.logFileName), "w")
		except IOError:
			print "Could not open log file. Outputting all messages to stdout.\n\n"
			for message in self.messages:
				print "Message at %s: %s\n" % (message[0], message[1])
			return
		
		logfile.write("Script started at: %s\n" % self.scriptStartTime)
		for message in self.messages:
			logfile.write("Message at %s: %s\n" % (message[0], message[1]))
		
		if len(self.messages) == 0:
			logfile.write("Log saved at %s, no errors encountered.\n" % self.logSaveTime)
			
		logfile.close()
		
	def backup(self):
		try:
			backuplogfile = open(os.path.join(masterRequestHandler.mainFolder, self.logFileName+".backup"), "a")
		except IOError:
			print "Could not open backup log file."
			print "You are pretty much doomed."
			return
			
		backuplogfile.write("\n---\n")
		for message in self.messages:
			backuplogfile.write("Message at %s: %s\n" % (message[0], message[1]))
		

class masterRequestHandler():
	mainFolder = "/home/users/project/Stephan"
	submittedJobs = False
	
	def __init__(self):
		print "*"*40
		print "New job check @ %s" % time.strftime("%a, %d %b %Y %H:%M:%S")
		print "*"*40
		
		self.PyC = PyCondor()

	def parsePaths(self):
		self.paths = {}
		pathsfile = open(os.path.join(self.mainFolder,"PATH.ini"))
		for path in pathsfile:
			p = path.split("=")
			self.paths[p[0].strip(" ")] = p[1].strip(" ")
			
		pathsfile.close()	
	
	def loadJobRequests(self, limit):
		print "Loading job requests..."
		jRequests = requests.get("http://cytosine.nl/GRIDNET/jobs/Queued?limit=%s" % limit )
		self.jobrequests = json.loads( jRequests.content )
		print "%s job requests found.\n" % len(self.jobrequests)
		
	def loadJobFiles(self):
		print "Loading job files...\n"
		for id,job in self.jobrequests.items():
			
			f = job['Files']
			try:
				os.mkdir("%s/Jobs/%s" % (self.mainFolder, id))
			except:
				print "%s already exists" % id
			print f
			tar = requests.get(f).content
			
			newtarname = "%s/Jobs/%s/job_%s_%s.tar.gz" % (self.mainFolder,id,id,job['Owner'])
			newtar = open( newtarname , "wb")
			newtar.write(tar)
			newtar.close()
			result = tarfile.open(newtarname,"r:gz")
			result.extractall(path="%s/Jobs/%s/" % (self.mainFolder,id))
			result.close()
			os.remove(newtarname)
			
	def startNewJobs(self):
		print "Starting new jobs"
		submittedJobs = {}
		for id in self.jobrequests:
			print "Starting job %s\n" % id
			jobdir = "%s/Jobs/%s" % (self.mainFolder,id)
			
			jfr = open(os.path.join(jobdir, "CondorFile.job"), "r")
			jf = jfr.read()
			jfr.close()
			
			jfw = open(os.path.join(jobdir, "CondorFile.job"),"w")			
			for path in re.findall("%(\w+)%",jf):
				jf = jf.replace("%"+path+"%", self.paths[path])
			
			jfw.write(jf)			
			jfw.close()
			
			if os.path.exists(jobdir):
				try:
					cId = self.PyC.startJob(id)
				except Exception as ex:
					print ex
				
				try:
					submittedJobs[id] = int(cId)
				except:
					print "Submission went wrong"
					print cId
					raise RuntimeError, str(cId) + " -> D:"
					
				time.sleep(2)
			else:
				print "Something went wrong, the path was not found"
				print jobdir
		
		
		runfn = "%s/Jobs/running.log" % (self.mainFolder)
		current = {}
		if os.path.exists(runfn):
			running = open(runfn,"r")
			try:
				current = json.loads(running.read())
			except:
				pass
			running.close()
		
		cqueue = []
		queue = self.PyC.getCondorQueue()
		for jobs in queue.values():
			for job in jobs:
				try:
					cqueue.append( int(dict(job)['ID']) )
				except:
					pass
				
		for k,v in current.items():
			if v not in cqueue:
				del current[k]	
		
		running = open(runfn,"w")
		running.write(  json.dumps( dict(current.items() + submittedJobs.items()) ) )
		running.close()
		self.submittedJobs = json.dumps(submittedJobs)
	
	
	def checkCompletedJobs(self):
		runfn = "%s/Jobs/running.log" % (self.mainFolder)
		try:
			condorids = json.loads(open(runfn, "r").read())
		except:
			condorids = {}
		
		running = []
		queue = self.PyC.getCondorQueue()
		for jobs in queue.values():
			for job in jobs:
				try:
					running.append( int(dict(job)['ID']) )
				except:
					pass
		
		completedJobs = {}
		jobs = os.listdir("%s/Jobs" % self.mainFolder)
		os.chdir("%s/Jobs" % self.mainFolder)
		
		for job in jobs:
			if "." not in job:
				try:
					CoId = condorids[job]
					print job, ":", CoId
					if int(CoId) in running:
						print "Still executing"
						continue
				except:
					pass
				
				os.chdir(job)
				allfiles = os.listdir(".")
				files = []
				for f in allfiles:
					#if ".out" in f or ".err" in f:
					files.append(f)
				
				if len(files) > 0:
				
					tarname = "job_%s_results.tar.gz" % ( job )
					
					if os.path.exists(tarname):
						continue
					
					tf = tarfile.open(tarname, "w:gz")
					for f in files:
						tf.add( f )
					tf.close()
					completedJobs[job] = "%s/Jobs/%s/%s" % (self.mainFolder,job,tarname)
				
				os.chdir("../")
			
		self.completedJobs = completedJobs
	
	def removeCompletedJobs(self):
		for job in self.completedJobs.keys():
			jf = os.path.join(self.mainFolder,"Jobs",job)
			for f in os.listdir(jf):
				os.remove(os.path.join(jf,f))
			os.rmdir(jf)
			
	def uploadCompletedJobs(self):
		for job,file in self.completedJobs.items():
			url = "http://www.cytosine.nl/GRIDNET/results/%s" % job
			files = {job: (file, open(file, 'rb'))}
			r = requests.post(url, files=files)
			print r.content
	
	def reportCurrentState(self):
		print "Reporting state to Master Server"

		status = self.PyC.getJSONCondorStatus()
		queue = self.PyC.getJSONCondorQueue()
		data = {}
		data['status'] = status
		data['queue'] = queue
		if self.submittedJobs:
			data['batch'] = self.submittedJobs		
		
		time.sleep(2)
		req = requests.post("http://www.cytosine.nl/GRIDNET/reportState", data)

		print req.content
		
	def reportLatestMRHLogs(self, *logs):
		logData = {}
		for log in logs:
			logFile = open(log.logFileName, "r")
			logData[log.logFileName] = logFile.read()
			logFile.close()
		
		jsonLogData = logData
		req = requests.post("http://www.cytosine.nl/GRIDNET/reportMRHLogs", jsonLogData)
		if req.status_code > 299:
			log.write("Couldn't connect to GRIDNET report server.")
			raise Exception
		
		print req.text
		
	def distressCall(self, message):
		req = requests.post("http://www.cytosine.nl/GRIDNET/distress", {"Error": message})
		if req.status_code > 299:
			err = "Couldn't connect to GRIDNET server. Distress call failed."
			log.write(err)
			print err
			raise Exception
			
if __name__ == "__main__":
	log = Log("log.txt")
	mRH = masterRequestHandler()
	
	try:
		mRH.checkCompletedJobs()
		mRH.uploadCompletedJobs()
		mRH.removeCompletedJobs()
	except Exception as ex:
		m = "Something went wrong whilst checking for, uploading and removing completed jobs: " + str(ex)
		log.write(m)
	
	try:
		jobLimit = mRH.PyC.getCondorStatus()['Totals']['Unclaimed'] # Determine the amount of job spaces available
		print "Available job spaces: %s" % jobLimit
	except Exception as ex:
		m = "Something went wrong whilst determining the job limit: " + str(ex)
		log.write(m)
	
	try:
		mRH.loadJobRequests(jobLimit)
	except Exception as ex:
		m = "Something went wrong whilst loading new job requests: " + str(ex)
		log.write(m)
	
	try:
		if len(mRH.jobrequests) > 0:
			mRH.parsePaths()
			mRH.loadJobFiles()
			mRH.startNewJobs()
		else:
			print "No new jobs @ %s" % time.strftime("%a, %d %b %Y %H:%M:%S")
	except Exception as ex:
		m = "Something went wrong whilst starting the new jobs: " + str(ex)
		log.write(m)
	
	try:
		mRH.reportCurrentState()
	except Exception as ex:
		m = "Something went wrong whilst reporting the current state to the server: " + str(ex)
		log.write(m)
		
	try:
		log.save()
	except:
		try:
			mRH.distressCall("Logs could not be stored.")
		except:
			print "Distress call failed. Logs are being stored sequentially. "
		log.backup()
		
	try:
		mRH.reportLatestMRHLogs(log)
	except:
		try:
			mRH.distressCall("Logs could not be reported.")
		except:
			print "Distress call failed. Logs are being stored sequentially. "			
		log.backup()
