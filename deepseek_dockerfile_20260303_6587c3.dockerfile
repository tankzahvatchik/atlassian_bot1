FROM python:3.11-slim

# Устанавливаем Java (OpenJDK 17)
RUN apt-get update && apt-get install -y \
    openjdk-17-jre-headless \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Проверяем что Java установилась
RUN java -version

CMD ["python", "host.py"]