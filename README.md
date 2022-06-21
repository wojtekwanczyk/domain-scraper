# domain-scraper :mag:

## Configure domain-scraper by setting variables to make send-summary work
 - DOMAINS_SUBSCRIBERS - comma separated vaild email addresses
 - GMAIL_APP_USERNAME - gmail username
 - GMAIL_APP_PASSWORD - gmail password

## Usage
Usage: domain-scraper [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  clean            For testing purposes: remove DB_FILE, rename...
  scrape           Scrape domains from emails from input_dir and print them
  scrape-and-send  Default command: Scrape domains and send email with...
  send             Read domains from file and send email with update to...

## Using docker image
Remember to add variables GMAIL_APP_USERNAME & GMAIL_APP_PASSWORD to docker run command or use env.list file with --env-file flag, e.g.

    mkdir -p emails/input emails/archive
    image_name="domain-scraper"
    app_path="/domain-scraper"
    docker run --rm \
        --mount type=bind,source=\${PWD}/emails,target=\${app_path}/emails \
        --volume db:${app_path}/db:rw \
        -e GMAIL_APP_USERNAME -e GMAIL_APP_PASSWORD -e DOMAINS_SUBSCRIBERS \
        "${image_name}" domain-scraper scrape

## minikube deployment
    minikube mount $HOME:/hosthome # run in separate terminal

    kubectl apply -f secrets.yaml # prepare secrets.yaml file with GMAIL_APP_USERNAME, GMAIL_APP_PASSWORD and DOMAINS_SUBSCRIBERS defined
    kubectl create -f cronjob.yaml

## In progress:
 - [ ] add kubernetes yaml, verify the deployment
 - [x] add variables to deployment with secrets.yaml (email-secrets)
 - [ ] configure persistent volume to store db

## TODO:
 - [x] move scanned emails to separate dir to avoid duplication
 - [x] add requirements.txt file
 - [x] add html alternative message template + use it
 - [x] add possibility to read INPUT_DIR, ARCHIEVE_DIR, DB_FILE from env
 - [x] add option for send-summary to send all emails instead of only new emails
 - [x] add setup.cfg, entrypoint and test building
 - [x] add Dockerfile, build and test the image
 - [ ] create helm chart from the repo
 - [ ] create and use separate config file (INPUT_DIR, DB_FILE, DOMAINS_SUBSCRIBERS)
 - [ ] do some refactoring, especially variable naming (msg, messages_to_send)
 - [ ] add logging and remove all prints
 - [ ] add coverage measurement
 - [ ] write unit tests
 - [ ] add docstrings
 - [ ] add types declarations
 - [ ] evaluate domain parsing - separate ipv4/ipv6 parsing from domains
