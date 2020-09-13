# LoBUCS
A load balancing framework using Amazon cloud services.
Create AWS account and register for amazon services- EC2 , S3 , SQS , DynamoDB.
Acqiure AWS access key and save the credentials for configuration purposes.
Follow the setup folder and follow the execution code. architecture.jpg shows the command flow.

With LoBUCS achieved efficient job
distribution driven by Client-Worker environment. This
was done by balancing the workload and using
parallel processing for utilizing the computation power of
workers.

To establish this efficiency, we dynamically generated
workers depending on the requirement of the workload.
Similarly, the framework dynamically discarded workers
created for a previous larger job that would not be required
for smaller jobs, thus maintaining efficiency in resource
utilization. With this framework we developed an application and hosted it on the Amazon Cloud
Servers that could accept images, videos and music clips
as inputs and create a video slideshow as output on
identifying these inputs. 

