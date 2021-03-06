from subprocess import *
from pprint import pformat as pf
from json import dumps,loads
import datetime,re,os,time,sys

class CondorError(Exception):
	def __init__(self, message):
		self.message = message
	def __str__(self):
		return repr(self.message)
		
class PyCondor():
	condordir = "P:\\Condor\\bin\\"
	mainFolder = "M:\\CondorMasterRequestHandler"
	
	def __init__(self):
		if(sys.platform in ["posix","linux2"]):
			self.eol = "\n"
		else:
			self.eol = "\r\n"
	
	def splitJob(self, taskname, owner, description, command, parameters, id, pieces, filename):
		splitname = filename.split(".")
		
		if pieces == -1:
			# Check how many machines are available
			pieces = self.getCondorStatus()['Totals']['Unclaimed']
		
		if splitname[-1] in ["fa","fasta","fas"]:
			# The file is a FASTA, we can split this :D
			fasta = self.__fasta2dict(open(filename))
			parts = self.__splitDict(fasta,pieces)
			
		
		
		jfns,jobfiles,nfns,nparts = [],[],[],[]
		nfc = '.'.join(splitname[:-1]+["$( Process )", "part"])
		nparams = parameters.replace(filename, nfc)
		njob = self.makeJobFile(taskname, owner, description, command, nparams, "%s.%s" %(id,p))
		
		for p in len(range(parts)):
			nfn = '.'.join(splitname[:-1]+[str(p), "part"])
			nfns.append(nfn)
			
			nf = open( nfn, "w" )
			nf.write( self.__dict2fasta(parts[p]) )
			nf.close()

			p+=1
		
		return njob, zip(nfns, parts)
	
	def __splitDict(self,dictionary,pieces):
		nDicts = []
		items = dictionary.items()
		pSize = int(len(dictionary)/pieces)
		for p in range(pieces):
			nDicts.append(dict( items[p*pSize:(p+1)*pSize] ) )

		return nDicts
			
	def __fasta2dict(self, f):
		k = []
		d = dict(zip(k, ''.join([";" if x == None else x for x in [k.append(v[:-1]) if v[0] == ">" else v[:-1].upper() for v in f]]).split(";")[1:]))
		return d
		
	def __dict2fasta(self, d):
		f = []
		for k,v in d.items():
			f+=[k,v,""]
		
		return "\n".join(f)
		
	def __generateDescription(job, owner, **info ):
		width = 60
		description = ["#"*(width+3)]
		descriptionContents = [	" "*width,
								("Job file generated by PyCondor").ljust(width),
								"~"*(width-1)+" ",
								("Job: %s" % job).ljust(width),
								("Owner: %s" % owner).ljust(width),
								("Date generated: %s" % str(datetime.datetime.today())[:-7]).ljust(width) ]

		for key,value in info.items():
				value = re.sub("[\n\r\t]", " ", value)
				if len(key)+len(value)+2 < width:
						descriptionContents.append(("%s: %s" % (key, value)).ljust(width) )
				else:
						offset = width-len(key)-3

						descriptionContents.append(("%s: %s" % (key, value[:offset])).ljust(width))
						vals = filter(lambda l: len(l) > 0, re.split(".{0:%s}" % width, value[offset:]))
						for v in vals:
								print v
								descriptionContents.append(v.ljust(width))

		descriptionContents.append(" "*width)			
		
		description.append( "# " + "# \n# ".join(descriptionContents) + "#")
		description.append("#"*(width+3))
		return '\n'.join(description)
		
	def makeJobFile(self, taskname, owner, description, command, parameters, id, **others):
		jobFile = []
		
		jobFile.append(self.__generateDescription(taskname,owner,Description=description) )
		jobFile.append("")
		jobParameters = {
							"Universe":"vanilla",
							"Executable": command,
							"Arguments": parameters,
							"Log":"%s.%s.%s.log" % ( owner, taskname, id),
							"Output":"%s.%s.%s.out" % ( owner, taskname, id),
							"Error":"%s.%s.%s.err" % (owner, taskname, id)
						}
		
		for key, value in jobParameters.items():
			jobFile.append("%s = %s" % (key.ljust(max([len(k) for k in jobParameters.keys()])),value))
				
		for key, value in others.items():
			jobFile.append("%s = %s" % (key.ljust(max([len(k) for k in jobParameters.keys()])),value))
			
		jobFile.append("Queue")
		
		return '\n'.join(jobFile)
	
	def startJob(self,jobid):		
		jobdir = os.path.abspath("%s/Jobs/%s" % (self.mainFolder, jobid))  
		
		command = "%scondor_submit CondorFile.job" % self.condordir
		try:
			os.chdir(jobdir)
		except Exception as ex:
			print "Something went wrong changing directories. "
		
		starter = Popen(command,shell=True,stdout=PIPE)
		starter.wait()
		submissionDetails = starter.stdout.read().split(self.eol)
		
		try:
			return re.search("cluster (\d+)\.",submissionDetails[-2]).group(1)
		except:
			return submissionDetails
	
	def __get_status(self):
		stat = Popen("%s/condor_status" % self.condordir,stdout=PIPE,stderr=PIPE)
		err = stat.stderr.read()
		if len(err) > 0:
			raise CondorError(err)
		
		self.__condorStatus = stat.stdout.read()
		try:
			stat.terminate()
		except:
			pass
			
	def __parse_status(self):
		# Split the status into manageble pieces
		stat = filter(lambda l: len(l)>0, self.__condorStatus.split(self.eol))
		
		splitstat = []
		for line in stat:
			splitstat.append([])
			for element in line.split(" "):
				if len(element) > 0:
					splitstat[-1].append(element)

		# Piece together the systems information
		systems = []
		sysstats = False
		for line in splitstat[1:]:			
			if 'Total' in line and 'Owner' in line:
				sysstats = True
				statcount = 0
				statkeys = line
				continue
						
			if not sysstats:
				# This will put together the system's properties
				systems.append([line[0], list(zip(splitstat[0][1:], line[1:]))])			
			else:
				if 'Total' in line:
					continue
				# This wil fix the overview of the systems
				statcount +=1

		systems = dict(systems)
		
		#print pf(systems)

		# This will calculate the totals for the systems
		totals = {}
		for key in statkeys:
			totals[key] = 0		
	
		for system in systems.values():
			if len(system) > 0:
				totals[ dict(system)['State'] ] +=1
				totals[ 'Total' ] +=1
		
		systems['Totals'] = totals

		# Define the nice status and get on with it
		self.__condorNiceStatus = systems
	
	def getCondorStatus(self):
		self.__get_status()
		self.__parse_status()
		return self.__condorNiceStatus

	def getJSONCondorStatus(self):
		self.__get_status()
		self.__parse_status()
		self.__condorNiceStatus['@'] = time.strftime("%a, %d %b %Y %H:%M:%S")
		return dumps(self.__condorNiceStatus)

	def combineJSONCondorStatus(self, *status):
		statuses = []
		for cstatus in status:
			if not isinstance(cstatus,str):
				raise ValueError, "Your status needs to be string"
			try:
				statuses.append( loads(cstatus) )
			except:
				raise ValueError, "Your status needs to be JSON encoded"

		totals = dict((str(k),0) for k in statuses[0]['Totals'].keys())
		bigStats = {}
		for status in statuses:
			for key in status['Totals']:
				totals[key]+=status['Totals'][key]
			for system in status:
				if system != "Totals":
					bigStats[str(system)] = dict([ (str(k) if isinstance(k,unicode) else k,
													str(v) if isinstance(v,unicode) else v)
													for k,v in status[system].items()
												])

		bigStats['Totals'] = totals
		return bigStats	

	def __get_queue(self):
		q = Popen("%s/condor_q" % self.condordir ,stdout=PIPE,stderr=PIPE)
		err = q.stderr.read()
		if len(err) > 0:
			raise CondorError(err)
		
		self.__condorQueue = q.stdout.read()
		try:
			q.terminate()
		except:
			pass

	def __parse_queue(self):
		q = filter(lambda l: len(l)>0, self.__condorQueue.split(self.eol))
		splitq = []
		for line in q:
			splitq.append([])
			for element in re.split(" ",line):
				if len(element) > 0 and element not in ["--",":"]:
					
					splitq[-1].append(element.strip(": "))
		

		submissions = {}
		keys = []
		for line in splitq:
			if line[0] == "ID" and len(keys) == 0:
				keys = line			
			elif "Submitter" in line:
				currentSubmitter = line[1]
				submissions[line[1]] = []
			elif len(keys) > 0:
				if len(line) != len(keys):	
					job = []
					k,v = 0,0
					while v < len(line):
						if k >= len(keys):
							job[-1][1] += " "+ line[v]
							v+=1
						else:
							val = line[v]
							key = keys[k]
							if key == "SUBMITTED":
								val = ' '.join(line[v:v+2])

								v+=1
							if key in ["ID","SIZE","PRI"]:
								try:
									val = float(line[v])
								except ValueError:
									val = line[v]
							
							if len(key)>0 and val>0:
								job.append([key,val])
							k+=1
							v+=1
					
					submissions[currentSubmitter].append(job)

		self.__condorNiceQueue = submissions
	
	def getCondorQueue(self):
		self.__get_queue()
		self.__parse_queue()
		return self.__condorNiceQueue

	def getJSONCondorQueue(self):
		self.__get_queue()
		self.__parse_queue()
		self.__condorNiceQueue['@'] = time.strftime("%a, %d %b %Y %H:%M:%S")
		return dumps(self.__condorNiceQueue)
