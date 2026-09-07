# inventory_analysis_v2_two_pointer.py
# OPTIMIZATION 2: Two-Pointer Algorithm
# Sort products once, then use efficient O(n²) scanning instead of brute force
# This is much faster because it exploits sorted order to skip impossible pairs

def find_product_combinations(products, target_price, price_margin=10):
    """
    Find all pairs of products where the combined price is within
    the target_price ± price_margin range.
    
    OPTIMIZATION: Two-Pointer Algorithm
    - Sort products by price once: O(n log n)
    - For each product, use two pointers to find valid pairs: O(n)
    - When sum is too low, move left pointer forward (need higher price)
    - When sum is too high, move right pointer backward (need lower price)
    - When sum is in range, record it
    
    Total complexity: O(n log n) + O(n²) = O(n²) with much smaller constants
    
    Args:
        products: List of dictionaries with 'id', 'name', and 'price' keys
        target_price: The ideal combined price
        price_margin: Acceptable deviation from the target price

    Returns:
        List of dictionaries with product pairs and their combined price
    """
    # Sort products by price once (O(n log n))
    sorted_products = sorted(products, key=lambda p: p['price'])
    results = []
    
    for i in range(len(sorted_products)):
        if i % 100 == 0:
            print(f"Processing product {i+1} of {len(sorted_products)}")
        
        # Two-pointer approach: start at i+1 and end
        left = i + 1
        right = len(sorted_products) - 1
        
        while left <= right:
            product1 = sorted_products[i]
            product2 = sorted_products[left]
            combined_price = product1['price'] + product2['price']
            
            # If sum is too small, we need a higher price on the right
            if combined_price < target_price - price_margin:
                left += 1
            # If sum is too large, we need a lower price on the left
            elif combined_price > target_price + price_margin:
                right -= 1
            # Sum is in range!
            else:
                product2 = sorted_products[left]
                pair = {
                    'product1': product1,
                    'product2': product2,
                    'combined_price': combined_price,
                    'price_difference': abs(target_price - combined_price)
                }
                results.append(pair)
                left += 1  # Continue searching for more matches

    # Sort by price difference from target
    results.sort(key=lambda x: x['price_difference'])
    return results

# Example usage
if __name__ == "__main__":
    import time
    import random

    # Generate a large list of products
    print("Generating Product List")
    product_list = []
    for i in range(5000):
        product_list.append({
            'id': i,
            'name': f'Product {i}',
            'price': random.randint(5, 500)
        })

    # Measure execution time
    print(f"Finding product combinations for {len(product_list)} products")
    start_time = time.time()
    combinations = find_product_combinations(product_list, 500, 50)
    end_time = time.time()

    print(f"Found {len(combinations)} product combinations")
    print(f"Execution time: {end_time - start_time:.2f} seconds")
    print(f"\nTop 5 best matches:")
    for i, combo in enumerate(combinations[:5]):
        print(f"  {i+1}. {combo['product1']['name']} (${combo['product1']['price']}) + {combo['product2']['name']} (${combo['product2']['price']}) = ${combo['combined_price']}")
