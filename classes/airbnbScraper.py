from . import *


class airbnbScraper:

	def __init__(self):
		self.downloadPath = "/Users/moeroddy/Desktop/programs/evn/airbnbDownloads"
		self.emailPath1 = '//*[@id="site-content"]/div/div/div[2]/div/div/div[15]/div[1]/div[1]/div/div/div/span'
		self.emailPath2 = '//*[@id="site-content"]/div/div/div/div[2]/div[16]/div[1]/div[1]/div/div/div/span'
		self.driver = None
		self.email = "customerservice@evonifyllc.com"
		self.password = "Moh*@Moh1995"


	def setupDriverMac(self):
		options = Options()
		options.add_argument("user-data-dir=/tmp/tarun")
		prefs = {"download.default_directory" : self.downloadPath}
		options.add_experimental_option("prefs",prefs)
		self.driver = webdriver.Chrome('/Users/moeroddy/desktop/programs/ruSync/chromedriver', chrome_options=options)

	def setupDriverServer(self):
		self.downloadPath = "/home/moe/Desktop/airbnbSfSync/airbnbDownloads"
		options = Options()
		options.binary_location = '/usr/bin/chromium-browser'
		options.headless = True
		options.add_argument('--user-data-dir=/home/moe/.config/chromium')
		prefs = {"download.default_directory" : self.downloadPath}
		options.add_experimental_option("prefs", prefs)
		self.driver = webdriver.Chrome('/home/moe/Desktop/airbnbSfSync/chromedriver', chrome_options=options)



	def startScraping(self, page, i):
		print("starting to scrape")
		if i==0:
			self.setupDriverMac()
		elif i==1:
			self.setupDriverServer()

		self.enterLoginInfo()
		self.downloadReservations(page)
		pathOfNewFile = self.changeFileName()
		sheetObject = csvFile(pathOfNewFile)
		return sheetObject.reservationsDict


	def endScraping(self):
		print("ending scraper program")
		self.exitBrowser()


	def enterLoginInfo(self):
		try:
			self.driver.get('https://www.airbnb.com/login/')
			username = self.driver.find_element_by_name("email")
			username.send_keys(self.email)
			time.sleep(1)
			password = self.driver.find_element_by_name("password")
			password.send_keys(self.password)
			time.sleep(1)
			self.driver.get_screenshot_as_file("capture.png")
			time.sleep(2)
			password.send_keys(Keys.RETURN);
			time.sleep(10)
			self.driver.get_screenshot_as_file("capture22.png")

		except Exception as e:
			print("couldn't enter username or password due to an error or page is already logged in")
			print(e)

	def downloadReservations(self, page):
		try:
			self.driver.get("https://www.airbnb.com/hosting/reservations/export.csv?sort_field=status&sort_order=asc&tab=upcoming&page=" + page)
			time.sleep(4)
			self.driver.get_screenshot_as_file("capture1.png")
			print("file has been downloaded")

		except Exception as e:
			print("file couldn't download due to an error")
			print(e)

	def changeFileName(self):
		try:
			list_of_files = glob.glob(self.downloadPath + "/*") # * means all if need specific format then *.csv
			latest_file = max(list_of_files, key=os.path.getctime)
			print (latest_file)
			newfile = self.downloadPath + "/" + datetime.date.today().strftime("%Y-%m-%d") + ".csv"
			os.rename(latest_file, newfile)
			print("file has been renamed")
			return newfile

		except Exception as e:
			print("file couldn't be renamed due to an error")
			print(e)

	def findEmail(self, code):
		#self.driver.get("https://www.airbnb.com/hosting/reservations/details/" + code)
		self.driver.get("https://www.airbnb.com/messaging/qt_for_reservation/" + code)
		time.sleep(5)
		print(code)
		try:
			temp = self.driver.find_element_by_css_selector('span._1jlnvra2')
			print(temp.text)
			return temp.text
		except Exception as e:
			print(e)
			try:
				print("trying again")
				temp = self.driver.find_element_by_xpath(self.emailPath1)
				print(temp.text)
				return temp.text
			except Exception as e:
				print("second try failed")
				print(e)

	def addAllEmails(self, sheetObject):
		try:
			for reservation in sheetObject.reservationsDict:
				email = ""
				email = self.findEmail(reservation['Confirmation code'])
				reservation.update({'Email':email})

			print("ALL EMAILS RETRIEVED")

		except Exception as e:
			print("couldn't retrieve emails due to an error")
			print(e)

	def exitBrowser(self):
		self.driver.quit()
