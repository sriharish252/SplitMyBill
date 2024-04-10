import PyPDF2
import re
import logging

# Global Variables
actual_subtotal = 0.0
actual_total = 0.0
pdf_text = ""
shopped_items = []
quantity_list = []
people_list = []


# Global Regular expression patterns
price_with_float_pattern = r'\$\d+\.\d{2}'
price_pattern = r'\$\d(.*)'

def extract_text_from_pdf(pdf_path: str):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ''
        for page_num in range(len(reader.pages)):
            text += reader.pages[page_num].extract_text()
        return text

def extract_and_remove_unavailable_items(initial_pdf_text: str):
    extracted_pdf_text = ""
    unavailable_item_lines = []
    pdf_lines = []
    for line in initial_pdf_text.splitlines():
        if line.__contains__("Unavailable"):
            unavailable_item_lines.append(line)
        else:
            extracted_pdf_text += line + "\n"
    return unavailable_item_lines, extracted_pdf_text

def validate_price_string(price: str):
    try:
        # Split the string at the first occurrence of '$' (if present)
        parts = price.split('$', 1)
        if len(parts)>1:
            clean_price = parts[1]  # Take the part after the first '$'
        else:
            clean_price = parts[0]  # Take the part before the first '$'
        # Try converting the cleaned price to float
        float(clean_price)
        return True, clean_price
    except ValueError:
        return False, price

def extract_actual_subtotal(pdf_text):
    subtotal = 0.0
    # Extract actual_subtotal
    try:
        subtotal_after_savings_pattern = r'Savings\s+-\$(\d+\.\d{2})\n\$(\d+\.\d{2})'
        subtotal_match = re.search(subtotal_after_savings_pattern, pdf_text)
        subtotal = subtotal_match.group(2)
    except AttributeError:
        subtotal_pattern = r'\b(Subtotal|subtotal)\b\s+\$(\d+\.\d{2})'
        subtotal_match = re.search(subtotal_pattern, pdf_text)
        subtotal = subtotal_match.group(2)
    is_valid, subtotal = validate_price_string(str(subtotal))
    subtotal = round(float(subtotal), 2) if is_valid else 0.0
    return subtotal

def calculate_expected_subtotal(pdf_text):
    # Extract prices
    start_till_subtotal_pattern = r'^.*?(?=Subtotal)'
    prices_text_match = re.search(start_till_subtotal_pattern, pdf_text, re.DOTALL)
    prices_pdf_text = prices_text_match.group()
    price_matches = re.findall(price_with_float_pattern, prices_pdf_text)
    
    # Sum prices to calculate expected_subtotal
    expected_subtotal = 0.0
    for _, match in enumerate(price_matches):
        value = float(match.replace('$', ''))
        expected_subtotal += value
        print(value)
    return round(expected_subtotal, 2)

def extract_fees(pdf_text):
    fees_till_total_pattern = r'\b(delivery|Delivery)\b(.*)Total'
    fees_text_match = re.search(fees_till_total_pattern, pdf_text, re.DOTALL)
    fees_text = fees_text_match.group(0)

    # Extract delivery price 
    delivery_text_match = re.search(price_pattern, fees_text.splitlines()[0]) # Use only the 1st line in fees text
    delivery_text = delivery_text_match.group()
    prices = delivery_text.split()  # Split the text by spaces
    delivery_price = 0.0
    # Check if there are at least two prices, if yes take 2nd one, since the 1st delivery price is not valid
    if len(prices) >= 2:
        delivery_price = prices[1][1:]
    else:
        delivery_price = prices[0][1:]
    is_valid, delivery_price = validate_price_string(delivery_price)
    if is_valid:
        delivery_price = round(float(delivery_price), 2)
    else:
        print("Error in Delivery Price extraction.")
        delivery_price = 0.0

    fees_text = re.search(r'\n(.*)', fees_text, re.DOTALL).group()
    price_matches = re.findall(price_with_float_pattern, fees_text)

    # Sum prices to calculate fees
    fees = 0.0
    fees += delivery_price
    for i, match in enumerate(price_matches):
        value = float(match.replace('$', ''))
        fees += value
    return round(fees, 2)

def extract_total(pdf_text):
    total_pattern = r'\bTotal\b(.*)'
    total_text_match = re.search(total_pattern, pdf_text)
    total_text = total_text_match.group(0)

    total_prices_match = re.search(price_pattern, total_text)
    total_price = total_prices_match.group(0)

    # Remove the space between digits using string manipulation
    total_price = total_price.replace(" ", "")

    # Extract the cost using float conversion
    try:
        total_price = float(total_price[1:])  # Skip the dollar sign ($)
    except ValueError:
        print("Invalid total price format")
    return round(total_price, 2)

def extract_shopped_items_list(input_pdf_text: str):
    start_till_subtotal_pattern = r'^.*?(?=Subtotal)'
    items_text_match = re.search(start_till_subtotal_pattern, input_pdf_text, re.DOTALL)
    items_pdf_text = items_text_match.group()
    
    shopped_items_list = []
    item_description_wtih_qty_pattern = r'^.*\$'
    for line in items_pdf_text.splitlines():
        item_description = re.search(item_description_wtih_qty_pattern, line)
        if item_description:
            shopped_items_list.append(item_description.group()[:-1])
    return shopped_items_list

def verify_total_match(pdf_text):
    actual_subtotal = extract_actual_subtotal(pdf_text)
    expected_subtotal = calculate_expected_subtotal(pdf_text)
    print(f'Actual Subtotal: {actual_subtotal}\nExpected Subtotal: {expected_subtotal}')

    if actual_subtotal == expected_subtotal:
        print("SubTotal matches!")

    fees = extract_fees(pdf_text)
    print(f'Fees: {fees}')

    actual_total = extract_total(pdf_text)
    print(f'Actual Total Price: {actual_total}')

    expected_total = round(expected_subtotal + fees, 2)
    print(f'Expected Total Price: {expected_total}')

    if actual_total == expected_total:
        print("Total matches!")
        return True
    return False

def extract_quantity_list(shopped_items):
    quantity_list = []
    for item in shopped_items:
        # Split the string at "Qty"
        parts = item.split("Qty")
        # Check if there's a part after "Qty"
        if len(parts) > 1:
            # Extract the last element (assuming "Qty" is at the end)
            quantity = parts[-1].strip()
        else:
            quantity = "NA"  # Use "NA" if "Qty" is not found
        # Add the quantity to the list
        quantity_list.append(quantity)
    return quantity_list

def get_people_list_from_user():
    people = []
    while True:
        name = input("Enter a person's name (or press Enter to finish): ")
        # Check if user pressed Enter to finish
        if not name:
            break
        people.append(name)
    return people

def get_person_contribution_list(person: str, shopped_items : list):
    shop_list = []
    print(f"Enter the split of each item for {person}: (Enter value >=0)")
    for item in shopped_items:
        split_value = input(f"{item}: ")
        try:
            split_value = float(split_value)
        except ValueError:
            logging.error("Error converting String to Float")
            split_value = 0
        if split_value<0:
            logging.error("Split value must be positive")
            exit
        shop_list.append(split_value)
    return shop_list

####################################################

# Assign pdf_path variable with the path to your PDF bill receipt file
pdf_path = 'resources/billPDFs/Bill2_WithUnavailable.pdf'
pdf_text = extract_text_from_pdf(pdf_path)

if len(pdf_text)<2:
    logging.error("Unable to extract text, Image based PDF or incorrect PDF selected!")
    exit

unavailable_item_lines, pdf_text = extract_and_remove_unavailable_items(pdf_text)

verify_total_match(pdf_text)


shopped_items = extract_shopped_items_list(pdf_text)
print(shopped_items)

quantity_list = extract_quantity_list(shopped_items)
print(quantity_list) 

people_list = get_people_list_from_user()
print(people_list)

if len(people_list)<1:
    logging.error("Atleast one person must be specified, Try again!")
    exit
elif len(people_list)==1:
    print("Why are you even here? There's no one else to split the bill with.")
    exit

item_split_dict = {}
for person in people_list:
    item_split_dict[person] = get_person_contribution_list(person, shopped_items)
print(item_split_dict)

# TODO: Create a method to calculate the value of each person

# TODO: Mark the person who paid th bill, calculate how much each person owes the bill owner

