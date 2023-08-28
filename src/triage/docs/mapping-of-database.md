# Visualizing The Database of Omega Triage Portal
This document provides instructions on how to create a visualization of the database for the Triage Portal.

## Instructions
Make sure you have the following packages installed or specified in your project's `requirements.txt`.
- django-extensions
  - https://pypi.org/project/django-extensions/
- pydot
  - https://pypi.org/project/pydot/

### Default Settings
In your Django project's `setting.py` file, add the following configurations:
```bash
INSTALLED_APPS = (
    # ...
    'django_extensions',
    # ...
)

GRAPH_MODELS = {
  'all_applications': True,
  'group_models': True,
}
```

### Docker Setup
If you are using Docker, add graphviz to your `Dockerfile` to install necessary packages and set up the environment:
```bash
RUN apt-get update && apt-get install -y --no-install-recommends \
                        # ...
                        graphviz \
                        # ...
                        && apt-get clean && rm -rf /var/lib/apt/lists/*
```

### Obtaining The Graph
Have the containers running and inside the Docker container for your Triage Portal application named `omega-triage-portal`,
execute the following command to generate the database visualization as a PNG image.
In this case, this will generate a PNG file named myapp_models.png.

```bash
python manage.py graph_models -a -o myapp_models.png
```

After the command is successfully executed, to access the generated image, you can download it from inside the Docker container.

### Helpful link
Documentation link: https://django-extensions.readthedocs.io/en/latest/graph_models.html
