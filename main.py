import pickle
from collections import UserDict
from datetime import datetime, date, timedelta

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


def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            return str(e) if str(e) else "Value error."
        except KeyError as e:
            return str(e) if str(e) else "Enter user name."
        except IndexError:
            return "Not enough arguments."
        except AttributeError:
            return "Contact not found"
        except TypeError as e:
            return str(e) if str(e) else "Type error"

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
        message = "Contact updated"
    record.add_phone(phone)
    return message


@input_error
def change_contact(args, book: AddressBook):
    name, old_phone, new_phone, *_ = args
    record = book.find(name)
    if record is None:
        raise ValueError("Contact not found.")
    record.edit_phone(old_phone, new_phone)
    return "Contact updated."


@input_error
def show_phone(args, book: AddressBook):
    name, *_ = args
    record = book.find(name)
    if record is None:
        raise ValueError("Contact not found.")
    if not record.phones:
        return "No phones for this contact."
    return ";".join(p.value for p in record.phones)


def show_all(book: AddressBook):
    if not book.data:
        return "No contacts found."
    return "\n".join(str(record) for record in book.data.values())


@input_error
def add_birthday(args, book: AddressBook):
    name, date_str, *_ = args
    record = book.find(name)
    if record is None:
        raise ValueError("Contact not found")
    record.add_birthday(date_str)
    return "Birthday added"


@input_error
def show_birthday(args, book: AddressBook):
    name, *_ = args
    record = book.find(name)
    if record is None:
        raise ValueError("Contact not found")
    if not record.birthday:
        return "No birthday set"
    return record.birthday.value


@input_error
def birthdays(_, book: AddressBook):
    items = book.get_upcoming_birthdays()
    if not items:
        return "No upcoming birthdays."
    groups = {}
    for it in items:
        groups.setdefault(it["birthday"], []).append(it["name"])
    ordered = sorted(
        groups.items(), key=lambda kv: datetime.strptime(kv[0], "%d.%m.%Y")
    )
    lines = [f'{d}: {", ".join(names)}' for d, names in ordered]
    return "\n".join(lines)


def main():
    book = load_data()
    print("Welcome to the assistant bot!")
    while True:
        user_input = input("Enter a command: ")
        command, args = parse_input(user_input)

        if command in ["close", "exit"]:
            print("Good bye!")
            save_data(book)
            break

        elif command == "hello":
            print("How can I help you?")

        elif command == "add":
            print(add_contact(args, book))

        elif command == "change":
            print(change_contact(args, book))

        elif command == "phone":
            print(show_phone(args, book))

        elif command == "all":
            print(show_all(book))
        elif command == "add-birthday":
            print(add_birthday(args, book))
        elif command == "show-birthday":
            print(show_birthday(args, book))
        elif command == "birthdays":
            print(birthdays(args, book))
        else:
            print("Invalid command.")


if __name__ == "__main__":
    main()