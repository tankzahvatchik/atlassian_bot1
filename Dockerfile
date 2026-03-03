# Клонируем репозиторий (если нет локально)
git clone https://github.com/tankzahvatchik/atlassian_bot1.git
cd atlassian_bot1

# Создаем Dockerfile (через блокнот или echo)
echo 'FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    openjdk-17-jre-headless \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN java -version

CMD ["python", "host.py"]' > Dockerfile

# Добавляем в git
git add Dockerfile
git commit -m "Add Dockerfile with Java installation"
git push
