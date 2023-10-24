# # pull official base image
# FROM python:3.11.4

# # set work directory
# WORKDIR /usr/src/app

# # set environment variables
# ENV PYTHONDONTWRITEBYTECODE 1
# ENV PYTHONUNBUFFERED 1

# # install dependencies
# RUN pip install --upgrade pip
# COPY ./requirements.txt /usr/src/app/requirements.txt
# RUN pip install -r requirements.txt
# RUN pip install -U django-celery-beat
# # copy entrypoint.sh
# COPY ./entrypoint.sh /usr/src/app/entrypoint.sh

# # copy project
# COPY . /airlines

# # run entrypoint.sh
# ENTRYPOINT ["/usr/src/app/entrypoint.sh"]

FROM python:3.11.4
# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /usr/src/app
RUN pip install --upgrade pip
# Копируем файл requirements.txt внутрь контейнера
COPY requirements.txt ./
# Устанавливаем зависимости, описанные в файле requirements.txt
RUN pip install -r requirements.txt