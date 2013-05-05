"""
Query a corpus using a textual description.
"""

import nltk
import urllib2
import simplejson
import person
import pymongo
import re, string
import operator

db = pymongo.MongoClient().introducemeto
lem = nltk.WordNetLemmatizer()

def lowerList(lst):
	return [l.lower() for l in lst]

def getPeople():
	"""Gets LinkedIn corpus"""
 	return [person.Person(x) for x in db.linkedin.find()]

def makeHeadlines():
	"""If words appear in people's headlines, they are most important - 
	check if proper noun keywords appear in headline corpus and if so, set them as requirements"""
	headers = []
	names = []
	for p in getPeople():
		headers.append(p.headline)
		names.append(p.name)
	return headers, names

def removeHandle(s):
	"""0: Remove @IntroduceMeTo handle"""
	found = s.find('@IntroduceMeTo')
	if found != -1:
		return s[len('@IntroduceMeTo '):]

def removePunctuation(s):
	"""1: Remove punctation"""
	return re.sub('[%s]' % re.escape(string.punctuation), '', s)
 	
def removeCommonWords(s):
	"""2: Remove common words"""
	fin = open('words/common_words.txt', 'r')
 	commons = [line.strip() for line in fin]
 	fin.close()
 	criticalwords = []
 	for w in s.split():
 		if w not in commons:
 			criticalwords.append(w)
 	return ' '.join(criticalwords)

def initialProcessing(s):
	"""0-2: Initial processing (Keep as String!)"""
	s = removeHandle(s)
	s = removePunctuation(s)
	s = removeCommonWords(s)
	return s

def listStates():
	states_list = '{"AL" : "Alabama","AK" : "Alaska","AZ" : "Arizona","AR" : "Arkansas","CA" : "California","CO" : "Colorado","CT" : "Connecticut","DE" : "Delaware","DC" : "District of Columbia","FL" : "Florida","GA" : "Georgia","HI" : "Hawaii","ID" : "Idaho","IL" : "Illinois","IN":"Indiana","IA":"Iowa","KS":"Kansas","KY":"Kentucky","LA":"Louisiana","ME":"Maine","MD":"Maryland","MA":"Massachusetts","MI":"Michigan","MN":"Minnesota","MO":"Missouri","MT":"Montana","NE":"Nebraska","NV":"Nevada","NH":"New Hampshire","NJ":"New Jersey","NM":"New Mexico","NY":"New York","NC":"North Carolina","ND":"North Dakota","OH":"Ohio","OK":"Oklahoma","OR":"Oregon","PA":"Pennsylvania","RI":"Rhode Island","SC":"South Carolina","SD":"South Dakota","TN":"Tennessee","TX":"Texas","UT":"Utah","VT":"Vermont","VA":"Virginia","WA":"Washington","WV":"West Virginia","WI":"Wisconsin","WY":"Wyoming"}'
 	states_dict = simplejson.loads(states_list)
 	return states_dict

def getLocation(s):
	"""Pull out cities and states"""
	states_dict = listStates()
 	fin = open('words/common_words.txt', 'rw')
 	state_req = None
 	city_req = None

 	for w in s.split():
 		if w.lower() in states_dict.keys():
 			state_req = w
 		if w.lower() in states_dict.values():
 			rev_states_dict = dict(zip(states_dict.values(), states_dict.keys()))
 			state_req = rev_states_dict[w]	
 	
 	cities = [line.strip() for line in open('words/cities.txt')]
 	cities = lowerList(cities)
 	for w in s.split():
 		if w.lower() in cities:
 			city_req = w
 	
 	res = []
 	if city_req != None:
 		res.append(city_req)
 	elif state_req != None:
 		res.append(state_req)
 	return res

def getHeadlines(s):
	"""Grabs the keywords that are in people's headlines and makes them requirements"""
 	headline_corpus, name_corpus = makeHeadlines()
 	reqs = []
 	names = []
 	for h in headline_corpus:
 		for w in s.split():
 			if w in h and w not in reqs:
 				reqs.append(w)
 	for n in name_corpus:
 		for w in s.split():
 			if w in n and w not in names:
 				names.append(w)
 	return reqs, names

def remove(s, keys):
	"""Removes requirements from keywords and adds them to the required list"""
	kw = []
	rq = []
	for w in s.split():
		if w not in keys:
			kw.append(w)
		else:
			rq.append(w)
	s = " ".join(kw)
	return [s, rq]

def createReqs(s):
	"""Creates the required and the keywords for a query"""
	reqs, names = getHeadlines(s)
	[s, req1] = remove(s, getLocation(s))
	[s, req2] = remove(s, reqs)
	[s, req3] = remove(s, names)
	reqs = req1 + req2 + req3
	return {"reqs" : reqs, "keys" : s.split(), "names" : names}

def postagAndLemma(lst):
	"""Helper function for processQuery -- tags and lemmatizes a list"""
	lst = nltk.pos_tag(lst)
	newlst = []
	for l in lst:
		lemmed = lem.lemmatize(l[0].lower())
		if lemmed != l[0].lower():
			l = (l[0], [l[1], lemmed])
		else:
			l = (l[0], [l[1]])
		newlst.append(l)
	return newlst


def processQuery(s):
	"""Tags and adds lemma version of each key and req"""
	s = initialProcessing(tweet)
	q = createReqs(s)
	q = {"keys" : postagAndLemma(q["keys"]), "reqs" : postagAndLemma(q["reqs"]), "names": q["names"]}
	return q


def narrowNameSearch(s):
	"""If someone puts in a name, it narrows the users down to just those with the correct name"""
	users = getPeople()
	requsers = []
	q = processQuery(s)
	for user in users:
		if len(user.search_name(lowerList(q["names"]))) > 0:
			requsers.append(user)
	if (len(requsers) == 0):
		requsers = users
	return requsers, q

tweet = '@IntroduceMeTo Developers that work in San Francisco at Pivotal Labs'
users, query = narrowNameSearch(tweet)
print query

