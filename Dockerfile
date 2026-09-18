FROM python:3.14-slim

WORKDIR /app

COPY freeze.txt .
RUN pip install --no-cache-dir -r freeze.txt

COPY . .
RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
CMD ["process"]
