# -*- coding: utf-8 -*-
# import pytz
import datetime
from datetime import datetime, timedelta
import calendar
import json
import webapp2

import re
from google.appengine.api import urlfetch
import logging
import xml.etree.ElementTree as ET
# 
pattern =re.compile('"Destination":"(.+?)",')
stationMap = {"skoyen":3012500,
		"eidsvoll":2370300,
		"oslos":3010010,
		"nationaltheatret":3010030,
		"leirsund":2310240}

def utc_to_local(utc_dt):
	return utc_dt+timedelta(hours =  1)
	# local_tz = pytz.timezone('Europe/Oslo')
	# local_dt = utc_dt.replace(tzinfo=pytz.utc).astimezone(local_tz)
	# return local_tz.normalize(local_dt) # .normalize might be unnecessary

class RealtimeStop(webapp2.RequestHandler):
	def get(self):
		station = self.request.get('station').lower()
		stationName=station
		if station in stationMap:
			station =stationMap [station]

		url = "http://reisapi.ruter.no/stopvisit/getdepartures/"+ str(station)
		logging.info(url)
		print ("something")
		
		result = urlfetch.fetch(url)

		
		# string = ""
		# while result.available():
		# 	string += result.read()
		# logging.info(result.content)
		# root = ET.fromstring(result.content)
		# root = tree.getroot()
		line = self.request.get('line')
		destination = self.request.get ('destination')
		destinationName=destination
		if destination in stationMap:
			destination =stationMap[destination]
		data =json.loads(result.content)
		
		now = utc_to_local(datetime.now())
		
		url= "http://api.trafikanten.no/reisrest/Travel/GetTravelsByPlaces/?time=%s&toplace=%s&fromplace=%s&isAfter=True&proposals=12&transporttypes=Train&changePunish=20" % (now.strftime("%d%m%Y%H%M"),  destination, station)
		print(url)
		result = urlfetch.fetch(url)
		everything =set(re.findall(pattern,result.content))
		logging.info (everything)
		times = []
		for elements in data:
			# self.response.write ("<p>")
			for destinationName in everything:	
				if  not destinationName or elements["MonitoredVehicleJourney"]["DestinationName"].lower()== destinationName.lower():
				# self.response.write (elements["MonitoredVehicleJourney"]["PublishedLineName"]+ "<br>")
					temporary =elements["MonitoredVehicleJourney"]["MonitoredCall"]["ExpectedDepartureTime"]
					temporaryAimed=elements["MonitoredVehicleJourney"]["MonitoredCall"]["AimedDepartureTime"]
					expected =datetime.strptime(temporary[0:temporary.index("+")], "%Y-%m-%dT%H:%M:%S")
					aimed=datetime.strptime(temporaryAimed[0:temporaryAimed.index("+")], "%Y-%m-%dT%H:%M:%S")
					delay = (expected-aimed).total_seconds()/ 60.0
					# logging.info(elements["Extensions"]["Deviations"][0]["Header"])
					try:
						deviation = ""
						for string in elements["Extensions"]["Deviations"]:
							deviation +=string["Header"]+ "\n"
					except:
						deviation = ""
					times.append((elements["MonitoredVehicleJourney"]["MonitoredCall"]["ExpectedDepartureTime"],elements["MonitoredVehicleJourney"]["MonitoredCall"]["DeparturePlatformName"], deviation, delay, destinationName))

				# for key,element in elements["MonitoredVehicleJourney"]["MonitoredCall"].items():
							
				# 	self.response.write (key + ": " )
				# 	self.response.write (element)
				# 	self.response.write ("<br>")
		times.sort()

		print(times)
		self.response.write( "%s; %s; %.02f; %s; P%s; %s"% (stationName.capitalize(),times[0][4],times[0][3],times[0][0][times[0][0].index('T')+ 1:times[0][0].index('+')],times[0][1],times[0][2]))
		# for journey in root.iter('MonitoredVehicleJourney'):
		# 	logging.info ("find line "+line)
		# 	if journey.find('LineRef').text == line:
		# 		call = journey.find('MonitoredCall')
		# 		for times in call:
		# 			self.response.write(times.tag +": " + times.text)
		# 	break



application = webapp2.WSGIApplication([
	('/', RealtimeStop),
], debug=True)