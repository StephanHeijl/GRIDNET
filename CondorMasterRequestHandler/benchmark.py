# GRIDNET Benchmark Script
# @author	Stephan Heijl
# @date		21/2/2012
# @owner	BioCOMP project
# @license	Open Source - Apache License
# @purpose	Testing an individual node on different
# 			operations using Python to determine a 
#			score for the node

# Operations:
# 1: Find 100 primes numbers over 1.000.000, with a naive algorithm
# 2: Sort 2500 integers with a bubblesort

# Test 1: Prime numbers
class CalcPrime():
	def isDivisible(self,a,b):
		return a % b == 0
	
	def isPrime(self,n):
		prime = True
		a = 3

		while a < n and prime == True:
			prime = self.isDivisible(n, a) != True				
			a+=1
		
		return prime
	
def testPrimes():
	primes = []
	n = 1000*1000
	cp = CalcPrime()
	
	while len(primes) < 10:
		p = cp.isPrime(n)
		if p:
			primes.append(n)		
		n+=1
	
class BubbleSort():
	def sort(self,array):
		swapped = True
		while (swapped):
			 swapped = False
			 for i in range(0,len(array)-1):
				 if (array[i] > array[i+1]):
				     temp = array[i]
				     array[i] = array[i+1]
				     array[i+1] = temp
				     swapped = True
				     
		return array
				     
	def makeRandomArray(self,n):
		array = range(n)
		import random
		random.shuffle(array)
		return array
	
	
def testBubbleSort():
	BS = BubbleSort()
	a = BS.makeRandomArray(5000)
	sa = BS.sort(a)
	
import timeit, socket,json

if __name__ == "__main__":
	hostname = socket.gethostname()
	print "This benchmark is running on %s " % hostname
	
	tests = 100
	
	primesR = []
	bubbleR = []
	for i in range(tests):
		primesR.append(timeit.timeit(testPrimes, number=1))
	
	for i in range(tests):
		bubbleR.append(timeit.timeit(testBubbleSort, number=1))
	
	
	print "This benchmark is running on %s " % hostname
	print "Test results primes test: %s " % primesR
	print "Test results bubble test: %s " % bubbleR 
	print "\nJSON:"
	data = {"hostname":hostname, "results" :{"PRIMES":primesR, "BUBBLE":bubbleR}}
	print json.dumps(data)
	print "\nCSV:"
	print '"hostname";"primes";"bubbles"'
	for i in range(tests):
		print ('"%s";%.3f;%.3f' % (hostname,primesR[i],bubbleR[i])).replace(".",",")
	
