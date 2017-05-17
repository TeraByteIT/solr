#!/usr/bin/env python

#####
# Author: Marcus Dempsey
# Date  : 17/05/2017
# Dependency: Need to install the following before running the script:
#				pip install boto
#				pip install requests
######

# import requirements
import os
import requests
import sys
import argparse
from datetime import datetime
from boto.s3.key import Key
from boto.s3.connection import S3Connection

def backup_solr_to_s3(argv):
	solr_url       = "" 		# Solr "http://localhost:8983/solr/"
	backup_dir     = ""			# Solr backup directory "/opt/solr/backup"
	bucket_name    = ""			# S3 bucket name to store backup files
	AWS_ACCESS_KEY = ""			# AWS access key
	AWS_SECRET     = ""			# AWS secret key
	W              = '\033[0m'	# white (normal)
	B              = "\033[34m" # blue
	R              = '\033[31m'	# red
	G              = '\033[32m'	# green

	parser = argparse.ArgumentParser()
	parser.add_argument("-u","--url", help="The URL of Solr e.g. http://localhost:8983/solr/", required=True)
	parser.add_argument("-d","--dir", help="The Solr backup directory e.g. /opt/solr/backup/", required=True)
	parser.add_argument("-b","--bucket", help="The S3 bucket to upload the backups to", required=True)
	parser.add_argument("-a","--accesskey", help="The AWS access key to connect to the S3 bucket", required=True)
	parser.add_argument("-s","--secretkey", help="The AWS secret key to connect to the S3 bucket", required=True)
	args = parser.parse_args()
	solr_url = args.url
	backup_dir = args.dir
	bucket_name = args.bucket
	AWS_ACCESS_KEY = args.accesskey
	AWS_ACCESS_KEY = args.secretkey

	# set backup name
	backup_name = "solr-backup-" + datetime.now().strftime("%Y-%M-%d-%H-%M") + ".tar.gz"

	# Call the Solr Backup API
	url = solr_url + "replication?command=backup&location=" + backup_dir + "&name=" + backup_name + "&wt=json"
	try:
		print (G + '[*]' +W + ' Attempting backup of Solr')
		print (B + '[?]' +W + ' Backup Dir : ' + backup_dir)
		print (B + '[?]' +W + ' Backup Name: ' + backup_name)

		res = requests.get(url)
	except:
		print(R + '[!]' +W + ' The URL: ' + url + ' is invalid' + W)
		sys.exit(2)

	try:
		# tar up the file ready to upload
		tar_file_name = backup_dir + backup_name + ".tar.gz "
		cmd = "tar -cvzf " + tar_file_name + "-C " + backup_dir + backup_name + " " + backup_name
		os.system(cmd)
	except:
		print (R + '[!]' +W +' There was an error executing: ' + cmd + W)
		sys.exit(2)
	try:
		# Create S3 connection and upload the backup
		print (G + '[*]' +W + ' Uploading ' + s3_backup_file + ' to ' + bucket  + W)
		conn = S3Connection(AWS_ACCESS_KEY, AWS_SECRET)
		bucket = conn.get_bucket(bucket_name)
		s3_backup_file = Key(bucket)
		s3_backup_file.key = backup_name
		s3_backup_file.set_contents_from_file = (tar_file_name, {'Content-Type':'application/x-tar'})
		print (G + '[*]' +W + ' Upload complete.' + W)
	except:
		print (R + '[!]' +W +' There was an error backing up the file' + backup_name + ' to S3 location: ' + bucket + W)
		sys.exit(2)

	# Find out the status of last backup
	status_url = solr_url = "replication?command=details&wt=json"
	res = requests.get(status_url)
	output = res.json()
	try:
		print G + "Start Time       : ", output['details']['backup'][1] + W
		print G + "End Time         : ", output['details']['backup'][7] + W
		print G + "Backup Status    : ", output['details']['backup'][5] + W
		print G + "Backup File Count: ", output['details']['backup'][3] + W
		print G + "Backup Name      : ", output['details']['backup'][9] + W
	except:
		pass

if __name__ == '__main__':
	backup_solr_to_s3(sys.argv[1:])