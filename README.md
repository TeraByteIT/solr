# Solr backup
This is a simple Pytyon script that will backup your solr cloud cluster instance to Amazon S3.  

## Requirements
a) You need to ensure that you have configured the ReplicationHandler within the Solrconfig.xml before this will work, as it utilises the Solr backup command.

b) Python needs to be installed (only tested against 3.6 so far)

c) Need to install: 

    pip install boto

    pip install requests


## Running
You run the script by passing parameters, an example is:

  sudo ./solr_backup.py -u http://localhost:8080/solr/ -c core1 -b solr-dev-backup -d ~/ -n 6 -a XXXXXXX -s XXXXXX
  
 Running ./solr_backup.py will provide you with available paramteres and help text.
