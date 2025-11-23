#FROM python:3.12-slim
#
#WORKDIR /app
#
#COPY requirements.txt .
#
#RUN pip install --no-cache-dir -r requirements.txt
#
#COPY src/* .
#
#EXPOSE 7777
#
#CMD ["python", "server.py"]


FROM public.ecr.aws/lambda/python:3.12

ARG CACHEBUST=1

# Copy requirements.txt
COPY requirements.txt ${LAMBDA_TASK_ROOT}

#COPY .env ${LAMBDA_TASK_ROOT}

#ENV AIRUN_API_KEY=$AIRUN_API_KEY

# Install the specified packages
RUN pip install -r requirements.txt

COPY ./text_filler ${LAMBDA_TASK_ROOT}/text_filler

# Copy function code
COPY lambda_function.py ${LAMBDA_TASK_ROOT}

COPY times.ttf ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "lambda_function.lambda_handler" ]