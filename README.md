# etl-airflow-docker

Welcome to this ETL project where we make used of airflow, docker, python and the most used cloud provider; aws.

To execute the ETL proccess in a property way we have to use a aws console account and create a S3 bucket with a aws user.

Please make sure to follow all the steps to succesfully be able to run this ETL.

## Create a S3 bucket into AWS.

Create a S3 bucket and call it as you want.

![Screen Shot 2022-10-17 at 9 52 17 AM](https://user-images.githubusercontent.com/81943031/196210435-ee390657-cce2-489a-adc4-f589cb484618.png)

## Structure of S3 bucket

This is an important part, as I follow a specific folder structure in python scripts. Define the structure as follow:


    -- datasets/

            -- cines/
            
            -- bibliotecas/
            
            -- museos/

In other words, create the datasets folder into the S3 bucket, and then create cines, bibliotecas, museos folders into datasets.

<img width="432" alt="Screen Shot 2022-10-17 at 9 58 51 AM" src="https://user-images.githubusercontent.com/81943031/196211886-7ccf341e-fae3-4d96-8295-2029f943a4e7.png">


## S3 IAM user

In order to be able to interact with the S3 bucket, we have to create an user (or use an existing one).

<img width="1038" alt="new user" src="https://user-images.githubusercontent.com/81943031/193344008-976ea65d-e611-4b8a-8477-b62d8a40d455.png">

### Permissions for the user

Since we have many services and specific permissions to interact with them, we have to assign the S3 permission to the new user.

<img width="1008" alt="permission" src="https://user-images.githubusercontent.com/81943031/193344085-a6d6aacf-ab3d-4564-ac55-a7f782f86b40.png">

## Credentials

This is a very important step. You have to make sure of copy and save the credentials because we will use them later.

<img width="982" alt="credentials" src="https://user-images.githubusercontent.com/81943031/193344520-98a07a83-9ef9-4397-baa4-1cd55c6950a2.png">
 
## Create .env file

To use credentials, which are sensitive information, create an .env file with the following env variables. 

If you see files in this repository, you will find a file called .env; you have to write there all the information related to the user IAM(credentials) 
and the bucket(region and bucket name)

pdt: Do not share credentials with anyone.

![Screen Shot 2022-10-17 at 10 01 24 AM](https://user-images.githubusercontent.com/81943031/196213495-4b5856de-1eff-452d-b659-c0a42c8cad1e.png)

# Install requirements.

Before running Python scripts or even interacting with the project. We must first install the
required dependencies

pd: Make sure to be in the parent folder and run the following command,

__pip install -r requirements.txt__

With all dependencies ready, we can continue with the most interesting things!!!

# Use dag template and .yaml files

Now that we have ready the parameters to interact with aws, we'll continue executing a file into the path __plugins/dynamic_dags/dag_generator.py__.

This file will use the dags template and render the variables defined in the .yaml files to create python scripts that contains diferent configurations 
based on the data that will be processed.

When we execute the file, these python scripts will appear in the dags folder.

<img width="282" alt="Screen Shot 2022-10-17 at 10 14 01 AM" src="https://user-images.githubusercontent.com/81943031/196215640-2d008b7b-85bf-4e7d-a620-53971f5297c8.png">

# Run Container

In order to run the airflow image, we have to write the following commands.

pd: make sure you are in the parent_folder.

__docker compose up airflow-init__

After run this, we will write the second command

__docker compose up__

This will run the airflow image.

# AIRFLOW WebServer

To interact with the create dags, enter to http://localhost:8080 . You can create an user or used the user define by default 

username: airflow

password: airflow

there you'll see the dags and you we'll able to run them.

Depends on the execution date, it's probably that dags will execute automatically or not.

If you want to run dags manually, just click on the run icon and then on trigger DAG.

<img width="1413" alt="Screen Shot 2022-10-17 at 10 30 01 AM" src="https://user-images.githubusercontent.com/81943031/196219894-2189c3b8-70a1-4143-8327-17a10fa0851f.png">

If everything is okay, you can go to the S3 bucket and find the cleaned files.
