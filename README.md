# Example Full-Stack Web App in Snowpark Container Services
This is a simple three-tiered web app that can be deployed
in Snowpark Container Services. It queries the TPC-H 100 
data set and returns the top sales clerks. The web app
provides date pickers to restrict the range of the sales
data and a slider to determine how many top clerks to display.
The data is presented in a table sorted by highest seller
to lowest.

This app was built with 3 containers:
* Frontend written in JavaScript using the Vue framework
* Backend written in Python using the Flask framework
* Router using nginx to allow the Frontend and Backend to 
  be on the same URL and avoid CORS issues.

This app is deployed as 3 separate SERVICES:
* The Frontend container is deployed in one service.
* The Backend container is deployed in its own service.
* The Router container is deployed in its own service and exposes a 
  single endpoint that will route to the Frontend and Backend 
  services over the internal network.

The reason to split them this way is so that the Frontend and 
Backend can autoscale differently. Moreover, you could deploy
the Frontend and Backend to different COMPUTE POOLS, which would
support the case where the Backend needs more compute power than 
the Frontend, which is typically pretty light.

The Router service is configured through the service specification,
specifically, the `args` that are passed to the service on creation.
In the `args` section of the `container`, specify one value per endpoint
you want to expose. The format is `<exposed_path>=<internal_dns_and_route>`.
For example, the following exposes 2 endpoints: the `/` path routes to
the `FRONTEND` service on port `8000` using the internal destination of
`http://frontend:8000`; and the `/api` path routes to the `BACKEND` service
in the `BACKENDSCHEMA` schema in the `BACKENDDB` database on port `8081` 
using the internal destination of 
`http://backenddb.backendschema.backend.snowflakecomputing.internal:8081`:
```
      args:
        - /=http://frontend:8000
        - /api=http://backenddb.backendschema.backend.snowflakecomputing.internal:8081
```

# Setup
This example requires importing the `SNOWFLAKE_SAMPLE_DATA`
data share, and an account with Snowpark Container Services
enabled.

1. Follow the "Common Setup" [here](https://docs.snowflake.com/en/LIMITEDACCESS/snowpark-containers/tutorials/common-setup)
2. In a SQL Worksheet, execute `SHOW IMAGE REPOSITORIES` and look
   for the entry for `TUTORIAL_DB.DATA_SCHEMA.TUTORIAL_REPOSITORY`.
   Note the value for `repository_url`.
3. In the main directory of this repo, execute 
   `bash ./configure.sh`. Enter the URL of the repository that you
   noted in step 2 for the repository. Enter the name of the warehouse
   you set up in step 1 (if you followed the directions, it would be
   `tutorial_warehouse`).
4. Log into the Docker repository, build the Docker image, and push
   the image to the repository by running `make all`
   1. You can also run the steps individually. Log into the Docker 
      repository by running `make login` and entering your credentials.
   2. Make the Docker image by running `make build`.
   3. Push the image to the repository by running `make push_docker`
5. Upload the `frontend.yaml`, `backend.yaml`, and `router.yaml` to the stage you created in step 1. 
   If you followed those steps, the stage should be `@TUTORIAL_DB.DATA_SCHEMA.TUTORIAL_STAGE`. 
   You can use SnowSQL, Snowsight, or any other method to `PUT` the file to the Stage.
6. We are going to create 2 compute pools, one for the frontend and one for the 
   backend.
   ```sql
   USE ROLE ACCOUNTADMIN;

   CREATE COMPUTE POOL frontend_compute_pool
      MIN_NODES = 1
      MAX_NODES = 1
      INSTANCE_FAMILY = CPU_X64_XS;
   GRANT USAGE, MONITOR ON COMPUTE POOL frontend_compute_pool TO ROLE test_role;

   CREATE COMPUTE POOL backend_compute_pool
      MIN_NODES = 1
      MAX_NODES = 1
      INSTANCE_FAMILY = CPU_X64_XS;
   GRANT USAGE, MONITOR ON COMPUTE POOL backend_compute_pool TO ROLE test_role;
   ```
6. The frontend includes loading the Snowflake logo from Wikipedia, 
   just to illustrate loading something into the webpage from an external
   source. In order to support this, we need to create an EXTERNAL
   ACCESS INTEGRATION:
   ```sql
   USE ROLE ACCOUNTADMIN;

   CREATE OR REPLACE NETWORK RULE nr_wiki
      MODE = EGRESS
      TYPE = HOST_PORT
      VALUE_LIST = ('upload.wikimedia.org');

   CREATE OR REPLACE EXTERNAL ACCESS INTEGRATION eai_wiki
      ALLOWED_NETWORK_RULES = ( nr_wiki )
      ENABLED = true;
   ```
7. Create the backend service by executing
   ```sql
   CREATE SERVICE backend
     IN COMPUTE POOL backend_compute_pool
     FROM @tutorial_db.data_schema.tutorial_stage
     SPECIFICATION_FILE = 'backend.yaml'
     QUERY_WAREHOUSE = tutorial_warehouse
     ;
   ```
   Substitute the name of your warehouse if not using `tutorial_warehouse`.
8. Create the frontend service by executing
   ```sql
   CREATE SERVICE frontend
     IN COMPUTE POOL frontend_compute_pool
     FROM @tutorial_db.data_schema.tutorial_stage
     SPECIFICATION_FILE = 'frontend.yaml'
     ;
   ```
9. Now create the router service. You can edit the `router.yaml` to supply
   different or additional `args` to specify the mapping from routes to 
   services. If you make changes, remember to upload `router.yaml` to the 
   stage you created in Step 1. Then run the following DDL:
   ```sql
   CREATE SERVICE router
     IN COMPUTE POOL frontend_compute_pool
     FROM @tutorial_db.data_schema.tutorial_stage
     SPECIFICATION_FILE = 'router.yaml'
     EXTERNAL_ACCESS_INTEGRATIONS = ( EAI_WIKI )
     ;
   ```
10. See that the services have started by executing `SHOW SERVICES IN COMPUTE POOL tutorial_compute_pool` 
   and `SELECT system$get_service_status('backend')`
   or `SELECT system$get_service_status('frontend')`
   or `SELECT system$get_service_status('router')`.
11. Find the public endpoint for the router service by executing `SHOW ENDPOINTS IN SERVICE router`.
12. Grant permissions for folks to visit the endpoint. You do this by granting 
   the SERVICE ROLE: `GRANT SERVICE ROLE router!app TO ROLE some_role`, 
   where you specify the role in place of `some_role`.
13. Navigate to the endpoint and authenticate. 
14. Enjoy!


## Local Testing
This web app can be tested running locally. To do that, build the
image for your local machine with `make build_local`.

In order to run the web app in the container, we need to set some 
environment variables in our terminal session before running the 
container. The variables to set are:
* `SNOWFLAKE_ACCOUNT` - the account locator for the Snowflake account
* `SNOWFLAKE_USER` - the Snowflake username to use
* `SNOWFLAKE_PASSWORD` - the password for the Snowflake user
* `SNOWFLAKE_WAREHOUSE` - the warehouse to use
* `SNOWFLAKE_DATABASE` - the database to set as the current database (does not really matter that much what this is set to)
* `SNOWFLAKE_SCHEMA` - the schema in the database to set as the current schema (does not really matter that much what this is set to)

Once those have been set, run the app with `make run`. This will 
use Docker Compose to start 3 containers to host the web app. Navigate
to `http://localhost:80`.