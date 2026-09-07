# inventory_analysis_v1_set_optimization.py
# OPTIMIZATION 1: Use Set for O(1) Duplicate Checks
# Instead of scanning results list (O(n)), use a set to track seen pairs (O(1))
# Also skips redundant pair checks by only iterating j > i

def find_product_combinations(products, target_price, price_margin=10):
    """
    Find all pairs of products where the combined price is within
    the target_price ± price_margin range.
    
    OPTIMIZATION: 
    - Track seen pairs in a set for O(1) lookup instead of O(n) list scan
    - Only check j > i to avoid duplicate pairs (A,B) and (B,A)
    
    Args:
        products: List of dictionaries with 'id', 'name', and 'price' keys
        target_price: The ideal combined price
        price_margin: Acceptable deviation from the target price

    Returns:
        List of dictionaries with product pairs and their combined price
    """
    results = []
    seen_pairs = set()  # Track seen pairs for O(1) lookup
    
    # For each possible pair of products
    for i in range(len(products)):
        if i % 100 == 0:
            print(f"Processing product {i+1} of {len(products)}")
        
        # Only check products AFTER current one (eliminate redundant pairs)
        for j in range(i + 1, len(products)):
            product1 = products[i]
            product2 = products[j]

            # Calculate combined price
            combined_price = product1['price'] + product2['price']

            # Check if the combined price is within the target range
            if (target_price - price_margin) <= combined_price <= (target_price + price_margin):
                # Use set for O(1) lookup instead of any() list scan
                pair_key = (product1['id'], product2['id'])
                if pair_key not in seen_pairs:
                    seen_pairs.add(pair_key)
                    
                    pair = {
                        'product1': product1,
                        'product2': product2,
                        'combined_price': combined_price,
                        'price_difference': abs(target_price - combined_price)
                    }
                    results.append(pair)

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
