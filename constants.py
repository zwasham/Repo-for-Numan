# Import packages
from openai import OpenAI
from os import getenv
from datetime import date
from pandas import Timestamp

# Use the environment variable OPENAI_API_KEY to define an OpenAI API client.
open_ai_api_key = getenv('OPENAI_API_KEY')
client = OpenAI(api_key = open_ai_api_key)

# Define a string with today's date in YYYY.MM.DD format.
TODAY = date.today().strftime('%Y.%m.%d')

# Define a cutoff date for isolating new transactions.
CUTOFF_DATE = Timestamp('4/1/24')

# Define file paths.
# Note: Files must contain a 'Description' column to be compatible with the simple_labeler and llm_labeler
# functions.
PATH_DICT = {
    'Amazon Order History' : 'Data/1. Initial/Amazon Order History.csv',
    "Emily's B of A Checking Transactions" : 'Data/1. Initial/Emily Bank of America Checking.csv',
    "Emily's B of A Credit Card Transactions" : 'Data/1. Initial/Emily Bank of America Credit Card.csv',
    "Emily's Chase Credit Card Transactions" : 'Data/1. Initial/Emily Chase Credit Card.csv',
    "Zach's WF Checking Transactions" : 'Data/1. Initial/Zach Wells Fargo Checking.csv',
    'Historical Data' : 'Data/0. Historical/Historical Data.csv'
}

# Define the last four digits of Emily's Chase credit card (for filtering Amazon product purchases).
LAST_FOUR = '0298'    # Alter this in the public version.

# Map vendor codes to vendor names, categories, and subcategories.    Collapse spaces in the public version.
VENDOR_DICT = {
    'WASHAM MEGAN': {'Vendor': 'Megan Washam', 'Category': 'Rent'},
    'DEPT EDUCATION DES:STUDENT LN': {'Vendor': 'Department of Education', 'Category': 'Debt', 'Subcategory': 'Student Loan'},
    'BANK OF AMERICA VEHICLE LOAN': {'Vendor': 'Bank of America', 'Category': 'Debt', 'Subcategory': 'Fiesta Loan'},
    'IRS USA': {'Vendor': 'IRS', 'Category': 'Taxes'},
    'ALDI': {'Vendor': 'Aldi', 'Category': 'Groceries'},
    'KROGER': {'Vendor': 'Kroger', 'Category': 'Groceries'},
    'TOM THUMB': {'Vendor': 'Tom Thumb', 'Category': 'Groceries'},
    'THECOLONYWTRUTIL': {'Vendor': 'The Colony', 'Category': 'Utilities', 'Subcategory': 'Water'},
    'GREEN MOUNTAIN ENERGY': {'Vendor': 'Green Mountain Energy', 'Category': 'Utilities', 'Subcategory': 'Electricity'},
    'ATT': {'Vendor': 'AT&T', 'Category': 'Utilities', 'Subcategory': 'Internet'},
    'SIMPLISAFE': {'Vendor': 'SimpliSafe', 'Category': 'Security'},
    'MOW MORE LANDSCAPES': {'Vendor': 'Mow More Landscapes', 'Category': 'Landscaping'},
    'NTTA': {'Vendor': 'NTTA', 'Category': 'Automotive', 'Subcategory': 'Tolls'},
    'CIRCLE K': {'Vendor': 'Circle K', 'Category': 'Automotive', 'Subcategory': 'Gas'},
    'EXXON': {'Vendor': 'Exxon', 'Category': 'Automotive', 'Subcategory': 'Gas'},
    'QT ': {'Vendor': 'QT', 'Category': 'Automotive', 'Subcategory': 'Gas'},
    'RACETRAC': {'Vendor': 'RaceTrac', 'Category': 'Automotive', 'Subcategory': 'Gas'},
    'ZOOM': {'Vendor': 'Zoom', 'Category': 'Subscriptions'},
    'GITHUB': {'Vendor': 'GitHub', 'Category': 'Subscriptions', 'Subcategory': 'Washam Consulting'},
    'OPENAI': {'Vendor': 'OpenAI', 'Category': 'Subscriptions', 'Subcategory': 'AI'},
    'SQSP': {'Vendor': 'Squarespace', 'Category': 'Subscriptions', 'Subcategory': 'Web and Email Hosting'},
    'ADOBE': {'Vendor': 'Adobe', 'Category': 'Subscriptions'},
    'APPLE.COM': {'Vendor': 'Apple', 'Category': 'Subscriptions', 'Subcategory': 'Cloud Storage'},
    'GOOGLE': {'Vendor': 'Google', 'Category': 'Subscriptions', 'Subcategory': 'Cloud Storage'},
    'BCBS': {'Vendor': 'Blue Cross Blue Shield', 'Category': 'Health & Personal Care', 'Subcategory': 'Health Insurance'},
    'CHMAPI': {'Vendor': 'CHM', 'Category': 'Health & Personal Care', 'Subcategory': 'Health Insurance'},
    'UNITEDHEALTHCARE': {'Vendor': 'UnitedHealthcare', 'Category': 'Health & Personal Care', 'Subcategory': 'Health Insurance'},
    'LEGACY OBGYN': {'Vendor': 'Legacy OB/GYN', 'Category': 'Health & Personal Care', 'Subcategory': 'Healthcare Services'},
    'GREAT CLIPS': {'Vendor': 'Great Clips', 'Category': 'Health & Personal Care'},
    'PLANET FITNESS': {'Vendor': 'Planet Fitness', 'Category': 'Other', 'Subcategory': 'Gym & Fitness'},
    'JW HOPP': {'Vendor': 'JW Hopp', 'Category': 'Other', 'Subcategory': 'Accounting Services'},
    'MARCUS AV': {'Vendor': 'Marcus', 'Category': 'Charity'},
    'TLEGROW01': {'Vendor': 'Tim', 'Category': 'Charity'},
    'BRAUMS': {'Vendor': 'Braums', 'Category': 'Other Food & Beverage'},
    'CAVA': {'Vendor': 'Cava', 'Category': 'Other Food & Beverage'},
    'CHIPOTLE': {'Vendor': 'Chipotle', 'Category': 'Other Food & Beverage'},
    'HAYSTACK': {'Vendor': 'Haystack', 'Category': 'Other Food & Beverage'},
    'Prime Video': {'Vendor': 'Amazon', 'Category': 'Entertainment'},
    'MICROSOFT*REALMS': {'Vendor': 'Microsoft', 'Category': 'Entertainment'},
    'ANNUAL MEMBERSHIP FEE': {'Vendor': 'Chase', 'Category': 'Subscriptions', 'Subcategory': 'Annual Credit Card Fees'},
    'HOME DEPOT': {'Vendor': 'Home Depot', 'Category': 'Home & Kitchen'},
    'AMAZON': {'Vendor': 'Amazon', 'Category': 'Other'},
    'Amazon': {'Vendor': 'Amazon', 'Category': 'Other'},
    'TJX': {'Vendor': 'T.J. Maxx', 'Category': 'Other'},
    'VENMO': {'Vendor': 'Venmo', 'Category': 'Other'},
    'WAL-MART': {'Vendor': 'Walmart', 'Category': 'Other'},
    'Wal-Mart': {'Vendor': 'Walmart', 'Category': 'Other'},
    'MATHEW RAGUINDIN': {'Vendor': 'Sean', 'Category': 'Other'}
 }

# Define a dictionary of old and new category names for Emily's Chase credit card transactions.
CHASE_CATEGORY_DICT = {
'Food & Drink': {'New Category': 'Other Food & Beverage', 'New Subcategory': ''},
'Gifts & Donations': {'New Category': 'Charity', 'New Subcategory': ''},
'Health & Wellness': {'New Category': 'Health & Personal Care', 'New Subcategory': ''},
'Health & Other Care': {'New Category': 'Health & Personal Care', 'New Subcategory': ''},
'Shopping': {'New Category': 'Other', 'New Subcategory': ''},
'Education': {'New Category': 'Other', 'New Subcategory': ''},
'Fees & Adjustments': {'New Category': 'Other', 'New Subcategory': ''},
'Bills & Utilities': {'New Category': 'Other', 'New Subcategory': ''},
'Professional Services': {'New Category': 'Other', 'New Subcategory': ''},
'Personal': {'New Category': 'Other', 'New Subcategory': ''},
'Home': {'New Category': 'Home & Kitchen', 'New Subcategory': ''},
'Gas': {'New Category': 'Automotive', 'New Subcategory': 'Gas'}
}

# Define a dictionary of Description substrings that indicate special transactions.
SPECIAL_SUBSTRINGS = {
    'z' : {
        'income' : '|'.join([
            'ZELLE FROM MACHINE LEARNING EDGE',
            'ZELLE FROM GILL A CHOWDHURY'
        ]),
        'exclusion' : '|'.join([
            'ZELLE TO WASHAM EMILY',
            'ZELLE TO BARLOW EMILY',
            'CHASE CREDIT CRD EPAY',
            'MOBILE DEPOSIT'
        ])
    },
    'e' : {
        'income' : '|'.join([
            'INSERT SUBSTRING HERE'    # Placeholder
        ]),
        'exclusion' : '|'.join([
            'RICHARDSON ISD DES:PAYROLL',    # Emily no longer works for Richardson ISD, so I will not need to extract these transactions for income analysis in the future. Therefore, I have placed this substring in the 'exclusion' item instead of the 'income' item.
            'KAIKOA LLC',    # Nanny income from the Jacobs. Same comment as Richardson ISD.
            'VENMO DES:CASHOUT',
            'Zelle payment from ZACHARY WASHAM',    # The simpler string 'Zelle payment from' would match cost sharing transactions (e.g. 'Zelle payment from Joey for hot pot') that I want to include in the analysis.
            'Zelle payment from CHRIS B WASHAM',
            'Zelle payment from Jason Barlow',
            'Online Banking transfer from',
            'BKOFAMERICA ATM',
            'Beginning balance',    # The beginning balance line of the Bank of America checking data.
            'BANK OF AMERICA CREDIT CARD',
            'Bank of America Credit Card',
            'CHASE CREDIT CRD DES:EPAY',    # Checking account debits from payments to Chase
            'Payment Thank You-Mobile',    # Chase account credits for payments
            'Online Banking payment to CRD 7688'
        ])
    }
}