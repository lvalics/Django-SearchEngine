"""
This file is used to configure the app name.
"""
from django.apps import AppConfig


class ApiConfig(AppConfig):
    """
    This class is a subclass of AppConfig and is used to hold
    configuration for a specific application in the Django project. 

    Args:
        AppConfig (Django AppConfig): This is the base class for all
        Django application configuration objects. It includes methods
        and attributes for configuring an application and its models, views, and templates.

    Attributes:
        name (str): The name of the application. This should be a
        short, unique name.
        verbose_name (str, optional): A human-readable name for the
        application. This is used in the Django admin interface.
        If not provided, Django will use a prettified version of the app's name.
        path (str, optional): The filesystem path to the application's directory.
        If not provided, Django will use the Python import path.
        models_module (module, optional): The Python module that contains the
        application's models. If not provided, Django will use the 'models'
        module within the application's package.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
