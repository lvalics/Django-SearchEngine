# Django-SearchEngine

uv pip install -r requirements.txt

# Workflow

An API to get request from sources, where it will be creating in QDrant Vector Database in a namespace a record with a metafield. Important to define for each API the metafield. Should be dynamic, where in metafields should be entered inportant information what to send back for identifying (ex: filename, categories, etc).

# Extra resources

## Django Documentation
https://www.django-rest-framework.org/tutorial/quickstart/
https://github.com/encode/django-rest-framework
https://djangopackages.org/
https://docs.djangoproject.com/en/5.0/
https://blog.logrocket.com/django-rest-framework-create-api/

## Qdrant
Start QGrant with 
docker run -p 6333:6333 -p 6334:6334 \
    -v $(pwd)/qdrant_storage:/qdrant/storage:z \
    qdrant/qdrant