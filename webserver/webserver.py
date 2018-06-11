#!/usr/bin/env python
import ConfigParser
import logging
from flask import Flask
import boto.sqs
from boto.sqs.message import Message
from flask import Flask
from flask import request
from flask import render_template
import boto.dynamodb
import shutil
import os

class Helper():
    def __init__(self):
        self.config = ConfigParser.RawConfigParser()   
        self.config.read('../config/config.cfg')
        logging.basicConfig(filename='../logs/server.log',level=logging.DEBUG)
    
        
    def create_sqs_connection(self,region,access_key_id,secret_access_key,queue_name):
        """Create connection object to sqs 
        Args:
            region: aws region where sqs is present
            aws_access_key_id,aws_secret_access_key : credentials to make connection
            queue_name: name of the queue
        """
        conn = boto.sqs.connect_to_region(region,
                                      aws_access_key_id= access_key_id,
                                      aws_secret_access_key= secret_access_key
                                      )
        if conn:
            queue_obj = conn.get_queue(queue_name)
            if queue_obj:
                logging.info('returning %s queueobject '%(queue_name))
                return queue_obj
            else:
                logging.error('unable to get %s queue '%(queue_name))
                return None
        else:
            logging.error('unable to make connection to aws')
            return None
    
    def create_dynamo_db_connection(self,region,access_key_id,secret_access_key,table_name):
        """
        Used to get table Object
        Args:
            region: aws region where sqs is present
            aws_access_key_id,aws_secret_access_key : credentials to make connection
            table_name: name of the table
        """
        conn = boto.dynamodb.connect_to_region(region,
                                                aws_access_key_id=access_key_id,
                                                aws_secret_access_key=secret_access_key
                                                )
        if conn:
            tableObj = conn.get_table(table_name)
            if tableObj:
                logging.info('returning %s tableObj '%(table_name))
                return tableObj
            else:
                logging.error('unable to create %s tableObj '%(table_name))
        else:
            logging.error('unable to make connection to aws')
            return None
    
    def check_item_exists(self,customer_id):
        """Checks whether an item exists in DynamoDB or Not
        """
        try:
            item = self.dynamoDB_obj.get_item(
            hash_key=customer_id)
            return item
        except:
            return None
        
    def add_to_dynamoDB(self,customer_id,job_status):
        """Adds the job details in dynamodb
        Args:
            customer_id: Primary key
            job_status: 'C' in case job is created
        """
        #check if JOB exists
        item = self.check_item_exists(customer_id)
        if item and (item['job_stats'] == 'C' or item['job_stats'] == 'P') : #if job stats is created or in progress
            logging.error('you have a pending JOB you cannot add now please try later')
            return False
            
        data ={'job_stats':job_status,'try_count':0}
        item = self.dynamoDB_obj.new_item(
            hash_key = customer_id,
            attrs= data
        )
        item.put()
        logging.info('added customer to  dynamodb with id %s'%(customer_id))
        return True
        
    def add_to_sqs_queue(self,customer_id,message):
        """Adds a message to SQS
        Args:
            message: Message to be added
        """
        m = Message()
        m.set_body(customer_id+"|"+message)
        self.request_q_obj.write(m)
        return True
    
    def initalize_server(self):
        """
        Initialize server objects like , request queue obj,
        dynamo db obj etc
        """
        self.request_q_obj = self.create_sqs_connection(self.config.get('AWS_CRED','REGION'),
                                   self.config.get('AWS_CRED','AWS_ACCESS_KEY_ID'),
                                   self.config.get('AWS_CRED','AWS_SECRECT_ACCESS_KEY'),
                                   self.config.get('SQS','QUEUE_NAME')
                                   )
        self.dynamoDB_obj = self.create_dynamo_db_connection(self.config.get('AWS_CRED','REGION'),
                                   self.config.get('AWS_CRED','AWS_ACCESS_KEY_ID'),
                                   self.config.get('AWS_CRED','AWS_SECRECT_ACCESS_KEY'),
                                   self.config.get('DYNAMODB','TABLE_NAME')
                                   )
        if self.request_q_obj and self.dynamoDB_obj:
            return True
            
        return False
    
    def validate_input(self,customer_id,job_desc):
        return True
    
    def process_input(self,customer_id,job_desc):
        logging.info("processing input")
        if self.validate_input:
            stat = self.add_to_sqs_queue(customer_id,job_desc)
            stat = self.add_to_dynamoDB(customer_id,'C')
            return stat
        return False 
        
    def check_status(self,customer_id):
        """Checks Status of submitted job
        Args:
            customer_id: Id of customer
        """
        message = ''
        item = self.check_item_exists(customer_id)
        if item:
            logging.info('item exists')
            job_status = item['job_stats']
            if job_status=='C':
                message = 'Job Created'
            elif job_status == 'P':
                message = 'Job in progress'
            elif job_status == 'F':
                message = 'Job completed'
            elif job_status == 'E':
                message = 'Error occured'
        else:
            logging.error('item does not exists')
            message = 'Job does not exists'
            
        return message
    
    def start_process(self):
        """starts the server if all configurations
        are set properly
        """
        logging.info('starting server')
        if not self.initalize_server():
            logging.error('unable to start server due to some error')
            self.server_start = False
        
        self.server_start =True
            
        

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
    config = read_config_file('../aws/aws.cfg')
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

#		
#download_config_file('../config')

app = Flask('server')
#used to load and configure itself
h = Helper()
h.start_process()

@app.route('/')
def home_page():
    return render_template('index.html')

@app.route('/makevideo')
def make_video():
    message = ''
    customer_id = request.args.get('customerId', None)
    job_desc = request.args.get('jobDesc',None)
    if customer_id and job_desc:
        stat = h.process_input(customer_id,job_desc)
        if stat:
            message = 'Job submitted successfully'
        else:
            message = 'Job submission failed'
    return render_template('JobRequest.html',message=message)  

@app.route('/checkstatus')
def check_stats():
    message = ''
    customer_id = request.args.get('customerId', None)
    job_desc = request.args.get('jobDesc',None)
    if customer_id:
        message = h.check_status(customer_id)
    
    return render_template('jobResponce.html',message=message ,job_desc=job_desc)
	
	
if __name__ == "__main__":
    if h.server_start:
        print 'Server started!'
        app.run(host='localhost',port=8083)
    