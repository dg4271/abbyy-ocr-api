#!/usr/bin/python

# Usage: process.py <input file> <output file> [-l <Language>] [-pdf|-txt|-rtf|-docx|-xml]

import os
import time

from abbyy.AbbyyOnlineSdk import *


def resultFilePath(file_name, result_path, output_format):
	return os.path.join(result_path, file_name.rsplit('.', 1)[0] + '.' + output_format)

# Recognize a pdf file and return result to xml
def api(processor, pdfFile, file_name, result_path, language='English', output_format='xml'):
	print("Uploading..")
	settings = ProcessingSettings()
	settings.Language = language
	settings.OutputFormat = output_format
	#task = processor.process_image(file_path, settings)
	task = processor.process_image_file(pdfFile, settings)
	if task is None:
		print("Error")
		return
	if task.Status == "NotEnoughCredits":
		print("Not enough credits to process the document. Please add more pages to your application's account.")
		return

	print("Id = {}".format(task.Id))
	print("Status = {}".format(task.Status))

	# Wait for the task to be completed
	print("Waiting..")
	# Note: it's recommended that your application waits at least 2 seconds
	# before making the first getTaskStatus request and also between such requests
	# for the same task. Making requests more often will not improve your
	# application performance.
	# Note: if your application queues several files and waits for them
	# it's recommended that you use listFinishedTasks instead (which is described
	# at https://ocrsdk.com/documentation/apireference/listFinishedTasks/).

	while task.is_active():
		time.sleep(5)
		print(".")
		task = processor.get_task_status(task)

	print("Status = {}".format(task.Status))

	if task.Status == "Completed":
		if task.DownloadUrl is not None:
			# file download
			xmlFilePath = resultFilePath(file_name, result_path, output_format)
			print("OCR xml saved at {}".format(xmlFilePath))
			processor.download_result(task, xmlFilePath)
			xml_string = ''
			with open(xmlFilePath, 'r') as file:
				xml_string = file.read()
			print("Result was written")
			return xml_string
			
	else:
		print("Error processing task")