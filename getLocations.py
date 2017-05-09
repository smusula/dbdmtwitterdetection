"""
	For each hashtag found in file hashtag.txt (ordered by number of
	appearances), we request Location identification on locationiq.org
	and store the result in a specific folder.
	It aims to overcome the limit of 10k requests/day for free users.
"""

import json
from time import sleep
from urllib.request import Request, urlopen
from os.path import exists


api = "http://locationiq.org/v1/"
key = "508de9783544d5e389f1"

def getJson(h):
	php = "balance" if(h == -1) else "search"
	url = api + php +".php?key="+ key + "&q="+ str(h) +"&format=json"
	req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
	return json.loads(urlopen(req).read())

def getError(js):
	if type(js) != type({}):
		return -1
	return js['error']

def getFilename(h):
	return "locationiq/h-"+h+".txt"

def getBalance():
	req = getJson(-1)
	status = req['status']
	if status != "ok":
		return status
	return req['balance']['day']

def dimBalance(b, i=1):
	b -= i
	if b > 0:
		return b
	b = getBalance()
	return b


balance = getBalance()
print("Balance: "+ str(balance))
sleep(2)

hashtags = open("hashtags.txt", "r").read().split("\n")
for h in hashtags[:]:
	if exists(getFilename(h)):
		print("x Already Requested   "+ h)
		continue

	req = getJson(h)
	while getError(req) != -1:
		print("x "+ getError(req))
		if getError(req) != "Rate Limited":
			break
		sleep(.8)
		req = getJson(h)
		balance = dimBalance(balance, 2)

	l = len(req)
	if l:
		print("{:2}   location{}  for   {}".format(l, 's' if l>1 else ' ', h))
	else:
		print(  "     nothing    for   "+ h)
	
	file = open(getFilename(h), "w")
	file.write(json.dumps(req, indent=2))
	file.close()
	sleep(.8)

	balance = dimBalance(balance)
	if balance <= 0:
		break
	

print("\nNo balance left")

