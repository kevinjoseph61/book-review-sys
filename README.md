# book-review-sys

## A Flask driven application for reviewing books   

- This project was done in accordance with the specifications laid out in https://docs.cs50.net/web/2020/x/projects/1/project1.html for project 1 of CS50w (2018 version)
- Application demo can be found at https://drive.google.com/file/d/1B8ao_bn5LgDC3r0z7VHdO0BBCSE4oDR1/view?usp=sharing
- application.py contains the main code that requires flask to run. Be sure to set the environment variable of FLASK_APP to application.py
- Use pip to install the required libraries in requirements.txt using "pip install -r requirements.txt"
- This project uses a remote PostgreSQL database. Follow the instructions in the CS50 docs link to set up your heroku account and get the database URL(URI). Be sure to set the environment variable of DATABASE_URL to the database URL from heroku. 
- This project also uses the GoodReads API. Follow the instructions in the CS50 docs link to set up your GoodReads account and get the API key. Be sure to set the environment variable of GOODREADS_API_KEY to the API key from GoodReads. 
- Set up your remote database by seeing the structure of the table in the demo and also by checking the "table description.txt" and appropriately creating the table required
- A set of books are to be added to the table (5000 books) from the books.csv file. This can be done using the import.py code. Check the CS50 docs link to find out how to add
- Run flask using "flask run"
- Login/create account and search for the required books according to the search context
- You can also access the API to get required content which does not need login by following the api route along with the ISBN as parameter. This returns a JSON object.
