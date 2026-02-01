New Fast API project
you are an awesome BE API developer with knowledge of datascience and machine learning

the server app will take a csv list of domain names, 

the server app will will crawl through the the main page of the domain name and then find links to crawl further, and so on will crawl the whole website, also check if the site map is available, then crawl accordingly with the site map as well, basically just  a crawler that will use all means possible for crawling the whole website, including pdfs not just htm and html, if the pdfs do not have text then it will run OCR on the pdf to get relevant data, the text in the website  can be multilingual like english, arabic, urdu, hindi, etc.

it will have the option of using either Gemini LLM API or DeepSeek LLM API for getting its work done

then it will create a vector database from this data of the websites domain names given in the csv list, from the data it received by crawling

it will generate an API to make RAG search in this vector data, where it will get a query in natural language text in a POST query, it will search in the vector data acquired by crawling the domain name websites given, along with the question, the post query will have other options like context, and other general options for these kind of APIs, the response will be a reply generated with the help of the LLM and a list of the sources being used for the response that will define which links of the crawled websites data was used to formulate the response so that the client sending the POST request will get exact information to cross verify the response, by knowing the exact links on the website that were used to find the answers to his query, if the source has a pdf file, then the API response must also mention its page number if possible, if the source was a htm/html/ or other web link, then the source must mention the link with the highlighted text so the client will easily find the exact text, the API response must also have a short text say like 300 characters (configurable to be changed later) to show the verbatim text used for the response

the server app will continue to poll every 24 hours in the background and check if the domain names given in the csv file, it will log its crawling activities to a log file with timestamps, domain and links crawled, and update the vector database accordingly for the latest data on the website

make improvements as necessary, and add all extra functionalities that a server app like this must be having

also advise suggestions that you might have for me to approve/disaprove