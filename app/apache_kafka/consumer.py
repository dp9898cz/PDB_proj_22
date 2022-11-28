from kafka import KafkaConsumer
from kafka.consumer.fetcher import ConsumerRecord
from json import loads
import mongoengine as me

from apache_kafka.enums import KafkaKey, KafkaTopic

from entity.nosql.author import Author
from entity.nosql.book import Book
from entity.nosql.book_copy import BookCopy
from entity.nosql.category import Category
from entity.nosql.location import Location
from entity.nosql.schemas_mongo import author_schema, books_schema, category_schema, book_copy_schema, location_schema


def manage_author(key, value):
    if (key == KafkaKey.CREATE.value):
        # create new author object
        author = author_schema.load(value)
        author.save()

    if (key == KafkaKey.UPDATE.value):
        # update author object itself
        author = Author.objects(id=int(value["id"])).first()
        author.update(**value)

        # we dont want to add books and description
        if "books" in value:
            del value["books"]
        if "description" in value:
            del value["description"]

        # update each book that holds this author
        books = Book.objects(authors__id=int(value["id"]))
        for book in books:
            # for each book update author by author id
            author_object = next((a for a in book.authors if a.id == int(value["id"])), None)
            if author_object:
                book.authors.remove(author_object)
                book.authors.append(value)
            book.update(authors=book.authors)

    if (key == KafkaKey.DELETE.value):
        # delete author object itself
        author = Author.objects(id=int(value["id"])).first().delete()

        # delete author object from books
        books = Book.objects(authors__id=int(value["id"]))
        for book in books:
            # for each book delete author by author id
            author_object = next((x for x in book.authors if x.id == int(value["id"])), None)
            if author_object:
                book.authors.remove(author_object)
            book.update(authors=book.authors)


def manage_category(key, value):
    if (key == KafkaKey.CREATE.value):
        # create new category object
        c = category_schema.load(value)
        c.save()

    if (key == KafkaKey.UPDATE.value):
        # update category object itself
        c = Category.objects(id=int(value["id"])).first()
        c.update(**value)

        """         # we dont want to add books and description
        if "books" in value:
            del value["books"]"""
        if "description" in value:
            del value["description"]

        # update each book that holds this category
        books = Book.objects(categories__id=int(value["id"]))
        for book in books:
            # for each book update category by category id
            cat = next((a for a in book.categories if a.id == int(value["id"])), None)
            if cat:
                book.categories.remove(cat)
                book.categories.append(value)
            book.update(categories=book.categories)

    if (key == KafkaKey.DELETE.value):
        # delete category object itself
        c = Category.objects(id=int(value["id"])).first().delete()

        # delete categ object from books
        books = Book.objects(categories__id=int(value["id"]))
        for book in books:
            # for each book delete cat by cat id
            cat = next((x for x in book.categories if x.id == int(value["id"])), None)
            if cat:
                book.categories.remove(cat)
            book.update(categories=book.categories)


def manage_location(key, value):
    if (KafkaKey.CREATE.value == key):
        l = location_schema.load(value)
        l.save()

    if (KafkaKey.UPDATE.value == key):
        # update location object itself
        l = Location.objects(id=int(value["id"])).first()
        l.update(**value)

        # update each book_copy object
        books = BookCopy.objects(location__id=int(value["id"]))
        for book in books:
            # for each book update location
            book.update(location=value)

    if (KafkaKey.DELETE.value == key):
        # delete location object itself
        l = Location.objects(id=int(value["id"])).first().delete()


func_dict = {
    KafkaTopic.AUTHOR.value: manage_author,
    KafkaTopic.CATEGORY.value: manage_category,
    KafkaTopic.LOCATION.value: manage_location
}


def run_consumer() -> None:
    print("Connecting to mongo database...")
    me.connect(host="mongodb://mongodb:27017/pdb", username="pdb", password="pdb", authentication_source="admin")

    print("Running Kafka consumer...")
    consumer = KafkaConsumer(
        "pdb",
        bootstrap_servers=['kafka:29092'],
        key_deserializer=lambda x: x.decode(),
        value_deserializer=lambda x: loads(x.decode("utf-8")),
        api_version=(0, 10, 2)
    )
    print("Subscribing to topics...")
    consumer.subscribe([t.value for t in KafkaTopic])

    print("Listening for messages...")
    for msg in consumer:
        topic = msg.topic
        key = msg.key
        value = msg.value
        print(f'{topic=}\t{key=}\t{value=}')

        # call function specified by topic name
        func_dict[msg.topic](key, value)


if __name__ == '__main__':
    run_consumer()