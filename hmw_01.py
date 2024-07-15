import re
import pickle
from datetime import datetime, timedelta
from collections import UserDict
from abc import ABC, abstractmethod

class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

class Name(Field):
    pass

class Phone(Field):
    def __init__(self, value):
        if not re.match(r'^\d{10}$', value):
            raise ValueError("Phone number must be 10 digits.")
        super().__init__(value)

class Birthday(Field):
    def __init__(self, value):
        try:
            self.value = datetime.strptime(value, "%d.%m.%Y")
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")

class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    def remove_phone(self, phone):
        phone_obj = self.find_phone(phone)
        if phone_obj:
            self.phones.remove(phone_obj)

    def edit_phone(self, old_phone, new_phone):
        phone_obj = self.find_phone(old_phone)
        if phone_obj:
            try:
                self.phones.remove(phone_obj)
                self.add_phone(new_phone)
            except ValueError as e:
                raise ValueError(str(e))
        else:
            raise ValueError("Old phone not found.")

    def find_phone(self, phone):
        for p in self.phones:
            if p.value == phone:
                return p
        return None

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def __str__(self):
        phones = "; ".join(str(p) for p in self.phones)
        birthday = self.birthday.value.strftime("%d.%m.%Y") if self.birthday else "Not set"
        return f"Contact name: {self.name.value}, phones: {phones}, birthday: {birthday}"

class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        if name in self.data:
            del self.data[name]

    def get_upcoming_birthdays(self, days=7):
        today = datetime.now()
        upcoming = []
        for record in self.data.values():
            if record.birthday:
                next_birthday = record.birthday.value.replace(year=today.year)
                if today <= next_birthday <= today + timedelta(days=days):
                    upcoming.append(record)
        return upcoming

def input_error(handler):
    def wrapper(*args, **kwargs):
        try:
            return handler(*args, **kwargs)
        except (ValueError, IndexError, KeyError) as e:
            return str(e)
    return wrapper

@input_error
def add_contact(args, book: AddressBook):
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return message

@input_error
def change_phone(args, book: AddressBook):
    name, old_phone, new_phone = args
    record = book.find(name)
    if record:
        record.edit_phone(old_phone, new_phone)
        return "Phone number updated."
    else:
        return "Contact not found."

@input_error
def show_phone(args, book: AddressBook):
    name, *_ = args
    record = book.find(name)
    if record:
        return f"{name}: {', '.join(str(phone) for phone in record.phones)}"
    else:
        return "Contact not found."

@input_error
def add_birthday(args, book: AddressBook):
    name, birthday = args
    record = book.find(name)
    if record:
        record.add_birthday(birthday)
        return "Birthday added."
    else:
        return "Contact not found."

@input_error
def show_birthday(args, book: AddressBook):
    name, *_ = args
    record = book.find(name)
    if record:
        if record.birthday:
            return f"{name}'s birthday is {record.birthday.value.strftime('%d.%m.%Y')}"
        else:
            return f"{name} has no birthday set."
    else:
        return "Contact not found."

@input_error
def show_birthdays(args, book: AddressBook):
    upcoming = book.get_upcoming_birthdays()
    if upcoming:
        return "\n".join(str(record) for record in upcoming)
    else:
        return "No upcoming birthdays."

def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)

def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()

class BaseView(ABC):
    @abstractmethod
    def show_message(self, message):
        pass

    @abstractmethod
    def show_contacts(self, contacts):
        pass

    @abstractmethod
    def show_commands(self):
        pass

class ConsoleView(BaseView):
    def show_message(self, message):
        print(message)

    def show_contacts(self, contacts):
        for contact in contacts:
            print(contact)

    def show_commands(self):
        commands = [
            "add [name] [phone]: Add a new contact with name and phone or update phone for existing contact.",
            "change [name] [old phone] [new phone]: Change the phone number for the specified contact.",
            "phone [name]: Show the phone number for the specified contact.",
            "all: Show all contacts in the address book.",
            "add-birthday [name] [birthday]: Add a birthday for the specified contact.",
            "show-birthday [name]: Show the birthday for the specified contact.",
            "birthdays: Show upcoming birthdays within the next week.",
            "hello: Get a greeting from the bot.",
            "close or exit: Close the application."
        ]
        print("\n".join(commands))

class AddressBookApp:
    def __init__(self, view: BaseView):
        self.book = load_data()
        self.view = view

    def parse_input(self, user_input):
        parts = user_input.split()
        return parts[0], parts[1:]

    def execute_command(self, command, args):
        if command == "add":
            self.view.show_message(add_contact(args, self.book))
        elif command == "change":
            self.view.show_message(change_phone(args, self.book))
        elif command == "phone":
            self.view.show_message(show_phone(args, self.book))
        elif command == "all":
            self.view.show_contacts(self.book.values())
        elif command == "add-birthday":
            self.view.show_message(add_birthday(args, self.book))
        elif command == "show-birthday":
            self.view.show_message(show_birthday(args, self.book))
        elif command == "birthdays":
            self.view.show_message(show_birthdays(args, self.book))
        elif command == "hello":
            self.view.show_message("How can I help you?")
        elif command in ["close", "exit"]:
            save_data(self.book)
            self.view.show_message("Goodbye!")
            return False
        else:
            self.view.show_message("Invalid command.")
        return True

    def run(self):
        self.view.show_message("Welcome to the assistant bot!")
        self.view.show_commands()
        while True:
            user_input = input("Enter a command: ")
            command, args = self.parse_input(user_input)
            if not self.execute_command(command, args):
                break

if __name__ == "__main__":
    view = ConsoleView()
    app = AddressBookApp(view)
    app.run()