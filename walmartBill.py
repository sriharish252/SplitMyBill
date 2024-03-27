import PyPDF2
import re

# Global Variables
actual_subtotal = 0.0
actual_total = 0.0
pdf_text = ""

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
    global pdf_text
    pdf_text = ""
    pdf_text_lines = initial_pdf_text.splitlines()
    unavailable_item_lines = []
    pdf_lines = []
    for line in pdf_text_lines:
        if line.__contains__("Unavailable"):
            unavailable_item_lines.append(line)
        else:
            pdf_text += line + "\n"
    return unavailable_item_lines

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
    for i, match in enumerate(price_matches):
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


# Replace 'path_to_pdf.pdf' with the path to your PDF bill receipt file
pdf_path = 'Bill2_WithUnavailable.pdf'
pdf_text = extract_text_from_pdf(pdf_path)

if len(pdf_text)<2:
    print("Unable to extract text, Image based PDF or incorrect PDF selected!")
    exit

unavailable_items = extract_and_remove_unavailable_items(pdf_text)
print(pdf_text)


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
