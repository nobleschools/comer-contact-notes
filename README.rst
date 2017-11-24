Comer Contact Notes
===================

Processes Salesforce Contact Note data from Comer, to

  * create new Contact Notes at Noble
  * save a report of the Comer Contact Notes with the corresponding Noble SF ID

Currently set up to run on Lambda in response to the file Put on S3; after
sending the Comer file to S3, retrieve report from Comer bucket (TODO: send
out report automatically).

Lambda
------
  * src/lambda_function.py
  * triggered to run on S3 Put
  * report saved to S3 bucket
  * create_deploy.sh creates the zip file ready for lambda

Local interface
---------------
  * cli.py
  * report saved to working dir
