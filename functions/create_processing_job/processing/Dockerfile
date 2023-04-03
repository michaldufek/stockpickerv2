#FROM amazon/aws-glue-libs:glue_libs_1.0.0_image_01
FROM python:3.7-slim-buster
#FROM 446299261295.dkr.ecr.ca-central-1.amazonaws.com/sagemaker-spark-processing:3.2-cpu-py39-v1.0

# Install OpenJDK 8
RUN apt-get update && \
    apt-get install -y openjdk-11-jdk-headless && \
    rm -rf /var/lib/apt/lists/*

#RUN python3 -m pip install --upgrade pip 
RUN python3 -m pip install awswrangler==2.14.0 fsspec==2022.1.0 h5py==3.1.0 \ 
                        pandas pyspark==3.2.3 boto3 \
                        s3fs==2022.1.0 s3transfer==0.5.2 sagemaker scikit-learn==1.2.1

ENV PYTHONBUFFERED=TRUE

# Set JAVA_HOME environment variable
ENV JAVA_HOME /usr/lib/jvm/java-11-openjdk-amd64/

# Set the entrypoint
ENTRYPOINT ["python3"]