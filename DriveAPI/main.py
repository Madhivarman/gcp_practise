from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import io
from apiclient import errors
from apiclient.http import MediaIoBaseDownload
from oauth2client.service_account import ServiceAccountCredentials
import gspread
import pandas as pd
import numpy as np

class DriveClient(object):

	#initial class
	def __init__(self):
		self.SCOPES = ['https://www.googleapis.com/auth/drive.readonly',
		'https://spreadsheets.google.com/feeds',
		'https://www.googleapis.com/auth/drive']
		self.creds = None

		if os.path.exists('token.pickle'):
			with open('token.pickle', 'rb') as token:
				self.creds = pickle.load(token)

		#if there are no user token, let google create a new token for the first time
		if not self.creds or not self.creds.valid:
			if self.creds and self.creds.expired and self.creds.refresh_token:
				self.creds.refresh(Request())
			else:
				flow = InstalledAppFlow.from_client_secrets_file(
					'credentials.json', self.SCOPES)
				self.creds = flow.run_local_server()

			#save the credentials for next run
			with open('token.pickle', 'wb') as token:
				pickle.dump(self.creds, token)


		self.service = build('drive', 'v3', credentials=self.creds)
		self.sheetService = build('sheets', 'v4', credentials=self.creds)

	"""search if the folder is present in the drive"""
	def search(self, query_str):
		page_token = None 
		while True:
			response = self.service.files().list(
				q = query_str,
				spaces='drive',
				fields = 'nextPageToken, files(id, name)',
				pageToken=page_token
			).execute()

			for file in response.get('files', []):
				name = file.get('name')
				file_id = file.get('id')

				print("Folder Name:{}".format(name))
				print("Folder Id:{}".format(file_id))

				return name, file_id

			page_token = response.get('nextPageToken', None)

			if page_token is None:
				break


	def get_files_in_folder(self, folderid):

		v2_service = build('drive', 'v2', credentials=self.creds)
		get_all_links = [] #to store all links
		page_token = None
		while True:
			try:
				param = {}
				if page_token:
					param['pageToken'] = page_token

				children = v2_service.children().list(folderId=folderid).execute()

				for child in children.get('items', []):
					get_all_links.append(child)

				page_token = children.get('nextPageToken')

				if not page_token:
					break

			except errors.HttpError as error:
				print("An Error Occured:{}".format(error))
				break

		return get_all_links


	def read_sheet(self, filename, fileId):
		credentials = ServiceAccountCredentials.from_json_keyfile_name('GCP-DE-EXP-2c2689c0c14a.json', self.SCOPES)
		gc = gspread.authorize(credentials)
		
		#split the sheet name
		sheetname = filename.split(".")[0]
		opensheets = gc.copy(fileId)
		allsheets =  opensheets.worksheets()

		concatdf = pd.DataFrame() #create an empty dataframe

		for num, sheets in enumerate(allsheets):
			records = opensheets.get_worksheet(num)
			aslist = records.get_all_values()

			if num == 0:
				candidate = aslist[5]
				name, reporting_to = candidate[1], candidate[6] 

			onlyRecords = aslist[6:19]
			
			df = pd.DataFrame(onlyRecords)

			concatdf = pd.concat([concatdf, df], axis=0)

		#remove columns where it is null
		concatdf = concatdf.dropna(axis=1, how='all')
		concatdf = concatdf.reset_index()

		return concatdf, name, reporting_to



drive_client = DriveClient()