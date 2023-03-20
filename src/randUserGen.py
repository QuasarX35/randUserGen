import requests
from bs4 import BeautifulSoup
from faker import Faker
import random
from datetime import datetime
import re
import math


def generate_fake_nric(dob, dob_format='%Y-%m-%d', gender='M'):
    """
    Generates a random fake Malaysian NRIC number based on the date of birth.
    :param dob: date of birth string
    :param dob_format: format of date of birth string (default: '%Y-%m-%d')
    :param gender: gender of the person (default: 'M')
    :return: string representation of the generated NRIC number
    """
    # Extract the year, month, and day from the date of birth
    dob_date = datetime.strptime(dob, dob_format)
    year = dob_date.strftime('%y')
    month = dob_date.strftime('%m')
    day = dob_date.strftime('%d')

    # Generate the last four digits of the NRIC number
    last_four = '{:04d}'.format(random.randint(0, 9999))

    # Generate the first two digits of the NRIC number based on the birth year and gender
    if gender == 'M':
        first_two = '{:02d}'.format(random.randint(0, 49))
    elif gender == 'F':
        first_two = '{:02d}'.format(random.randint(50, 99))
    else:
        raise ValueError('Gender must be either "M" or "F"')

    # Calculate the check digit based on the first six digits of the NRIC number
    nric_digits = year + month + day + first_two + last_four
    weights = [2, 7, 6, 5, 4, 3, 2]
    sum = 0
    for i in range(len(weights)):
        sum += int(nric_digits[i]) * weights[i]
    remainder = sum % 11
    check_digit = 11 - remainder
    if check_digit == 10:
        check_digit = 'A'
    elif check_digit == 11:
        check_digit = 'B'
    else:
        check_digit = str(check_digit)

    # Construct the final NRIC number
    nric_number = '{}{}-{}-{}'.format(year, month,
                                      day, first_two + last_four + check_digit)

    return nric_number


def parse_config(file_path):
    """
    Parse a configuration file and return a dictionary of configuration options.

    The function takes a file path as an argument and reads the contents of the file.
    The file should contain configuration options in the following format:
    key: value

    If a line starts with "#" or is empty, it will be ignored.

    If a line starts with "default_", it will be treated as a default value.
    Default values are stored in a separate dictionary and are used when a key is not found in the main dictionary.

    The function returns a dictionary containing the configuration options.
    If a key is not found in the main dictionary, the function will use the default value for that key.

    :param file_path: The path to the configuration file.
    :return: A dictionary containing the configuration options.
    """
    with open(file_path, "r") as configFile:
        default_config = {}
        config_dict = {}
        for line in configFile:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if line.startswith("default_"):
                d_key, d_value = line.split(":", maxsplit=1)
                d_key = d_key.replace("default_", "")
                if d_value.lower() == "true":
                    d_value = True
                elif d_value.lower() == "false":
                    d_value = False
                elif d_value.isdigit():
                    d_value = int(d_value)
                default_config[d_key] = d_value

            key, value = line.split(":", maxsplit=1)
            key = key.strip()
            value = value.strip()
            if value.lower() == "true":
                value = True
            elif value.lower() == "false":
                value = False
            elif value.isdigit():
                value = int(value)
            elif value == '':
                value = default_config[key]
            config_dict[key] = value

    return config_dict


if __name__ == "__main__":
    faker = Faker()

    config = parse_config("config.txt")
    num_users = config["num_users"]
    if config["replace_spaces"] == True:
        space_char = config["space_char"]

    url = 'https://www.random-name-generator.com/malaysia?s=' + str(random.randint(100, 999)) + '&gender=&n=' + str(num_users)
    response = requests.get(url)
    html_content = response.content

    soup = BeautifulSoup(html_content, 'html.parser')

    id_counter = 1
    name_elements = soup.find_all('dd', {'class': 'h4 col-12'})
    attribute_elements = soup.find_all('dd', {'class': 'col-sm-8'})
    attributes = [a.text.strip() for a in attribute_elements]

    ids = [config["id_format"].format(i + 1) for i in range(num_users)]
    names = [n.text.strip().split("(")[0][:-1] for n in name_elements]
    if config["replace_spaces"] == True:
        names = [name.replace(" ", space_char) for name in names]
    genders = [g.text.strip().split("(")[1][:-1] for g in name_elements]

    iterables = []
    for i in range(6):
        if i == 3:
            continue
        lst = attributes[i::11]
        if i == 0 and config["replace_spaces"] == True:
            lst = [address.replace(" ", space_char) for address in lst]
        iterables.append(lst)
    
    dobs = []
    ics = []
    for i in range(num_users):
        dob = faker.date_of_birth(minimum_age=config["minimum_age"], maximum_age=config["maximum_age"])
        dob = dob.strftime(config["dob_format"])
        dobs.append(dob)
        ic = generate_fake_nric(dob, config["dob_format"])
        ics.append(ic)
    
    user_attrs = list(zip(ids, names, genders, *iterables, dobs, ics))

    users = []
    attr_keys = ["ID", "Name", "Gender", "Address", "Phone Number", "Email", "Username", "Password", "Date of Birth", "NRIC"]
    for user in user_attrs:
        user_details = dict(zip(attr_keys, user))
        users.append(user_details)

    with open(config["output_file"], "w") as output_file:
        result_string = ""
        for user in users:
            # print user details
            for detail in user:
                print(f"{detail} : {user[detail]}")
            print()

            user_details_string = config["data_format"].format(
                id=user['ID'],
                name=user['Name'],
                email=user['Email'],
                username=user['Username'],
                password=user['Password'],
                gender=user['Gender'],
                phone_number=user['Phone Number'],
                dob=user['Date of Birth'],
                ic_number=user['NRIC'],
                address=user['Address']
            ) + '\n'

            result_string += user_details_string

        # write user details to the file
        output_file.write(result_string)
