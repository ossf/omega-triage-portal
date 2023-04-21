# Omega Triage Portal

The Omega Triage Portal is a web-application that can help manage automated vulnerability reports.
It was designed for scale, (hundreds of thousands of projects, many millions of findings),
but may also be useful at lower scale.

**The Portal is in early development, and is not ready for general use.**

## Getting Started

This extension can be used from GitHub Codespaces:

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://github.com/codespaces/new?machine=basicLinux32gb&repo=426394209&ref=scovetta%2Fadd-triage-portal&location=WestUs2&devcontainer_path=.devcontainer%2Ftriage-portal%2Fdevcontainer.json)

Once loaded, open the `.vscode/project.code-workspace` file and then click the `Open Workspace`
button. A new widow will open. This is needed because VS Code launch settings are nested
within the omega/triage-portal folder.

You can then run the Django launch task to start the application. Navigate to
<http://localhost:0/admin> and enter the default credentials (admin/admin), then
navigate back to <http://localhost:8001>.

## Local Development

### Docker Compose

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

## Contributing

TBD

## Security

See [SECURITY.md](https://github.com/ossf/omega-triage-portal/blob/main/SECURITY.md).
