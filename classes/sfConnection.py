import pytz
import datetime
from collections import OrderedDict
from simple_salesforce import Salesforce
import time
import smtplib
import requests
import xml.etree.ElementTree as ET





class sForce:

	def __init__(self):
		self.sf = Salesforce(username='petraluxuryrentals-cxv1@force.com', password='Evonify@@Evonify2020', security_token='Akkdxr4TF0sdRtDR9gEHiYEU')
		self.end = datetime.datetime.now(pytz.UTC)
		self.today = datetime.datetime.now()

	def importRecords(self, queryConditions):
		allRecords = []
		records = self.sf.query(queryConditions)
		for i in records['records']:
			allRecords.append(i['Id'])
		print(allRecords)
		return allRecords


	def grabAllBookingsPerUnit(self, unitId, numOfDays):
		daysAgo = self.today - datetime.timedelta(days=numOfDays)
		daysAgo = daysAgo.strftime("%Y-%m-%d")
		queryConditions = "SELECT Id FROM Booking__c WHERE Reservation_Status__c = '1' and Don_t_Block_RU_Calendar__c = False and Unit_RU_property_ID__c = " + unitId + " and CalendarEndDate__c > " + daysAgo
		return self.importRecords(queryConditions)

	def grabAllActiveMainUnits(self):
		queryConditions = "SELECT Id FROM Unit__c WHERE Active__c = True and Main_Unit__c = True"
		return self.importRecords(queryConditions)

	def updateBookingRecord(self, sfId, updateDict):
		try:
			self.sf.Booking__c.update(sfId,updateDict)
			print("booking record: ", sfId, " Has been updated")
		except Exception as e:
			print("booking record couldn't update due to an error: ")
			print (e)



class sfReservation:

	def __init__(self, sfId, sfConnection):
		self.sf = sfConnection
		self.sfId = sfId
		self.reservationInfo = self.sf.Booking__c.get(self.sfId)
		self.startDate = self.reservationInfo['start_date__c']
		self.endDate = self.reservationInfo['End_Date__c']
		self.calendarEndDate = self.reservationInfo['CalendarEndDate__c']
		self.unitId = self.reservationInfo['Unit_RU_property_ID__c']
		self.unitSfId = self.reservationInfo['Unit__c']

class sfUnit:
	def __init__(self, sfUnitId, sf):
		self.sf = sf
		self.sfId = sfUnitId
		self.unitInfo = self.sf.Unit__c.get(self.sfId)
		self.id = self.unitInfo['RU_Property_ID__c'] #RU Property Id

class sendCheckFormReminderProgram:

	def __init__(self):
		self.sf = sForce()
		self.today = datetime.datetime.now()

	def sendCheckinFormReminder(self):
		updateDict = {'Was_Check_in_form_reminder_sent__c': 0, 'Send_Check_in_form_reminder__c': 1}
		queryConditions = "SELECT Id FROM Booking__c WHERE Reservation_Status__c = '1' and 	Was_check_in_form_filled__c = False and was_check_in_form_sent__c = True and start_date__c > " + self.today.strftime("%Y-%m-%d")
		for sfId in self.sf.importRecords(queryConditions):
			res = sfReservation(sfId, self.sf.sf)
			print(res.sfId)
			self.sf.updateBookingRecord(res.sfId,updateDict)

class sendInstructionSheetProgram:

	def __init__(self):
		self.sf = sForce()
		self.today = datetime.datetime.now()
		self.afterThreeDays = self.today + datetime.timedelta(days=3)
		self.msg = "send sendInstructionSheetProgram" + "\n"
		print(self.today, self.afterThreeDays)

	def importRecords(self):
		queryConditions = "SELECT Id FROM Booking__c WHERE Reservation_Status__c = '1' and was_instruction_sheet_sent__c = False and Was_check_in_form_filled__c = True and IsPaid__c = True and start_date__c >= " + self.today.strftime("%Y-%m-%d") + " and start_date__c <= " + self.afterThreeDays.strftime("%Y-%m-%d")
		return self.sf.importRecords(queryConditions)

	def case1(self, res, unit):
		case1 = ["SELECT Id from Booking__c WHERE Reservation_Status__c = '1' and start_date__c <= ", res.startDate, " and End_Date__c > ", res.startDate ," and Unit__c = ", "'", unit.sfId, "'", " and Id != ", "'" , res.sfId, "'"]
		return self.sf.importRecords("".join(case1))

	def case2(self, res, unit):
		case2 = ["SELECT Id from Booking__c WHERE Reservation_Status__c = '1' and start_date__c < ", res.endDate, " and End_Date__c >= ", res.endDate ," and Unit__c = ", "'", unit.sfId, "'", " and Id != ", "'" , res.sfId, "'"]
		return self.sf.importRecords("".join(case2))

	def case3(self, res, unit):
		case3 = ["SELECT Id from Booking__c WHERE Reservation_Status__c = '1' and start_date__c >= ", res.startDate, " and End_Date__c <= ", res.endDate ," and Unit__c = ", "'", unit.sfId, "'", " and Id != ", "'" , res.sfId, "'"]
		return self.sf.importRecords("".join(case3))

	def updateBookingRecord(self, sfId):
		updateDict = {'Send_Check_in_Instructions__c': 1}
		self.sf.updateBookingRecord(sfId, updateDict)

	def sendEmail(self,msg):
		#sending an email 
		email  = Email()
		email.sendEmail("results of sendInstructionSheetProgram ", self.msg)

	def msgContent(self, sfId, i):
		# i = 1 -> pass alert
		# i = 2 -> double booking alert
		if i == 1:
			self.msg = self.msg + " Sending the instruction sheet for Reservation: " + sfId + "\n"
		if i == 2:
			self.msg = self.msg + " DOUBLE BOOKING ALERT FOR Reservation: " + sfId + "\n"




	def startProgram(self):
		for sfId in self.importRecords():
			res = sfReservation(sfId, self.sf.sf)
			unit = sfUnit(res.unitSfId, self.sf.sf)
			
			print("*************")
			print("unitRuID: ", unit.id)

			print("case1: ")
			if len(self.case1(res, unit)) == 0:
				print("case1 passed")
				print("case2: ")
				if len(self.case2(res, unit)) == 0:
					print("case2 passed")
					print("case3: ")
					if len(self.case3(res, unit)) == 0:
						print("case3 passed")
						self.updateBookingRecord(res.sfId)
						self.msgContent(res.sfId, 1)
					else:
						self.msgContent(res.sfId, 2)
						continue
				else:
					self.msgContent(res.sfId, 2)
					continue
			else:
				self.msgContent(res.sfId, 2)
				continue

		self.sendEmail(self.msg)







class rentalsunited:

	def __init__(self):
		self.username = 'petraluxuryrentals@gmail.com'
		self.password = 'Bol@Bol1995'
		self.url = url = "http://rm.rentalsunited.com/api/Handler.ashx"
		self.headers = {'Content-Type': 'application/x-www-form-urlencoded'}


	def blockCalendar(self, pid, startDate, endDate, status):
		#when status is false, calendar will be blocked 
		payload = "\n<Push_PutAvb_RQ>\n <Authentication>\n <UserName>{}</UserName>\n <Password>{}</Password>\n </Authentication>\n <Calendar PropertyID=\"{}\">\n <Availability DateFrom=\"{}\" DateTo=\"{}\">{}</Availability>\n </Calendar>\n</Push_PutAvb_RQ>"
		payload = payload.format(self.username, self.password, pid, startDate, endDate, status)
		response = requests.request("GET", self.url, headers=self.headers, data = payload)
		tree = ET.fromstring(response.text)
		responseStatus = tree[0].get("ID")
		print(startDate, " ", endDate)
		print(responseStatus)
		print(response.text)
		return responseStatus


class sfRuCalendarBlock:

	def __init__(self):
		self.sf = sForce()
		self.rentalsunited = rentalsunited()
		self.msg = ""

	def grabBookingsPerUnit(self, unitId, numOfDays):
		bookingsPerUnit = self.sf.grabAllBookingsPerUnit(unitId, numOfDays)
		return bookingsPerUnit
	
	def getReservationObject(self, sfId):
		#return the reservation object
		booking = sfReservation(sfId, self.sf.sf)
		return booking

	def blockRuCalendar(self, unitId):
		quotes = "'" #must add quotes to the unitID string for the query call 
		unitId = quotes + unitId + quotes
		for sfId in self.grabBookingsPerUnit(unitId, 1): #one sf api call
			booking = self.getReservationObject(sfId) # one sf api call
			print("sfId: ", booking.sfId,"unitId: ", booking.unitId)
			responseStatus = self.rentalsunited.blockCalendar(booking.unitId, booking.startDate, booking.calendarEndDate, 'false')
			if responseStatus != '0':
				self.msg = self.msg + "the reservation: " + str(sfId) + " couldn't block the calendar on RU for the unit: " + str(unitId) + " check-in: " + booking.startDate + " check-out: " + booking.endDate + "\n"

	def freeAllCalendar(self, unitId):
		#free all the calendar in case any cancellation is present # this function should be included twice a day as it's very slow
		today = datetime.datetime.now()
		for x in range(90):
			self.rentalsunited.blockCalendar(unitId, today.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d"), 'true')
			today = today + datetime.timedelta(days=1)

	def fixCalendarForOneUnit(self, unitId):
		print("Fixing the calendar for unit: ", unitId)
		print("***********************************")
		self.blockRuCalendar(unitId)
		print("\n")

	def sendEmail(self,msg):
		#sending an email 
		email  = Email()
		email.sendEmail("results of blocking the calendar for all units unit", self.msg)

	def getUnitPropertyId(self, unit):
		ruPropertyId = sfUnit(unit, self.sf.sf).id
		return ruPropertyId

	def startProgram(self):
		print("starting the program for blocking and freeing the calendars")
		units = self.sf.grabAllActiveMainUnits() # one SF API CALL
		for unit in units:
			ruPropertyId = self.getUnitPropertyId(unit) # one API call x units.len()
			print(ruPropertyId)
			#self.freeAllCalendar(ruPropertyId) 
			self.fixCalendarForOneUnit(ruPropertyId)


class Email:

	def __init__(self):
		self.server = smtplib.SMTP('smtp.gmail.com: 587')
		self.server.ehlo()
		self.server.starttls()
		self.server.login("moe@evonifyllc.com", "Mohammed@Elkhatib1995")

	def sendEmail(self,subject,msg):
		try:
			message = 'Subject: {}\n\n{}'.format(subject, msg)
			self.server.sendmail('moe@evonifyllc.com','moe@evonifyllc.com',message)
			print("email has been sent")
			self.server.quit()
		except Exception as e:
			print("email couldn't be send due to an error")
			print(e)




