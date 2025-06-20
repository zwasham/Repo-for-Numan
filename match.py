# Import Packages

# Replace Amazon transactions in the Chase data with the associated individual product purchases from the 
# Amazon data.
for order in amazon_data_chase['Date'].unique():
    debug(f'Order = {order}')
    
    # Define a DataFrame containing all of the product purchases in the order.
    all_order_rows = amazon_data_chase[amazon_data_chase['Date'] == order].copy()    # The copy method ensures that all_order_rows is a distinct DataFrame, not merely a view.
    debug(f'all_order_rows:\n{all_order_rows[['Date', 'Amount']]}')
    
    # Gather the indices of all Amazon transactions in the Chase data with a date equal to or one day after
    # order.date().
    date_match_indices = []
    date_match_indices_to_remove = []    # When the program identifies a Chase transaction with a matching Amount while looping through date_match_indices, it will store the index of the matching transaction in date_match_indices_to_remove for removal from date_match_indices after the completion of the loop that is iterating through date_match_indices. Removing matched indices during the loop rather than after the completion of the loop would cause the loop to skip elements of the iterable (because such removal would change the positions of the iterable elements without any change to the internal for loop position counter).
    for index in e_chase_cc_amazon.index:
        chase_date = e_chase_cc_amazon.loc[index, 'Date'].date()    # The date function converts these objects from pandas Timestamps (which include time of day) to PSL dates (which do not).
        order_date = order.date()

        # If the date of any transaction in the Chase data is equal to or up to two days greater than order_date,
        # then append the index of that transaction to date_match_indices.
        if chase_date in [order_date, order_date + timedelta(days = 1), order_date + timedelta(days = 2)]:
            date_match_indices.append(index)
    
    # If no transaction in the Chase data has a matching date, then append the individual product purchase data
    # to unmatched_orders and proceed to the next order.
    if len(date_match_indices) == 0:
        debug(f'No matching Chase transactions for order {order}.')
        unmatched_orders.append(all_order_rows)
        debug(f'Appending unmatched order:\n{all_order_rows[['Date', 'Amount']]}\nto unmatched_orders.')
        continue
    
    debug(f'Matching Chase transactions for order {order}:\n{date_match_indices}')
    debug(f'Number of matching Chase transactions: {len(date_match_indices)}')

    # Attempt to match product purchase rows in the Amazon data to transactions in the Chase data.
    all_order_rows_matched = False
    
    # For each Chase transaction with a date match, try matching the 'Amount' value of the whole Amazon
    # order.
    total_order_cost = all_order_rows['Amount'].sum()
    debug(f'Total order cost: {total_order_cost}')
    for chase_index in date_match_indices:
        chase_amount = e_chase_cc.loc[chase_index, 'Amount']
        debug(f'Chase Amount: {chase_amount}')
        if chase_amount == total_order_cost:
            debug(f'Chase Amount matches total order cost for order {order}.')
            all_order_rows_matched = True

            # Reset the index of all_order_rows to prepare for concatenation.
            new_starting_index = e_chase_cc.index.max() + 1
            debug(f'Final index of e_chase_cc: {e_chase_cc.index.max()}')
            debug(f'New starting index for all_order_rows: {new_starting_index}')
            all_order_rows.index = range(new_starting_index, new_starting_index + len(all_order_rows))
            debug(f'Updated all_order_rows index:\n{all_order_rows.index}')

            # Add all_order_rows to e_chase_cc.
            e_chase_cc = pd.concat([e_chase_cc, all_order_rows], join = 'outer')    # In a future iteration, I could gather matched rows in a list and add them to e_chase_cc at the end of the order loop with a single concat function call.
            debug(f'Added all_order_rows to e_chase_cc:\n{e_chase_cc.tail(len(all_order_rows))[['Date', 'Amount']]}')

            # Drop the matched Chase transaction from both Chase DataFrames.
            e_chase_cc = e_chase_cc.drop(index = chase_index)    # The drop method never returns a view, so calling the copy method is unnecessary.
            debug(f'Dropped matched Chase transaction (index {chase_index}) from e_chase_cc.')
            e_chase_cc_amazon = e_chase_cc_amazon.drop(index = chase_index)
            debug(f'Dropped matched Chase transaction (index {chase_index}) from e_chase_cc_amazon.')

            # Break out of the chase_index loop.
            debug(f'Breaking out of the chase_index loop because the whole order has been matched.')
            break

    # If the prior loop matched the whole Amazon order to a Chase transaction, then proceed to the 
    # next order.
    if all_order_rows_matched:
        debug(f'All product purchases in order {order} have been matched to a Chase transaction. Proceeding to the next order.')
        continue

    # If the Amazon order contains only one product and the prior for loop did not find a match, then 
    # there is no match. Add the unmatched row to unmatched_orders and continue to the next index.
    elif len(all_order_rows) == 1:
        debug(f'Order {order} contains only one product purchase which has not been matched to a Chase transaction. Adding unmatched row to unmatched_orders.')
        unmatched_orders.append(all_order_rows)
        debug(f'unmatched_orders:\n{unmatched_orders[-1][['Date', 'Amount']]}')
        debug(f'Proceeding to the next order.')
        continue

    # Try matching the 'Amount' value of each individual product in the Amazon order.
    debug(f'Attempting to match individual product purchases in order {order} to Chase transactions.')
    product_purchase_indices_to_remove = []
    changes_made = False
    for chase_index in date_match_indices:
        debug(f'Chase Index: {chase_index}')
        for product_purchase_index in all_order_rows.index:
            
            # Extract the product purchase row as a DataFrame (for easier concatenation).
            product_purchase = all_order_rows.loc[[product_purchase_index]].copy()
            debug(f'Product Purchase: {product_purchase[['Date', 'Amount']]}')

            # Define Amount variables for comparison.
            chase_amount = e_chase_cc.loc[chase_index, 'Amount']
            debug(f'Chase Amount: {chase_amount}')
            product_purchase_amount = all_order_rows.loc[product_purchase_index, 'Amount']
            debug(f'Product Purchase Amount: {product_purchase_amount}')

            if chase_amount == product_purchase_amount:
                debug(f'Chase Amount matches Product Purchase Amount.')
                changes_made = True
                debug(f'The value of changes_made has been set to True.')

                # Update the index of product_purchase to prepare for concatenation.
                new_index = e_chase_cc.index.max() + 1
                debug(f'Final index of e_chase_cc: {e_chase_cc.index.max()}')
                debug(f'New index for product_purchase: {new_index}')
                product_purchase.index = [new_index]
                debug(f'Updated product_purchase index:\n{product_purchase.index}')

                # Add product_purchase to e_chase_cc.
                e_chase_cc = pd.concat([e_chase_cc, product_purchase], join = 'outer')
                debug(f'Added product_purchase to e_chase_cc:\n{e_chase_cc.tail(1)[['Date', 'Amount']]}')

                # Drop the matched Chase transaction from both Chase DataFrames.
                e_chase_cc = e_chase_cc.drop(index = chase_index)
                debug(f'Dropped matched Chase transaction (index {chase_index}) from e_chase_cc.')
                e_chase_cc_amazon = e_chase_cc_amazon.drop(index = chase_index)
                debug(f'Dropped matched Chase transaction (index {chase_index}) from e_chase_cc_amazon.')

                # Append the index of the matched product_purchase row to product_purchase_indices_to_remove
                # (in case dropping the row from all_order_rows within this loop would break the loop, which
                # I have not tested).
                # Update: I just tested the above case, and it does not break the loop. For simplicity, I 
                # should revert to dropping the product purchase row from all_order_rows inside the loop. 
                product_purchase_indices_to_remove.append(product_purchase_index)
                debug(f'Product purchase index {product_purchase_index} has been appended to product_purchase_indices_to_remove.')

                # Append the matched index to date_match_indices_to_remove.
                date_match_indices_to_remove.append(chase_index)
                debug(f'Chase index {chase_index} has been appended to date_match_indices_to_remove.')
                debug(f'Breaking out of the product_purchase_index loop.')

                # Break out of the product_purchase_index loop.
                break
        
        # Remove all matched product purchase rows from all_order_rows.
        debug(f'Removing matched product purchase rows from all_order_rows.')
        for i in product_purchase_indices_to_remove:    # Revert to the prior solution.
            all_order_rows = all_order_rows.drop(index = i)    
        debug(f'len(all_order_rows):\n{len(all_order_rows)}')

        # Clear the list for the next iteration of the chase_index loop.
        product_purchase_indices_to_remove.clear()    
        debug(f'Cleared product_purchase_indices_to_remove.')

        # If the most recent iteration matched the final product purchase in all_order_rows, then flag 
        # all_order_rows_matched and break out of the chase_index loop.
        if len(all_order_rows) == 0:
            debug(f'All product purchases in order {order} have been matched to Chase transactions.')
            all_order_rows_matched = True
            debug(f'The value of all_order_rows_matched has been set to True.')
            debug(f'Breaking out of the chase_index loop.')
            break
    
        # If the prior loop matched at least one product purchase in the order, then test the combined 
        # Amount of all remaining product purchases in all_order_rows against the Amount of each Chase 
        # transaction.
        elif changes_made:
            debug(f'Changes have been made. Testing the combined Amount of all remaining product purchases in all_order_rows against the Amount of each Chase transaction.')
            debug(f'len(all_order_rows): {len(all_order_rows)}')
            total_remaining_order_amount = all_order_rows['Amount'].sum()
            debug(f'total_remaining_order_amount: {total_remaining_order_amount}')
            for chase_index_2 in date_match_indices:
                debug(f'chase_index_2: {chase_index_2}')

                # Look for chase_index_2 in e_chase_cc.index. If it is there, then assign the amount
                # of the corresponding row to chase_amount_2. If it is not, then the corresponding row
                # has been removed from the DataFrame because it was matched. In this case, proceed to
                # the next index.
                if chase_index_2 in e_chase_cc.index:
                    debug(f'chase_index_2 is in e_chase_cc.index.')
                    chase_amount_2 = e_chase_cc.loc[chase_index_2, 'Amount']    
                    debug(f'chase_amount_2: {chase_amount_2}')
                else:
                    debug(f'chase_index_2 is not in e_chase_cc.index. Proceed to the next index in date_match_indices.')
                    continue

                # If there is a match, update the indicator variable and modify the data accordingly.
                if chase_amount_2 == total_remaining_order_amount:
                    debug(f'chase_amount_2 == total_remaining_order_amount')
                    all_order_rows_matched = True
                    debug(f'The value of all_order_rows_matched has been set to True.')

                    # Add all product purchase rows remaining in all_order_rows to e_chase_cc.
                    debug(f'Adding all remaining product purchase rows in all_order_rows to e_chase_cc.')
                    for product_purchase_index in all_order_rows.index:
                        product_df = all_order_rows.loc[[product_purchase_index]].copy()
                        debug(f'product_df:\n{product_df[['Date', 'Amount']]}')
                        debug(f'Final index of e_chase_cc: {e_chase_cc.index.max()}')
                        new_index = e_chase_cc.index.max() + 1
                        debug(f'New index for product_df: {new_index}')
                        product_df.index = [new_index]
                        e_chase_cc = pd.concat([e_chase_cc, product_df], join = 'outer')
                        debug(f'Added product_df to e_chase_cc:\n{e_chase_cc.tail(1)[['Date', 'Amount']]}')
                    debug(f'All remaining product purchase rows have been added to e_chase_cc.')

                    # Clear all rows from all_order_rows.
                    debug(f'Clearing all rows from all_order_rows.')
                    all_order_rows = all_order_rows.drop(index = all_order_rows.index)
                    debug(f'len(all_order_rows): {len(all_order_rows)}')

                    # Drop the matched Chase transaction from both Chase DataFrames.
                    e_chase_cc = e_chase_cc.drop(index = chase_index_2)
                    debug(f'Dropped matched Chase transaction (index {chase_index_2}) from e_chase_cc.')
                    e_chase_cc_amazon = e_chase_cc_amazon.drop(index = chase_index_2)
                    debug(f'Dropped matched Chase transaction (index {chase_index_2}) from e_chase_cc_amazon.')

                    # Break out of the chase_index_2 loop.
                    debug(f'Breaking out of the chase_index_2 loop because the whole order has been matched.')
                    break
        
        # If the prior loop matched the the remaining product purchases in all_order_rows, then break 
        # out of the chase_index loop.
        if all_order_rows_matched:
            debug(f'Breaking out of the chase_index loop because all product purchases in order {order} have been matched to Chase transactions.')
            break

    # If the prior loop matched all product purchases in the order, then proceed to the next Amazon order.
    if all_order_rows_matched:
        debug(f'All product purchases in order {order} have been matched to Chase transactions. Proceeding to the next order.')
        continue

    # Otherwise...
    else:
        debug(f'Not all product purchases in order {order} have been matched to Chase transactions. Proceeding to removing the indices of matched Chase transactions from date_match_indices.')
        # remove any matched indices from date_match_indices and clear date_match_indices_to_remove, and
        for i in date_match_indices_to_remove:
            debug(f'Removing matched index {i} from date_match_indices.')
            date_match_indices.remove(i)
        debug(f'Removed all matched indices from date_match_indices:\n{date_match_indices}')
        date_match_indices_to_remove.clear()
        debug(f'Cleared date_match_indices_to_remove.')
    
        # ...if the prior loop matched at least one product purchase in the order, then test the combined
        # Amount of all remaining product purchases in all_order_rows against the Amount of each Chase
        # transaction.
        if changes_made:
            debug(f'Changes have been made. Testing the combined Amount of all remaining product purchases in all_order_rows against the Amount of each Chase transaction.')
            total_remaining_order_amount = all_order_rows['Amount'].sum()
            debug(f'total_remaining_order_amount: {total_remaining_order_amount}')
            for chase_index in date_match_indices:
                debug(f'chase_index: {chase_index}')
                chase_amount = e_chase_cc.loc[chase_index, 'Amount']
                debug(f'chase_amount: {chase_amount}')

                # If there is a match, update the indicator variable and modify the data accordingly.
                if chase_amount == total_remaining_order_amount:
                    debug(f'chase_amount == total_remaining_order_amount')
                    all_order_rows_matched = True
                    debug(f'The value of all_order_rows_matched has been set to True.')

                    # Add all product purchase rows remaining in all_order_rows to e_chase_cc.
                    debug(f'Adding all remaining product purchase rows in all_order_rows to e_chase_cc.')
                    for product_purchase_index in all_order_rows.index:
                        product_df = all_order_rows.loc[[product_purchase_index]].copy()
                        debug(f'product_df:\n{product_df[['Date', 'Amount']]}')
                        debug(f'Final index of e_chase_cc: {e_chase_cc.index.max()}')
                        new_index = e_chase_cc.index.max() + 1
                        debug(f'New index for product_df: {new_index}')
                        product_df.index = [new_index]
                        e_chase_cc = pd.concat([e_chase_cc, product_df], join = 'outer')
                        debug(f'Added product_df to e_chase_cc:\n{e_chase_cc.tail(1)[['Date', 'Amount']]}')

                    # Clear all rows from all_order_rows.
                    debug(f'Clearing all rows from all_order_rows.')
                    all_order_rows = all_order_rows.drop(index = all_order_rows.index)
                    debug(f'len(all_order_rows): {len(all_order_rows)}')

                    # Drop the matched Chase transaction from both Chase DataFrames.
                    e_chase_cc = e_chase_cc.drop(index = chase_index)
                    debug(f'Dropped matched Chase transaction (index {chase_index}) from e_chase_cc.')
                    e_chase_cc_amazon = e_chase_cc_amazon.drop(index = chase_index)
                    debug(f'Dropped matched Chase transaction (index {chase_index}) from e_chase_cc_amazon.')

                    # Break out of the chase_index loop.
                    debug(f'Breaking out of the chase_index loop because the whole order has been matched.')
                    break

    # If all_order_rows now contains only one row, then the prior for loop must have matched and added at 
    # least one product purchase from the order but did not find a match for the one remaining product
    # purchase. This would be odd, and I do not expect this to happen, but in this case, there is no match 
    # for the remaining product purchase. 
    # 
    # By this point, I have tested the combined amount of all rows and the amount of each individual row. 
    # If len(all_order_rows) is now two or three, then at least one subset of rows must consist of only one 
    # row. This subset was already tested when the program attempted to match the amounts of individual rows. 
    # I assume that if at least one subset of all_order_rows must contain only one row and no single row 
    # amount matches a Chase transaction, then no other subsets of all_order_rows match a Chase transaction. 
    # This assumption could be wrong, but I do not see how Amazon would charge Emily's Chase credit card for
    # the whole value of one part of an order but not the other(s).
    #
    # Based on the reasoning above, if all_order_rows now contains fewer than four rows, they have no match
    # (unless Amazon did something odd). Therefore, add all remaining rows to unmatched_orders and proceed
    # to the next order.
    if len(all_order_rows) < 4:
        debug(f'len(all_order_rows) < 4 ({len(all_order_rows)}, precisely). There is no match. Adding all remaining rows to unmatched_orders.')
        unmatched_orders.append(all_order_rows)
        debug(f'Appending all_order_rows to unmatched_orders.')
        debug(f'Proceeding to the next order.')
        continue

    # Look for a match between the total Amount of all untested combinations of products and all Chase
    # transactions with a matching date.
    for n in range(len(all_order_rows)):
        debug(f'Start of n loop. n = {n}')
        
        # Define the number of elements in the subset. The smallest subset must contain two rows.
        r = n + 2
        debug(f'r = {r}')

        # If all_order_rows comprises multiple subsets with matching Chase transactions, at least one of those
        # subsets must contain half or fewer of the elements of all_order_rows. Therefore, after confirming
        # that the combined amount of all_order_rows does not match a Chase transaction, each iteration of
        # this loop searches only for the smallest matching subset. If no subset containing half or fewer of
        # the elements of all_order_rows matches a Chase transaction, then no larger subset will match, either
        # (unless Amazon did something odd).
        if r > len(all_order_rows) / 2:
            debug(f'{r} > {len(all_order_rows) / 2}. No matching subset will be found. Breaking out of the n loop and proceeding to the next order.')
            break
        
        # Define a list containing all r-length combinations of the indices of all_order_rows.
        r_length_combinations = [combo for combo in combinations(all_order_rows.index, r)]
        debug(f'r_length_combinations:\n{r_length_combinations}')

        # Initialize a list for storing the product purchase indices of matched transactions (to support
        # cleaning up the r_length_combinations iterable after each pass of the chase_index loop).
        product_purchase_indices_to_remove = []
        
        # Attempt to match the total Amount of each product purchase combination to the Amount of each Chase
        # transaction in date_match_indices.
        debug(f'Attempting to match the total Amount of each product purchase combination to the Amount of each Chase transaction in date_match_indices.')
        for chase_index in date_match_indices:
            debug(f'chase_index: {chase_index}')
            chase_amount = e_chase_cc.loc[chase_index, 'Amount']
            debug(f'chase_amount: {chase_amount}')
            for product_combo in r_length_combinations:
                debug(f'product_combo: {product_combo}')
                combo_amount = all_order_rows.loc[[row for row in product_combo], 'Amount'].sum()
                debug(f'combo_amount: {combo_amount}')
                if chase_amount == combo_amount:
                    debug(f'chase_amount == combo_amount')
                
                    # Add all product purchase rows (as DataFrames) from product_combo to e_chase_cc (with new 
                    # indices) and drop all product purchase rows from all_order_rows.
                    for product_purchase_index in product_combo:
                        debug(f'product_purchase_index: {product_purchase_index}')
                        product_df = all_order_rows.loc[[product_purchase_index]].copy()
                        debug(f'product_df:\n{product_df[['Date', 'Amount']]}')
                        debug(f'Final index of e_chase_cc: {e_chase_cc.index.max()}')
                        new_index = e_chase_cc.index.max() + 1
                        debug(f'New index for product_df: {new_index}')
                        product_df.index = [new_index]
                        e_chase_cc = pd.concat([e_chase_cc, product_df], join = 'outer')
                        debug(f'Added product_df to e_chase_cc:\n{e_chase_cc.tail(1)[['Date', 'Amount']]}')
                        all_order_rows = all_order_rows.drop(index = product_purchase_index)
                        debug(f'Dropped product purchase index {product_purchase_index} from all_order_rows.')
                    debug(f'All product purchase rows in product_combo have been added to e_chase_cc and dropped from all_order_rows.')

                    # Drop the matched Chase transaction from both Chase DataFrames.
                    e_chase_cc = e_chase_cc.drop(index = chase_index)
                    debug(f'Dropped matched Chase transaction (index {chase_index}) from e_chase_cc.')
                    e_chase_cc_amazon = e_chase_cc_amazon.drop(index = chase_index)
                    debug(f'Dropped matched Chase transaction (index {chase_index}) from e_chase_cc_amazon.')

                    # If the program has matched all product purchases in the order, break out of the
                    # product_combo loop. A subsequent check will break out of the chase_index loop.
                    if len(all_order_rows) == 0:
                        debug(f'All product purchases in order {order} have been matched to Chase transactions.')
                        all_order_rows_matched = True
                        debug(f'The value of all_order_rows_matched has been set to True.')
                        debug(f'Breaking out of the product_combo loop.')
                        break

                    # Otherwise, prepare to clean up the loop iterators by appending the matched Chase index 
                    # to date_match_indices_to_remove and appending the matched product purchase indices to
                    # product_purchase_indices_to_remove.
                    else:
                        debug(f'Not all product purchases in order {order} have been matched to Chase transactions. Preparing to clean up the loop iterators.')
                        date_match_indices_to_remove.append(chase_index)                       
                        debug(f'Chase index {chase_index} has been appended to date_match_indices_to_remove.')
                        for i in product_combo:
                            debug(f'Appending product purchase index {i} to product_purchase_indices_to_remove.')
                            product_purchase_indices_to_remove.append(i)
                    
                    # Compare the combined Amount of all remaining rows in all_order_rows to each remaining
                    # Chase index.
                    debug(f'Comparing the combined Amount of all remaining rows in all_order_rows to each remaining Chase index.')
                    total_remaining_order_amount = all_order_rows['Amount'].sum()
                    debug(f'total_remaining_order_amount: {total_remaining_order_amount}')
                    for chase_index_2 in date_match_indices:    # Because I currently do not use chase_index after this nested loop, using a new variable name is not strictly necessary. However, doing so is harmless and may prevent an error if I change the program in the future.
                        debug(f'chase_index_2: {chase_index_2}')

                        # Look for chase_index_2 in e_chase_cc.index. If it is there, then assign the amount
                        # of the corresponding row to chase_amount_2. If it is not, then the corresponding row
                        # has been removed from the DataFrame because it was matched. In this case, proceed to
                        # the next index.
                        if chase_index_2 in e_chase_cc.index:
                            debug(f'chase_index_2 is in e_chase_cc.index.')
                            chase_amount_2 = e_chase_cc.loc[chase_index_2, 'Amount']
                            debug(f'chase_amount_2: {chase_amount_2}')
                        else:
                            debug(f'chase_index_2 is not in e_chase_cc.index. Proceed to the next index in date_match_indices.')
                            continue
                        
                        # If there is a match, update the indicator variable and modify the data accordingly.
                        if chase_amount_2 == total_remaining_order_amount:
                            debug(f'chase_amount_2 == total_remaining_order_amount')
                            all_order_rows_matched = True
                            debug(f'The value of all_order_rows_matched has been set to True.')
                            
                            # Add all product purchase rows remaining in all_order_rows to e_chase_cc.
                            debug(f'Adding all remaining product purchase rows in all_order_rows to e_chase_cc.')
                            for product_purchase_index in all_order_rows.index:
                                debug(f'product_purchase_index: {product_purchase_index}')
                                product_df = all_order_rows.loc[[product_purchase_index]].copy()
                                debug(f'product_df:\n{product_df[['Date', 'Amount']]}')
                                debug(f'Final index of e_chase_cc: {e_chase_cc.index.max()}')
                                new_index = e_chase_cc.index.max() + 1
                                debug(f'New index for product_df: {new_index}')
                                product_df.index = [new_index]
                                e_chase_cc = pd.concat([e_chase_cc, product_df], join = 'outer')
                                debug(f'Added product_df to e_chase_cc:\n{e_chase_cc.tail(1)[['Date', 'Amount']]}')

                            # Drop all rows from all_order_rows.
                            debug(f'Clearing all rows from all_order_rows.')
                            all_order_rows = all_order_rows.drop(index = all_order_rows.index)
                            debug(f'len(all_order_rows): {len(all_order_rows)}')

                            # Drop the matched Chase transaction from both Chase DataFrames.
                            e_chase_cc = e_chase_cc.drop(index = chase_index_2)
                            debug(f'Dropped matched Chase transaction (index {chase_index_2}) from e_chase_cc.')
                            e_chase_cc_amazon = e_chase_cc_amazon.drop(index = chase_index_2)
                            debug(f'Dropped matched Chase transaction (index {chase_index_2}) from e_chase_cc_amazon.')
                            
                            # Since the whole order has been matched, there is no need to clean up the loop 
                            # iterators. Break out of the chase_index_2 loop.
                            debug(f'Breaking out of the chase_index_2 loop because the whole order has been matched.')
                            break

                    # Break out of the product_combo loop.
                    debug(f'Breaking out of the product_combo loop because the whole order has been matched.')
                    break

            # If all_order_rows_matched == True, break out of the chase_index loop.
            if all_order_rows_matched:
                debug(f'All product purchases in order {order} have been matched to Chase transactions. Breaking out of the chase_index loop.')
                break

            # If len(all_order_rows) < 4, then there is no match (unless len(all_order_rows) == 3 and Amazon 
            # did something odd). Break out of the chase_index loop. The final line of the order loop will
            # add the remaining rows in all_order_rows to unmatched_orders.
            if len(all_order_rows) < 4:
                debug(f'len(all_order_rows) < 4 ({len(all_order_rows)}, precisely). There is no match. Breaking out of the chase_index loop.')
                break

            # Before the next pass of the chase_index loop, clean up the r_length_combinations iterator by 
            # removing all combinations containing any of the matched rows in
            # product_purchase_indices_to_remove. Then, clear product_purchase_indices_to_remove.
            debug(f'Cleaning up r_length_combinations by removing all combinations containing any of the matched rows in product_purchase_indices_to_remove.')
            for i in product_purchase_indices_to_remove:
                debug(f'Removing product purchase index {i} from r_length_combinations.')
                for c in r_length_combinations:
                    debug(f'Checking combination {c} for product purchase index {i}.')
                    if i in c:
                        debug(f'Product purchase index {i} is in combination {c}. Removing combination {c} from r_length_combinations.')
                        r_length_combinations.remove(c)
            debug(f'Updated r_length_combinations:\n{r_length_combinations}')
            product_purchase_indices_to_remove.clear()
            debug(f'Cleared product_purchase_indices_to_remove.')

        # If all_order_rows_matched == True, break out of the n loop.
        if all_order_rows_matched:
            debug(f'All product purchases in order {order} have been matched to Chase transactions. Breaking out of the n loop.')
            break

        # If len(all_order_rows) < 4, break out of the n loop.
        if len(all_order_rows) < 4:
            debug(f'len(all_order_rows) < 4 ({len(all_order_rows)}, precisely). There is no match. Breaking out of the n loop.')
            break

        # Clean up the date_match_indices iterator before the next pass of the n loop by removing any elements
        # in date_match_indices_to_remove. Then, clear date_match_indices_to_remove.
        debug(f'Cleaning up date_match_indices by removing all matched indices in date_match_indices_to_remove.')
        for i in date_match_indices_to_remove:
            debug(f'Removing matched index {i} from date_match_indices.')
            date_match_indices.remove(i)

    # If, at this point, len(all_order_rows) > 0, then there is no match for the remaining rows. Therefore, 
    # append all remaining rows to unmatched_orders.
    if len(all_order_rows) > 0:
        debug(f'len(all_order_rows) > 0 ({len(all_order_rows)}, precisely). There is no match for the remaining rows. Appending all remaining rows to unmatched_orders.')
        unmatched_orders.append(all_order_rows)
        debug(f'Appended all_order_rows to unmatched_orders.')

# Compile the elements of unmatched_orders into a DataFrame and export it as a CSV for review.
debug(f'Compiling unmatched_orders into a DataFrame.')
unmatched_orders = pd.concat(unmatched_orders, ignore_index = True)
debug(f'Exporting unmatched_orders to CSV.')
unmatched_orders.to_csv(f'Data/3. Final/{TODAY} Unmatched Amazon Orders.csv', index = False)
