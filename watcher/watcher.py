
# coding: utf-8

# In[19]:

import ConfigParser
import boto
import boto.sqs
import boto.ec2
import time
import boto.s3.connection
import shutil
import os


# In[ ]:

"""
reads and downloads config files from s3
"""
#read config file
def read_config_file(file_name):
    config = ConfigParser.RawConfigParser()
    config.read(file_name)
    return config

def dowload_config_file(directory):
    if os.path.exists(directory):
        shutil.rmtree(directory)
    os.makedirs(directory)
    #get conf file info and s3 name
    config = read_config_file('/home/ec2-user/aws/aws.cfg')
    #get connection
    conn = boto.connect_s3(
        aws_access_key_id= config.get('AWS_CRED','AWS_ACCESS_KEY_ID'),
        aws_secret_access_key = config.get('AWS_CRED','AWS_SECRECT_ACCESS_KEY')
        )
    #read from S3
    s3obj = conn.get_bucket(config.get('AWS_CRED','BUCKET_NAME'))
    if s3obj:
        key = s3obj.get_key(config.get('AWS_CRED','FILE_NAME'))
        key.get_contents_to_filename(directory+'/'+config.get('AWS_CRED','FILE_NAME'))


# In[ ]:

dowload_config_file('/home/ec2-user/config/')


# In[18]:

#read config file
def read_config_file(file_name):
    config = ConfigParser.RawConfigParser()
    config.read(file_name)
    return config


# In[16]:

config = read_config_file('/home/ec2-user/config/config.cfg')


# In[4]:

connsqs = boto.sqs.connect_to_region( config.get('AWS_CRED','REGION'),
                                   aws_access_key_id= config.get('AWS_CRED','AWS_ACCESS_KEY_ID'),
                                   aws_secret_access_key=config.get('AWS_CRED','AWS_SECRECT_ACCESS_KEY'))


# In[5]:

conn = boto.ec2.connect_to_region(config.get('AWS_CRED','REGION'),
                                  aws_access_key_id= config.get('AWS_CRED','AWS_ACCESS_KEY_ID'),
                                  aws_secret_access_key=config.get('AWS_CRED','AWS_SECRECT_ACCESS_KEY'))


# In[6]:

def sqs_size():
    queue = connsqs.get_queue(config.get('WATCHER','QUEUE_NAME'))
    return queue.count()


# In[9]:

def get_instances():    
    reservations = conn.get_all_reservations(filters={'instance-state-name' : 'running','instance_type':'m3.medium'})
    return reservations


# In[10]:

def get_number_of_instances():
    return len(get_instances())


# In[11]:

def launch_instance():
    start_worker_code = """#!/bin/sh
    python /home/ec2-user/worker/worker.py
    """
    conn.run_instances(config.get('WORKER','IMAGE_ID'),
        key_name=  config.get('AWS_CRED','KEY_NAME'),
        instance_type= config.get('WORKER','INSTANCE_TYPE'),
        security_groups= [config.get('WORKER','SEQURITY_GROUP_NAME')],
        user_data = start_worker_code
        )


# In[12]:

def stop_instance():
    instances = [i for r in get_instances() for i in r.instances]
    if instances and len(instances) > 1:
        conn.terminate_instances(instance_ids=[str(instances[0]).split(':')[1]])


# In[122]:

while(True):
    if get_number_of_instances() < int(config.get('WATCHER','MIN_SIZE')):
        launch_instance()
    elif get_number_of_instances() > int(config.get('WATCHER','MAX_SIZE')):
        stop_instance()
    elif int(config.get('WATCHER','AUTO_SCALE')) == 0 and sqs_size() > int(config.get('WATCHER','THRESHOLD')) and get_number_of_instances() < int(config.get('WATCHER','MAX_SIZE')):
        launch_instance()
    elif int(config.get('WATCHER','AUTO_SCALE')) == 0 and sqs_size() < int(config.get('WATCHER','THRESHOLD')) and get_number_of_instances() > int(config.get('WATCHER','MIN_SIZE')):
        stop_instance()
    time.sleep(int(config.get('WATCHER','FREEZE_TIME')))

