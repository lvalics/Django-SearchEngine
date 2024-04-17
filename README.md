# Django-SearchEngine

Clone the project from GitHub by executing the following commands:

```
git clone https://github.com/lvalics/Django-SearchEngine
cd Django-SearchEngine
python3 -m venv venv
source venv/bin/activate 
pip install -r requirements.txt
```

# Set up the .env File

Create a .env file in the root directory of the project and populate it with the following content:

```
SECRET_KEY='django-add_a_random_string_here'
ALLOWED_HOSTS=['127.0.0.1,0.0.0.0']  #your IP to allow to do requests
EMBEDDINGS_MODEL="sentence-transformers/all-MiniLM-L6-v2"
VECTOR_SIZE=1536
QDRANT_URL="http://localhost" #your qdrant URL
QDRANT_PORT="6333"
```

# Workflow Description

This API retrieves requests from various sources and creates records in the QDrant Vector Database within a designated collection, each with a payload. It is essential to define the payload for each API. Payloads should contain key information (e.g., filename, categories) that will be used for identification and response purposes.

## Qdrant
To start QDrant with two ports for improved performance, you can use the following command:

```
docker run -p 6333:6333 -p 6334:6334 -v $(pwd)/qdrant_storage:/qdrant/storage:z  qdrant/qdrant
```

## How to search via API

To ensure the search includes the collection name and the search value, you should structure your API endpoint like this:

```
http://127.0.0.1:8000/api/search?q=Chicago&collection_name=1_SearchEngineGP&&type=neural
```

This URL will make a request to the search API at the given local address (127.0.0.1) on port 8000. The query parameters q and collection_name are used to specify the search term ("Chicago") and the collection name ("1_SearchEngineGP"), neural search.

## Create a superuser in Django

To ensure that each user has a unique collection name and to create a superuser that will be used to generate access tokens, you will need to run the Django createsuperuser command:

```
python3 manage.py createsuperuser
```

When you execute this command, it will prompt you to enter a username, email address, and password for the superuser. This superuser can then be used to access the Django admin panel where you can manage tokens and ensure that the collection_name is unique for each user. It's important that the collection_name is generated or assigned in a way that guarantees uniqueness, perhaps by incorporating the user's ID or a unique identifier that persists across sessions.

## Create collection

To include the user ID in the collection name when creating a namespace through your API, you need to modify the JSON payload to dynamically insert the user's ID into the collection_name. Assuming the user ID is provided or available in your application context, here's how you could construct the request.
NOTE: If collection exist, it will delete the old collection and create a new one.

TODO: Add an extra key to check if exist and add a value to DELETE.

http://127.0.0.1:8000/api/create-namespace/

 ```
 {
   "collection_name": "SearchEngineGP"
 }
```

## Insert data

When creating or updating records in a collection, it's crucial to include both the collection_name and data in the payload, with a focus on using unique identifiers for efficient retrieval and safe modifications. Here's how you can structure your payload to meet these requirements:

It is essential to carefully define and use these identifiers because they will not only allow for precise updates and deletions but also determine how search results are returned. Ensure that each object in the payload array has all the necessary identifiers and that they are assigned accurately to reflect the nature of the data.

For example, if ID 1234 represents the data for a company, and this company has various types of information that can be easily categorized, then you should include these categories in the payload. For instance, you could use categories such as 'music', 'news', 'movies', etc.

http://127.0.0.1:8000/api/insert-data/

```
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
```

## Update data

You must include 'id_value', 'id_key', and 'collection_name' in your submission. The 'id_value' will be utilized to filter and identify the data that needs to be deleted before new data is inserted. It is crucial to accurately define your data in the payload to facilitate easier identification later.

If your data requires matching across two values for a search, utilize 'id_value' and 'id_value2' for this purpose. Currently, our system is only capable of handling matches using two values.

TODO: Develop a dynamic system for matching values.

http://127.0.0.1:8000/api/update-data/

```
{
  "filter_conditions": {
        "companyID": "1772",
        "type": "primarie"
    },
  "collection_name": "1_SearchEngineGP",
   "payload": {
          "name": "Hyde Park Angels1333",
          "companyID": "1234",
          "category": "music"
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
```

## Create Refresh Token

To send a username and password to the Django backend for authentication, you would typically make a POST request to the /auth/jwt/create/ endpoint. Here's how you can structure this request: http://127.0.0.1:8000/auth/token/login/

TODO: Implement a mechanism for a non-expiring key. Currently, JWTs typically expire after a set duration for security reasons.

```
POST /auth/token/login/ HTTP/1.1
Host: 127.0.0.1:8000
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}

response ex:  "auth_token": "49ece790dbf9beaa2901bc8118b20abba1795c8f"

And you need to send as Authorization: Token 49ece790dbf9beaa2901bc8118b20abba1795c8f
```

## PDF - OCR

```
sudo apt install tesseract-ocr libtesseract-dev poppler-utils
```

## TO DO 

- Chunk the data to avoid large context.
- dockerize.

def get_chunks(text):
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=100,
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    return chunks

with open("story.txt") as f:
    raw_text = f.read()

texts = get_chunks(raw_text)

vectorstore.add_texts(texts)