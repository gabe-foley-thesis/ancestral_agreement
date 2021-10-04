FROM python:3.6
COPY requirements.txt aa/requirements.txt
WORKDIR /aa
RUN pip install -r requirements.txt
COPY . /aa