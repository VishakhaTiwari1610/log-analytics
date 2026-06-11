#!/bin/bash
 echo "Starting consumer.... "
 
 cd consumer
 python consumer.py & 

 echo "Starting FastAPI..."

cd ..
 uvicorn api:app --host 0.0.0.0 --port $PORT