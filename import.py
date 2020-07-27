import os, csv

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.environ.get('DATABASE_URL'))
db = scoped_session(sessionmaker(bind=engine))
print("Connection established")
f = open("books.csv")

reader = csv.reader(f)
next(reader, None)

i=1

for isbn, title, author, year in reader:

    db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
                {"isbn": isbn, 
                 "title": title,
                 "author": author,
                 "year": year})

    print(f"{i}. Added book {title} to database.")

    db.commit()
    i+=1
    
db.close()
print("Connection closed")

f.close()
