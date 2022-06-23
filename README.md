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
        --mount type=bind,source=${PWD}/emails,target=${app_path}/emails \
        --volume db:${app_path}/db:rw \
        -e GMAIL_APP_USERNAME -e GMAIL_APP_PASSWORD -e DOMAINS_SUBSCRIBERS \
        "${image_name}" domain-scraper scrape

## minikube deployment
    eval $(minikube docker-env) # to add image to minikube docker repo
    minikube mount $HOME:/hosthome # run in separate terminal

    kubectl apply -f secrets.yaml # prepare secrets.yaml file with GMAIL_APP_USERNAME, GMAIL_APP_PASSWORD and DOMAINS_SUBSCRIBERS defined
    kubectl create -f cronjob.yaml

## TODO:
 - [x] move scanned emails to separate dir to avoid duplication
 - [x] add requirements.txt file
 - [x] add html alternative message template + use it
 - [x] add possibility to read INPUT_DIR, ARCHIEVE_DIR, DB_FILE from env
 - [x] add option for send-summary to send all emails instead of only new emails
 - [x] add setup.cfg, entrypoint and test building
 - [x] add Dockerfile, build and test the image
 - [x] add variables to deployment with secrets.yaml (email-secrets)
 - [x] configure persistent volume to store db
 - [x] add kubernetes yaml, verify the deployment
 - [x] do some refactoring, especially variable naming (msg, messages_to_send)
 - [x] add docstrings
 - [x] add types declarations
 - [x] add logging and remove all prints
 - [x] add option to parse only one email
 - [ ] create helm chart from the repo
 - [ ] add coverage measurement
 - [ ] write unit tests
 - [ ] evaluate domain parsing - separate ipv4/ipv6 parsing from domains
 - [ ] add exception handling when file in INPUT_DIR is not email file or does not contain Received header
 - [ ] add validation for input files, to check if they are actually emails
 - [ ] add validation for DOMAINS_SUBSCRIBERS
