
## -- TECHNICAL TEST: APIFIED AND DOCKERIZED OPTIMIZATION ALGORITHM --


## The general outline of the project is as follows:

```	
my_api/
	├── API.py
	├── Dockerfile
	├── requirements.txt
	├── logs/
	│   └── app.log
```

1. **In order to create the Docker image, the following command must be executed in the directory where the project is hosted:**

```
docker build -t my_api .
|
|-> The Dockerfile is configured so that the container can receive requests from any IP (0.0.0.0.0).
```

2. **In order to run that image and thus create the container, the following command must be executed on any path on the computer:**


```
docker run -p 8888:8888 my_api
|
|-> This makes the port through which the communication with the server that wraps the API is going to be established to be 8888.
```

3. **In order to send a POST request to the Server and therefore to the API, the following command is executed in the path where the payload data is located:**

```
Invoke-RestMethod -Uri "http://localhost:8888/productionplan"
                  -Method POST 
                  -Body (Get-Content -Raw -Path "payloadX.json")
                  -ContentType "application/json" 
|
|-> Note that the file name ".json" is a generic name to be adapted to the desired payload.		
```

4. **In order to review both the log and the data the following commands will be executed from any path:**

```
docker ps -a
|-> To be able to identify the API container being used

docker exec -it <ID_CONTAINER> sh
|-> To be able to browse the container files as if it were a console, using shellscripting

cat logs/app.log
|-> To review the logs

cat response.json
|-> For reviewing the response
```