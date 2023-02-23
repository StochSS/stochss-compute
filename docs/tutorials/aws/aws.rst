StochSS-Compute on AWS
======================

1. Install extra dependecies.

.. code-block:: bash

    python -m pip install 'stochss_compute[AWS]'
    # installs boto3, paramiko, and python-dotenv

2. Import necessary classes.

.. code-block:: python

    import gillespy2
    from stochss_compute.cloud import EC2Cluster
    from stochss_compute import RemoteSimulation

3. Launch an EC2 Instance. Make sure to check `instance_type` pricing before launching.

.. code-block:: python

    cluster = EC2Cluster()

    cluster.launch_single_node_instace('t2.micro')

4. Run a simulation.

.. code-block:: python

    simulation = RemoteSimulation(model, server=cluster, solver=gillespy2.TauHybridSolver)

    results = simulation.run()

    results.plot()

5. Clean up.

.. code-block:: python

    cluster.clean_up()


AWS Configuration
-----------------

1. Create an AWS account `here <https://aws.amazon.com/>`_ if you have not already done so.

2. In order to make the AWS API calls to your account, you need an AWS access key and access key ID.  
   
   From the IAM dashboard, click 'My security credentials'.  
   
   Then, under the Access keys tab, click 'Create Access Key'.  
   
   Make sure to record the Access and Secrety keys. We recommend you download the CSV file now, as it can only be downloaded once. if you lose these keys you can just make a new ones.  
   
   This file contains the Access Key ID and a Secret Access Key.

3. The simplest way to configure API calls is to download and install `AWS Command Line Interface <https://aws.amazon.com/cli/>`_.  
   
   Then, run:

.. code-block:: bash

    aws configure

4. You will be asked for your AWS Access Key ID, your AWS Secret Access Key, and default `region name <https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.RegionsAndAvailabilityZones.html#Concepts.RegionsAndAvailabilityZones.Regions>`_, such as 'us-east-2'.  

   If you prefer not to install this, you can set the environment variables 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', and 'AWS_DEFAULT_REGION'.  
   
   For a full list of environment variables you can set, see `here <https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html#using-environment-variables>`_.
   
   The stochss_compute AWS sub-package includes `python-dotev` which is handy for loading .env files into a python process.

.. code-block:: python

    from dotenv import load_dotenv
    load_dotenv() # Loads from a file named .env by default
