# LoBUCS
A load balancing framework using Amazon cloud services.
Create AWS account and register for amazon services- EC2 , S3 , SQS , DynamoDB.
Acqiure AWS access key and save the credentials for configuration purposes.
Follow the setup folder and follow the execution code. architecture.jpg shows the command flow.

With LoBUCS we aim at achieving efficient job
distribution driven by Client-Worker environment. This
would be done by balancing the workload and using
parallel processing for utilizing the computation power of
workers.
To establish this efficiency, we will dynamically generate
workers depending on the requirement of the workload [1].
Similarly, the framework will dynamically discard workers
created for a previous larger job that would not be required
for smaller jobs, thus maintaining efficiency in resource
utilization. With the framework as proposed we will
develop an application to hosted on the Amazon Cloud
Servers that would accept images, videos and music clips
as inputs and create a video slideshow as output on
identifying these inputs. Then we will conduct a
corresponding comparison with speeds in existing
frameworks and determine the difference in performance
with respect to the speed and management of incoming
workload.
