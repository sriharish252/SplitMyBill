import PyPDF2
import re

# Global Variables
actual_subtotal = 0.0
actual_total = 0.0

# Global Regular expression patterns
price_pattern = r'\$\d+\.\d{2}'

def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ''
        for page_num in range(len(reader.pages)):
            text += reader.pages[page_num].extract_text()
        return text

def calculate_expected_subtotal(pdf_text):
    # Regular expression patterns for different values
    subtotal_after_savings_pattern = r'Savings\s+-\$(\d+\.\d{2})\n\$(\d+\.\d{2})'
    start_till_subtotal_pattern = r'^.*?(?=Subtotal)'
    
    # Extract actual_subtotal
    actual_subtotal_match = re.search(subtotal_after_savings_pattern, pdf_text)
    global actual_subtotal
    actual_subtotal = float(actual_subtotal_match.group(2))
    # group number '2' since the second price is our subtotal. 1st is the savings value.

    # Extract prices
    prices_text_match = re.search(start_till_subtotal_pattern, pdf_text, re.DOTALL)
    prices_pdf_text = prices_text_match.group()
    price_matches = re.findall(price_pattern, prices_pdf_text)
    
    # Sum prices to calculate expected_subtotal
    expected_subtotal = 0.0
    for i, match in enumerate(price_matches):
        value = float(match.replace('$', ''))
        expected_subtotal += value
    return round(expected_subtotal, 2)

def extract_fees(pdf_text):
    fees_till_end_pattern = r'\b(delivery|Delivery)\b(.*)'
    fees_text_match = re.search(fees_till_end_pattern, pdf_text, re.DOTALL)
    fees_text = fees_text_match.group(0)

    delivery_pattern = r'\$\d(.*)'
    delivery_text_match = re.search(delivery_pattern, fees_text.splitlines()[0]) # Use only the 1st line in fees text
    delivery_text = delivery_text_match.group()
    prices = delivery_text.split()  # Split the text by spaces
    delivery_price = 0.0
    # Check if there are at least two prices, if yes take 2nd one, since the 1st delivery price is not valid
    if len(prices) >= 2:
        delivery_price = prices[1][1:]
    else:
        delivery_price = prices[0][1:]
    delivery_price = round(float(delivery_price), 2)

    fees_text = re.search(r'\n(.*)', fees_text, re.DOTALL).group()
    price_matches = re.findall(price_pattern, fees_text)

    # Sum prices to calculate fees
    fees = 0.0
    fees += delivery_price
    for i, match in enumerate(price_matches):
        value = float(match.replace('$', ''))
        fees += value
    return round(fees, 2)
    


# Replace 'path_to_pdf.pdf' with the path to your PDF bill receipt file
pdf_path = 'Bill1.pdf'
pdf_text = extract_text_from_pdf(pdf_path)

expected_subtotal = calculate_expected_subtotal(pdf_text)

print(f'Actual Subtotal: {actual_subtotal}\nExpectedSubtotal: {expected_subtotal}')

if actual_subtotal == expected_subtotal:
    print("SubTotal matches!")

fees = extract_fees(pdf_text)
print(f'Fees: {fees}')

