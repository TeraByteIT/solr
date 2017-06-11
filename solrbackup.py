#!/usr/bin/env python

#########################################################################
# Author	: Marcus Dempsey
# Date  	: 05/06/2017
# Dependency: Need to install the following before running the script:
#				* pip install boto
#				* pip install requests
#########################################################################

# import requirements
import os
import requests
import sys
import argparse
import time
import boto
from datetime import datetime
from boto.s3.key import Key
from boto.s3.connection import S3Connection

def backup_solr_to_s3(argv):
	solr_url       = ""			# Solr "http://localhost:8983/solr/"
	backup_dir     = ""			# The location where you want the backup to be placed"
	bucket_name    = ""			# S3 bucket name to store backup files
	core_name      = ""			# Name of the core to back up
	AWS_ACCESS_KEY = ""			# AWS access key
	AWS_SECRET_KEY = ""			# AWS secret key
	backup_qty     = ""			# How many copies of the backup to you want to keep on the machine
	W              = '\033[0m'	# white (normal)
	B              = '\033[34m'	# blue
	R              = '\033[31m'	# red
	G              = '\033[32m'	# green
	MAX_SIZE       = 20 * 1000 * 1000  # max size in bytes before uploading in parts. between 1 and 5 GB recommended
	PART_SIZE      = 6 * 1000 * 1000   # size of parts when uploading in parts

	parser = argparse.ArgumentParser()
	parser.add_argument("-u","--url", help="The URL of Solr e.g. http://localhost:8983/solr/", required=True)
	parser.add_argument("-d","--dir", help="The location where you want the backup to be placed - /home/centos/", required=True)
	parser.add_argument("-b","--bucket", help="The S3 bucket to upload the backups to (must exist)", required=True)
	parser.add_argument("-c","--corename", help="Name of the solr core to backup", required=True)
	parser.add_argument("-a","--accesskey", help="The AWS access key to connect to the S3 bucket", required=True)
	parser.add_argument("-s","--secretkey", help="The AWS secret key to connect to the S3 bucket", required=True)
	parser.add_argument("-n","--number", help="How many copies of the backups do you want to keep", required=True)
	args = parser.parse_args()
	core_name = args.corename
	solr_url = args.url + core_name
	backup_dir = args.dir
	backup_qty = args.number
	bucket_name = args.bucket
	AWS_ACCESS_KEY = args.accesskey
	AWS_SECRET_KEY = args.secretkey

	# set backup name
	backup_name = "solr-backup-" + core_name + "-" + datetime.now().strftime("%Y%M%d%H%M")
	# Call the Solr Backup API
	url = solr_url + "/replication?command=backup&location=" + backup_dir + "&name=" + backup_name + "&wt=json" + "&numberToKeep=" + backup_qty
	try:
		print (G + '[*]' +W + ' Starting backup of the Solr core:' + core_name)
		print (B + '[?]' +W + ' Backing up to: ' + backup_dir + backup_name + ".tar.gz")
		print (B + '[?]' +W + ' URL called: ' + url)
		res = requests.get(url)
	except:
		print(R + '[!]' +W + ' The URL: ' + url + ' is invalid' + W)
		sys.exit(2)

	try:
		print (G + '[*]' +W + ' Waiting 15 minutes for Solr snapshot to complete...')
		### TO DO: Monitor the backup details url and wait until the snapshot is complete - will be cleaner ###
		# this sleep is here to allow the solr snapshot to complete so we have a complete tar file.  If data is small, this time can be reduced
		time.sleep(900)
		# tar up the file ready to upload
		tar_file_name = backup_dir + "snapshot." + backup_name
		backup_name = backup_name + ".tar.gz"
		cmd = "tar -czvf " + backup_dir + backup_name + " " + tar_file_name
		print (G + '[*]' +W + ' Compressing snapshot data to: ' + backup_dir + backup_name)
		os.system(cmd)
	except:
		print (R + '[!]' +W +' There was an error executing: ' + cmd + W)
		sys.exit(2)

	# Create S3 connection and upload the backup
	print (B + '[?]' +W + " Attempting to establish connection to Amazon S3...")
	conn = boto.connect_s3(AWS_ACCESS_KEY,AWS_SECRET_KEY)
	bucket = conn.get_bucket(bucket_name)
	tar_file_name = backup_dir + backup_name
	print (G + '[*]' +W + ' Uploading %s to Amazon S3 %s' % (tar_file_name, bucket_name))
	def percent_cb(complete, total):
		sys.stdout.write('.')
		sys.stdout.flush()
	filesize = os.path.getsize(tar_file_name)
	if filesize > MAX_SIZE:
	        mp = bucket.initiate_multipart_upload(bucket_name)
        	fp = open(tar_file_name,'rb')
        	fp_num = 0
        	while (fp.tell() < filesize):
			fp_num += 1
			mp.upload_part_from_file(fp, fp_num, cb=percent_cb, num_cb=10, size=PART_SIZE)
        	mp.complete_upload()
		print (G + '[*]' +W + ' Upload complete.' + W)
	else:
		k = boto.s3.key.Key(bucket_name)
		k.key = bucket_name
		k.set_contents_from_filename(tar_file_name, cb=percent_cb, num_cb=10)

	# Find out the status of last backup
	status_url = solr_url = "replication?command=details&wt=json"

if __name__ == '__main__':
	backup_solr_to_s3(sys.argv[1:])
