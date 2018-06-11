#!/usr/bin/env python
import ConfigParser
import logging
import boto.sqs
from boto.sqs.message import Message
import boto.dynamodb
from boto.s3.connection import S3Connection
import time
import shutil
import os
from boto.s3.key import Key

class Worker:
    def __init__(self):
        self.config = ConfigParser.RawConfigParser()   
        self.config.read('../configs/worker.cfg')
        logging.basicConfig(filename='../logs/worker.log',level=logging.DEBUG)
    
    def fetch_job_from_sqs(self):
        rs = self.sqsObj.get_messages()
        if rs and rs[0]:
            message = rs[0]
            message = message.get_body()
            message = message.split('|')
            if len(message) < 2:
                return False
            self.customer_id = message[0]
            self.job = message[1:]
            self.message = rs[0]
            return True
        return False
    
    def check_item_exists(self):
        """Checks whether an item exists in DynamoDB or Not
        """
        try:
            item = self.dynamoObj.get_item(
            hash_key = self.customer_id)
            return item
        except:
            return None
    
    def remove_job_from_sqs(self):
        self.sqsObj.delete_message(self.message)
        return True
    
    def update_count_by_1(self):
        item = self.check_item_exists()
        if item:
            item['try_count'] = item['try_count']+1
            item.put()
        
    def is_job_already_taken(self):
        item = self.check_item_exists()
        if item and (item['job_stats'] == 'P' and item['try_count'] <3 ):
            self.update_count_by_1()
            return True
        return False
    
    def validate_job(self):
        return True
    
    def download_files_from_s3(self,s3obj):
        directory = './'+self.customer_id+'/'
        if os.path.exists(directory):
            shutil.rmtree(directory)
        os.makedirs(directory) 
        for key in s3obj.list():
            key.get_contents_to_filename(directory+'/'+key.name)
            
    def put_video_to_s3(self,s3obj):
        k = Key(s3obj)
        k.key = 'myvideo.mpeg'
        filename = './'+self.customer_id+'/'+'out.mpeg'
        k.set_contents_from_filename(filename)
        
        shutil.rmtree('./'+self.customer_id+'/')
        return True
    
    def process_downloaded_files(self):
        directory = './'+self.customer_id+'/'
        cmd = 'convert '+directory+'*.jpg -delay 50 -morph 10 '+ directory+'out.mpeg'
        ret = os.system(cmd)
        return ret
            
    
    def process_video_job(self,bucket_name):
        s3obj = self.create_s3_connection(self.config.get('AWS_CRED','AWS_ACCESS_KEY_ID'),
                                   self.config.get('AWS_CRED','AWS_SECRECT_ACCESS_KEY'),
                                   bucket_name
                                   )
        if s3obj:
            logging.info("connected to %s S3 bucket"%(bucket_name))
            self.download_files_from_s3(s3obj)
            if self.process_downloaded_files() ==0:
                self.put_video_to_s3(s3obj)
                logging.info("video now available in %s bucket"%(bucket_name))
                return True
            
        else:
            logging.error("Unable to connect to %s S3 bucket"%(bucket_name))
        
        return False
        
    def process_job(self):
        for job in self.job:
            t = job.strip().split()
            if len(t) == 2:#sleep job
                logging.debug('Sleeping for %d seconds'%(int(t[1])))
                time.sleep(int(t[1]))
            elif len(t) == 1:#video  job
                logging.debug('Started video  job')
                self.process_video_job(job)
            else:
                return False
        return True
    
    def change_job_status(self,status):
        item = self.check_item_exists()
        if item:
            item['job_stats'] = status
            item.put()
            return True
        
        return False
    
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
                return None
        else:
            logging.error('unable to make connection to aws')
            return None
    
    def create_s3_connection(self,access_key_id,secret_access_key,bucket_name):
        conn = S3Connection(access_key_id,secret_access_key)
        if conn:
            s3obj = conn.get_bucket(bucket_name)
            if s3obj:
               logging.info('returning %s s3Obj '%(bucket_name))
               return s3obj
            else:
                logging.error('unable to create %s s3Obj '%(bucket_name))
                return None
        else:
            logging.error('unable to make connection to aws')
            return None
        
    def start_process(self):
        self.sqsObj = self.create_sqs_connection(self.config.get('AWS_CRED','REGION'),
                                   self.config.get('AWS_CRED','AWS_ACCESS_KEY_ID'),
                                   self.config.get('AWS_CRED','AWS_SECRECT_ACCESS_KEY'),
                                   self.config.get('SQS','QUEUE_NAME')
                                   )
        self.dynamoObj = self.create_dynamo_db_connection(self.config.get('AWS_CRED','REGION'),
                                   self.config.get('AWS_CRED','AWS_ACCESS_KEY_ID'),
                                   self.config.get('AWS_CRED','AWS_SECRECT_ACCESS_KEY'),
                                   self.config.get('DYNAMODB','TABLE_NAME')
                                   )
        
        if not self.sqsObj or not self.dynamoObj:
            print self.dynamoObj
            logging.error('unable to make connection to sqs or dynamoDB')
            return False
        
        while(True):
            if self.fetch_job_from_sqs() and not self.is_job_already_taken():
                self.change_job_status('P')
                if self.process_job():
                    self.change_job_status('F')
                else:
                    self.change_job_status('E')
                    
                self.remove_job_from_sqs()



if __name__ == "__main__":
    worker = Worker()
    worker.start_process()
