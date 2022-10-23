The service consists of two components:
1. **updater** calculates tickers prices once a second and saves these values to the database
2. **backend** works as a web server for the main page and as an API for receiving data

The minimum logic for displaying the chart is implemented in the built-in script in the index.html file.

Build and run the service with following commands:

`docker-compose -f docker-compose.yml build`

`docker-compose -f docker-compose.yml up`

Now you can open http://127.0.0.1:8080 and check tickers' course.
