from collections import UserDict
from datetime import datetime, date, timedelta
from abc import ABC, abstractmethod
import pickle

def save_data(book, filename='addressbook.pkl'):
    with open(filename, 'wb') as f:
        pickle.dump(book, f)

def load_data(filename='addressbook.pkl'):
    try:
        with open(filename, 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()

class Field:
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return str(self.value)

class Name(Field):
    pass

class Phone(Field):
    def __init__(self, value):
        if not value.isdigit() or len(value) != 10:
            raise ValueError("Phone number must be exactly 10 digits.")
        super().__init__(value)

class Birthday(Field):
    def __init__(self, value):
        try:
            datetime.strptime(value, "%d.%m.%Y")
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")
        super().__init__(value)

class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def __str__(self):
        phones_str = ";".join(p.value for p in self.phones) if self.phones else ""
        birthday_str = f", birthday: {self.birthday.value}" if self.birthday else ""
        return f"Contact name: {self.name.value}, phones: {phones_str}{birthday_str}"

    def add_phone(self, phone):
        new_phone = Phone(phone)
        self.phones.append(new_phone)

    def remove_phone(self, phone: str):
        phone_obj = self.find_phone(phone)
        if phone_obj:
            self.phones.remove(phone_obj)
        else:
            raise ValueError("Phone number not found.")

    def edit_phone(self, old_phone: str, new_phone: str):
        if not self.find_phone(old_phone):
            raise ValueError("Old phone number not found.")
        self.add_phone(new_phone)
        self.remove_phone(old_phone)

    def find_phone(self, phone: str):
        for p in self.phones:
            if p.value == phone:
                return p
        return None

    def add_birthday(self, date_str: str):
        self.birthday = Birthday(date_str)

class AddressBook(UserDict):
    def add_record(self, record: Record):
        self.data[record.name.value] = record

    def find(self, name: str):
        return self.data.get(name, None)

    def delete(self, name: str):
        if name in self.data:
            del self.data[name]
        else:
            raise KeyError("Contact not found.")

    def get_upcoming_birthdays(self, days: int = 7):
        today = date.today()
        window = days - 1
        items = []

        for record in self.data.values():
            if not record.birthday:
                continue
            born = datetime.strptime(record.birthday.value, "%d.%m.%Y").date()
            this_year_bd = born.replace(year=today.year)
            if this_year_bd < today:
                this_year_bd = born.replace(year=today.year + 1)

            delta = (this_year_bd - today).days
            if 0 <= delta <= window:
                congr_date = this_year_bd
                if congr_date.weekday() >= 5:
                    shift = 7 - congr_date.weekday()
                    congr_date = congr_date + timedelta(days=shift)

                items.append(
                    (
                        congr_date,
                        {
                            "name": record.name.value,
                            "birthday": congr_date.strftime("%d.%m.%Y"),
                        },
                    )
                )

        items.sort(key=lambda t: t[0])
        return [d for _, d in items]

    def __str__(self):
        return "\n".join(str(record) for record in self.data.values())

class UserView(ABC):
    @abstractmethod
    def render_welcome(self): ...
    @abstractmethod
    def render_prompt(self): ...
    @abstractmethod
    def render_message(self, text): ...
    @abstractmethod
    def render_error(self, text): ...
    @abstractmethod
    def render_contact(self, record): ...
    @abstractmethod
    def render_contacts(self, records): ...
    @abstractmethod
    def render_help(self, commands): ...
    @abstractmethod
    def render_upcoming_birthdays(self, items): ...
    @abstractmethod
    def render_goodbye(self): ...
    @abstractmethod
    def read_command(self): ...

class ConsoleView(UserView):
    def render_welcome(self):
        print("Welcome to the assistant bot! Type 'help' to see commands.")

    def render_prompt(self):
        print("Enter a command: ", end="", flush=True)

    def render_message(self, text):
        print(text)

    def render_error(self, text):
        print(f"Error: {text}")

    def render_contact(self, record: Record):
        name = record.name.value
        phones = ";".join(p.value for p in record.phones) if record.phones else "—"
        bd = record.birthday.value if record.birthday else "—"
        print("Contact")
        print(f"- name: {name}")
        print(f"- phones: {phones}")
        print(f"- birthday: {bd}")

    def render_contacts(self, records):
        if not records:
            print("No contacts found.")
            return
        for i, rec in enumerate(records, start=1):
            name = rec.name.value
            phones = ";".join(p.value for p in rec.phones) if rec.phones else "—"
            bd = rec.birthday.value if rec.birthday else "—"
            print(f"{i}) {name} — {phones} — {bd}")

    def render_help(self, commands: dict):
        print("Available commands:")
        width = max(len(cmd) for cmd in commands.keys())
        for cmd, info in commands.items():
            desc = info.get("desc", "")
            ex = info.get("example", "")
            line = f"- {cmd.ljust(width)} — {desc}"
            if ex:
                line += f" | e.g. {ex}"
            print(line)

    def render_upcoming_birthdays(self, items):
        if not items:
            print("No upcoming birthdays.")
            return
        groups = {}
        for it in items:
            groups.setdefault(it["birthday"], []).append(it["name"])
        print("Upcoming birthdays (next 7 days):")
        for d in sorted(groups.keys(), key=lambda k: datetime.strptime(k, "%d.%m.%Y")):
            print(f"{d}: {', '.join(groups[d])}")

    def render_goodbye(self):
        print("Good bye!")

    def read_command(self):
        self.render_prompt()
        return input()

def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            msg = str(e) if str(e) else "Value error."
            return ("ERROR", msg)
        except KeyError as e:
            msg = str(e) if str(e) else "Enter user name."
            return ("ERROR", msg)
        except IndexError:
            return ("ERROR", "Not enough arguments.")
        except AttributeError:
            return ("ERROR", "Contact not found")
        except TypeError as e:
            msg = str(e) if str(e) else "Type error"
            return ("ERROR", msg)
    return inner

def parse_input(user_input):
    parts = user_input.strip().split()
    if not parts:
        return "", []
    cmd, *args = parts
    return cmd.lower(), args

@input_error
def add_contact(args, book: AddressBook):
    name, phone, *_ = args
    record = book.find(name)
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    else:
        message = "Contact updated."
    record.add_phone(phone)
    save_data(book)
    return ("OK", message)

@input_error
def change_contact(args, book: AddressBook):
    name, old_phone, new_phone, *_ = args
    record = book.find(name)
    if record is None:
        raise ValueError("Contact not found.")
    record.edit_phone(old_phone, new_phone)
    save_data(book)
    return ("OK", "Contact updated.")

@input_error
def show_phone(args, book: AddressBook):
    name, *_ = args
    record = book.find(name)
    if record is None:
        raise ValueError("Contact not found.")
    if not record.phones:
        return ("OK", "No phones for this contact.")
    return ("OK", ";".join(p.value for p in record.phones))

def show_all(book: AddressBook):
    if not book.data:
        return ("OK", "No contacts found.")
    return ("MANY_CONTACTS", list(book.data.values()))

@input_error
def add_birthday(args, book: AddressBook):
    name, date_str, *_ = args
    record = book.find(name)
    if record is None:
        raise ValueError("Contact not found")
    record.add_birthday(date_str)
    save_data(book)
    return ("OK", "Birthday added.")

@input_error
def show_birthday(args, book: AddressBook):
    name, *_ = args
    record = book.find(name)
    if record is None:
        raise ValueError("Contact not found")
    if not record.birthday:
        return ("OK", "No birthday set.")
    return ("OK", record.birthday.value)

@input_error
def birthdays(_, book: AddressBook):
    items = book.get_upcoming_birthdays()
    return ("UPCOMING_BIRTHDAYS", items)

def help_info():
    return ("HELP", {
        "hello": {"desc": "Greet the assistant"},
        "add <name> <phone>": {
            "desc": "Add phone to contact (create if not exists)",
            "example": "add Alice 0501234567",
        },
        "change <name> <old> <new>": {
            "desc": "Replace a phone number",
            "example": "change Alice 0501234567 0937654321",
        },
        "phone <name>": {
            "desc": "Show all phones for a contact",
            "example": "phone Alice",
        },
        "all": {"desc": "Show all contacts"},
        "add-birthday <name> <DD.MM.YYYY>": {
            "desc": "Set birthday for a contact",
            "example": "add-birthday Alice 14.03.1990",
        },
        "show-birthday <name>": {
            "desc": "Show contact's birthday",
            "example": "show-birthday Alice",
        },
        "birthdays": {"desc": "Upcoming birthdays for the next 7 days"},
        "help": {"desc": "Show this help"},
        "close | exit": {"desc": "Exit the program"},
    })

def main():
    book = load_data()
    view = ConsoleView()
    view.render_welcome()

    while True:
        raw = view.read_command()
        command, args = parse_input(raw)

        if command in ["close", "exit"]:
            view.render_goodbye()
            save_data(book)
            break

        elif command == "hello":
            view.render_message("How can I help you?")

        elif command == "help":
            tag, payload = help_info()
            view.render_help(payload)

        elif command == "add":
            tag, payload = add_contact(args, book)
            view.render_message(payload) if tag == "OK" else view.render_error(payload)

        elif command == "change":
            tag, payload = change_contact(args, book)
            view.render_message(payload) if tag == "OK" else view.render_error(payload)

        elif command == "phone":
            tag, payload = show_phone(args, book)
            view.render_message(payload) if tag == "OK" else view.render_error(payload)

        elif command == "all":
            tag, payload = show_all(book)
            if tag == "MANY_CONTACTS":
                view.render_contacts(payload)
            elif tag == "OK":
                view.render_message(payload)
            else:
                view.render_error(payload)

        elif command == "add-birthday":
            tag, payload = add_birthday(args, book)
            view.render_message(payload) if tag == "OK" else view.render_error(payload)

        elif command == "show-birthday":
            tag, payload = show_birthday(args, book)
            view.render_message(payload) if tag == "OK" else view.render_error(payload)

        elif command == "birthdays":
            tag, payload = birthdays(args, book)
            view.render_upcoming_birthdays(payload) if tag == "UPCOMING_BIRTHDAYS" else view.render_error(payload)

        elif command == "":
            continue

        else:
            view.render_error("Invalid command.")

if __name__ == "__main__":
    main()
