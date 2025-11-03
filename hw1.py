from collections import UserDict
from typing import List, Optional, Callable
from datetime import date, datetime, timedelta

def input_error(func: Callable):
    """
    Decorator for handling user input errors.
    Handles KeyError, ValueError, IndexError and returns friendly messages.
    Program execution does not stop.
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyError:
            return "Contact not found. Please check the name."
        except ValueError:
            return "Give me name and phone please."
        except IndexError:
            return "Enter user name."
        except Exception as e:
            return f"Unexpected error: {e}"
    return wrapper


class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.value!r})"


class Name(Field):
    def __init__(self, value: str):
        if not isinstance(value, str):
            raise TypeError("Name must be a string.")
        name = value.strip()
        if not name:
            raise ValueError("Name cannot be empty.")
        super().__init__(name)


class Phone(Field):
    def __init__(self, value: str):
        if not isinstance(value, str):
            raise TypeError("Phone must be a string of digits.")
        digits = value.strip()
        if not digits.isdigit() or len(digits) != 10:
            raise ValueError("Phone must contain exactly 10 digits.")
        super().__init__(digits)


class Birthday(Field):
    def __init__(self, value: str):
        if not isinstance(value, str):
            raise TypeError("Birthday must be a string in 'DD.MM.YYYY' format.")
        try:
            date = datetime.strptime(value.strip(), '%d.%m.%Y').date()
        except ValueError:
            raise ValueError("Birthday date must be in 'DD.MM.YYYY' format.")
        super().__init__(date)

    def __str__(self):
        return self.value.strftime('%d.%m.%Y')


class Record:
    def __init__(self, name: str):
        self.name = Name(name)
        self.phones: List[Phone] = []
        self.birthday = None

    def edit_birthday(self, birthday_str: str) -> None:
        self.birthday = Birthday(birthday_str)

    def remove_birthday(self) -> None:
        self.birthday = None

    def add_phone(self, phone_str: str) -> None:
        phone = Phone(phone_str)
        self.phones.append(phone)

    def remove_phone(self, phone_str: str) -> None:
        for i, ph in enumerate(self.phones):
            if ph.value == phone_str:
                del self.phones[i]
                return
        raise ValueError(f"Phone '{phone_str}' not found for contact '{self.name.value}'.")

    def edit_phone(self, old_phone: str, new_phone: str) -> None:
        for i, ph in enumerate(self.phones):
            if ph.value == old_phone:
                new_ph = Phone(new_phone)
                self.phones[i] = new_ph
                return
        raise ValueError(f"Old phone '{old_phone}' not found for contact '{self.name.value}'.")

    def find_phone(self, phone_str: str) -> Optional[Phone]:
        for ph in self.phones:
            if ph.value == phone_str:
                return ph
        return None

    def __str__(self) -> str:
        phones_str = "; ".join(p.value for p in self.phones) if self.phones else "No phones"
        return f"Contact name: {self.name.value}, phones: {phones_str}, birthday:{self.birthday}"

    def __repr__(self) -> str:
        return f"Record(name={self.name!r}, phones={self.phones!r}, birthday={self.birthday})"


class AddressBook(UserDict):
    def add_record(self, record: Record) -> None:
        if not isinstance(record, Record):
            raise TypeError("add_record expects a Record instance.")
        self.data[record.name.value] = record

    def find(self, name: str) -> Optional[Record]:
        return self.data.get(name)

    def delete(self, name: str) -> bool:
        if name in self.data:
            del self.data[name]
            return True
        return False

    def get_upcoming_birthdays(self) -> List[dict]:
        upcoming = []
        today = date.today()
        for record in self.data.values():
            if not record.birthday:
                continue
            bday: date = record.birthday.value
            this_year_bday = bday.replace(year=today.year)
            if this_year_bday < today:
                this_year_bday = this_year_bday.replace(year=today.year + 1)
            delta_days = (this_year_bday - today).days
            if 0 <= delta_days <= 7:
                congratulate_day = this_year_bday
                if congratulate_day.weekday() >= 5:
                    shift = 7 - congratulate_day.weekday()
                    congratulate_day += timedelta(days=shift)

                upcoming.append({
                    "name": record.name.value,
                    "birthday": congratulate_day.strftime("%Y-%m-%d")
                })
        return upcoming

    def __str__(self) -> str:
        if not self.data:
            return "<AddressBook: empty>"
        lines = []
        for name, record in self.data.items():
            lines.append(str(record))
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"AddressBook({self.data!r})"


def parse_input(user_input: str) -> (str, List[str]):
    """Parsing user input into command and arguments."""
    parts = user_input.strip().split()
    if not parts:
        return "", []
    cmd = parts[0].lower()
    args = parts[1:]
    return cmd, args


@input_error
def add_contact(args: List[str], contacts: AddressBook) -> str:
    """Adds a new contact to the AddressBook."""
    name, phone = args
    existing_record = contacts.find(name)
    if existing_record:
        existing_record.add_phone(phone)
        return f"Added phone '{phone}' to existing contact '{name}'."
    record = Record(name)
    record.add_phone(phone)
    contacts.add_record(record)
    return f"Contact '{name}' with phone '{phone}' added."


@input_error
def add_birthday(args: List[str], contacts: AddressBook) -> str:
    """Adds birthday to the contact."""
    name, birthday = args
    existing_record = contacts.find(name)
    if not existing_record:
        raise KeyError
    existing_record.edit_birthday(birthday)
    return f"Added birthday '{birthday}' to existing contact '{name}'."


@input_error
def show_birthday(args: List[str], contacts: AddressBook) -> str:
    """Show contact's birthday's."""
    name = args[0]
    existing_record = contacts.find(name)
    if not existing_record:
        raise KeyError
    return f"{name}: {existing_record.birthday}."


@input_error
def birthdays(args: List[str], contacts: AddressBook) -> str:
    """Show birthdays for the next 7 days with the dates when they should be congratulated."""
    upcoming = contacts.get_upcoming_birthdays()
    lines = ["Upcoming birthdays (next 7 days):"]
    for contact in upcoming:
        lines.append(f"{contact['name']} -> {contact['birthday']}")
    return "\n".join(lines)


@input_error
def change_contact(args: List[str], contacts: AddressBook) -> str:
    """Changes the phone number for an existing contact."""
    name, old_phone, new_phone = args
    record = contacts.find(name)
    if not record:
        raise KeyError
    record.edit_phone(old_phone, new_phone)
    return f"Contact '{name}': phone '{old_phone}' changed to '{new_phone}'."


@input_error
def show_phone(args: List[str], contacts: AddressBook) -> str:
    """Shows all phones of a contact by name."""
    name = args[0]
    record = contacts.find(name)
    if not record:
        raise KeyError
    phones = "; ".join(ph.value for ph in record.phones) if record.phones else "No phones"
    return f"{name}: {phones}"


@input_error
def show_all(args: List[str], contacts: AddressBook) -> str:
    """Shows all contacts in the AddressBook."""
    if not contacts.data:
        return "No contacts saved."
    lines = []
    for record in contacts.data.values():
        phones = "; ".join(ph.value for ph in record.phones) if record.phones else "No phones"
        lines.append(f"{record.name.value}: phones: {phones}")
    return "\n".join(lines)


def help_text() -> str:
    return (
        "Available commands:\n"
        "  add [name] [phone]    - add a new contact\n"
        "  change [name] [old phone] [phone] - change phone of existing contact\n"
        "  phone [name]          - show phone of contact\n"
        "  add-birthday [name] [birthday] - add contact's birthday\n"
        "  show-birthday [name] - show contact's birthday\n"
        "  birthdays - show birthdays for the next 7 days with the dates when they should be congratulated.\n"
        "  all                   - show all contacts\n"
        "  hello                 - greet\n"
        "  exit / close / good bye - exit the program\n"
    )

if __name__ == "__main__":
    book = AddressBook()
    print("Welcome to the assistant bot!")
    print(help_text())


    command_handlers = {
        "add": add_contact,
        "change": change_contact,
        "phone": show_phone,
        "all": show_all,
        "add-birthday": add_birthday,
        "show-birthday": show_birthday,
        "birthdays": birthdays,
    }

    while True:
        user_input = input("Enter a command: ")
        command, args = parse_input(user_input)

        if command in ("exit", "close", "goodbye"):
            print("Good bye!")
            break

        if command == "":
            continue

        if command == "hello":
            print("How can I help you?")
            continue

        if command == "help":
            print(help_text())
            continue

        handler = command_handlers.get(command)
        if handler:
            result = handler(args, book)
            print(result)
        else:
            print("Invalid command. Type 'help' to see available commands.")








"""
    'AddressBook test'
    book = AddressBook()


    john_record = Record("John")
    john_record.add_phone("1234567890")
    john_record.add_phone("5555555555")
    john_record.edit_birthday((date.today() + timedelta(days=1)).strftime("%Y-%m-%d"))  # ДР завтра
    book.add_record(john_record)

    jane_record = Record("Jane")
    jane_record.add_phone("9876543210")
    jane_record.edit_birthday((date.today() + timedelta(days=6)).strftime("%Y-%m-%d"))  # ДР через 6 дней
    book.add_record(jane_record)

    bob_record = Record("Bob")
    bob_record.add_phone("2223334444")

    book.add_record(bob_record)

    print("All contacts:")
    print(book)
    print("------")


    john = book.find("John")
    if john:
        john.edit_phone("1234567890", "1112223333")
    print("After edit John:")
    print(john)


    found_phone = john.find_phone("5555555555") if john else None
    print(f"{john.name.value}: {found_phone.value if found_phone else 'not found'}")


    deleted = book.delete("Jane")
    print(f"Jane deleted: {deleted}")

    print("Final address book:")
    print(book)
    print("------")


    upcoming = book.get_upcoming_birthdays()
    print("Upcoming birthdays (next 7 days):")
    for contact in upcoming:
        print(f"{contact['name']} -> {contact['birthday']}")


    next_saturday = date.today() + timedelta((5 - date.today().weekday()) % 7)
    weekend_record = Record("WeekendGuy")
    weekend_record.edit_birthday(next_saturday.strftime("%Y-%m-%d"))
    book.add_record(weekend_record)

    print("Upcoming birthdays including weekend adjustment:")
    upcoming = book.get_upcoming_birthdays()
    for contact in upcoming:
        print(f"{contact['name']} -> {contact['birthday']}") """