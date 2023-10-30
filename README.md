### This is no longer a maintained repository and documents will be kept for historical tracking

# Omega Triage Portal

The Omega Triage Portal is a web-application that can help manage automated vulnerability reports.
It was designed for scale, (hundreds of thousands of projects, many millions of findings),
but may also be useful at lower scale.

**The Portal is in early development, and is not ready for general use.**

## Getting Started
Deployment of the Triage Portal in GitHub's development environment

This extension can be used from GitHub Codespaces:

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://github.com/codespaces/new?machine=basicLinux32gb&repo=426394209&ref=scovetta%2Fadd-triage-portal&location=WestUs2&devcontainer_path=.devcontainer%2Ftriage-portal%2Fdevcontainer.json)

Once loaded, open the `.vscode/project.code-workspace` file and then click the `Open Workspace`
button. A new widow will open. This is needed because VS Code launch settings are nested
within the omega/triage-portal folder.

You can then run the Django launch task to start the application. Navigate to
<http://localhost:8001/admin/login/?next=/admin/> and enter the default credentials that you created (admin/admin),
then navigate back to <http://localhost:8001>.

## Local Development

### Docker Compose
Make sure to have Docker installed and set up before running the following commands.

To build the application, run the following command:
```bash
docker-compose build
```

To run the application, run the following command:
```bash
docker-compose up
```

**NOTE:** The first time you run the application, you will need to run the following commands to
create the database. This command MUST be run after the application is running with the above commands.

```bash
docker-compose run triage-portal python manage.py migrate
```

```bash
docker-compose run triage-portal python manage.py createsuperuser
```

### Local Windows Development
Issues enabling python virtualenv

    1. Open PowerShell
    2. Run the following command: Set-ExecutionPolicy RemoteSigned -Scope CurrentUser OR Set-ExecutionPolicy -ExecutionPolicy Unrestricted -Scope CurrentUser

https://stackoverflow.com/questions/69605313/vs-code-terminal-activate-ps1-cannot-be-loaded-because-running-scripts-is-disa


## The API Connecting The Omega Analyser And Triage Portal

The documentation for the API that connects the Omega Analyzer and Triage Portal is housed within the GraphiQL IDE, which is basically a playground
offered by GraphQL to facilitate interactions with its APIs. It is conveniently accessible through the `http://localhost:8001/graphql` endpoint.
This documentation becomes available after the application is successfully deployed.

**_File Size:_** Please be aware that the current file size limitation for the API stands at `200 MB`. This constraint should be considered when handling file uploads or other data interactions within the Triage Portal's API.

## Azure Development Environment

The Proof of concept webapp is available at https://otpdev1.eastus.cloudapp.azure.com/admin

In the event of a virtual machine having to be destroy and a new one taken it's place, here are important details when deploying a new proof of concept using Azure VM

* In the Networking settings for the Azure VM, ensure that HTTP, HTTPS, and SSH are configured in the firewall.
* In the VM,
  * Perform a git pull via HTTP git clone URI in the `/app` directory
  * Install the following and any of their dependencies
    * [nginx](https://www.digitalocean.com/community/tutorials/how-to-install-nginx-on-ubuntu-22-04)
    * [docker](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-22-04)
    * [docker compose](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-compose-on-ubuntu-22-04)
    * [gunicorn](https://docs.gunicorn.org/en/stable/install.html)
  * Update `/etc/nginx/nginx.conf` and `/etc/nginx/sites-available/default` file with the respected settings
  * Collecting the static files for UI
    * Ensure that the `/opt/omega/static` directory is available, if not, create it.
    * Enter the triage-portal container ( `docker exec -it omega-triage-portal /bin/bash` ) and run `python manage.py collectstatic`
    * Move the static files from container to the VM's `/opt/omega/static` directory ( `cp core/settings.py /opt/omega/static`)

## Contributing

TBD

## Security

See [SECURITY.md](https://github.com/ossf/omega-triage-portal/blob/main/SECURITY.md).
