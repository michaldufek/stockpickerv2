FROM public.ecr.aws/lambda/python:3.9

COPY requirements.txt .

RUN pip3 install -r requirements.txt -t .

COPY download_prices.py .

CMD ["download_prices.lambda_handler"]
