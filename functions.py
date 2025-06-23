# Import packages.
from constants import *
from classes import *
from decimal import Decimal
import pandas as pd
from matplotlib import pyplot as plt, set_loglevel
set_loglevel("WARNING")    # Suppress matplotlib debug messages.
from tqdm.auto import tqdm


# Define high-level functions.

def update_columns(df, spender, account, *, columns_to_drop: list = None, columns_to_rename: dict = None, do_not_initialize: list = None) -> pd.DataFrame:
    df = drop_columns(df, columns_to_drop)
    df = rename_columns(df, columns_to_rename)
    df = set_column_data_types(df)
    df = initialize_new_columns(df, spender, account, do_not_initialize)
    return df

def label_rows(df, data_type: 'payment' | 'product'):
    if data_type == 'payment': label_payment_data(df)
    elif data_type == 'product' : label_product_data(df)
    else: print("'data_type' must be 'payment' or 'product'.")

# def convert_chase_labels

def display_charts(df, instructions: list[dict[str, dict[str, str]]]):    
    for chart in instructions:
        for chart_type, kwargs in chart.items():
            if chart_type == 'pie': display_pie_chart(df, **kwargs)    # Could polymorphism make this function more easily extendable? Perhaps I could create an [abstract base class? Protocol?] named 'Chart' with [nominally or structurally polymorphic] children like 'Pie' and 'Bar', and then perhaps I could design this function to receive any child, including child types that I create in the future.
            if chart_type == 'bar': display_bar_chart(df, **kwargs)


# Define helper functions for update_columns.

def drop_columns(df, columns_to_drop):
    if columns_to_drop:
        for column in columns_to_drop:
            if column in df.columns:
                df = df.drop(column, axis = 1)
            else:
                print(f'Warning: {df} does not include a column named {column}. Therefore, no such column was dropped from the DataFrame.')
    return df                         

def rename_columns(df, columns_to_rename):
    if columns_to_rename:
        for old_name, new_name in columns_to_rename.items():
            if old_name in df.columns:
                df = df.rename(columns = {old_name : new_name})
            else:
                print(f'Warning: {df} does not include a column named {old_name}. Therefore, no column name was updated to {new_name}.')
    return df

def set_column_data_types(df):
    df = set_date_column_type(df)
    df = set_amount_column_type(df)
    df = set_description_column_type(df)
    return df

def set_date_column_type(df):
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
    else:
        print(f'Warning: {df} does not include a column named Date. Therefore, no column in this DataFrame was set to the pandas datetime type.')
    return df

def set_amount_column_type(df):
    if 'Amount' in df.columns:
        df = convert_amount_column_to_decimal(df)
    else:
        print(f'Warning: {df} does not include a column named Amount. Therefore, no column in this DataFrame was set to the Decimal type.')
    return df

def convert_amount_column_to_decimal(df):
    df['Amount'] = pd.to_numeric(df['Amount'], errors = 'coerce')    # Process the column with to_numeric to eliminate commas, etc.
    df['Amount'] = df['Amount'].astype(str)    # Converting values into strings eliminates float imprecision which, in rare cases, can cause rounding errors in the following decimal conversion.
    df['Amount'] = df['Amount'].map(convert_value_to_decimal)    # Convert values to the Decimal type to prevent arithmetic errors caused by float imprecision. The map method applies the convert_value_to_decimal function to every value in the Amount column. 
    return df

def convert_value_to_decimal(value):
    return Decimal(value).quantize(Decimal('0.01'))

def set_description_column_type(df):
    if 'Description' in df.columns:
        df['Description'] = df['Description'].astype('string')    # This uses pandas’ newer string dtype instead of Python's built-in str type. The pandas 'string' type supports missing values (<NA>) and vectorized string operations.
    else:
        print(f'Warning: {df} does not include a column named Description. Therefore, no column in this DataFrame was set to the pandas string type.')
    return df

def initialize_new_columns(df, spender, account, do_not_initialize):
    optional_new_columns = define_optional_new_columns(do_not_initialize)
    df = initialize_mandatory_new_columns(df, spender, account)
    df = initialize_optional_new_columns(df, optional_new_columns)
    return df

def define_optional_new_columns(do_not_initialize):
    optional_new_columns = [
        'Vendor',
        'Category',
        'Subcategory',
        'LLM Vendor',
        'LLM Category',
        'Vendor Unclear',
        'Category Unclear'
    ]
    if do_not_initialize:
        optional_new_columns = remove_columns(optional_new_columns, do_not_initialize)
    return optional_new_columns

def remove_columns(optional_new_columns, do_not_initialize):
    for column in do_not_initialize:
            if column in optional_new_columns:
                optional_new_columns.remove(column)
            else:
                print(f'Warning: {column} is not one of the optional new columns.')
    return optional_new_columns

def initialize_mandatory_new_columns(df, spender, account):
    df['Spender'] = spender
    df['Account'] = account
    return df

def initialize_optional_new_columns(df, optional_new_columns):
    for column in optional_new_columns:
        df[column] = ''
    return df


# Define helper functions for label_rows.

def label_payment_data(df):
    for index in tqdm(df.index):
        df = attempt_to_label_with_vendor_dict(df, index)
        if payment_remains_unlabeled(df, index):
            df = generate_payment_labels_with_OpenAI(df, index)
    return df

def label_product_data(df):
    for index in tqdm(df.index):
        df = generate_label_from_product_name(df, index)
    return df

def attempt_to_label_with_vendor_dict(df, index):
    transaction_description = df.loc[index, 'Description']
    vendor_codes = VENDOR_DICT.keys()
    for vendor_code in vendor_codes:
        if vendor_code in transaction_description:
            df = apply_vendor_dict_labels(df, index, vendor_code)
            break
    return df

def apply_vendor_dict_labels(df, index, vendor_code):
    df.loc[index, 'Vendor'] = VENDOR_DICT[vendor_code]['Vendor']
    df.loc[index, 'Category'] = VENDOR_DICT[vendor_code]['Category']
    subcategory_included = 'Subcategory' in VENDOR_DICT[vendor_code].keys()
    if subcategory_included:
        df.loc[index, 'Subcategory'] = VENDOR_DICT[vendor_code]['Subcategory']
    return df

def payment_remains_unlabeled(df, index):
    return df.loc[index, 'Vendor'] == ''

def generate_payment_labels_with_OpenAI(df, index):
    description = df.loc[index, 'Description']
    df = generate_vendor_label_from_description(df, index, description)
    df = generate_category_label_from_description(df, index, description)
    return df

def generate_vendor_label_from_description(df, index, description):
    if vendor_is_clear(description):
        vendor = extract_vendor(description)
        df.loc[index, 'Vendor'] = vendor
        df.loc[index, 'LLM Vendor'] = 1
    else:
        df.loc[index, 'Vendor Unclear'] = 1
    return df

def vendor_is_clear(description):
    system_prompt = 'The user will provide a transaction description that was automatically generated by a financial institution. If the description unambiguously identifies a counterparty, return True. Otherwise, return False.'
    response = prompt('gpt-4.1', description, system_prompt, BooleanResponse)
    return response

def extract_vendor(description):
    system_prompt = 'The user will provide a transaction description that was automatically generated by a financial institution. Identify the transaction counterparty and return their name in title case. Do not return anything except the counterparty name. In no case should the counterparty be Zachary (Zach) Washam, Emily Barlow, or Emily Washam.'    # Update this in the public version.
    response = prompt('gpt-4.1', description, system_prompt)
    return response

def generate_category_label_from_description(df, index, description):
    if category_is_clear(description):
        category = infer_category(description)
        df.loc[index, 'Category'] = category
        df.loc[index, 'LLM Category'] = 1
    else:
        df.loc[index, 'Category Unclear'] = 1
    return df

def category_is_clear(description):
    system_prompt = 'The goal of the user is to automatically categorize a personal financial transaction. Before classifying the transaction, the user wants to determine whether or not the transaction description provides sufficient information to label the transaction category with a reasonable degree of confidence. Sufficient information is defined as either 1) the name of a vendor (e.g. Kroger or GameStop) that is associated with a particular category of personal expense (e.g. Groceries or Entertainment) or 2) other keywords associated with a particular category of personal expense (e.g. a description like, "Zelle payment to Jon for brunch" would be clearly associated with Other Food & Beverage ("Zelle" combined with the phrase "for brunch" indicates that the user paid a friend for a shared meal expense). The transaction description might not include any elements (e.g. vendor names, expense types, or activities) that are associated with a particular expense category; in this case, the category is unclear. The user will provide a transaction description. If the description indicates that the transaction is associated with any particular category of personal expense (including those not mentioned in this prompt), return True. Otherwise, return False.'
    response = prompt('gpt-4.1', description, system_prompt, BooleanResponse)
    return response

def infer_category(description):
    system_prompt = 'The goal of the user is to automatically categorize a personal financial transaction based on a transaction description. The description will contain 1) the name of a vendor (e.g. Kroger or GameStop) that is associated with a particular category of personal expense (e.g. Groceries or Entertainment) or 2) other keywords associated with a particular category of personal expense (e.g. a description like, "Zelle payment to Jon for brunch" would be clearly associated with Other Food & Beverage ("Zelle" combined with the phrase "for brunch" indicates that the user paid a friend for a shared meal expense). The user will provide a transaction description. Limiting the response to one of the options in the supplied JSON schema, return the category of personal expense most closely associated with the description.'
    response = prompt('gpt-4.1', description, system_prompt, CategoryResponse)
    return response

def generate_label_from_product_name(df, index):
    product_name = df.loc[index, 'Description']
    system_prompt = 'The user will provide an Amazon product name. Return the most fitting category from the supplied JSON schema.'
    category = prompt('gpt-4.1', product_name, system_prompt, CategoryResponse)
    df.loc[index, 'Category'] = category
    df.loc[index, 'LLM Category'] = 1
    return df

def prompt(model: str, user_prompt: str, system_prompt: str = None, response_format = None):
    prompt_list = create_prompt_list(user_prompt, system_prompt)
    model_response = generate_response(model, prompt_list, response_format)
    return model_response

def create_prompt_list(user_prompt, system_prompt):
    if system_prompt == None:
        prompt_list = [
            {'role' : 'user', 'content' : user_prompt}
        ]
    else:
        prompt_list = [
                {'role' : 'system', 'content' : system_prompt},
                {'role' : 'user', 'content' : user_prompt}
        ]
    return prompt_list

def generate_response(model, prompt_list, response_format):
    if response_format == None:
        model_response = generate_normal_response(model, prompt_list)
    else:
        model_response = generate_structured_response(model, prompt_list, response_format)
    return model_response

def generate_normal_response(model, prompt_list):
    whole_response = client.chat.completions.create(
        model = model,
        messages = prompt_list
    )
    unpacked_response = whole_response.choices[0].message.content
    return unpacked_response

def generate_structured_response(model, prompt_list, response_format):
    whole_response = client.beta.chat.completions.parse(
        model = model,
        messages = prompt_list,
        response_format = response_format
    )
    unpacked_response = whole_response.choices[0].message.parsed.response    # The final .response is the consistently-named variable defined in both JSON schemata. To be compatible with this function, additional schemata must use the 'response' variable name.
    return unpacked_response

# !!!
# REFACTOR THIS FUNCTION
# !!!

def update_chase_categories(chase_df):
    for transaction in chase_df.index:
        for old_category in CHASE_CATEGORY_DICT.keys():
            if transaction_category_is_old(chase_df, transaction, old_category):
                chase_df = update_transaction_category(chase_df, transaction, old_category)
                break
    return chase_df

def transaction_category_is_old(chase_df, transaction, old_category):
    chase_df.loc[transaction, 'Category'] == old_category

def update_transaction_category(chase_df, transaction, old_category):
    chase_df.loc[transaction, 'Category'] = CHASE_CATEGORY_DICT[old_category]['New Category']
    chase_df.loc[transaction, 'Subcategory'] = CHASE_CATEGORY_DICT[old_category]['New Subcategory']
    return chase_df

# Define helper functions for display_charts.

def display_pie_chart(df, grouping):
    prepared_data, removals = prepare_chart_data(df, grouping)
    prepare_pie_chart_visual_components(prepared_data, grouping)
    plt.show()
    print_removal_message(removals)

def display_bar_chart(df, grouping, title):
    prepared_data, removals = prepare_chart_data(df, grouping)
    prepare_bar_chart_visual_components(prepared_data, grouping)
    plt.show()
    print_removal_message(removals)

def unpack_instructions(instructions):   ######INCOMPLETE######
    for chart_type
    pie_grouping = instructions['pie']['grouping']
    pie_title = instructions['pie']['title']
    bar_grouping = instructions['bar']['grouping']
    bar_title = instructions['bar']['title']

def prepare_chart_data(df, grouping):
    data = df.copy()
    data = data.groupby(grouping)['Amount'].sum()
    data = data.sort_values(ascending = False)
    prepared_data, removals = regulate_values(data)
    return prepared_data, removals

def regulate_values(data):
    data, removals = remove_positive_categories(data)    # Positive categories represent net income, which charts cannot display alongside expenses.
    data = data.astype(float)    # Change values from Decimal to float to accomodate ax.pie.
    data = -data    # Change signs from negative to positive to accomodate ax.pie.
    return data, removals

def remove_positive_categories(data):
    removals = []
    for category in data.index:
        value = data[category]
        if value > 0:
            removals.append([category, value])
            data = data.drop(category)
    return data, removals

def prepare_pie_chart_visual_components(data, grouping):
    fig, ax = plt.subplots()
    wedges, texts, autotexts = ax.pie(
        data,
        labels = data.index,
        autopct = make_autopct_function(data),
        startangle = 90
    )
    ax.axis('equal')    # This normalizes the x and y scales so that the resulting chart is circular, not elliptical.
    ax.set_title(f'Net Spending by {grouping.title()}')

def print_removal_message(removals):
    if len(removals) > 0:
        print('The data records income in the following categories:')
        for category, value in removals:
            print(f'{category}: ${value}')

# Define a function that creates label formatting functions to pass to the Matplotlib pie chart method.
def make_autopct_function(grouped_df):
    def autopct(wedge_percentage):
        total_dollar_value = grouped_df.sum()
        wedge_dollar_value = (wedge_percentage / 100) * total_dollar_value 
        return f'${wedge_dollar_value:,.2f}\n({wedge_percentage:.1f}%)'
    return autopct

def prepare_bar_chart_visual_components(data, grouping):
    fig, ax = plt.subplots()
    data.plot(kind='barh', ax=ax)
    ax.set_title(f'Net Spending by {grouping.title()}')
    ax.set_xlabel(f'{title} ($)')
