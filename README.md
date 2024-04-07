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
Start QGrant with 2 ports for faster work.
docker run -p 6333:6333 -p 6334:6334 -v $(pwd)/qdrant_storage:/qdrant/storage:z  qdrant/qdrant

## Search must have also the collection name inside.

http://127.0.0.1:8000/api/search?q=Chicago&collection_name=1_SearchEngineGP

## Insert data

http://127.0.0.1:8000/api/insert-data/

'''
{
  "collection_name": "1_SearchEngineGP",
   "payload": {
	 "name": "Hyde Park Angels",
     "description": "Hyde Park Angels is the largest and most active angel group in the Midwest. With a membership of over 100 successful entrepreneurs, executives, and venture capitalists, the organization prides itself on providing critical strategic expertise to entrepreneurs and ...",
	 "images": "https://d1qb2nb5cznatu.cloudfront.net/startups/i/61114-35cd9d9689b70b4dc1d0b3c5f11c26e7-thumb_jpg.jpg?buster=1427395222",
     "alt": "Hyde Park Angels - ",
     "companyID": "1234",
	 "link": "http://hydeparkangels.com",
     "city": "Chicago"
   },
   "data": {
     "name": "Hyde Park Angels",
     "images": "https://d1qb2nb5cznatu.cloudfront.net/startups/i/61114-35cd9d9689b70b4dc1d0b3c5f11c26e7-thumb_jpg.jpg?buster=1427395222",
     "alt": "Hyde Park Angels - ",
     "description": "Hyde Park Angels is the largest and most active angel group in the Midwest. With a membership of over 100 successful entrepreneurs, executives, a venture capitalists, the organization prides itself on providing critical strategic expertise to entrepreneurs and ...",
     "link": "http://hydeparkangels.com",
     "city": "Chicago",
	 "pdfText1": "Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book. It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged. It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum.",
	 "pdfText2": "Contrary to popular belief, Lorem Ipsum is not simply random text. It has roots in a piece of classical Latin literature from 45 BC, making it over 2000 years old. Richard McClintock, a Latin professor at Hampden-Sydney College in Virginia, looked up one of the more obscure Latin words, consectetur, from a Lorem Ipsum passage, and going through the cites of the word in classical literature, discovered the undoubtable source. Lorem Ipsum comes from sections 1.10.32 and 1.10.33 of de Finibus Bonorum et Malorum (The Extremes of Good and Evil) by Cicero, written in 45 BC. This book is a treatise on the theory of ethics, very popular during the Renaissance. The first line of Lorem Ipsum, Lorem ipsum dolor sit amet.., comes from a line in section 1.10.32.",
	 "pdfText3": "The standard chunk of Lorem Ipsum used since the 1500s is reproduced below for those interested. Sections 1.10.32 and 1.10.33 from de Finibus Bonorum et Malorum by Cicero are also reproduced in their exact original form, accompanied by English versions from the 1914 translation by H. Rackham."
   }
 }
 '''

## Create namespace

ID of the user will be add to the collection.
 http://127.0.0.1:8000/api/create-namespace/

 
 {
   "collection_name": "SearchEngineGP"
 }

## Create Refresh Token
You need to send username and password from Django.

 http://127.0.0.1:8000/auth/jwt/create/