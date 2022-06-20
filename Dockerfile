FROM python:3.10.5-slim-bullseye

WORKDIR /domain-scraper

# All files because we have .dockerignore
COPY . .

RUN pip install -r requirements.txt && \
    pip install .

CMD ["domain-scraper"]
