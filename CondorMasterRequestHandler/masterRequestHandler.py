from PyCondor import *
import json, requests, os, tarfile, time, re

class masterRequestHandler():
	jobsFolder = "M:\\CondorMasterRequestHandler"
	submittedJobs = False
	def __init__(self):
		print "*"*40
		print "New job check @ %s" % time.strftime("%a, %d %b %Y %H:%M:%S")
		print "*"*40
		
		self.PyC = PyCondor()

	def parsePaths(self):
		self.paths = {}
		pathsfile = open(os.path.join(self.jobsFolder,"PATH.ini"))
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
				os.mkdir("%s/Jobs/%s" % (self.jobsFolder, id))
			except:
				print "%s already exists" % id
			print f
			tar = requests.get(f).content
			
			newtarname = "%s/Jobs/%s/job_%s_%s.tar.gz" % (self.jobsFolder,id,id,job['Owner'])
			newtar = open( newtarname , "wb")
			newtar.write(tar)
			newtar.close()
			result = tarfile.open(newtarname,"r:gz")
			result.extractall(path="%s/Jobs/%s/" % (self.jobsFolder,id))
			result.close()
			os.remove(newtarname)
			
	def startNewJobs(self):
		print "Starting new jobs"
		submittedJobs = {}
		for id in self.jobrequests:
			print "Starting job %s\n" % id
			jobdir = "%s/Jobs/%s" % (self.jobsFolder,id)
			 
			jfr = open(os.path.join(jobdir, "CondorFile.job"), "r")
			jf = jfr.read()
			jfr.close()
			
			jfw = open(os.path.join(jobdir, "CondorFile.job"),"w")
			
			for path in re.findall("%(\w+)%",jf):
				jf = jf.replace("%"+path+"%", self.paths[path])
			
			jfw.write(jf)			
			jfw.close()
			
			if os.path.exists(jobdir):
				cId = self.PyC.startJob(id)
				submittedJobs[id] = int(cId)
				time.sleep(2)
		
		runfn = "%s/Jobs/running.log" % (self.jobsFolder)
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
		runfn = "%s/Jobs/running.log" % (self.jobsFolder)
		condorids = json.loads(open(runfn, "r").read())
		running = []
		queue = self.PyC.getCondorQueue()
		for jobs in queue.values():
			for job in jobs:
				try:
					running.append( int(dict(job)['ID']) )
				except:
					pass
		
		print running
		
		completedJobs = {}
		jobs = os.listdir("%s/Jobs" % self.jobsFolder)
		os.chdir("%s/Jobs" % self.jobsFolder)
		
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
					if ".out" in f or ".err" in f:
						files.append(f)
				
				if len(files) > 0:
				
					tarname = "job_%s_results.tar.gz" % ( job )
					tf = tarfile.open(tarname, "w:gz")
					for f in files:
						tf.add( f )
					tf.close()
					completedJobs[job] = "%s/Jobs/%s/%s" % (self.jobsFolder,job,tarname)
				
				os.chdir("../")
			
		self.completedJobs = completedJobs
	
	def removeCompletedJobs(self):
		for job in self.completedJobs.keys():
			jf = os.path.join(self.jobsFolder,"Jobs",job)
			for f in os.listdir(jf):
				os.remove(os.path.join(jf,f))
			os.rmdirs(jf)
			
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
			
if __name__ == "__main__":
	mRH = masterRequestHandler()
	
	# Do a checkup of the completed jobs.
	mRH.checkCompletedJobs()
	mRH.uploadCompletedJobs()
	mRH.removeCompletedJobs()
	
	jobLimit = mRH.PyC.getCondorStatus()['Totals']['Unclaimed']+1 # Determine the amount of job spaces available
	print "Available job spaces: %s" % jobLimit
	
	mRH.loadJobRequests(jobLimit)
	
	if len(mRH.jobrequests) > 0:
		mRH.parsePaths()
		mRH.loadJobFiles()
		mRH.startNewJobs()
	else:
		print "No new jobs @ %s" % time.strftime("%a, %d %b %Y %H:%M:%S")
	
	# Report the current state
	mRH.reportCurrentState()